// Jedna definice počtu předků a generací (template/web/src/lib/predci.js).
import { expect, test } from 'bun:test';
import { pocetPredku, doplnPocty } from '../skills/rodokmen-plus/template/web/src/lib/predci.js';

const os = (slug, k, gen, extra = {}) => ({ slug, k, gen, ...extra });

test('kořen (k = 1) se nepočítá, osoby bez k také ne', () => {
  const people = { a: os('a', 1, 0), b: os('b', 2, 1), c: os('c', 3, 1), d: os('d', 5, 2), x: os('x', null, null) };
  expect(pocetPredku(people)).toEqual({ predku: 3, generaci: 2 });
});

test('předek v implexu (víc Kekulého čísel) se počítá jednou', () => {
  const people = { a: os('a', 1, 0), b: os('b', 4, 2, { also: [{ k: 6 }] }), c: os('c', 2, 1) };
  expect(pocetPredku(people).predku).toBe(2);
});

test('bez předků je 0 předků i generací', () => {
  expect(pocetPredku({ a: os('a', 1, 0) })).toEqual({ predku: 0, generaci: 0 });
});

test('doplnPocty nahradí známé placeholdery a neznámé nechá', () => {
  expect(doplnPocty('{predku} předků ve {generaci} generacích, {nic}', { predku: 399, generaci: 13 })).toBe('399 předků ve 13 generacích, {nic}');
});
