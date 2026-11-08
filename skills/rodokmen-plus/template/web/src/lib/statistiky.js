// Statistiky rodokmenu pro stránku /statistiky/ – počítá se při buildu z people a records (site.json).
// Převzato a přepsáno z Pythonu do JS z hnizdiljan/rodokmen-skill@d172316 (MIT):
// https://github.com/hnizdiljan/rodokmen-skill/blob/d172316bc190d0f44894fa67115505729d587c6a/skills/rodokmen/tools/statistiky.py
// Data a věk bere z lib/data.js (parseDate, birthOf, ageAt), aby věk seděl se stránkou osoby a časovou osou.
// Počítají se jen předci (p.k ≥ 1) s nějakým doložením (st ≠ unk); boční příbuzní ne.
import { people, recordList, parseDate, birthOf, ageAt } from './data.js';

const MESICE = ['leden', 'únor', 'březen', 'duben', 'květen', 'červen', 'červenec', 'srpen', 'září', 'říjen', 'listopad', 'prosinec'];

// klíčové slovo (začátek slova, malými písmeny – „Kovář“ s velkým je příjmení) → [povolání, skupina];
// rozhoduje první shoda v pořadí seznamu, proto obecná slova (dělník, mistr) až nakonec
const POVOLANI = [
  ['tkad', 'tkadlec', 'řemeslo'], ['tkalc', 'tkadlec', 'řemeslo'], ['soukeník', 'soukeník', 'řemeslo'],
  ['obuvn', 'obuvník', 'řemeslo'], ['švec', 'obuvník', 'řemeslo'], ['krejč', 'krejčí', 'řemeslo'],
  ['kovář', 'kovář', 'řemeslo'], ['kolář', 'kolář', 'řemeslo'], ['zedník', 'zedník', 'řemeslo'], ['tesař', 'tesař', 'řemeslo'],
  ['truhlář', 'truhlář', 'řemeslo'], ['bednář', 'bednář', 'řemeslo'], ['sklenář', 'sklenář', 'řemeslo'],
  ['hrnčíř', 'hrnčíř', 'řemeslo'], ['jirchář', 'jirchář', 'řemeslo'], ['koželuh', 'koželuh', 'řemeslo'],
  ['mlynář', 'mlynář', 'řemeslo'], ['pekař', 'pekař', 'řemeslo'], ['řezník', 'řezník', 'řemeslo'], ['sládek', 'sládek', 'řemeslo'],
  ['sedlák', 'sedlák', 'zemědělství'], ['rolník', 'rolník', 'zemědělství'], ['hospodář', 'hospodář', 'zemědělství'],
  ['chalupník', 'chalupník', 'zemědělství'], ['domkář', 'domkář', 'zemědělství'], ['podsedník', 'podsedník', 'zemědělství'],
  ['familiant', 'familiant', 'zemědělství'], ['výměnk', 'výměnkář', 'zemědělství'], ['na výměnku', 'výměnkář', 'zemědělství'],
  ['podruh', 'podruh', 'zemědělství'], ['čeledín', 'čeledín', 'zemědělství'], ['děveč', 'děvečka', 'zemědělství'],
  ['zahradník', 'zahradník', 'zemědělství'], ['pastýř', 'pastýř', 'zemědělství'], ['ovčák', 'ovčák', 'zemědělství'],
  ['hajný', 'hajný', 'les'], ['myslivec', 'myslivec', 'les'], ['lesník', 'lesník', 'les'], ['lesní', 'lesník', 'les'],
  ['strojvůd', 'strojvůdce', 'doprava'], ['výpravčí', 'výpravčí', 'doprava'], ['průvodčí', 'průvodčí', 'doprava'],
  ['železničář', 'železničář', 'doprava'], ['na dráze', 'železničář', 'doprava'], ['při dráze', 'železničář', 'doprava'],
  ['kočí', 'kočí', 'doprava'], ['povozník', 'povozník', 'doprava'], ['vozka', 'kočí', 'doprava'],
  ['kupec', 'kupec', 'obchod'], ['obchodník', 'obchodník', 'obchod'], ['hokynář', 'hokynář', 'obchod'],
  ['hostinsk', 'hostinský', 'úřad a služby'], ['šenkýř', 'hostinský', 'úřad a služby'], ['učitel', 'učitel', 'úřad a služby'],
  ['kantor', 'učitel', 'úřad a služby'], ['úředník', 'úředník', 'úřad a služby'], ['četník', 'četník', 'úřad a služby'],
  ['policajt', 'policista', 'úřad a služby'], ['strážník', 'policista', 'úřad a služby'], ['rychtář', 'rychtář', 'úřad a služby'],
  ['soudní sluha', 'soudní sluha', 'úřad a služby'], ['sluha', 'sluha', 'úřad a služby'], ['služka', 'služka', 'úřad a služby'],
  ['voják', 'voják', 'úřad a služby'], ['kaprál', 'voják', 'úřad a služby'], ['vysloužil', 'voják', 'úřad a služby'],
  ['havíř', 'horník', 'dělník'], ['horník', 'horník', 'dělník'], ['nádeník', 'nádeník', 'dělník'],
  ['tovární', 'tovární dělník', 'dělník'], ['dělník v továrně', 'tovární dělník', 'dělník'], ['dělník', 'dělník', 'dělník'],
  ['mistr', 'mistr řemesla', 'řemeslo'], // „tkalcovský mistr“ dopadne jako tkadlec, „purkmistr“ se nepočítá (začátek slova)
].map(([kw, name, group]) => [new RegExp(`(?<![\\p{L}\\p{N}])${kw}`, 'u'), name, group]);

const avg = (xs) => (xs.length ? Math.round((xs.reduce((a, b) => a + b, 0) / xs.length) * 10) / 10 : null);
const counts = (xs) => [...xs.reduce((m, x) => m.set(x, (m.get(x) ?? 0) + 1), new Map())]
  .map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count || String(a.name).localeCompare(String(b.name), 'cs'));
/** Celé roky z ageAt („29 let“, „asi 54 let“); měsíce a dny (malé děti) → 0. */
const years = (birth, ev) => {
  const t = ageAt(birth, ev);
  if (!t) return null;
  const m = /(\d+) (?:rok|roky|let)$/.exec(t);
  return m ? Number(m[1]) : 0;
};
/** „* 28. 7. 1870 Horní Lhota čp. 45“ → „Horní Lhota“. */
const placeOf = (fact) => {
  const d = parseDate(fact);
  if (!d) return null;
  const rest = fact.slice(d.end).split(/\s+čp\.|\s*\(|,|;|\s+–/)[0].trim();
  return /^\p{Lu}/u.test(rest) ? rest : null;
};
const factsOf = (p, sign) => p.facts.filter((f) => f.trimStart().startsWith(sign));

const anc = Object.values(people).filter((p) => p.k >= 1 && p.st !== 'unk');
const ref = (p, val) => ({ slug: p.slug, name: p.name, years: p.years, ...(val !== undefined ? { val } : {}) });
const born = new Map(anc.map((p) => [p.slug, birthOf(p)]).filter(([, b]) => b));

// dožití
const life = [];
for (const p of anc) {
  const d = factsOf(p, '†').map((f) => parseDate(f.replace(/^\s*†/, ''))).find(Boolean);
  const a = d && born.has(p.slug) ? years(born.get(p.slug), d) : null;
  if (a != null) life.push(ref(p, a));
}
life.sort((a, b) => b.val - a.val);

// sňatky: věk (první zapsaný sňatek) a měsíc (každý sňatek jednou, i když je zapsaný u obou manželů)
const wed = { M: [], F: [] };
const wedSeen = new Set();
const months = Array(12).fill(0);
for (const p of anc) {
  const fs = factsOf(p, '×');
  for (const f of fs) {
    const w = parseDate(f.replace(/^\s*×/, ''));
    if (!w || !w.m) continue;
    const key = `${w.y}-${w.m}-${w.d}-${placeOf(f.replace(/^\s*×/, ''))}`;
    if (!wedSeen.has(key)) { wedSeen.add(key); months[w.m - 1]++; }
  }
  const w = fs.map((f) => parseDate(f.replace(/^\s*×/, ''))).find(Boolean);
  const a = w && born.has(p.slug) ? years(born.get(p.slug), w) : null;
  if (a != null && a >= 14 && a <= 80) wed[p.sex === 'F' ? 'F' : 'M'].push(ref(p, a));
}

// věk rodičů při narození dítěte z rodokmenu
const gap = { M: [], F: [] };
for (const p of anc) {
  const b = born.get(p.slug);
  if (!b) continue;
  for (const [par, sex] of [['father', 'M'], ['mother', 'F']]) {
    const q = people[p[par]];
    const a = q && born.has(q.slug) ? years(born.get(q.slug), b) : null;
    if (a != null && a >= 12 && a <= 70) gap[sex].push({ parent: ref(q), child: ref(p), val: a });
  }
}

// povolání (u každého jednou, první shoda na fakt)
const occ = new Map();
const groups = [];
for (const p of anc) {
  const found = [];
  for (const f of p.facts) {
    if (/^\s*[*†×]/.test(f) || /(?<![\p{L}])(dcera|syn)(?![\p{L}])/u.test(f)) continue;
    const hit = POVOLANI.find(([rx]) => rx.test(f));
    if (hit && !found.some((x) => x[0] === hit[1])) found.push([hit[1], hit[2]]);
  }
  for (const [name, group] of found) {
    const key = `${name}|${group}`;
    if (!occ.has(key)) occ.set(key, { name, group, people: [] });
    occ.get(key).people.push(ref(p));
  }
  if (found.length) groups.push(found[0][1]);
}

const places = anc.map((p) => factsOf(p, '*').map((f) => placeOf(f.replace(/^\s*\*/, ''))).find(Boolean)).filter(Boolean);
const firstName = (p) => (p.name.split(/\s+/)[0] || '').replace(/[?()]/g, '');
const names = (sex) => counts(anc.filter((p) => (p.sex === 'F') === (sex === 'F')).map(firstName).filter((n) => /^\p{Lu}/u.test(n))).slice(0, 8);
const has = (p, rx) => [...p.facts, p.note || ''].some((f) => rx.test(f));
const decade = (r) => { const y = (r.date || '').match(/\d{4}/g); return y ? Math.floor(Number(y.at(-1)) / 50) * 50 : null; };
const decades = counts(recordList.map(decade).filter((d) => d != null)).sort((a, b) => a.name - b.name);
const gens = counts(anc.map((p) => p.gen ?? 0)).sort((a, b) => a.name - b.name);
const firstBirth = [...born.values()].filter((b) => !b.approx).map((b) => b.y).sort((a, b) => a - b)[0] ?? null;
const sumWith = (v) => ({ prumer: avg(v.map((x) => x.val)), nejmladsi: v.length ? v.reduce((a, b) => (b.val < a.val ? b : a)) : null,
  nejstarsi: v.length ? v.reduce((a, b) => (b.val > a.val ? b : a)) : null, pocet: v.length });

export const stat = {
  prehled: {
    predku: anc.length,
    dolozeno: anc.filter((p) => p.st === 'doc').length,
    generaci: gens.length ? Math.max(...gens.map((g) => g.name)) + 1 : 0,
    zapisu: recordList.length,
    nejstarsi_narozeni: firstBirth,
    prijmeni: new Set(anc.map((p) => p.name.split(/\s+/).at(-1).replace(/[?()]/g, '').replace(/ová$/, ''))).size,
  },
  generace: gens.map((g) => ({ gen: g.name, pocet: g.count, max: 2 ** g.name })),
  povolani: [...occ.values()].sort((a, b) => b.people.length - a.people.length || a.name.localeCompare(b.name, 'cs')),
  povolani_skupiny: counts(groups),
  mista: counts(places).slice(0, 15),
  doziti: { list: life, prumer: avg(life.map((r) => r.val)) },
  snatek_vek: Object.fromEntries(Object.entries(wed).map(([s, v]) => [s, { list: v.sort((a, b) => a.val - b.val), prumer: avg(v.map((r) => r.val)) }])),
  snatek_mesice: months.map((count, i) => ({ name: MESICE[i], count })),
  rodice_vek: { M: sumWith(gap.M), F: sumWith(gap.F) },
  jmena: { M: names('M'), F: names('F') },
  vira: anc.flatMap((p) => p.facts.filter((f) => /církv|vyznání|evangel|přestoupil|židovsk|izraelit/i.test(f)).map((f) => ref(p, f))),
  nemanzelske: anc.filter((p) => has(p, /nemanželsk/i)).map((p) => ref(p)),
  legitimace: anc.filter((p) => has(p, /legitim/i)).map((p) => ref(p)),
  zapisy_druh: counts(recordList.map((r) => ({ N: 'křty a narození', O: 'sňatky', Z: 'úmrtí' })[r.kind] ?? 'jiné')),
  zapisy_portal: counts(recordList.map((r) => r.portal || 'jiné')),
  zapisy_obdobi: decades.map((d) => ({ name: `${d.name}–${d.name + 49}`, count: d.count })),
};
