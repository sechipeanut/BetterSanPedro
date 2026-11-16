/**
 * Fetch an LGU's Cities and Municipalities Competitiveness Index (CMCI) scores
 * from the DTI profile pages and write src/data/statistics/cmci.json.
 *
 * Source: https://cmci.dti.gov.ph/lgu-profile.php (Department of Trade and Industry)
 *
 * Usage: node scripts/fetch-cmci.js "San Pedro" [firstYear] [lastYear]
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUTPUT = path.join(ROOT, 'src/data/statistics/cmci.json');

const PILLARS = {
  'Economic Dynamism': [
    'Local Economy Size',
    'Local Economy Growth',
    'Active Establishments in the Locality',
    'Safety Compliant Business',
    'Employment Generation',
    'Cost of Living',
    'Cost of Doing Business',
    'Financial Deepening',
    'Productivity',
    'Presence of Business and Professional Organizations',
  ],
  'Government Efficiency': [
    'Compliance to National Directives',
    'Presence of Investment Promotion Unit',
    'Compliance to ARTA Citizens Charter',
    'Capacity to Generate Local Resource',
    'Capacity of Health Services',
    'Capacity of School Services',
    'Recognition of Performance',
    'Getting Business Permits',
    'Peace and Order',
    'Social Protection',
  ],
  Infrastructure: [
    'Road Network',
    'Distance to Ports',
    'Availability of Basic Utilities',
    'Transportation Vehicles',
    'Education',
    'Health',
    'LGU Investment',
    'Accommodation Capacity',
    'Information Technology Capacity',
    'Financial Technology Capacity',
  ],
  Resiliency: [
    'Land Use Plan',
    'Disaster Risk Reduction Plan',
    'Annual Disaster Drill',
    'Early Warning System',
    'Budget for DRRMP',
    'Local Risk Assessments',
    'Emergency Infrastructure',
    'Utilities',
    'Employed Population',
    'Sanitary System',
  ],
  Innovation: [
    'ICT Plan',
    'Innovation Financing: R&D Expenditures Allotment',
    'ICT Use: E-BPLS Software',
    'Online Payment Facilities',
    'STEM graduates',
    'Intellectual Property Registration',
    'Internet Capability',
    'Availability of Basic Internet Service',
    'Start Up and Innovation Facilities',
    'New Technology',
  ],
};

const escape = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

/** Flatten the page to "|"-separated text so cells can be matched in order. */
function flatten(html) {
  return html
    .replace(/<script[\s\S]*?<\/script>/g, ' ')
    .replace(/<[^>]+>/g, '|')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/\|(\s*\|)+/g, '|')
    .replace(/\s+/g, ' ');
}

/** A cell label is followed by "| rank | suffix | score". */
function scoreAfter(text, label) {
  const match = text.match(
    new RegExp(
      `\\|\\s*${escape(label)}\\s*\\|\\s*\\d*\\s*\\|[a-z]*\\|\\s*([\\d.]+)`,
      'i'
    )
  );
  return match ? Number(match[1]) : null;
}

async function fetchYear(lgu, year) {
  const url = `https://cmci.dti.gov.ph/lgu-profile.php?lgu=${encodeURIComponent(lgu)}&year=${year}`;
  const response = await fetch(url, {
    headers: { 'User-Agent': 'Mozilla/5.0' },
  });
  if (!response.ok) throw new Error(`${year}: HTTP ${response.status}`);
  const html = await response.text();
  const text = flatten(html);
  const overall = html.match(/class="knob"[^>]*value="([\d.]+)"/);

  const names = Object.keys(PILLARS);
  // Section headers read "ECONOMIC DYNAMISM - 20%" (or "- 33.33%" before 2017).
  const starts = names.map(name =>
    text.search(new RegExp(`${escape(name)} - [\\d.]+%`, 'i'))
  );
  const pillars = {};
  names.forEach((name, index) => {
    const start = starts[index];
    if (start < 0) {
      pillars[name] = {
        score: null,
        indicators: PILLARS[name].map(() => null),
      };
      return;
    }
    const later = starts.filter(s => s > start);
    const section = text.slice(
      start,
      later.length ? Math.min(...later) : undefined
    );
    pillars[name] = {
      score: scoreAfter(section, name),
      indicators: PILLARS[name].map(indicator =>
        scoreAfter(section, indicator)
      ),
    };
  });
  return { overall: overall ? Number(overall[1]) : null, pillars };
}

async function main() {
  const lgu = process.argv[2];
  if (!lgu) {
    console.error(
      'Usage: node scripts/fetch-cmci.js "<LGU name>" [firstYear] [lastYear]'
    );
    process.exit(1);
  }
  const first = Number(process.argv[3] || 2014);
  const last = Number(process.argv[4] || 2024);
  const years = [];
  const results = [];
  for (let year = first; year <= last; year++) {
    const result = await fetchYear(lgu, year);
    console.log(year, 'overall', result.overall);
    years.push(year);
    results.push(result);
    await sleep(1500);
  }

  // The charts expect a number for every year; a year without data is 0.
  const value = number => number ?? 0;
  const data = {
    meta: {
      source:
        'Cities and Municipalities Competitiveness Index (CMCI), Department of Trade and Industry',
      source_url: `https://cmci.dti.gov.ph/lgu-profile.php?lgu=${encodeURIComponent(lgu)}`,
      lgu,
      years,
    },
    overall_score: results.map(r => value(r.overall)),
    pillars: Object.entries(PILLARS).map(([name, indicators]) => ({
      name,
      scores: results.map(r => value(r.pillars[name].score)),
      indicators: indicators.map((indicator, index) => ({
        name: indicator,
        values: results.map(r => value(r.pillars[name].indicators[index])),
      })),
    })),
  };
  fs.writeFileSync(OUTPUT, JSON.stringify(data, null, 2) + '\n');
  console.log('wrote', OUTPUT);
}

main().catch(error => {
  console.error(error);
  process.exit(1);
});
