// „Kniha předků“ (/kniha/<slug>/): výběr předků od libovolného kořene. Stejná logika jako stránky osob
// (localTree = Kekulé od kořene po father/mother, depthOf = známé generace), žádný druhý výpočet.
import { people, config, localTree, depthOf, genName, houseList, records, dateKey, statusClass, lineByK } from './data.js';
import { zapisyMode, selectHouses, selectStories, selectRecords, usedBooks, anchorId } from './kniha-vyber.js';

/** web.json → kniha: generaci = počet generací včetně kořene (6), domy a pribehy (true), zapisy "vybrane" | "vse" | false. */
const kc = { generaci: 6, domy: true, pribehy: true, ...(config.kniha ?? {}) };
export const knihaConfig = { ...kc, zapisy: zapisyMode(kc.zapisy) };

/** Kniha vzniká jen pro osoby s ≥ 2 generacemi předků (jinak by byla prázdná). */
export const MIN_GENERACI = 2;
export const hasBook = (p) => depthOf(p) >= MIN_GENERACI;
export const bookSlugs = () => Object.values(people).filter(hasBook).map((p) => p.slug);

/** Roky do knihy: u žijících jen rok narození (jako web), jinak roky života. */
export const bookYears = (p) => (p.alive ? (p.birth?.y ? `* ${p.birth.y}` : '') : p.years ?? '');

/**
 * Předci kořene po generacích: [{ gen, title, people: [{ k, p }] }], gen 1 = rodiče.
 * Kekulé čísla jsou místní (1 = kořen, 2k otec, 2k + 1 matka), omezená na knihaConfig.generaci.
 */
export function bookGenerations(slug, gens = knihaConfig.generaci) {
  const t = localTree(slug, gens);
  const out = [];
  for (let g = 1; g < gens; g++) {
    const list = [];
    for (let k = 2 ** g; k < 2 ** (g + 1); k++) if (t[k]) list.push({ k, p: t[k] });
    if (list.length) out.push({ gen: g, title: genName(g), people: list });
  }
  return out;
}

/**
 * Soukromí v knize = pravidlo webu (reference/soukromi.md): žijící (p.alive z export_web.py, stejný příznak jako web)
 * jen jménem a rokem narození – bez faktů, bydliště, zápisů a odkazů z příběhů.
 */
export const isPublic = (p) => !p.alive;

// příběhy webu (rozbalené wiki odkazy z export_web.py): hlavní, příběh domu, další z web.json → pribehy
const storyFiles = import.meta.glob(['../generated/pribeh.md', '../generated/pribeh_domu.md', '../generated/pribehy/*.md'], { eager: true });
async function allStories() {
  const out = [];
  for (const [f, m] of Object.entries(storyFiles)) {
    const slug = f.endsWith('/pribeh.md') ? 'pribeh-rodu' : f.endsWith('/pribeh_domu.md') ? 'pribeh-domu' : f.split('/').pop().replace(/\.md$/, '');
    out.push({ slug, title: m.frontmatter?.title ?? '', lead: m.frontmatter?.lead ?? '', html: await m.compiledContent() });
  }
  const order = (s) => (s.slug === 'pribeh-rodu' ? 0 : s.slug === 'pribeh-domu' ? 1 : 2);
  return out.sort((a, b) => order(a) - order(b));
}

/** Všechno, co kniha pro kořen potřebuje (výběr podle web.json → kniha). */
export async function bookData(slug) {
  const root = people[slug];
  const gens = bookGenerations(slug);
  const all = gens.flatMap((g) => g.people);
  const seen = new Set();
  for (const g of gens) for (const x of g.people) { x.first = !seen.has(x.p.slug); seen.add(x.p.slug); }
  const pub = new Set(all.filter(({ p }) => isPublic(p)).map(({ p }) => p.slug));
  const doc = all.filter(({ p }) => statusClass(p.st) === 'st-doc').length;
  const years = all.map(({ p }) => p.birth?.y).filter(Boolean);
  const surnames = [...new Set(all.map(({ p }) => p.line && lineByK[p.line]?.name).filter(Boolean))];
  const recKeys = all.filter(({ p }) => pub.has(p.slug)).flatMap(({ p }) => p.records ?? []);
  const allRecs = [...new Set(recKeys)].map((k) => records[k]).filter(Boolean);
  const houses = knihaConfig.domy ? selectHouses(houseList, pub, (s) => people[s]?.homes) : [];
  const stories = knihaConfig.pribehy ? selectStories(await allStories(), pub) : [];
  const sources = selectRecords(recKeys, records, knihaConfig.zapisy, dateKey);
  const targets = new Set([
    ...[...pub].map((s) => anchorId('osoba', s)),
    ...houses.map(({ h }) => anchorId('dum', h.slug)),
    ...sources.map((r) => anchorId('zdroj', r.key)),
    ...stories.map((s) => anchorId('pribeh', s.slug)),
  ]);
  return {
    root, gens, all, pub, targets, houses, stories, sources, books: usedBooks(allRecs),
    stats: { ancestors: new Set(all.map(({ p }) => p.slug)).size, generations: gens.length, docPct: all.length ? Math.round((100 * doc) / all.length) : 0 },
    oldest: years.length ? Math.min(...years) : null,
    surnames,
  };
}
