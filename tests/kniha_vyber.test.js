// bun test tests/ – pravidla výběru obsahu „Knihy předků“ (template/web/src/lib/kniha-vyber.js)
import { test, expect } from 'bun:test';
import { zapisyMode, selectHouses, selectStories, bookLinks, selectRecords, usedBooks } from '../skills/rodokmen-plus/template/web/src/lib/kniha-vyber.js';

const dateKey = (d) => Number((d.match(/\d{4}/) || ['9999'])[0]);

test('zapisyMode: false, vse, jinak vybrane', () => {
  expect(zapisyMode(false)).toBe(false);
  expect(zapisyMode('vse')).toBe('vse');
  expect(zapisyMode(undefined)).toBe('vybrane');
  expect(zapisyMode('nesmysl')).toBe('vybrane');
});

test('selectHouses: dům přes držitele i bydliště, cizí dům ne', () => {
  const houses = [
    { slug: 'a-1', owners: [{ person: 'otec' }, { person: 'cizi' }] },
    { slug: 'b-2', owners: [] },
    { slug: 'c-3', owners: [{ person: 'cizi' }] },
  ];
  const homes = { matka: [{ house: 'b-2' }] };
  const out = selectHouses(houses, new Set(['otec', 'matka']), (s) => homes[s]);
  expect(out.map((x) => x.h.slug)).toEqual(['a-1', 'b-2']);
  expect([...out[0].pred]).toEqual(['otec']);
});

test('selectStories: jen příběhy s odkazem na předka z knihy', () => {
  const st = [
    { slug: 'x', html: '<p><a href="/osoba/otec/">Otec</a></p>' },
    { slug: 'y', html: '<p><a href="/osoba/zijici/">Petr</a> a <a href="/dum/a-1/">dům</a></p>' },
  ];
  expect(selectStories(st, new Set(['otec'])).map((s) => s.slug)).toEqual(['x']);
});

test('bookLinks: cíl v knize → ref s kotvou, mimo knihu → text bez čísla', () => {
  const html = '<a href="/osoba/otec/">Otec</a>, <a href="/osoba/soused/">Soused</a>, <a href="/dum/a-1/">čp. 1</a>, <a href="https://x.cz/">web</a>';
  const out = bookLinks(html, new Set(['osoba-otec', 'dum-a-1']));
  expect(out).toBe('<a class="ref" href="#osoba-otec">Otec</a>, <span class="ref-out">Soused</span>, <a class="ref" href="#dum-a-1">čp. 1</a>, <a href="https://x.cz/">web</a>');
});

test('selectRecords: vybrane jen s přepisem, vse všechny s výřezem, false nic', () => {
  const records = {
    a: { key: 'a', img: true, date: '1890', orig: 'x' },
    b: { key: 'b', img: true, date: '1850' },
    c: { key: 'c', img: false, date: '1800', cs: 'y' },
    d: { key: 'd', img: true, date: '1700', cs: 'y' },
  };
  expect(selectRecords(['a', 'b', 'c', 'd', 'a'], records, 'vybrane', dateKey).map((r) => r.key)).toEqual(['d', 'a']);
  expect(selectRecords(['a', 'b', 'c', 'd'], records, 'vse', dateKey).map((r) => r.key)).toEqual(['d', 'b', 'a']);
  expect(selectRecords(['a'], records, false, dateKey)).toEqual([]);
  expect(selectRecords(['a', 'd'], records, 'vybrane', dateKey, 1).map((r) => r.key)).toEqual(['d']);
});

test('usedBooks: svazky po archivech bez duplicit', () => {
  const out = usedBooks([
    { archive: 'SOA Zámrsk', volume: 'N Holice 1880' },
    { archive: 'SOA Zámrsk', volume: 'N Holice 1880' },
    { archive: 'SOA Zámrsk', volume: 'O Holice 1900' },
    { archive: '', vdesc: 'od rodiny' },
  ]);
  expect(out).toEqual([
    { archive: 'Ostatní prameny', volumes: ['od rodiny'] },
    { archive: 'SOA Zámrsk', volumes: ['N Holice 1880', 'O Holice 1900'] },
  ]);
});
