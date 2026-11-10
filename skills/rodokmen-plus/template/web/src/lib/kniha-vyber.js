// Výběr obsahu „Knihy předků“ bez závislosti na site.json (čisté funkce, testy: tests/kniha_vyber.test.js v repu skillu).
// Data dodává src/lib/kniha.js; tady jen pravidla: co do knihy patří a jak se odkazuje mezi jejími částmi.

/** web.json → kniha → zapisy: "vybrane" | "vse" | false (cokoli jiného = výchozí "vybrane"). */
export const zapisyMode = (v) => (v === false || v === 'vse' ? v : 'vybrane');

/** Id kotvy v knize pro cíl odkazu webu (/osoba/x/ → osoba-x). */
export const anchorId = (kind, x) => `${kind}-${x}`;

/** Domy, kde žil nebo který držel někdo z knihy (předci = slugs). Vrací [{ h, pred: Set }] v pořadí houseList. */
export function selectHouses(houseList, slugs, homesOf) {
  const out = [];
  for (const h of houseList) {
    const pred = new Set();
    for (const o of [...(h.owners ?? []), ...(h.family ?? []), ...(h.people ?? [])]) if (o.person && slugs.has(o.person)) pred.add(o.person);
    for (const s of slugs) if ((homesOf(s) ?? []).some((b) => b.house === h.slug)) pred.add(s);
    if (pred.size) out.push({ h, pred });
  }
  return out;
}

const LINK = /<a href="\/(osoba|dum|zdroj|rod|misto|pribeh)\/([^/"#?]+)\/"[^>]*>([\s\S]*?)<\/a>/g;

/** Osoby, na které odkazuje HTML příběhu (rozbalené wiki odkazy [[osoba:…]] z export_web.py). */
export const linkedPeople = (html) => [...html.matchAll(LINK)].filter((m) => m[1] === 'osoba').map((m) => m[2]);

/** Příběhy, které zmiňují aspoň jednoho předka z knihy (žijící se nepočítají – nesmí příběh do knihy přitáhnout). */
export const selectStories = (stories, slugs) => stories.filter((s) => linkedPeople(s.html).some((x) => slugs.has(x)));

/**
 * Odkazy webu v HTML příběhu → odkazy v knize. Cíl, který v knize má kotvu (targets = Set id), dostane
 * <a class="ref" href="#id">, a CSS k němu přidá „→ s. N“ (target-counter). Cíl mimo knihu (osoba mimo linii,
 * žijící osoba, rod, místo) zůstane jen textem bez čísla strany.
 */
export const bookLinks = (html, targets) =>
  html.replace(LINK, (_, kind, x, label) => {
    const id = anchorId(kind, x);
    return targets.has(id) ? `<a class="ref" href="#${id}">${label}</a>` : `<span class="ref-out">${label}</span>`;
  });

/**
 * Zápisy do pramenů: "vse" = všechny zápisy osob knihy s výřezem; "vybrane" = jen s přepisem nebo překladem,
 * nejvýš `limit`; false = žádné. Řazeno podle data (dateKey).
 */
export function selectRecords(keys, records, mode, dateKey, limit = 12) {
  if (mode === false) return [];
  const list = [...new Set(keys)].map((k) => records[k]).filter((r) => r && r.img);
  list.sort((a, b) => dateKey(a.date) - dateKey(b.date));
  return mode === 'vse' ? list : list.filter((r) => r.orig || r.cs).slice(0, limit);
}

/** Použité knihy (matriky a další svazky) po archivech: [{ archive, volumes: [..] }] – z ukázaných i neukázaných zápisů. */
export function usedBooks(recs) {
  const by = new Map();
  for (const r of recs) {
    const a = r.archive || 'Ostatní prameny';
    const v = r.volume || r.vdesc || r.title;
    if (!by.has(a)) by.set(a, new Set());
    by.get(a).add(v);
  }
  return [...by].map(([archive, v]) => ({ archive, volumes: [...v].sort((x, y) => x.localeCompare(y, 'cs')) }))
    .sort((x, y) => x.archive.localeCompare(y.archive, 'cs'));
}

/** Box „Svět kolem“ u generace: id událostí z exportu (p.svet[gen - 1], výběr tools/udalosti.py → svet_kolem) → položky
 *  z site.events; neznámá id vypadnou, nejvýš 5. Prázdný seznam = box vynechat. */
export const svetKolem = (ids, events) => (ids ?? []).map((id) => events[id]).filter(Boolean).slice(0, 5);
