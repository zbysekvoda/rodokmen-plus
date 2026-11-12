// Výřez rodokmenu pro stránku příběhu: předci (Kekulého čísla), na které příběh odkazuje.
// Linie mezi odkazovanými předky se doplní: z k se jde k potomkovi (k >> 1), dokud cesta nenarazí na jiného
// odkazovaného předka nebo na už vybranou linii. Kdo s nikým nesouvisí, zůstane sám. Ke každému předkovi se přidá
// manžel/manželka z přímé linie (k ^ 1), když je znám. Výsledek: souvislé větve, v každé řádky generací od nejstarší,
// v řádku páry {otec, matka} (Kekulého čísla nebo null), seřazené podle k.
export const generace = (k) => Math.floor(Math.log2(k));

export function vyrezStromu(znama, odkazovana) {
  const known = (k) => k >= 1 && znama.has(k);
  const S = [...new Set(odkazovana.filter(known))].sort((a, b) => a - b);
  const vybrane = new Set();
  for (const k of S) {
    // cesta k nejbližšímu dříve vybranému (mladšímu) odkazovanému předkovi
    const cesta = [k];
    let j = k >> 1;
    while (j >= 1 && !vybrane.has(j)) { cesta.push(j); j >>= 1; }
    if (j >= 1 && cesta.slice(1).every(known)) cesta.forEach((x) => vybrane.add(x));
    else vybrane.add(k);
  }
  // větve: komponenty podle vztahu rodič–dítě uvnitř výběru
  const koren = (k) => { while (vybrane.has(k >> 1) && k > 1) k >>= 1; return k; };
  const vetve = new Map();
  for (const k of vybrane) {
    const r = koren(k);
    if (!vetve.has(r)) vetve.set(r, new Set());
    vetve.get(r).add(k);
  }
  return [...vetve.keys()].sort((a, b) => a - b).map((r) => {
    const pary = new Map();
    for (const k of vetve.get(r)) {
      if (k === 1) { pary.set(1, { otec: null, matka: null, sam: 1 }); continue; }
      const o = k & ~1;
      pary.set(o, { otec: known(o) ? o : null, matka: known(o + 1) ? o + 1 : null });
    }
    const radky = new Map();
    for (const [o, p] of pary) {
      const g = generace(o);
      if (!radky.has(g)) radky.set(g, []);
      radky.get(g).push(p);
    }
    return [...radky.entries()].sort((a, b) => b[0] - a[0]).map(([gen, ps]) => ({
      gen, pary: ps.sort((a, b) => (a.otec ?? a.matka ?? a.sam) - (b.otec ?? b.matka ?? b.sam)),
    }));
  });
}

// Osoby z odkazů /osoba/<slug>/ v textu příběhu (pořadí prvního výskytu, bez duplicit).
export const osobyZTextu = (text) =>
  [...new Set([...String(text).matchAll(/\/osoba\/([^/\s)#?"']+)\//g)].map((m) => m[1]))];
