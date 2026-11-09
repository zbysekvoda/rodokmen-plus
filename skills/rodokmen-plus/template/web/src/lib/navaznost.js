// Časová návaznost pro /osa/: co v datech časově nesedí (narození dítěte po smrti rodiče, sňatek před narozením …).
// Myšlenka a pravidla podle mplisek/rodokmen-skill@cc35533 (MIT), tam jako Python v tools/chronologie.py:
// https://github.com/mplisek/rodokmen-skill/blob/cc35533cda7753a31e87f915fef6555542df1798/skills/rodokmen/tools/chronologie.py
// Tady jen jako vizuální upozornění na webu – tytéž rozpory hlásí i tools/kontrola.py (věcné kontroly), duplicitně se nepočítají v Pythonu.
// Upozornění padne jen tehdy, když rozpor platí pro všechna možná data v intervalech (rok bez dne = celý rok).
import { people, parseDate } from './data.js';

const POHROBEK_DNI = 280;     // dítě se může narodit až ~9 měsíců po smrti otce
const NEJISTE = ['prob', 'mh', 'fam'];
const DEN = 86400000;
const day = (y, m, d) => Math.floor(Date.UTC(y, m - 1, d) / DEN);

/** Interval dnů {lo, hi, text, approx} z textu data; rok bez měsíce = celý rok, „asi“ ± 5 let. */
function interval(text) {
  const d = parseDate(text);
  if (!d) return null;
  const pad = d.approx ? 5 : 0;
  const lo = d.d ? day(d.y, d.m, d.d) : d.m ? day(d.y, d.m, 1) : day(d.y - pad, 1, 1);
  const hi = d.d ? lo : d.m ? day(d.y, d.m + 1, 1) - 1 : day(d.y + pad + 1, 1, 1) - 1;
  return { lo, hi, text: text.slice(d.start, d.end).trim(), approx: d.approx };
}
const fact = (p, sign) => p.facts.find((f) => f.trimStart().startsWith(sign) && parseDate(f));
/** Narození / úmrtí z faktu, jinak z odhadu roku na ose (kromě „neznámé“). */
function event(p, sign, key) {
  const f = fact(p, sign);
  if (f) return interval(f.trimStart().slice(1));
  const e = p[key];
  if (!e || e.q === 'unk') return null;
  return { lo: day(e.lo, 1, 1), hi: day(e.hi + 1, 1, 1) - 1, text: e.lo === e.hi ? `${e.lo}` : `${e.lo}–${e.hi}`, approx: e.q !== 'doc' };
}
const let_ = (n) => `${n} ${n === 1 ? 'rok' : n >= 2 && n <= 4 ? 'roky' : 'let'}`;
const years = (a, b) => Math.floor((b - a) / 365.25);

/** [{ slug, text, mozna, osoby }] – slug je osoba, u které se na ose ukáže ⚠ (u pravidel rodič–dítě dítě). */
export function navaznost() {
  const ud = {};
  for (const p of Object.values(people)) {
    ud[p.slug] = { b: event(p, '*', 'birth'), d: p.alive ? null : event(p, '†', 'death'), m: fact(p, '×') ? interval(fact(p, '×').trimStart().slice(1)) : null };
  }
  const out = [];
  const add = (slug, text, data, osoby) => {
    const mozna = data.some((x) => x.approx) || osoby.some((s) => NEJISTE.includes(people[s].st));
    out.push({ slug, text: text + (mozna ? ' – údaje jsou nejisté, možná nesedí.' : ' – jeden z údajů asi nesedí.'), mozna, osoby });
  };
  for (const p of Object.values(people)) {
    const { b, d, m } = ud[p.slug], n = p.name, F = p.sex === 'F';
    if (b && d && d.hi < b.lo) add(p.slug, `${n}: úmrtí (${d.text}) je dřív než narození (${b.text})`, [b, d], [p.slug]);
    if (b && m && m.hi < b.lo) add(p.slug, `${n}: sňatek (${m.text}) je dřív než narození (${b.text})`, [b, m], [p.slug]);
    else if (b && m && years(b.lo, m.hi) < 12) add(p.slug, `${n}: při sňatku (${m.text}) by ${F ? 'jí' : 'mu'} bylo nejvýš ${let_(years(b.lo, m.hi))}`, [b, m], [p.slug]);
    if (m && d && m.lo > d.hi) add(p.slug, `${n}: sňatek (${m.text}) je až po úmrtí (${d.text})`, [m, d], [p.slug]);
    if (!b) continue;
    const [syn, syna, narodil] = F ? ['dcera', 'dcery', 'narodila'] : ['syn', 'syna', 'narodil'];
    for (const [rs, otec] of [[p.father, true], [p.mother, false]]) {
      const r = people[rs];
      if (!r) continue;
      const { b: rb, d: rd } = ud[rs];
      if (rd && b.lo - rd.hi > (otec ? POHROBEK_DNI : 0))
        add(p.slug, `${r.name} ${otec ? 'zemřel' : 'zemřela'} ${rd.text}, ${syn} ${n} se ${narodil} ${b.text}`, [b, rd], [p.slug, rs]);
      if (rb && b.hi < rb.lo)
        add(p.slug, `${r.name} se podle údajů ${otec ? 'narodil' : 'narodila'} (${rb.text}) až po narození ${syna} (${n}, ${b.text})`, [b, rb], [p.slug, rs]);
      else if (rb && years(rb.lo, b.hi) < 12)
        add(p.slug, `${r.name}: při narození ${syna} (${n}, ${b.text}) by ${otec ? 'mu' : 'jí'} bylo nejvýš ${let_(years(rb.lo, b.hi))}`, [b, rb], [p.slug, rs]);
    }
  }
  return out;
}
