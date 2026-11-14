// DNA linie ve vějíři předků podle Kekulého čísla (kořen 1, otec 2n, matka 2n+1).
// Linie se počítá z pozice (čísla), ne z osoby – předek v implexu se tak posoudí na každém místě zvlášť.

/** Kroky od kořene k číslu k: false = otec, true = matka. */
const kroky = (k) => k.toString(2).slice(1).split('').map((b) => b === '1');

/**
 * Je pozice k v linii, od níž kořen mohl zdědit danou DNA?
 * @param {number} k Kekulého číslo
 * @param {'y'|'mt'|'x'} linie
 * @param {'M'|'F'|undefined} sex pohlaví kořene
 */
export function vLinii(k, linie, sex) {
  if (!Number.isInteger(k) || k < 1) return false;
  const s = kroky(k);
  if (linie === 'y') return sex === 'M' && s.every((m) => !m);
  if (linie === 'mt') return s.every((m) => m);
  if (linie === 'x') {
    // otec předává X jen dceři: cesta nesmí jít z muže na jeho otce (kořen-muž počítá jako muž)
    let muz = sex === 'M';
    for (const m of s) {
      if (muz && !m) return false;
      muz = !m;
    }
    return true;
  }
  return false;
}

/** Čísla v linii pro generace 1..gen (pro testy a statistiku). */
export function cislaLinie(linie, sex, gen) {
  const out = [];
  for (let k = 2; k < 2 ** (gen + 1); k++) if (vLinii(k, linie, sex)) out.push(k);
  return out;
}

export const POPIS = {
  y: 'Y-DNA dědí jen synové po otci – zvýrazněná je čistě otcovská linie (otec, jeho otec…).',
  mt: 'Mitochondriální DNA předávají matky všem dětem – zvýrazněná je čistě mateřská linie (matka, její matka…).',
  x: 'Chromozom X dostává syn jen od matky a dcera od obou rodičů – zvýraznění předci mohli kořeni předat kus X.',
  yZena: 'Y-DNA nese jen muž; u ženy ji lze sledovat přes otce nebo bratra.',
};
