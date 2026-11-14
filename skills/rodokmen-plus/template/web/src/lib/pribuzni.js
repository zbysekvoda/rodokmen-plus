// „Jak jsme příbuzní?“ – čím je osoba b osobě a, česky.
// Zrcadlo tools/graf.py (nazev_pokrevni, vztah_obecny) – názvy i pořadí pravidel držet shodně.
// people: {slug: {father, mother, spouses, sex}}; osoby mimo people (žijící, které web nepošle) se přeskočí.

function nahoru(x, rod) {
  // BFS → nejkratší cesta i při implexu (předek ve více větvích)
  const out = new Map([[x, [0, null]]]);
  let fr = [x];
  while (fr.length) {
    const nxt = [];
    for (const i of fr) for (const r of rod(i)) if (!out.has(r)) { out.set(r, [out.get(i)[0] + 1, i]); nxt.push(r); }
    fr = nxt;
  }
  return out;
}

function dolu(p, nah) {
  const c = [p];
  while (nah.get(c.at(-1))[1] !== null) c.push(nah.get(c.at(-1))[1]);
  return c;
}

export function nazevPokrevni(da, db, s, polovicni = false) {
  const z = s === 'F';
  const pra = (n) => 'pra'.repeat(Math.max(n, 0));
  if (da === 0) return db === 1 ? (z ? 'dcera' : 'syn') : pra(db - 2) + (z ? 'vnučka' : 'vnuk');
  if (db === 0) return da === 1 ? (z ? 'matka' : 'otec') : pra(da - 2) + (z ? 'babička' : 'dědeček');
  if (da === 1 && db === 1) return (polovicni ? 'nevlastní ' : '') + (z ? 'sestra' : 'bratr');
  if (da === 1) return pra(db - 2) + (z ? 'neteř' : 'synovec');
  if (db === 1) return pra(da - 2) + (z ? 'teta' : 'strýc');
  if (da === db) return (z ? 'sestřenice' : 'bratranec') + (da > 2 ? ` z ${da - 1}. kolena` : '');
  return (z ? 'vzdálená příbuzná' : 'vzdálený příbuzný') + ` (společný předek ${da}. a ${db}. generace)`;
}

function obecny(a, b, rod, man, sex) {
  if (a === b) return null;
  const na = nahoru(a, rod), nb = nahoru(b, rod);
  const spol = [...na.keys()].filter((p) => nb.has(p));
  if (spol.length) {
    const klic = (p) => [na.get(p)[0] + nb.get(p)[0], Math.max(na.get(p)[0], nb.get(p)[0])];
    const nej = spol.map(klic).reduce((m, k) => (k[0] < m[0] || (k[0] === m[0] && k[1] < m[1]) ? k : m));
    const predci = spol.filter((p) => { const k = klic(p); return k[0] === nej[0] && k[1] === nej[1]; });
    const p = predci[0];
    const da = na.get(p)[0], db = nb.get(p)[0];
    const pol = da === 1 && db === 1 && predci.length === 1;
    return { nazev: nazevPokrevni(da, db, sex(b), pol), cesta: [...dolu(p, na).reverse(), ...dolu(p, nb).slice(1)], predci, da, db };
  }
  const z = sex(b) === 'F';
  const ma = man(a);
  const sn = (nazev, cesta) => ({ nazev, cesta, predci: [], da: 0, db: 0 });
  if (ma.includes(b)) return sn(z ? 'manželka' : 'manžel', [a, b]);
  for (const m of ma) if (rod(m).includes(b)) return sn(z ? 'tchyně' : 'tchán', [a, m, b]);
  for (const m of man(b)) if (rod(m).includes(a)) return sn(z ? 'snacha' : 'zeť', [a, m, b]);
  for (const m of ma) {
    const r = obecny(m, b, rod, () => [], sex);
    if (r && r.da === 1 && r.db === 1) return { ...r, nazev: z ? 'švagrová' : 'švagr', cesta: [a, ...r.cesta] };
  }
  for (const m of man(b)) {
    const r = obecny(a, m, rod, () => [], sex);
    if (r && r.da === 1 && r.db === 1) return { ...r, nazev: z ? 'švagrová' : 'švagr', cesta: [...r.cesta, b] };
  }
  return null;
}

/** → {nazev, cesta: [a … b], predci: [nejbližší společní předci], da, db} nebo null. */
export function vztah(people, a, b) {
  if (!people[a] || !people[b]) return null;
  const rod = (i) => [people[i]?.father, people[i]?.mother].filter((r) => r && people[r]);
  const man = (i) => (people[i]?.spouses ?? []).filter((m) => people[m]);
  return obecny(a, b, rod, man, (i) => people[i]?.sex);
}
