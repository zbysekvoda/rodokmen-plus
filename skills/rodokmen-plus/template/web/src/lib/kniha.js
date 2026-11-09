// „Kniha předků“ (/kniha/<slug>/): výběr předků od libovolného kořene. Stejná logika jako stránky osob
// (localTree = Kekulé od kořene po father/mother, depthOf = známé generace), žádný druhý výpočet.
import { people, config, localTree, depthOf, genName } from './data.js';

/** web.json → kniha (generaci = počet generací včetně kořene, výchozí 6). */
export const knihaConfig = { generaci: 6, ...(config.kniha ?? {}) };

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
