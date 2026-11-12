// Výřez rodokmenu na stránce příběhu (template/web/src/lib/vyrez.js).
import { expect, test } from 'bun:test';
import { vyrezStromu, osobyZTextu } from '../skills/rodokmen-plus/template/web/src/lib/vyrez.js';

const z = (...ks) => new Set(ks);

test('linie mezi odkazovanými předky se doplní, s manžely', () => {
  const v = vyrezStromu(z(2, 3, 4, 5, 8, 9), [9, 2]);
  expect(v).toEqual([[
    { gen: 3, pary: [{ otec: 8, matka: 9 }] },
    { gen: 2, pary: [{ otec: 4, matka: 5 }] },
    { gen: 1, pary: [{ otec: 2, matka: 3 }] },
  ]]);
});

test('nesouvisející předci tvoří samostatné větve, chybějící článek cestu přeruší', () => {
  const v = vyrezStromu(z(4, 5, 12, 26), [4, 26]); // 26 → 13 neznámý → 6
  expect(v.length).toBe(2);
  expect(v[0]).toEqual([{ gen: 2, pary: [{ otec: 4, matka: 5 }] }]);
  expect(v[1]).toEqual([{ gen: 4, pary: [{ otec: 26, matka: null }] }]);
});

test('linie otce a matky se spojí jen přes odkazovaného potomka', () => {
  expect(vyrezStromu(z(2, 3, 4, 5, 6, 7), [4, 6, 2]).length).toBe(2);
  expect(vyrezStromu(z(1, 2, 3, 4, 5, 6, 7), [4, 6, 1])).toEqual([[
    { gen: 2, pary: [{ otec: 4, matka: 5 }, { otec: 6, matka: 7 }] },
    { gen: 1, pary: [{ otec: 2, matka: 3 }] },
    { gen: 0, pary: [{ otec: null, matka: null, sam: 1 }] },
  ]]);
});

test('osoby mimo přímou linii (bez k) a duplicity se ignorují', () => {
  expect(vyrezStromu(z(2, 3), [undefined, null, 3, 3])).toEqual([[{ gen: 1, pary: [{ otec: 2, matka: 3 }] }]]);
  expect(vyrezStromu(z(2), [])).toEqual([]);
});

test('osobyZTextu najde odkazy na osoby v pořadí výskytu', () => {
  expect(osobyZTextu('[A](/osoba/a/) a [B](/osoba/b/#x) a <a href="/osoba/a/">')).toEqual(['a', 'b']);
});
