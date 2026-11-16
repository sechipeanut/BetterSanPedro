#!/usr/bin/env python3
"""
Parse the City of San Pedro Citizen's Charter PDF into
src/data/citizens-charter/citizens-charter.json.

The charter follows the ARTA template: every service is a table whose rows are

  Office or Division | Classification | Type of Transaction | Who may avail
  CHECKLIST OF REQUIREMENTS | WHERE TO SECURE        (then one row per item)
  CLIENT STEPS | AGENCY ACTIONS | FEES | PROCESSING TIME | PERSON RESPONSIBLE
  ...step rows..., TOTAL row

with the numbered service title and a short description printed above it.
Tables continue across pages. Internal (G2G-only) services are skipped: the
portal lists services for residents and businesses.

Usage (requires `pip install pdfplumber`):

  python3 scripts/parse_citizens_charter.py path/to/Citizens-Charter.pdf

Then run `npm run merge:services` to rebuild merged-services.json.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "src/data/citizens-charter/citizens-charter.json"

PAGE_MARK = re.compile(r"^\s*[ivxlcdm\d]+\s*\|\s*P\s*a\s*g\s*e\s*$", re.I)
OFFICE_ROW = re.compile(r"^office\b.*(division|:)", re.I)
TITLE_START = re.compile(r"^(\d+)\.\s+(.*)$")
TRANSACTION = re.compile(r"G2[CBG]", re.I)


def clean(text) -> str:
    return re.sub(r"\s+", " ", (text or "").replace(" ", " ")).strip()


def cells(row) -> list[str]:
    return [clean(c) for c in row]


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def read_toc(pdf, first_service_page: int) -> list[str]:
    """Service titles from the "List of Services" pages, longest first."""
    lines: list[str] = []
    for page in pdf.pages[: first_service_page - 1]:
        for line in (page.extract_text() or "").splitlines():
            line = line.strip()
            if line and not PAGE_MARK.match(line):
                lines.append(line)
    titles: list[str] = []
    entry = ""
    for line in lines:
        if TITLE_START.match(line):
            if entry:
                titles.append(entry)
            entry = TITLE_START.match(line).group(2)
        elif entry and not re.fullmatch(r"\d+", line) and not re.search(
            r"(Services|Office|Floor|Unit|Section|Division|Department)\s*(\(.*\))?$", line
        ):
            entry += " " + line
        elif entry:
            titles.append(entry)
            entry = ""
    if entry:
        titles.append(entry)
    titles = [clean(re.sub(r"\s+\d+$", "", t)) for t in titles]
    return sorted({t for t in titles if len(t) > 5}, key=len, reverse=True)


def split_title(block: str, toc: list[str]) -> tuple[str, str, str]:
    """Split the text above a service table into (number, title, description).

    The table of contents gives the exact title when it matches; otherwise the
    title is the numbered paragraph up to the first line that starts the
    description.
    """
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    lines = [ln for ln in lines if not PAGE_MARK.match(ln)]
    start = None
    for i, line in enumerate(lines):
        if TITLE_START.match(line):
            start = i
    if start is None:
        return "", clean(" ".join(lines)), ""
    number, first = TITLE_START.match(lines[start]).groups()
    body = clean(" ".join([first] + lines[start + 1 :]))
    for known in toc:
        if norm(body).startswith(norm(known)):
            # Cut the body where the known title ends, ignoring punctuation.
            target, seen, cut = len(norm(known)), 0, len(body)
            for position, char in enumerate(body):
                if seen == target:
                    cut = position
                    break
                seen += bool(re.match(r"[a-z0-9]", char.lower()))
            while cut < len(body) and body[cut] in ")”\"'":
                cut += 1
            name, remainder = body[:cut].strip(), body[cut:].strip()
            # A shorter title from another office can be a prefix of this one;
            # the description always starts a new sentence.
            if name.count("(") == name.count(")") and (
                not remainder or remainder[0].isupper() or remainder[0].isdigit()
            ):
                return number, name, remainder
    title = [first]
    rest = lines[start + 1 :]
    # A title wraps only when its line runs to the right margin (~70+ chars).
    while rest and len(title[-1]) >= 68 and not re.match(
        r"^(The|This|It|A|An|To|Any|All|Clients?|For)\b", rest[0]
    ):
        title.append(rest.pop(0))
    return number, clean(" ".join(title)), clean(" ".join(rest))


def new_service(office: str, block: str, page: int, toc: list[str]) -> dict:
    number, title, description = split_title(block, toc)
    return {
        "_number": number,
        "_page": page,
        "service_name": title,
        "description": description,
        "office_division": re.sub(r"\s*\([^)]*\)\s*$", "", office).strip(),
        "classification": "",
        "type_of_transaction": "",
        "who_may_avail": "",
        "requirements": [],
        "client_steps": [],
        "_totals": [],
    }


def transaction_codes(text: str) -> list[str]:
    codes = {m.upper() for m in TRANSACTION.findall(text)}
    spelled = re.sub(r"[^a-z]", "", text.lower())
    for word, code in (
        ("tocitizen", "G2C"),
        ("toclient", "G2C"),
        ("tobusiness", "G2B"),
        ("togovernment", "G2G"),
    ):
        if "government" + word in spelled:
            codes.add(code)
    return sorted(codes)


def classification_label(text: str) -> str:
    spelled = text.lower().replace("-", " ")
    found = [
        label
        for label in ("Simple", "Complex", "Highly Technical")
        if label.lower() in spelled
    ]
    return ", ".join(found) or text


def finish(service: dict, office_index: dict, previous_office: str) -> dict | None:
    if classification_label(service["office_division"]) != service["office_division"]:
        # The office cell was left out, so every value sits one row too high.
        service["office_division"], service["classification"], service["type_of_transaction"], service["who_may_avail"] = (
            previous_office,
            service["office_division"],
            service["classification"],
            service["type_of_transaction"],
        )
    # Some entries have the Classification and Type of Transaction values swapped.
    if transaction_codes(service["classification"]) and not transaction_codes(
        service["type_of_transaction"]
    ):
        service["classification"], service["type_of_transaction"] = (
            service["type_of_transaction"],
            service["classification"],
        )
    codes = transaction_codes(service["type_of_transaction"])
    if codes == ["G2G"]:
        return None
    if not service["service_name"]:
        return None

    office = service["office_division"]
    section = office_index.setdefault(office, len(office_index) + 1)
    fees = [t[0] for t in service["_totals"] if t[0]]
    times = [t[1] for t in service["_totals"] if t[1]]

    def unique(values):
        seen = []
        for value in values:
            if value not in seen:
                seen.append(value)
        return seen

    result = {
        "service_number": f"{section}.{service['_number'] or '0'}",
        "service_name": service["service_name"],
        "office_division": office,
        "classification": classification_label(service["classification"]),
        "type_of_transaction": ", ".join(codes) or service["type_of_transaction"],
        "who_may_avail": service["who_may_avail"],
        "requirements": service["requirements"],
        "client_steps": [
            {"step": i + 1, **step} for i, step in enumerate(service["client_steps"])
        ],
        "fees": {"amount": " / ".join(unique(fees)), "description": ""},
        "processing_time": " / ".join(unique(times)),
        "turnaround_time": "",
        "plain_language_name": service["service_name"],
        "source_page": service["_page"],
    }
    if service["description"]:
        result["description"] = service["description"]
    return result


def parse(pdf_path: str) -> list[dict]:
    services: list[dict] = []
    office_index: dict[str, int] = {}
    current: dict | None = None
    mode = ""

    def close():
        nonlocal current
        if current:
            previous_office = services[-1]["office_division"] if services else ""
            done = finish(current, office_index, previous_office)
            if done:
                services.append(done)
        current = None

    with pdfplumber.open(pdf_path) as pdf:
        toc: list[str] | None = None
        for page_number, page in enumerate(pdf.pages, start=1):
            tables = sorted(page.find_tables(), key=lambda t: t.bbox[1])
            previous_bottom = 0
            for table in tables:
                top = max(table.bbox[1], previous_bottom)
                block = ""
                if top > previous_bottom:
                    region = page.crop((0, previous_bottom, page.width, top))
                    block = region.extract_text() or ""
                previous_bottom = table.bbox[3]

                for raw in table.extract():
                    row = cells(raw)
                    filled = [c for c in row if c]
                    if not filled:
                        continue
                    head = row[0]

                    if OFFICE_ROW.match(head):
                        close()
                        if toc is None:
                            toc = read_toc(pdf, page_number)
                        current = new_service(
                            filled[1] if len(filled) > 1 else "", block, page_number, toc
                        )
                        block = ""
                        mode = "header"
                        continue
                    if current is None:
                        continue

                    # Labels are sometimes broken mid-word ("Classificat ion:").
                    label = norm(head)
                    value = " ".join(filled[1:])
                    if label.startswith("classification"):
                        current["classification"] = value
                        mode = "header"
                    elif label.startswith("typeoftransaction"):
                        current["type_of_transaction"] = value
                        mode = "header"
                    elif label.startswith("whomayavail"):
                        current["who_may_avail"] = value
                        mode = "who"
                    elif label.startswith("checklistofrequirement"):
                        mode = "requirements"
                    elif label.startswith("clientstep") or any(
                        norm(c).startswith("agencyaction") for c in row
                    ):
                        mode = "steps"
                    elif mode == "who":
                        current["who_may_avail"] = clean(
                            current["who_may_avail"] + " " + " ".join(filled)
                        )
                    elif mode == "requirements":
                        current["requirements"].append(
                            {
                                "requirement": filled[0],
                                "where_to_secure": filled[-1] if len(filled) > 1 else "",
                            }
                        )
                    elif mode == "steps":
                        total_at = next(
                            (i for i, c in enumerate(row) if c.upper().startswith("TOTAL")), None
                        )
                        if total_at is not None:
                            if len(row) >= 5:
                                # Standard layout: fees in column 3, time in column 4.
                                current["_totals"].append((row[2], row[3]))
                            else:
                                after = [c for c in row[total_at + 1 :] if c]
                                current["_totals"].append(
                                    (after[0] if after else "", after[1] if len(after) > 1 else "")
                                )
                        elif len(filled) == 1:
                            # A spanning row labels a variant of the procedure.
                            current["client_steps"].append({"action": filled[0]})
                        elif not head and current["client_steps"]:
                            # Agency-side rows continue the previous client step.
                            previous = current["client_steps"][-1]
                            padded = row + [""] * 5
                            for key, extra in (
                                ("agency_action", padded[1]),
                                ("fee", padded[2]),
                                ("processing_time", padded[3]),
                                ("person_responsible", padded[4]),
                            ):
                                if extra:
                                    previous[key] = clean(previous.get(key, "") + " " + extra)
                        elif head:
                            step = {"action": head}
                            padded = row + [""] * 5
                            if padded[1]:
                                step["agency_action"] = padded[1]
                            if padded[2]:
                                step["fee"] = padded[2]
                            if padded[3]:
                                step["processing_time"] = padded[3]
                            if padded[4]:
                                step["person_responsible"] = padded[4]
                            current["client_steps"].append(step)
    close()
    return services


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse a Citizen's Charter PDF")
    parser.add_argument("pdf")
    parser.add_argument("--out", default=str(OUTPUT))
    parser.add_argument("--edition", default="", help="e.g. '2025 (1st Edition)'")
    parser.add_argument("--source-url", default="")
    args = parser.parse_args()

    services = parse(args.pdf)
    if not services:
        sys.exit("No services found; is this an ARTA-format charter?")

    data = {
        "meta": {
            "source": "City of San Pedro, Laguna Citizen's Charter",
            "edition": args.edition,
            "source_url": args.source_url,
        },
        "services": services,
    }
    Path(args.out).write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    offices = sorted({s["office_division"] for s in services})
    print(f"{len(services)} services from {len(offices)} offices -> {args.out}")


if __name__ == "__main__":
    main()
