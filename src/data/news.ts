/**
 * City announcements shown on the home page.
 *
 * The official website (cityofsanpedrolaguna.gov.ph) is offline, so each item
 * links to its Internet Archive capture. Titles and excerpts are the city's
 * own words. Add new items at the top; leave the array empty to hide the
 * section.
 */
export interface NewsItem {
  id: string;
  title: string;
  excerpt: string;
  /** ISO 8601 publication date */
  date: string;
  category: string;
  source: string;
  /** Link to the original announcement */
  url: string;
}

export const news: NewsItem[] = [
  {
    id: 'ligtas-tigdas',
    title: 'Ligtas Tigdas',
    excerpt:
      'Muling pinaaalalahanan ang lahat ng magulang at tagapag-alaga na makiisa sa Measles-Rubella Supplemental Immunization Activity (SIA) o Ligtas Tigdas! Sino ang dapat pabakunahan?Mga batang edad 6 hanggang 59 buwan (wala pang 5 taong gulang) Iskedyul ng…',
    date: '2026-05-06T03:23:30+00:00',
    category: 'health',
    source: 'City Government of San Pedro',
    url: 'https://web.archive.org/web/20260506134748/https://cityofsanpedrolaguna.gov.ph/ligtas-tigdas/',
  },
  {
    id: 'pinagtibay-ng-sangguniang-panlungsod-of-the-city-of-san-pedr',
    title:
      'Pinagtibay ng Sangguniang Panlungsod of the City of San Pedro ang dalawang resolusyon bilang pagkilala sa natatanging tagumpay ng ating San Pedro City Civil Registrar’s Office, Laguna',
    excerpt:
      'Pinagtibay ng Sangguniang Panlungsod of the City of San Pedro ang dalawang resolusyon bilang pagkilala sa natatanging tagumpay ng ating San Pedro City Civil Registrar’s Office, Laguna: 1st Place – 2024 Outstanding Local Civil Registry Office (Provincial…',
    date: '2026-05-05T10:07:05+00:00',
    category: 'city',
    source: 'City Government of San Pedro',
    url: 'https://web.archive.org/web/20260505123956/https://cityofsanpedrolaguna.gov.ph/pinagtibay-ng-sangguniang-panlungsod-of-the-city-of-san-pedro-ang-dalawang-resolusyon-bilang-pagkilala-sa-natatanging-tagumpay-ng-ating-san-pedro-city-civil-registrars-office-laguna/',
  },
  {
    id: 'capacity-building-session-on-the-proper-accomplishment-of-ci',
    title:
      'Capacity-Building Session on the proper accomplishment of Civil Registry Forms',
    excerpt:
      'Participants from medical records units, birthing facilities, and funeral services gathered for a capacity-building session on the proper accomplishment of civil registry forms on Thursday, April 30, 2026 at the Pavilion Hall, San Pedro City Hall. Organized…',
    date: '2026-05-01T09:45:00+00:00',
    category: 'city',
    source: 'City Government of San Pedro',
    url: 'https://web.archive.org/web/20260504124742/https://cityofsanpedrolaguna.gov.ph/capacity-building-session-on-the-proper-accomplishment-of-civil-registry-forms/',
  },
  {
    id: '%F0%9D%90%85%F0%9D%90%AB%F0%9D%90%9E%F0%9D%90%9E-%F0%9D%90%8',
    title:
      'Free Hands-on Training on Hydroponics Boosts Urban Agriculture in San Pedro',
    excerpt:
      'In line with strengthening food security and sustainable livelihood, a Free Hands-on Training on Hydroponics Production was successfully conducted for San Pedrenses under the city’s Urban Agriculture and Livelihood Program led by the Office of City…',
    date: '2026-05-01T08:33:00+00:00',
    category: 'city',
    source: 'City Government of San Pedro',
    url: 'https://web.archive.org/web/20260504134555/https://cityofsanpedrolaguna.gov.ph/%F0%9D%90%85%F0%9D%90%AB%F0%9D%90%9E%F0%9D%90%9E-%F0%9D%90%87%F0%9D%90%9A%F0%9D%90%A7%F0%9D%90%9D%F0%9D%90%AC-%F0%9D%90%A8%F0%9D%90%A7-%F0%9D%90%93%F0%9D%90%AB%F0%9D%90%9A%F0%9D%90%A2%F0%9D%90%A7/',
  },
  {
    id: 'samyo-ng-sampaguita-bango-ng-ilang-ilang',
    title: 'SAMYO NG SAMPAGUITA, BANGO NG ILANG-ILANG!',
    excerpt:
      'Nakikiisa ang San Pedro City Tourism, Culture and Arts Office sa pormal na pagsisimula ngayong araw ng Sampaguita Month sa ating Lungsod! Ipinagdiriwang ito alinsunod sa City Ordinance No. 2018-08 na ipinasa ng ating Sangguniang Panlungsod noong 2018.…',
    date: '2026-05-01T01:45:00+00:00',
    category: 'culture',
    source: 'City Government of San Pedro',
    url: 'https://web.archive.org/web/20260504161824/https://cityofsanpedrolaguna.gov.ph/samyo-ng-sampaguita-bango-ng-ilang-ilang/',
  },
  {
    id: 'pormal-nang-pinasinayaan-at-binasbasan-ang-bagong-septage-tr',
    title:
      'Pormal nang pinasinayaan at binasbasan ang bagong Septage Treatment Facility ng San Pedro Water District (SPWD) sa Barangay Estrella, isang mahalagang hakbang tungo sa mas maayos na pamamahala ng wastewater at pangangalaga sa kalikasan sa lungsod ng San Pedro.',
    excerpt:
      '29 Abril 2026 | Pormal nang pinasinayaan at binasbasan ang bagong Septage Treatment Facility ng San Pedro Water District (SPWD) sa Barangay Estrella, isang mahalagang hakbang tungo sa mas maayos na pamamahala ng wastewater at pangangalaga sa kalikasan sa…',
    date: '2026-04-30T07:30:52+00:00',
    category: 'city',
    source: 'City Government of San Pedro',
    url: 'https://web.archive.org/web/20260430124723/https://cityofsanpedrolaguna.gov.ph/pormal-nang-pinasinayaan-at-binasbasan-ang-bagong-septage-treatment-facility-ng-san-pedro-water-district-spwd-sa-barangay-estrella-isang-mahalagang-hakbang-tungo-sa-mas-maayos-na-pamamahala-ng-wast/',
  },
];
