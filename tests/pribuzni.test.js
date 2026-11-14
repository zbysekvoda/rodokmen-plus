// „Jak jsme příbuzní?“ – template/web/src/lib/pribuzni.js na ukázkových datech; názvy musí sedět s tools/graf.py.
import { expect, test } from 'bun:test';
import { vztah } from '../skills/rodokmen-plus/template/web/src/lib/pribuzni.js';

const ROOT = new URL('..', import.meta.url).pathname;
// graf.py načte ukázku → osoby pro web (rodiče, manželé, pohlaví) a vztahy podle Pythonu pro všechny dvojice
const py = `
import json, sys
sys.path.insert(0, "skills/rodokmen-plus/tools")
import graf
g = graf.nacti("skills/rodokmen-plus/template/ukazka/osoby.py")
ids = [i for i, d in g.osoby.items() if d.get("druh") != "bocni" and not d.get("tataz")]
people = {}
for i in ids:
    o, m = g.rodice(i)
    people[i] = dict(father=o, mother=m, spouses=g.manzele(i), sex=g.osoby[i].get("sex"))
vz = {}
for a in ids:
    for b in ids:
        r = g.vztah(a, b)
        if r: vz[a + "|" + b] = [r["nazev"], r["cesta"]]
print(json.dumps(dict(people=people, vz=vz)))
`;
const out = Bun.spawnSync(['python3', '-c', py], { cwd: ROOT });
if (out.exitCode !== 0) throw new Error(out.stderr.toString());
const { people, vz } = JSON.parse(out.stdout.toString());
const n = (a, b) => vztah(people, a, b)?.nazev;

test('sourozenci', () => {
  expect(n('jan-novak-1890', 'marie-novakova-1892')).toBe('sestra');
  expect(n('marie-novakova-1892', 'jan-novak-1890')).toBe('bratr');
});

test('bratranec přes společné prarodiče', () => {
  const r = vztah(people, 'frantisek-novak-1921', 'karel-hajek-1921');
  expect(r.nazev).toBe('bratranec');
  expect(r.predci.sort()).toEqual(['barbora-mala-1862', 'vaclav-novak-1858']);
  expect(r.cesta).toEqual(['frantisek-novak-1921', 'jan-novak-1890', 'vaclav-novak-1858', 'marie-novakova-1892', 'karel-hajek-1921']);
});

test('teta a synovec', () => {
  expect(n('frantisek-novak-1921', 'marie-novakova-1892')).toBe('teta');
  expect(n('marie-novakova-1892', 'frantisek-novak-1921')).toBe('synovec');
  expect(n('josef-novak-1952', 'marie-novakova-1892')).toBe('prateta');
});

test('švagr (manžel sestry) a švagrová', () => {
  expect(n('jan-novak-1890', 'josef-hajek-1888')).toBe('švagr');
  expect(n('josef-hajek-1888', 'jan-novak-1890')).toBe('švagr');
  expect(n('josefa-pokorna-1895', 'marie-novakova-1892')).toBe('švagrová');
});

test('přímá linie a sňatek', () => {
  expect(n('petr-novak-1980', 'jan-novak-1890')).toBe('pradědeček');
  expect(n('jan-novak-1890', 'petr-novak-1980')).toBe('pravnuk');
  expect(n('josef-novak-1952', 'eva-dvorakova-1955')).toBe('manželka');
});

test('vzdálenější vztah má fallback', () => {
  expect(n('josef-novak-1952', 'karel-hajek-1921')).toBe('vzdálený příbuzný (společný předek 3. a 2. generace)');
});

test('žijící (mimo people) se do cesty nedostanou', () => {
  const bez = { ...people };
  delete bez['jan-novak-1890'];
  const r = vztah(bez, 'frantisek-novak-1921', 'karel-hajek-1921');
  expect(r).toBeNull();
});

test('JS dává pro všechny dvojice ukázky stejný název i cestu jako graf.py', () => {
  const ids = Object.keys(people);
  let pocet = 0;
  for (const a of ids) for (const b of ids) {
    const r = vztah(people, a, b);
    const p = vz[`${a}|${b}`];
    expect(r ? [r.nazev, r.cesta] : null).toEqual(p ?? null);
    pocet += r ? 1 : 0;
  }
  expect(pocet).toBeGreaterThan(1000);
});
