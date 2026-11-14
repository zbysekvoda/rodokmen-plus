// DNA linie ve vějíři předků (template/web/src/lib/dna.js).
import { expect, test } from 'bun:test';
import { vLinii, cislaLinie } from '../skills/rodokmen-plus/template/web/src/lib/dna.js';

test('Y-DNA: jen otcové u mužského kořene', () => {
  expect(cislaLinie('y', 'M', 5)).toEqual([2, 4, 8, 16, 32]);
  expect(vLinii(1, 'y', 'M')).toBe(true);
});

test('Y-DNA u ženského kořene nic nezvýrazní', () => {
  expect(cislaLinie('y', 'F', 5)).toEqual([]);
  expect(vLinii(1, 'y', 'F')).toBe(false);
});

test('mtDNA: jen matky, bez ohledu na pohlaví kořene', () => {
  expect(cislaLinie('mt', 'M', 5)).toEqual([3, 7, 15, 31, 63]);
  expect(cislaLinie('mt', 'F', 5)).toEqual([3, 7, 15, 31, 63]);
});

test('X-DNA, mužský kořen do 5. generace (prapradědové)', () => {
  expect(cislaLinie('x', 'M', 4)).toEqual([3, 6, 7, 13, 14, 15, 26, 27, 29, 30, 31]);
});

test('X-DNA, ženský kořen', () => {
  expect(cislaLinie('x', 'F', 3)).toEqual([2, 3, 5, 6, 7, 10, 11, 13, 14, 15]);
});

test('X-DNA: počty po generacích jsou Fibonacciho čísla', () => {
  const po = (sex) => [1, 2, 3, 4, 5, 6].map((g) => cislaLinie('x', sex, g).filter((k) => k >= 2 ** g).length);
  expect(po('M')).toEqual([1, 2, 3, 5, 8, 13]);
  expect(po('F')).toEqual([2, 3, 5, 8, 13, 21]);
});

test('implex: rozhoduje pozice, ne osoba (táž osoba na 12 a 15)', () => {
  expect(vLinii(12, 'x', 'M')).toBe(false);
  expect(vLinii(15, 'x', 'M')).toBe(true);
  expect(vLinii(15, 'mt', 'M')).toBe(true);
  expect(vLinii(12, 'mt', 'M')).toBe(false);
});
