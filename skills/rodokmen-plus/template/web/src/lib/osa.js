// Časová osa /osa/: rozvržení řádků. Sdílí ho statické SVG (build) i JS ostrůvek v prohlížeči.
export const NOW = 2026;
export const SORTS = { rod: 'rod', gen: 'generace', misto: 'místo', chrono: 'chronologicky' };
const by = (...fs) => (a, b) => { for (const f of fs) { const x = f(a), y = f(b); if (x < y) return -1; if (x > y) return 1; } return 0; };
const start = (r) => r.b.y ?? r.b.lo;

export function groupsOf(rows, sort) {
  const key = {
    rod: (r) => [r.lineOrder, r.lineName],
    gen: (r) => [r.gen ?? 99, r.gen == null ? 'Mimo přímou linii' : `${r.gen}. generace`],
    misto: (r) => [r.place ? 0 : 1, r.place || 'Místo neznámé'],
    chrono: (r) => [Math.floor(start(r) / 50) * 50, `${Math.floor(start(r) / 50) * 50}–${Math.floor(start(r) / 50) * 50 + 49}`],
  }[sort];
  const sorted = [...rows].sort(by((r) => key(r)[0], (r) => key(r)[1], start, (r) => r.name));
  const out = [];
  for (const r of sorted) {
    const [, label] = key(r);
    if (!out.length || out[out.length - 1].label !== label) out.push({ label, rows: [] });
    out[out.length - 1].rows.push(r);
  }
  return out;
}

// Historický kontext: pásy událostí (od–do) v pruzích nad osou životů. Pás je široký aspoň na svůj popisek.
// Nejvýš maxLanes pruhů: události se rozmisťují od nejvýznamnějších (vaha z exportu) do prvního pruhu, kde se
// nepřekryjí; co se nevejde, se při daném přiblížení nezobrazí (přiblížení uvolní místo). Vrací [{id, lane, x1, x2, w}].
export const EV_LANE = 17;
export function eventLanes(events, x, maxLanes = 5) {
  const lanes = [], out = [];
  for (const e of [...events].sort((a, b) => (b.vaha ?? 0) - (a.vaha ?? 0) || a.od - b.od || a.id.localeCompare(b.id))) {
    const x1 = x(e.od), w = Math.max(3, x(e.do + 1) - x1), x2 = x1 + Math.max(w, e.nazev.length * 5.6 + 8);
    const free = (l) => l.every(([a, b]) => x2 + 4 <= a || b + 4 <= x1);
    let lane = lanes.findIndex(free);
    if (lane < 0 && lanes.length < maxLanes) lane = lanes.push([]) - 1;
    if (lane < 0) continue;
    lanes[lane].push([x1, x2]);
    out.push({ id: e.id, lane, x1, x2: x1 + w, w });
  }
  return { bands: out, lanes: lanes.length };
}

// px na rok, výška řádku; vrací pozice řádků a nadpisů skupin (a pásy kontextu, když events a ctx)
export function layout(rows, { sort = 'rod', pxy = 6, hidden = new Set(), from, to = NOW + 4, events = [], ctx = false } = {}) {
  const ROW = 26, HEAD = 30;
  const x = (y) => Math.round((y - from) * pxy * 10) / 10;
  const ev = ctx && events.length ? eventLanes(events.filter((e) => e.do >= from), x) : { bands: [], lanes: 0 };
  const evTop = 36, TOP = 34 + (ev.lanes ? ev.lanes * EV_LANE + 12 : 0);
  let y = TOP;
  const heads = [], pos = {};
  for (const g of groupsOf(rows.filter((r) => !hidden.has(r.line)), sort)) {
    heads.push({ label: g.label, y: y + 18 });
    y += HEAD;
    for (const r of g.rows) { pos[r.id] = y; y += ROW; }
  }
  return { x, heads, pos, height: y + 26, width: x(to) + 10, ev: { ...ev, top: evTop, bottom: TOP - 6 } };
}

// tvar pruhu: vous na začátku (bl→bh), plný úsek, vous / rozplynutí na konci
export function bar(r, x) {
  const s = r.b.q === 'doc' ? r.b.y : r.b.hi;
  const e = r.alive ? NOW : r.d.q === 'doc' ? r.d.y : r.d.lo;
  return {
    in: r.b.q === 'doc' ? null : [x(r.b.lo), x(s)],
    solid: [x(s), Math.max(x(e), x(s) + 2)],
    out: r.alive || r.d.q === 'doc' ? null : [x(e), x(r.d.hi)],
    open: r.d?.q === 'unk',
  };
}
