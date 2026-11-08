// Data exported from the research repo by tools/export_web.py (re-run `npm run data` after changes).
import site from '../data/site.json';

export const { people, families, lines, stats, issues, hypotheses, docs, config } = site;
export const houses = site.houses ?? {};
export const villages = site.villages ?? {};
export const houseList = Object.values(houses);
/** „Horní Lhota čp. 12 – U Nováků“ */
export const houseTitle = (h) => `${h.obec} čp. ${h.cp}${h.name ? ` – ${h.name}` : ''}`;
/** Roky pobytu „1910–1921“, „od 1934“, „1901“. */
export const span = (a, b) => (a && b ? (a === b ? `${a}` : `${a}–${b}`) : a ? `od ${a}` : b ? `do ${b}` : '');
/** Počet rodů slovem pro nadpisy („Osm rodů“). */
export const linesTitle = (n) => (['Žádný rod', 'Jeden rod', 'Dva rody', 'Tři rody', 'Čtyři rody', 'Pět rodů', 'Šest rodů', 'Sedm rodů', 'Osm rodů'][n] ?? `${n} rodů`);
export const root = people[site.root];
/** Kořeny rodokmenu (KORENY v data/osoby.py): [{ key, id, name }]; první je výchozí. */
export const roots = site.roots ?? [{ key: 'hlavni', id: site.root, name: people[site.root].name }];
export const records = Object.fromEntries(site.records.map((r) => [r.key, r]));
export const recordList = site.records;
export const byK = Object.fromEntries([
  ...Object.values(people).map((p) => [p.k, p]),
  ...Object.entries(site.aliases ?? {}).map(([k, slug]) => [Number(k), people[slug]]),
]);
/** Předci osoby číslovaní od ní (1 = osoba, 2j = otec, 2j+1 = matka) – průchod po father/mother, ne po globálním k. */
export function localTree(slug, gens = 4) {
  const t = { 1: people[slug] };
  for (let j = 1; j < 2 ** (gens - 1); j++) {
    const p = t[j];
    if (!p) continue;
    if (p.father && people[p.father]) t[2 * j] = people[p.father];
    if (p.mother && people[p.mother]) t[2 * j + 1] = people[p.mother];
  }
  return t;
}
/** Počet známých generací za osobou (0 = rodiče neznámí). */
export const depthOf = (p) => {
  if (!p) return 0;
  const f = people[p.father], m = people[p.mother];
  return f || m ? 1 + Math.max(depthOf(f), depthOf(m)) : 0;
};
/** Počet známých předků včetně osoby (osoba ve více větvích se počítá vícekrát, jako dřív). */
export const knownOf = (p) => (p ? 1 + knownOf(people[p.father]) + knownOf(people[p.mother]) : 0);
export const lineByK = Object.fromEntries(Object.values(lines).map((l) => [l.k, l]));

export const href = {
  person: (slug) => `/osoba/${slug}/`,
  family: (id) => `/rodina/${id}/`,
  line: (slug) => `/rod/${slug}/`,
  record: (key) => `/zdroj/${key}/`,
  house: (slug) => `/dum/${slug}/`,
  place: (slug) => `/misto/${slug}/`,
};

/** Sortable number from dates like "12. 5. 1811", "3/1867", "12/1790", "1797". */
export function dateKey(date) {
  const y = (date.match(/\d{4}/) || ['9999'])[0];
  const parts = date.replace(y, '').match(/\d+/g) || [];
  const [d, m] = parts.length >= 2 ? [parts[0], parts[1]] : [0, parts[0] || 0];
  return Number(y) * 10000 + Number(m) * 100 + Number(d);
}

export const genName = (g) =>
  ['výchozí osoba', 'rodiče', 'prarodiče', 'praprarodiče'][g] ?? `${g}. generace (${'pra'.repeat(g - 1)}rodiče)`;

export const statusClass = (st) => ({ doc: 'st-doc', lit: 'st-fam', prob: 'st-prob', fam: 'st-fam', mh: 'st-mh' })[st] ?? 'st-unk';

// ---- Věk osoby k datu události („× 20. 6. 1919 (29 let) Holice …“) ----
// Převzato a upraveno z xkraust/rodokmen-skill@79d3685 (MIT):
// https://github.com/xkraust/rodokmen-skill/blob/79d36850afaa080b0ebcf70a368cbbb5237d700e/skills/rodokmen/template/web/src/lib/data.js
const APPROX = /(asi|≈|~|kolem|cca|okolo)\s*$/i;
const BOUND = /(před|po)\s*$/i;

/** Datum z textu („12. 5. 1811“, „3/1867“, „1797“, „asi 1720“) jako {y, m, d, approx, start, end}; null, když chybí nebo je jen „před/po“. */
export function parseDate(text) {
  const mt = /(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})|(\d{1,2})\/(\d{4})|(\d{4})/.exec(text ?? '');
  if (!mt) return null;
  const before = text.slice(0, mt.index);
  if (BOUND.test(before)) return null;
  const [y, m, d] = mt[3] ? [mt[3], mt[2], mt[1]] : mt[5] ? [mt[5], mt[4], 0] : [mt[6], 0, 0];
  return { y: Number(y), m: Number(m), d: Number(d), approx: APPROX.test(before), start: mt.index, end: mt.index + mt[0].length };
}

const plural = (n, one, few, many) => `${n} ${n === 1 ? one : n >= 2 && n <= 4 ? few : many}`;

/** Věk mezi narozením a událostí jako text („29 let“, „asi 54 let“, „3 měsíce“) nebo null, když ho nelze rozumně určit. */
export function ageAt(birth, event) {
  if (!birth || !event) return null;
  const exact = birth.d && birth.m && event.d && event.m && !birth.approx && !event.approx;
  if (!exact) {
    const years = event.y - birth.y;
    return years >= 1 && years <= 110 ? `asi ${plural(years, 'rok', 'roky', 'let')}` : null;
  }
  const before = event.m < birth.m || (event.m === birth.m && event.d < birth.d);
  const years = event.y - birth.y - (before ? 1 : 0);
  if (years < 0 || years > 110) return null;
  if (years >= 1) return plural(years, 'rok', 'roky', 'let');
  const months = (event.y - birth.y) * 12 + event.m - birth.m - (event.d < birth.d ? 1 : 0);
  if (months >= 1) return plural(months, 'měsíc', 'měsíce', 'měsíců');
  const days = Math.round((Date.UTC(event.y, event.m - 1, event.d) - Date.UTC(birth.y, birth.m - 1, birth.d)) / 86400000);
  if (days < 0) return null;
  return days === 0 ? 'v den narození' : plural(days, 'den', 'dny', 'dní');
}

/** Datum narození osoby z faktu „* …“ (jinak z doloženého roku); u nejistých údajů (prob, mh) jen přibližně. */
export function birthOf(p) {
  let b = parseDate(p?.facts?.find((f) => f.trimStart().startsWith('*'))?.replace(/^\s*\*/, ''));
  if (!b && p?.birth?.q === 'doc' && p.birth.y) b = { y: p.birth.y, m: 0, d: 0, approx: false };
  return b && ['prob', 'mh'].includes(p.st) ? { ...b, approx: true } : b;
}

/** Fakt sňatku nebo úmrtí s věkem za datem: „× 20. 6. 1919 (29 let) Holice …“. Ostatní fakta beze změny. */
export function factWithAge(fact, birth) {
  if (!birth || !/^\s*[×†]/.test(fact)) return fact;
  const ev = parseDate(fact);
  const age = ageAt(birth, ev);
  return age ? `${fact.slice(0, ev.end)} (${age})${fact.slice(ev.end)}` : fact;
}
