// „Vějíř potomků“ (/potomci/<slug>/): sunburst od zvolené osoby – ve středu ona, v prstencích děti, vnuci…
// Úhel osoby ∝ počet listů jejího podstromu (potomků je nepravidelně), barva podle větve dítěte kořene.
// Generuje se při buildu (Astro), ne ve fan_chart.py: data (children, alive) jsou v site.json, stránka je statická,
// a předkový vějíř zůstává nedotčený.
import { people } from './data.js';
import { isPublic } from './kniha.js';

/** Veřejné děti osoby (žijící vypuštěni i s podstromem – pravidlo webu, reference/soukromi.md). */
const kids = (p) => (p.children ?? []).filter((c) => typeof c === 'string' && people[c] && isPublic(people[c]));

/** Má stránku vějíře potomků: veřejná osoba s aspoň jedním veřejným dítětem. */
export const hasDescFan = (p) => !!p && isPublic(p) && kids(p).length > 0;
export const descFanSlugs = () => Object.values(people).filter(hasDescFan).map((p) => p.slug);

/**
 * Strom potomků: { p, kids, leaves, depth, again } – again = osoba se ve stromu už objevila
 * (sňatek mezi potomky), dál se nerozbaluje a v grafu má zlatý okraj.
 */
export function descTree(slug) {
  const seen = new Set();
  const walk = (s) => {
    const again = seen.has(s);
    seen.add(s);
    const ch = again ? [] : kids(people[s]).map(walk);
    return { p: people[s], kids: ch, again, leaves: ch.reduce((a, c) => a + c.leaves, 0) || 1, depth: ch.length ? 1 + Math.max(...ch.map((c) => c.depth)) : 0 };
  };
  return walk(slug);
}

const esc = (t) => String(t ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const R0 = 70, W = 120;
const pt = (r, a) => [r * Math.sin(a), -r * Math.cos(a)].map((v) => +v.toFixed(2));

function arc(r1, r2, a1, a2) {
  if (a2 - a1 >= 2 * Math.PI - 1e-6) {
    // celý prstenec: dva půloblouky (jeden oblouk 360° SVG neumí)
    const m = a1 + Math.PI;
    return `M${pt(r2, a1)}A${r2},${r2} 0 1 1 ${pt(r2, m)}A${r2},${r2} 0 1 1 ${pt(r2, a1)}M${pt(r1, a1)}A${r1},${r1} 0 1 0 ${pt(r1, m)}A${r1},${r1} 0 1 0 ${pt(r1, a1)}Z`;
  }
  const big = a2 - a1 > Math.PI ? 1 : 0;
  return `M${pt(r1, a1)}L${pt(r2, a1)}A${r2},${r2} 0 ${big} 1 ${pt(r2, a2)}L${pt(r1, a2)}A${r1},${r1} 0 ${big} 0 ${pt(r1, a1)}Z`;
}

/** SVG vějíře potomků (viewBox kolem celého kruhu), segmenty jsou odkazy na stránky osob. */
export function descFanSvg(slug) {
  const t = descTree(slug);
  const n = t.kids.length;
  const R = R0 + t.depth * W + 10;
  const segs = [];
  const place = (node, gen, a1, a2, hue) => {
    const r1 = R0 + (gen - 1) * W, r2 = r1 + W - 3;
    const mid = (a1 + a2) / 2, rm = (r1 + r2) / 2;
    const fill = `hsl(${hue} 45% ${Math.min(88, 62 + gen * 4)}%)`;
    // text radiálně podél osy segmentu; vejde se, když je oblouk na středu aspoň ~13 jednotek
    const room = Math.min((a2 - a1) * rm, W * 0.9);
    // plný prstenec (jediné dítě): popisek vodorovně nahoře; jinak radiálně, dolní polovina otočená, ať se nečte vzhůru nohama
    const full = a2 - a1 >= 2 * Math.PI - 1e-6;
    let deg = full ? 0 : (mid * 180) / Math.PI - 90;
    if (!full && mid > Math.PI) deg += 180;
    const fs = Math.min(15, Math.max(7, room * 0.42));
    const max = full ? 40 : Math.floor((W - 8) / (fs * 0.55));
    const name = node.p.name.length > max ? node.p.name.slice(0, max - 1) + '…' : node.p.name;
    const label = room >= 12
      ? `<text transform="translate(${pt(rm, full ? 0 : mid)}) rotate(${deg.toFixed(1)})" font-size="${fs.toFixed(1)}" text-anchor="middle"><tspan x="0" dy="-0.15em">${esc(name)}</tspan><tspan x="0" dy="1.1em" class="y">${esc(node.p.years ?? '')}</tspan></text>`
      : '';
    segs.push(`<a href="/osoba/${node.p.slug}/" data-slug="${node.p.slug}"><title>${esc(node.p.name)}${node.p.years ? ` (${esc(node.p.years)})` : ''}${node.again ? ' – ve stromu potomků víckrát' : ''}</title><path d="${arc(r1, r2, a1, a2)}" fill="${fill}"${node.again ? ' class="again"' : ''}/>${label}</a>`);
    let a = a1;
    for (const c of node.kids) {
      const b = a + ((a2 - a1) * c.leaves) / node.leaves;
      place(c, gen + 1, a, b, hue);
      a = b;
    }
  };
  let a = 0;
  t.kids.forEach((c, i) => {
    const b = a + (2 * Math.PI * c.leaves) / t.leaves;
    place(c, 1, a, b, Math.round((i * 360) / Math.max(n, 1) + 25) % 360);
    a = b;
  });
  const root = `<a href="/osoba/${t.p.slug}/"><title>${esc(t.p.name)}</title><circle r="${R0 - 3}" class="root"/><text font-size="13" text-anchor="middle"><tspan x="0" dy="-0.2em">${esc(t.p.name.length > 18 ? t.p.name.slice(0, 17) + '…' : t.p.name)}</tspan><tspan x="0" dy="1.2em" class="y">${esc(t.p.years ?? '')}</tspan></text></a>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${-R} ${-R} ${2 * R} ${2 * R}" class="desc-fan" role="img" aria-label="Vějíř potomků: ${esc(t.p.name)}"><g class="desc-links">${segs.join('')}${root}</g></svg>`;
}
