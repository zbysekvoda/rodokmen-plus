// Pásy historického kontextu na /osa/ (template/web/src/lib/osa.js): pruhy bez překryvu, limit pruhů, přednost váhy.
import { expect, test } from 'bun:test';
import { eventLanes, layout } from '../skills/rodokmen-plus/template/web/src/lib/osa.js';

const x = (y) => (y - 1800) * 6;
const ev = (id, od, d, vaha = 1) => ({ id, od, do: d, nazev: id, vaha });

test('překrývající se pásy jdou do různých pruhů, nepřekrývající do stejného', () => {
  const { bands, lanes } = eventLanes([ev('a', 1800, 1810), ev('b', 1805, 1806), ev('c', 1850, 1851)], x);
  const lane = Object.fromEntries(bands.map((b) => [b.id, b.lane]));
  expect(lane.a).not.toBe(lane.b);
  expect(lane.c).toBe(0);
  expect(lanes).toBe(2);
});

test('nejvýš maxLanes pruhů, vypadnou méně významné', () => {
  const evs = [ev('silna', 1800, 1801, 10), ev('slaba', 1800, 1801, 1), ev('stredni', 1800, 1801, 5)];
  const { bands, lanes } = eventLanes(evs, x, 2);
  expect(lanes).toBe(2);
  expect(bands.map((b) => b.id).sort()).toEqual(['silna', 'stredni']);
});

test('layout: kontext zapnutý posune řádky pod pásy, vypnutý ne', () => {
  const rows = [{ id: 'p', name: 'P', line: 'x', lineName: 'X', lineOrder: 0, b: { y: 1820, lo: 1820, hi: 1820, q: 'doc' }, d: { y: 1880, lo: 1880, hi: 1880, q: 'doc' } }];
  const events = [ev('a', 1830, 1840)];
  const off = layout(rows, { from: 1800, events, ctx: false });
  const on = layout(rows, { from: 1800, events, ctx: true });
  expect(off.ev.bands).toEqual([]);
  expect(on.ev.bands.length).toBe(1);
  expect(on.pos.p).toBeGreaterThan(off.pos.p);
});
