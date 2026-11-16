#!/usr/bin/env node

/**
 * Generate public/sitemap.xml, public/llms.txt and public/robots.txt from the
 * portal's own data: config/lgu.config.json, the directory files and the
 * merged services list. Sections whose feature flag is off are left out.
 *
 * Usage: npm run generate:sitemap
 * Run after `npm run merge:services` so the services list is current.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = file => JSON.parse(fs.readFileSync(path.join(ROOT, file), 'utf8'));

const config = read('config/lgu.config.json');
const categories = read('src/data/service_categories.json').categories;
const services = read('src/data/citizens-charter/merged-services.json');
const departments = read('src/data/directory/departments.json');
const barangays = read('src/data/directory/barangays.json');
const executive = read('src/data/directory/executive.json');
const legislative = read('src/data/directory/legislative.json');

const baseUrl = config.portal.baseUrl.replace(/\/$/, '');
const enabled = feature => config.features[feature] !== false;
const today = new Date().toISOString().slice(0, 10);
const title = text =>
  text
    .toLowerCase()
    .replace(/(^|[\s(/-])([a-z])/g, (_, a, b) => a + b.toUpperCase());

/** Every public route, as { path, priority, changefreq }. Mirrors src/App.tsx. */
function collectPages() {
  const pages = [];
  const add = (route, priority, changefreq) =>
    pages.push({ path: route, priority, changefreq });

  add('/', '1.0', 'daily');
  add('/services', '0.9', 'weekly');
  for (const category of categories) {
    add(`/services?category=${category.slug}`, '0.7', 'weekly');
  }
  for (const service of services)
    add(`/services/${service.slug}`, '0.6', 'monthly');

  add('/government/elected-officials', '0.8', 'monthly');
  add('/government/elected-officials/committees', '0.5', 'monthly');
  add('/government/departments', '0.8', 'monthly');
  for (const dept of departments)
    add(`/government/departments/${dept.slug}`, '0.6', 'monthly');
  add('/government/barangays', '0.8', 'monthly');
  for (const brgy of barangays)
    add(`/government/barangays/${brgy.slug}`, '0.6', 'monthly');

  if (enabled('statistics')) {
    add('/statistics', '0.7', 'monthly');
    add('/statistics/municipal-income', '0.6', 'monthly');
    add('/statistics/competitiveness', '0.6', 'monthly');
  }
  if (enabled('transparency')) {
    add('/transparency', '0.8', 'weekly');
    add('/transparency/financial', '0.7', 'monthly');
    add('/transparency/procurement', '0.7', 'daily');
    add('/transparency/infrastructure', '0.7', 'weekly');
  }
  if (enabled('openLGU')) {
    add('/openlgu', '0.8', 'weekly');
    add('/openlgu/officials', '0.6', 'monthly');
    add('/openlgu/terms', '0.5', 'monthly');
  }

  add('/data/weather', '0.4', 'hourly');
  add('/data/forex', '0.3', 'daily');
  add('/about', '0.5', 'monthly');
  add('/contact', '0.4', 'yearly');
  add('/join-us', '0.4', 'yearly');
  add('/ideas', '0.3', 'monthly');
  add('/accessibility', '0.3', 'yearly');
  add('/terms-of-service', '0.2', 'yearly');
  add('/sitemap', '0.2', 'monthly');
  add('/search', '0.2', 'monthly');
  return pages;
}

function sitemapXml(pages) {
  const escape = text => text.replace(/&/g, '&amp;');
  const urls = pages.map(
    page => `  <url>
    <loc>${escape(baseUrl + page.path)}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${page.changefreq}</changefreq>
    <priority>${page.priority}</priority>
  </url>`
  );
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.join('\n')}
</urlset>
`;
}

function llmsTxt() {
  const { lgu, portal } = config;
  const council = legislative[0];
  const lines = [
    `# ${portal.name}`,
    '',
    `> ${portal.description} ${portal.name} is a volunteer-run, open-source civic portal. It is not the official website of the ${lgu.fullName}.`,
    '',
    `- LGU: ${lgu.fullName}, ${lgu.province}, ${lgu.region} (${lgu.regionCode})`,
    `- Official LGU website: ${lgu.officialWebsite}`,
    `- Portal: ${baseUrl}`,
    '',
    '## Services',
    `Requirements, steps, fees and processing times for ${services.length} services, taken from the city's Citizen's Charter.`,
    '',
    ...categories.map(
      category =>
        `- [${category.name}](${baseUrl}/services?category=${category.slug}): ${category.description}`
    ),
    '',
    '## Government',
    ...executive.map(official => `- ${official.role}: ${official.name}`),
  ];
  if (council) {
    lines.push(
      `- ${council.chamber}: ${council.officials.length} members`,
      `- [Elected officials](${baseUrl}/government/elected-officials)`
    );
  }
  lines.push(
    `- [Departments](${baseUrl}/government/departments): ${departments.length} offices`,
    `- [Barangays](${baseUrl}/government/barangays): ${barangays.length} barangays`,
    '',
    '### Departments',
    ...departments.map(
      dept =>
        `- [${title(dept.office_name)}](${baseUrl}/government/departments/${dept.slug})`
    ),
    '',
    '### Barangays',
    ...barangays.map(
      brgy =>
        `- [${title(brgy.barangay_name)}](${baseUrl}/government/barangays/${brgy.slug})`
    )
  );
  if (enabled('statistics')) {
    lines.push(
      '',
      '## Statistics',
      `- [Population](${baseUrl}/statistics): Philippine Statistics Authority census counts`,
      `- [Local income](${baseUrl}/statistics/municipal-income): Bureau of Local Government Finance`,
      `- [Competitiveness](${baseUrl}/statistics/competitiveness): DTI Cities and Municipalities Competitiveness Index`
    );
  }
  if (enabled('transparency')) {
    lines.push(
      '',
      '## Transparency',
      `- [Financial reports](${baseUrl}/transparency/financial): quarterly Statement of Receipts and Expenditures (BLGF)`,
      `- [Procurement](${baseUrl}/transparency/procurement): PhilGEPS awards for ${config.transparency.procurement.organizationName}`,
      `- [Infrastructure](${baseUrl}/transparency/infrastructure): DPWH projects in ${lgu.name}`
    );
  }
  if (enabled('openLGU')) {
    lines.push(
      '',
      '## Legislation',
      `- [OpenLGU](${baseUrl}/openlgu): ordinances, resolutions and executive orders`
    );
  }
  lines.push('', '## Sitemap', `- ${baseUrl}/sitemap.xml`, '');
  return lines.join('\n');
}

const robotsTxt = `User-Agent: *
Allow: /
Disallow: /admin
Disallow: /api/

Sitemap: ${baseUrl}/sitemap.xml
`;

const pages = collectPages();
fs.writeFileSync(path.join(ROOT, 'public/sitemap.xml'), sitemapXml(pages));
fs.writeFileSync(path.join(ROOT, 'public/llms.txt'), llmsTxt());
fs.writeFileSync(path.join(ROOT, 'public/robots.txt'), robotsTxt);
console.log(`sitemap.xml: ${pages.length} URLs for ${baseUrl}`);
console.log('llms.txt and robots.txt written');
