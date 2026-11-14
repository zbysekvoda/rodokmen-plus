// „Jak jsme příbuzní?“ – template/web/src/lib/pribuzni.js na ukázkových datech; názvy musí sedět s tools/graf.py.
import { expect, test } from 'bun:test';
import { nazevPokrevni, vztah } from '../skills/rodokmen-plus/template/web/src/lib/pribuzni.js';

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

test('strýc a synovec z 2. kolena v ukázce (bratranec otce / syn bratrance)', () => {
  expect(n('josef-novak-1952', 'karel-hajek-1921')).toBe('strýc z 2. kolena');
  expect(n('karel-hajek-1921', 'josef-novak-1952')).toBe('synovec z 2. kolena');
  expect(n('petr-novak-1980', 'karel-hajek-1921')).toBe('prastrýc z 2. kolena');
});

// fiktivní Novákovi: sourozenci František 1921 a Ludmila 1923, jejich děti Josef 1952, Jana 1956 a Pavel Bureš 1950
const P = (father, mother, sex) => ({ father, mother, spouses: [], sex });
const nov = {
  'vaclav': P(null, null, 'M'), 'anna': P(null, null, 'F'),
  'frantisek': P('vaclav', 'anna', 'M'), 'ludmila': P('vaclav', 'anna', 'F'),
  'josef': P('frantisek', null, 'M'), 'jana': P('frantisek', null, 'F'),
  'pavel': P(null, 'ludmila', 'M'), 'vera': P(null, 'ludmila', 'F'),
  'petr': P('josef', null, 'M'), 'lucie': P('josef', null, 'F'),
  'tomas': P('pavel', null, 'M'), 'hana': P('pavel', null, 'F'),
  'ondrej': P('petr', null, 'M'), 'eliska': P('tomas', null, 'F'),
};
const m = (a, b) => vztah(nov, a, b)?.nazev;

test('bratranec a sestřenice z 2. kolena', () => {
  expect(m('pavel', 'josef')).toBe('bratranec');
  expect(m('petr', 'tomas')).toBe('bratranec z 2. kolena');
  expect(m('petr', 'hana')).toBe('sestřenice z 2. kolena');
  expect(m('ondrej', 'eliska')).toBe('sestřenice z 3. kolena');
});

test('o generaci vedle: strýc/teta z 2. kolena nahoru, synovec/neteř z 2. kolena dolů', () => {
  expect(m('petr', 'pavel')).toBe('strýc z 2. kolena');
  expect(m('petr', 'vera')).toBe('teta z 2. kolena');
  expect(m('pavel', 'petr')).toBe('synovec z 2. kolena');
  expect(m('pavel', 'lucie')).toBe('neteř z 2. kolena');
  expect(m('ondrej', 'vera')).toBe('prateta z 2. kolena');
  expect(m('vera', 'ondrej')).toBe('prasynovec z 2. kolena');
  expect(m('ondrej', 'hana')).toBe('teta z 3. kolena');
  expect(m('hana', 'ondrej')).toBe('synovec z 3. kolena');
});

test('příliš vzdálený vztah má obecný fallback', () => {
  expect(nazevPokrevni(6, 6, 'M')).toBe('vzdálený příbuzný (společný předek 6. a 6. generace)');
  expect(nazevPokrevni(7, 2, 'F')).toBe('vzdálená příbuzná (společný předek 7. a 2. generace)');
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
