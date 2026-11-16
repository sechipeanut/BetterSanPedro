#!/usr/bin/env python3
"""
Extract one LGU's fiscal data from BLGF spreadsheets into the JSON files the
portal reads:

  src/data/transparency/sre.json   quarterly Statement of Receipts and Expenditures
  src/data/statistics/ari.json     Annual Regular Income and dependencies

Source: Bureau of Local Government Finance, https://blgf.gov.ph/lgu-fiscal-data/
(catalogued at https://data.bettergov.ph/datasets/9). Public domain.

The spreadsheets are labelled "In Php Million" but hold raw pesos; values are
written here in millions, rounded to two decimals. Quarterly SRE figures are
cumulative year-to-date, exactly as BLGF publishes them.

Usage (requires `pip install openpyxl`):

  python3 scripts/extract_blgf_fiscal.py \
      --lgu "San Pedro City" --province Laguna --name "San Pedro" \
      --sre SRE-QTR-2024.xlsx SRE-QTR-2025.xlsx \
      --ari By-LGU-ARI-and-Dependencies-2024.xlsx
"""

import argparse
import json
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
SRE_OUT = ROOT / "src/data/transparency/sre.json"
ARI_OUT = ROOT / "src/data/statistics/ari.json"

# Column positions (0-based, column A unused) shared by every SRE-QTR sheet.
SRE_COLUMN_COUNT = 58
ARI_COLUMN_COUNT = 27


def millions(value) -> float:
    """Pesos to millions of pesos, two decimals, half rounded up."""
    amount = Decimal(str(value or 0)) / Decimal(1_000_000)
    return float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def percent(ratio) -> str:
    amount = Decimal(str(ratio or 0)) * 100
    return f"{amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}%"


def find_row(sheet, lgu: str, province: str):
    """Return the data row for the LGU, matched on province and LGU name."""
    for row in sheet.iter_rows(values_only=True):
        if len(row) < 5 or row[3] is None or row[2] is None:
            continue
        if (
            str(row[3]).strip().lower() == lgu.lower()
            and str(row[2]).strip().lower() == province.lower()
        ):
            return row
    return None


def location(row, name: str) -> dict:
    return {
        "region": str(row[1]).strip(),
        "province": str(row[2]).strip(),
        "lgu_name": name,
        "lgu_type": str(row[4]).strip(),
    }


def sre_period(row, name: str, period: str) -> dict:
    if len(row) < SRE_COLUMN_COUNT:
        sys.exit(f"{period}: expected {SRE_COLUMN_COUNT} columns, got {len(row)}")
    m = [millions(v) if i >= 5 else v for i, v in enumerate(row)]
    return {
        "period": period,
        "location_info": location(row, name),
        "current_operating_income": {
            "local_sources": {
                "tax_revenue": {
                    "real_property_tax": {
                        "general_fund": m[5],
                        "special_education_fund": m[6],
                        "total": m[7],
                    },
                    "tax_on_business": m[8],
                    "other_taxes": m[9],
                    "total_tax_revenue": m[10],
                },
                "non_tax_revenue": {
                    "regulatory_fees": m[11],
                    "service_user_charges": m[12],
                    "receipts_from_economic_enterprises": m[13],
                    "other_receipts": m[14],
                    "total_non_tax_revenue": m[15],
                },
                "total_local_sources": m[16],
            },
            "external_sources": {
                "national_tax_allotment": m[17],
                "other_shares_from_national_tax_collection": m[18],
                "inter_local_transfers": m[19],
                "extraordinary_receipts_grants_donations_aids": m[20],
                "total_external_sources": m[21],
            },
            "total_current_operating_income": m[22],
        },
        "total_current_operating_expenditures": {
            "general_public_services": m[23],
            "social_services": {
                "education_culture_sports_manpower_development": m[24],
                "health_nutrition_population_control": m[25],
                "labor_and_employment": m[26],
                "housing_and_community_development": m[27],
                "social_services_and_social_welfare": m[28],
                "total_social_services": m[29],
            },
            "economic_services": m[30],
            "debt_service_interest_expense": m[31],
            "total_current_operating_expenditures": m[32],
        },
        "net_operating_income_loss_from_current_operations": m[33],
        "non_income_receipts": {
            "capital_investment_receipts": {
                "proceeds_from_sale_of_assets": m[34],
                "proceeds_from_sale_of_debt_securities_of_other_entities": m[35],
                "collection_of_loans_receivables": m[36],
                "total_capital_investment_receipts": m[37],
            },
            "receipts_from_loans_and_borrowings": {
                "acquisition_of_loans": m[38],
                "issuance_of_bonds": m[39],
                "total_receipts_from_loans_and_borrowings": m[40],
            },
            "other_non_income_receipts": m[41],
            "total_non_income_receipts": m[42],
        },
        "non_operating_expenditures": {
            "capital_investment_expenditures": {
                "purchase_construct_of_property_plant_and_equipment": m[43],
                "purchase_of_debt_securities_of_other_entities": m[44],
                "grant_make_loan_to_other_entities": m[45],
                "total_capital_investment_expenditures": m[46],
            },
            "debt_service_principal_cost": {
                "payment_of_loan_amortization": m[47],
                "retirement_redemption_of_bonds_debt_securities": m[48],
                "total_debt_service_principal_cost": m[49],
            },
            "other_non_operating_expenditures": m[50],
            "total_non_operating_expenditures": m[51],
        },
        "fund_summary": {
            "net_increase_decrease_in_funds": m[52],
            "add_cash_balance_beginning": m[53],
            "fund_cash_available": m[54],
            "less_payment_of_prior_years_accounts_payable": m[55],
            "continuing_appropriation": m[56],
            "fund_cash_balance_end": m[57],
        },
    }


def ari_year(row, name: str, year: str) -> dict:
    if len(row) < ARI_COLUMN_COUNT:
        sys.exit(f"ARI {year}: expected {ARI_COLUMN_COUNT} columns, got {len(row)}")
    m = [millions(v) if 5 <= i <= 23 else v for i, v in enumerate(row)]
    return {
        "period": f"FY-{year}",
        "location_info": location(row, name),
        "locally_sourced_revenue": {
            "tax_revenue": {
                "real_property_tax_general_fund": m[5],
                "tax_on_business": m[6],
                "other_taxes": m[7],
                "total_tax_revenue": m[8],
            },
            "non_tax_revenue": {
                "regulatory_fees": m[9],
                "service_user_charges": m[10],
                "receipts_from_economic_enterprises": m[11],
                "total_non_tax_revenue": m[12],
            },
            "total_locally_sourced_revenue": m[13],
        },
        "other_income_sources": {
            "interest_income": m[14],
            "national_tax_allotment": m[15],
        },
        "other_shares_from_national_tax_collection": {
            "share_from_economic_zone": m[16],
            "share_from_evat": m[17],
            "share_from_national_wealth": m[18],
            "share_from_pagcor_pcso_lotto": m[19],
            "share_from_tobacco_excise_tax": m[20],
            "others": m[21],
            "total_other_shares": m[22],
        },
        "summary_indicators": {
            "annual_regular_income": m[23],
            "dependency_rates": {
                "lsr_dependency": percent(row[24]),
                "nta_dependency": percent(row[25]),
                "other_shares_from_national_tax_dependency": percent(row[26]),
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--lgu", required=True, help='LGU NAME as BLGF spells it')
    parser.add_argument("--province", required=True)
    parser.add_argument("--name", help="Display name written to lgu_name")
    parser.add_argument("--sre", nargs="*", default=[], help="SRE-QTR-<year>.xlsx")
    parser.add_argument("--ari", nargs="*", default=[], help="By-LGU-ARI-*.xlsx")
    parser.add_argument("--sre-out", default=str(SRE_OUT))
    parser.add_argument("--ari-out", default=str(ARI_OUT))
    args = parser.parse_args()
    name = args.name or args.lgu

    quarters = []
    for path in args.sre:
        workbook = load_workbook(path, read_only=True, data_only=True)
        for sheet in workbook.worksheets:
            match = re.fullmatch(r"Q([1-4])(\d{4})", sheet.title.strip())
            if not match:
                continue
            period = f"Q{match.group(1)}-{match.group(2)}"
            row = find_row(sheet, args.lgu, args.province)
            if row is None:
                print(f"warning: {args.lgu} not in {period}", file=sys.stderr)
                continue
            quarters.append(sre_period(row, name, period))
    if quarters:
        quarters.sort(key=lambda q: (q["period"][3:], q["period"][:2]))
        Path(args.sre_out).write_text(
            json.dumps(quarters, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"sre: {', '.join(q['period'] for q in quarters)} -> {args.sre_out}")

    years = []
    for path in args.ari:
        workbook = load_workbook(path, read_only=True, data_only=True)
        for sheet in workbook.worksheets:
            match = re.fullmatch(r"ARI (\d{4})", sheet.title.strip())
            if not match:
                continue
            row = find_row(sheet, args.lgu, args.province)
            if row is None:
                print(f"warning: {args.lgu} not in {sheet.title}", file=sys.stderr)
                continue
            years.append(ari_year(row, name, match.group(1)))
    if years:
        years.sort(key=lambda y: y["period"])
        Path(args.ari_out).write_text(
            json.dumps(years, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"ari: {', '.join(y['period'] for y in years)} -> {args.ari_out}")


if __name__ == "__main__":
    main()
