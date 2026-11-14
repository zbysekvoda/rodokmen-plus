#!/usr/bin/env python3
"""Vějíř předků (360°) z data/osoby.py jako SVG.
Použití: fan_chart.py <out_dir> [--koren <klíč>]                       (plakát: SVG + HTML s nadpisem a legendou, PNG přes Chrome, je-li k dispozici)
         fan_chart.py <out_file.svg> --web <hrefs.json>  (holé klikací SVG pro web – volá ho export_web.py)
Volitelně --generaci <N>: nejvýš N generací včetně kořene (Kniha předků: web.json → kniha.generaci); prstence se
roztáhnou na celý poloměr. Bez něj plná hloubka (nejvýš 11 generací)."""
import html, itertools, json, math, os, re, subprocess, sys
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, "vystupy")
WEB = "--web" in sys.argv
KOREN = sys.argv[sys.argv.index("--koren") + 1] if "--koren" in sys.argv else None   # klíč z KORENY (nebo id osoby); výchozí = hlavní kořen
HREFS = {int(k): v for k, v in json.load(open(sys.argv[sys.argv.index("--web") + 1])).items()} if WEB else {}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prostredi import najdi_chrome   # společné s kniha_pdf.py
CHROME = najdi_chrome()

ns = {}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import graf; ns.update(graf.nacti_legacy(KOREN))
P, LINES, SAME = ns["P"], ns.get("LINES", {}), ns.get("SAME", {})
# rody leží v jedné generaci (obvykle pradědečci 8–15; při kořeni dítěti 16–31) – barvy podle pořadí rodů
LG = (min(LINES).bit_length() - 1) if LINES else 3
WEBCFG = json.load(open(os.path.join(ROOT, "data", "web.json"), encoding="utf-8")) if os.path.exists(os.path.join(ROOT, "data", "web.json")) else {}

W, H = (4520, 4520) if WEB else (4600, 5650)
CX, CY = (2260, 2260) if WEB else (W / 2, 2760)
RINGS = [(0, 240), (240, 440), (440, 650), (650, 880), (880, 1100), (1100, 1380),
         (1380, 1640), (1640, 1870), (1870, 2010), (2010, 2130), (2130, 2240)]
if "--generaci" in sys.argv:   # omezená hloubka (kniha): jen prvních N prstenců, roztažených na původní vnější poloměr
    try:
        GENERACI = int(sys.argv[sys.argv.index("--generaci") + 1])
    except (IndexError, ValueError):
        sys.exit("--generaci chce celé číslo ≥ 1")
    if GENERACI < 1:
        sys.exit("--generaci chce celé číslo ≥ 1")
    if GENERACI < len(RINGS):
        _f = RINGS[-1][1] / RINGS[GENERACI - 1][1]
        RINGS = [(round(a * _f), round(b * _f)) for a, b in RINGS[:GENERACI]]
PALETA = ["#EFB45F", "#F09A78", "#E58AA6", "#B99AE0", "#86B8E8", "#6FCBB9", "#9CD17A", "#D3D46A"]
BASE = {k: PALETA[i % len(PALETA)] for i, k in enumerate(sorted(LINES))}
BASE0 = PALETA[0]
LIGHT = {3: 0.0, 4: 0.18, 5: 0.32, 6: 0.44, 7: 0.55, 8: 0.64, 9: 0.72, 10: 0.78}
SIDE_COL = {0: "#E9DFCF", 1: "#D6E2EC"}          # father / mother half, generations 1–2
EMPTY, FONT = "#ECE8E0", "Helvetica Neue, Helvetica, Arial, sans-serif"
MINF = {5: 15, 6: 13, 7: 11, 8: 9.5, 9: 8.5, 10: 7.5}
MAXF = {5: 26, 6: 22, 7: 18, 8: 14, 9: 11, 10: 9}


def mix(hex_, t):
    r, g, b = (int(hex_[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % tuple(round(c + (255 - c) * t) for c in (r, g, b))


def years(y):
    y = (y or "").strip()
    ys = re.findall(r"\d{4}", y)
    if not ys:
        return ""
    approx = "≈" if re.match(r"^(asi|≈)", y) else ""
    head, dash, tail = y.partition("–")
    if y.startswith(("?", "†")) or (dash and not re.search(r"\d", head)) or re.match(r"po\b", y):
        # neznámé narození: ukázat jen úmrtí („? – před 1743“ → „† před 1743“, „– po 1921“ → „žil 1921“)
        if re.search(r"\bpo\b", tail or y):
            return "žil " + ys[-1]
        return "† " + ("před " if "před" in y else "") + ys[-1]
    if y.startswith("*"):
        return "* " + ys[0]
    if len(ys) == 1:
        return approx + ys[0] + ("–?" if dash else "")
    second = "?" if "před" in tail else ("po " if re.search(r"\bpo\b", tail) else "") + \
        ("≈" if re.search(r"(asi|≈)", tail) else "") + ys[-1]
    return f"{approx}{ys[0]}–{second}"


def pt(r, a):
    t = math.radians(a)
    return CX + r * math.sin(t), CY - r * math.cos(t)


def sector(r0, r1, a0, a1):
    large = 1 if a1 - a0 > 180 else 0
    x0, y0 = pt(r1, a0); x1, y1 = pt(r1, a1); x2, y2 = pt(r0, a1); x3, y3 = pt(r0, a0)
    if r0 == 0:
        return f"M{CX},{CY} L{x0:.1f},{y0:.1f} A{r1},{r1} 0 {large} 1 {x1:.1f},{y1:.1f} Z"
    return (f"M{x0:.1f},{y0:.1f} A{r1},{r1} 0 {large} 1 {x1:.1f},{y1:.1f} "
            f"L{x2:.1f},{y2:.1f} A{r0},{r0} 0 {large} 0 {x3:.1f},{y3:.1f} Z")


def gen(k):
    return k.bit_length() - 1


# Sloučení sdílených předků (pedigree collapse) převzato z forku vmi43 (Vaclav Miller), commit 5bd5904:
# https://github.com/vmi43/rodokmen-skill/blob/5bd59042d10714fe914bd6c48c54c7b065dd39ea/skills/rodokmen/tools/fan_chart.py
# Úprava rodokmen-plus: výskyt, který sloučit nejde, se nekreslí znovu se jménem a větví, ale jako šrafovaná
# značka „↺ viz č. N“ až k okraji vějíře – opakování je vidět, osoba se nevykreslí dvakrát.
def canon(k):
    """Slot → kanonický slot: předek (a celá jeho větev výš) vícekrát v rodokmenu se bere z prvního výskytu (SAME)."""
    for j in range(gen(k) + 1):
        if (k >> j) in SAME:
            return canon((SAME[k >> j] << j) | (k & ((1 << j) - 1)))
    return k


def parents_of(k, flags):
    return (2 * k + 1, 2 * k) if flags.get(k) else (2 * k, 2 * k + 1)


def pos(k, flags):
    """Pořadí slotu v jeho prstenci (zleva doprava) při daném otočení rodičů."""
    g, idx = gen(k), 0
    for lev in range(1, g + 1):
        node = k >> (g - lev)
        idx = idx * 2 + ((node & 1) ^ (1 if flags.get(node >> 1) else 0))
    return idx


def sibling_pairs():
    """Dvojice slotů (pa, pb) téhož prstence, jejichž oba rodiče jsou táž dvojice osob (SAME) – sourozenci."""
    out = set()
    for b, a in SAME.items():
        pa, pb = a // 2, b // 2
        if pa != pb and gen(pa) == gen(pb) and canon(pa) in P and canon(pb) in P \
                and canon(2 * pa) == canon(2 * pb) and canon(2 * pa + 1) == canon(2 * pb + 1):
            out.add((min(pa, pb), max(pa, pb)))
    return sorted(out)


def solve_flags():
    """Které páry rodičů otočit (muž ↔ žena), aby sourozenci stáli vedle sebe; co nejméně otočení."""
    flags, locked = {}, set()
    for pa, pb in sibling_pairs():
        var, x, y = set(), pa, pb
        while x != y:
            x >>= 1; y >>= 1
            var |= {x, y}
        var.discard(1)
        free = sorted(var - locked)
        for r in range(min(len(free), 6) + 1):
            hit = next((c for c in itertools.combinations(free, r)
                        if abs(pos(pa, {**flags, **dict.fromkeys(c, True)}) - pos(pb, {**flags, **dict.fromkeys(c, True)})) == 1), None)
            if hit is not None:
                flags.update(dict.fromkeys(hit, True))
                locked |= var
                break
    return flags


def build_cells(flags):
    """Buňky po prstencích; úhel jako podíl 0–1. Sourozenci vedle sebe sdílejí rodiče: ti dostanou dvojnásobnou šířku
    (merged=True). Opakovaný předek, kterého sloučit nejde, je buňka repeat=True bez rodičů."""
    rings = {0: [dict(k=1, f0=0.0, f1=1.0)]}
    for g in range(0, len(RINGS) - 1):
        out = []
        cells, i = rings[g], 0
        while i < len(cells):
            c = cells[i]; i += 1
            if c.get("repeat") or canon(c["k"]) not in P:
                continue
            k, nxt = c["k"], cells[i] if i < len(cells) else None
            f1, merged = c["f1"], False
            if (nxt and not nxt.get("repeat") and abs(c["f1"] - nxt["f0"]) < 1e-9 and canon(nxt["k"]) in P
                    and canon(2 * k) in P and canon(2 * k + 1) in P
                    and (canon(2 * k), canon(2 * k + 1)) == (canon(2 * nxt["k"]), canon(2 * nxt["k"] + 1))):
                f1, merged = nxt["f1"], True; i += 1
            half = (f1 - c["f0"]) / 2
            for j, pk in enumerate(parents_of(k, flags) if g else (2, 3)):
                cell = dict(k=pk, f0=c["f0"] + j * half, f1=c["f0"] + (j + 1) * half, merged=merged)
                if not merged and pk in SAME:
                    cell["repeat"] = SAME[pk]
                out.append(cell)
        rings[g + 1] = out
    return [c for g in sorted(rings) for c in rings[g]]


def fill(k):
    g = gen(k); p = P.get(canon(k))
    if p is None or p.get("st") == "unk":
        return EMPTY
    if g == 0:
        return "#5B4A3A"
    if g < LG:
        return SIDE_COL[(k >> (g - 1)) & 1]
    c = mix(BASE.get(k >> (g - LG), PALETA[0]), LIGHT[min(g - LG + 3, 10)])
    return mix(c, 0.45) if p.get("st") in ("prob", "mh") else c


def fit(text, avail, fmax, fmin):
    return max(fmin, min(fmax, avail / (0.56 * max(len(text), 1))))


paths, defs, texts, links = [], [], [], []
REPEAT_COL = "#D9D2C6"
defs.append('<pattern id="fan-repeat" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<rect width="14" height="14" fill="{REPEAT_COL}"/><rect width="5" height="14" fill="#C4BBAD"/></pattern>')
n_merged = n_repeat = 0
for cell in build_cells(solve_flags()):
    k = cell["k"]
    g = gen(k)
    r0, r1 = RINGS[g]
    a0, a1 = (0, 360) if g == 0 else (180 + cell["f0"] * 360, 180 + cell["f1"] * 360)
    ck = canon(k)
    if cell.get("repeat"):   # opakovaný předek: šrafovaná značka přes zbytek vějíře, žádné jméno ani větev
        n_repeat += 1
        rr = RINGS[-1][1]
        d = sector(r0, rr, a0, a1)
        paths.append(f'<path class="fan-repeat fan-seg" data-k="{k}" d="{d}" fill="url(#fan-repeat)" stroke="#8A7F70" stroke-width="2" '
                     f'stroke-dasharray="10 6" vector-effect="non-scaling-stroke"/>')
        p = P.get(ck, {})
        lab = f"↺ viz č. {ck}"
        am, rm = (a0 + a1) / 2, (r0 + r1) / 2
        f1 = min(40, max(7, math.radians(a1 - a0) * rm / 1.4), (r1 - r0) / (0.56 * len(lab)) if g > 4 else 40)
        rot = am - 90 if (am % 360) < 180 else am + 90
        if g <= 4:
            rot = am if (am % 360) <= 90 or (am % 360) >= 270 else am + 180
        x, y = pt(rm, am)
        texts.append(f'<text transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})" y="{f1 * 0.35:.1f}" text-anchor="middle" '
                     f'font-size="{f1:.1f}" font-style="italic" fill="#4A4036">{html.escape(lab)}</text>')
        if ck in HREFS:
            links.append(f'<a href="{HREFS[ck]}" class="fan-repeat-link" data-same="{ck}"><title>{html.escape(p.get("n", ""))} – '
                         f'v rodokmenu znovu (sdílený předek), větev viz č. {ck}</title><path d="{d}"/></a>')
        continue
    if g == 0:
        paths.append(f'<circle class="fan-seg" data-k="1" cx="{CX}" cy="{CY}" r="{r1}" fill="{fill(k)}" stroke="#fff" stroke-width="3"/>')
    else:
        paths.append(f'<path class="fan-seg" data-k="{k}" d="{sector(r0, r1, a0, a1)}" fill="{fill(k)}" stroke="#FBF8F2" stroke-width="{3 if g < 6 else 1.6}"/>')
    if cell.get("merged") and ck in P:   # sloučení předci sourozenců: přerušovaný obrys = sdílení více liniemi
        n_merged += 1
        paths.append(f'<path class="fan-merged" d="{sector(r0, r1, a0, a1)}" fill="none" stroke="#7A5C3E" stroke-width="2" '
                     f'stroke-dasharray="8 5" vector-effect="non-scaling-stroke"/>')
    p = P.get(ck)
    if not p:
        continue
    k = ck   # LINES a odkazy podle kanonického čísla
    name, yrs, st = p["n"], years(p.get("y")), p.get("st")
    if k in HREFS:
        shape = (f'<circle cx="{CX}" cy="{CY}" r="{r1}"/>' if g == 0 else f'<path d="{sector(r0, r1, a0, a1)}"/>')
        note = " (sdílený předek – společný více liniím)" if cell.get("merged") else ""
        links.append(f'<a href="{HREFS[k]}" data-k="{k}"><title>{html.escape(name)} {html.escape(yrs)}{note}</title>{shape}</a>')
    unknown = st == "unk"
    style = 'font-style="italic" fill="#8A8278"' if unknown else ('font-style="italic" fill="#2B2620"' if st in ("prob", "mh") else 'fill="#1F1A15"')
    if g == 0:
        texts.append(f'<text x="{CX}" y="{CY - 8}" text-anchor="middle" font-size="44" font-weight="700" fill="#FFF8EE">{html.escape(name)}</text>')
        texts.append(f'<text x="{CX}" y="{CY + 46}" text-anchor="middle" font-size="34" fill="#F1E3CF">{html.escape(yrs)}</text>')
        continue
    am = (a0 + a1) / 2
    if g <= 4:   # tangential text on arcs
        rm = (r0 + r1) / 2
        lines = []
        if k in LINES:
            lines.append((LINES[k][0].upper(), 21, 'font-weight="700" letter-spacing="4" fill="#5A4632"'))
        lines.append((name, {1: 40, 2: 34, 3: 30, 4: 27}[g], f'font-weight="600" {style}'))
        if yrs:
            lines.append((yrs, {1: 30, 2: 27, 3: 24, 4: 22}[g], f'{style}'))
        gap = [s * 1.25 for _, s, _ in lines]
        total = sum(gap)
        bottom = 90 < (am % 360) < 270
        # radii from outer to inner as read top-to-bottom
        cur = rm + total / 2
        order = []
        for (t, s, a), h in zip(lines, gap):
            cur -= h
            order.append((t, s, a, cur + h * 0.28))
        if bottom:   # read inner→outer, so reverse radii
            radii = [o[3] for o in order][::-1]
            order = [(t, s, a, r + s * 0.55) for (t, s, a, _), r in zip(order, radii)]
        for j, (t, s, a, r) in enumerate(order):
            pid = f"p{cell['k']}_{j}"
            pad = min(3.0, (a1 - a0) * 0.04)
            b0, b1 = a0 + pad, a1 - pad
            arc_len = math.radians(b1 - b0) * r
            s = min(s, arc_len / (0.56 * max(len(t), 1)))
            if bottom:
                xa, ya = pt(r, b1); xb, yb = pt(r, b0)
                d = f"M{xa:.1f},{ya:.1f} A{r:.1f},{r:.1f} 0 {1 if b1 - b0 > 180 else 0} 0 {xb:.1f},{yb:.1f}"
            else:
                xa, ya = pt(r, b0); xb, yb = pt(r, b1)
                d = f"M{xa:.1f},{ya:.1f} A{r:.1f},{r:.1f} 0 {1 if b1 - b0 > 180 else 0} 1 {xb:.1f},{yb:.1f}"
            defs.append(f'<path id="{pid}" d="{d}" fill="none"/>')
            texts.append(f'<text font-size="{s:.1f}" {a}><textPath href="#{pid}" startOffset="50%" text-anchor="middle">{html.escape(t)}</textPath></text>')
    else:        # radial text
        rm = (r0 + r1) / 2
        depth = (r1 - r0) - 22
        arc = math.radians(a1 - a0) * rm
        f1 = fit(name, depth, MAXF[g], MINF[g])
        f2 = fit(yrs, depth, MAXF[g] * 0.85, MINF[g] * 0.9) if yrs else 0
        two = yrs and arc >= (f1 + f2) * 1.15
        if not two:
            f1 = min(f1, arc / 1.25)
        rot = am - 90 if (am % 360) < 180 else am + 90
        x, y = pt(rm, am)
        tw = f'transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})"'
        if two:
            h = (f1 + f2) * 1.08
            texts.append(f'<g {tw}><text y="{-h / 2 + f1 * 0.85:.1f}" text-anchor="middle" font-size="{f1:.1f}" font-weight="600" {style}>{html.escape(name)}</text>'
                         f'<text y="{h / 2 - f2 * 0.15:.1f}" text-anchor="middle" font-size="{f2:.1f}" {style}>{html.escape(yrs)}</text></g>')
        else:
            texts.append(f'<g {tw}><text y="{f1 * 0.35:.1f}" text-anchor="middle" font-size="{f1:.1f}" font-weight="600" {style}>{html.escape(name)}</text></g>')

# statistics
known = [k for k, p in P.items() if k > 1 and not p["n"].startswith("otec neuveden")]
doc = [k for k in known if P[k].get("st") == "doc"]
zpath = os.path.join(ROOT, "data", "zaznamy.json")
recs = json.load(open(zpath, encoding="utf-8")) if os.path.exists(zpath) else []
maxg = max(gen(k) for k in P)

title = (f'<text x="{W / 2}" y="250" text-anchor="middle" font-family="Georgia, \'Times New Roman\', serif" font-size="128" fill="#3B2E22">{html.escape(WEBCFG.get("nazev", "Rodokmen"))}</text>'
         f'<text x="{W / 2}" y="370" text-anchor="middle" font-size="50" fill="#6B5A48">{len(known)} známých předků v {maxg + 1} generacích · {len(doc)} doloženo matrikou · {len(recs)} matričních zápisů</text>')

lx, ly = 300, CY + 2240 + 170
legend = []
items = [(k, LINES[k][0]) for k in sorted(LINES)]
desc = {k: (LINES[k][1].split(";")[0].split(".")[0])[:70] for k, _ in items}
for idx, (k, nm) in enumerate(items):
    col, row = idx // 4, idx % 4
    x, y = lx + col * 1950, ly + row * 78
    legend.append(f'<rect x="{x}" y="{y - 40}" width="52" height="52" rx="8" fill="{BASE[k]}"/>'
                  f'<text x="{x + 76}" y="{y}" font-size="40"><tspan font-weight="700" fill="#3B2E22">{html.escape(nm)}</tspan>'
                  f'<tspan fill="#5E5245"> – {html.escape(desc[k])}</tspan></text>')
sy = ly + 4 * 78 + 50
legend.append(f'<rect x="{lx}" y="{sy - 34}" width="44" height="44" rx="6" fill="{mix(BASE0, 0.2)}"/>'
              f'<text x="{lx + 64}" y="{sy}" font-size="36" fill="#3B2E22">doloženo matrikou</text>'
              f'<rect x="{lx + 520}" y="{sy - 34}" width="44" height="44" rx="6" fill="{mix(mix(BASE0, 0.2), 0.45)}"/>'
              f'<text x="{lx + 584}" y="{sy}" font-size="36" font-style="italic" fill="#3B2E22">pravděpodobné</text>'
              f'<rect x="{lx + 1000}" y="{sy - 34}" width="44" height="44" rx="6" fill="{EMPTY}"/>'
              f'<text x="{lx + 1064}" y="{sy}" font-size="36" fill="#3B2E22">zatím neznámé</text>'
              f'<text x="{lx + 1500}" y="{sy}" font-size="36" fill="#5E5245">uprostřed {html.escape(P[1]["n"].split()[0])}, každý prstenec = o generaci starší; vlevo otcova, vpravo matčina strana</text>')
footer = (f'<text x="{W / 2}" y="{H - 50}" text-anchor="middle" font-size="36" fill="#7A6B5B">'
          f'{html.escape(WEBCFG.get("zapati", ""))}</text>')

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">'
       f'<rect width="{W}" height="{H}" fill="#FBF8F2"/><defs>{"".join(defs)}</defs>'
       f'{title}{"".join(paths)}{"".join(texts)}{"".join(legend)}{footer}</svg>')
if WEB:
    open(OUT, "w", encoding="utf-8", newline="\n").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="{FONT}" class="fan" data-sex="{P[1].get("sex", "")}">'
        f'<defs>{"".join(defs)}</defs>{"".join(paths)}{"".join(texts)}<g class="fan-links">{"".join(links)}</g></svg>')
    print(OUT, len(links), "odkazů,", n_merged, "sloučených sdílených předků,", n_repeat, "opakování")
    sys.exit(0)
os.makedirs(OUT, exist_ok=True)
svg_path = os.path.join(OUT, "rodokmen_vejir.svg")
html_path = os.path.join(OUT, "rodokmen_vejir.html")
png_path = os.path.join(OUT, "rodokmen_vejir.png")
open(svg_path, "w", encoding="utf-8", newline="\n").write(svg)
open(html_path, "w", encoding="utf-8", newline="\n").write(f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#FBF8F2}}</style>{svg}')
import shutil, tempfile
if not CHROME:
    print(svg_path, "(PNG nevytvořen – chybí Google Chrome; HTML otevřete v prohlížeči a vytiskněte do PDF)")
    sys.exit(0)
prof = tempfile.mkdtemp(prefix="fanchart-")
before = os.path.getmtime(png_path) if os.path.exists(png_path) else 0
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={prof}",
                "--force-device-scale-factor=1", f"--window-size={W},{H}", f"--screenshot={png_path}",
                __import__("pathlib").Path(html_path).as_uri()], check=True, capture_output=True, timeout=120)
shutil.rmtree(prof, ignore_errors=True)
if not os.path.exists(png_path) or os.path.getmtime(png_path) <= before:
    sys.exit("PNG se nevygeneroval (Chrome)")
print(png_path, len(known), "předků", len(doc), "doc", len(recs), "zápisů", maxg + 1, "generací")
