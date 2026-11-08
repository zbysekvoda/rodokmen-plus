#!/usr/bin/env python3
"""Přehled prošlých matričních knih: co už se v které knize hledalo a co se našlo.

Použití (z kořene projektu):
  python3 -I tools/prosle_knihy.py [příjmení] [--data <složka>]   -> výpis + pracovni/prosle_knihy.md

Skládá dohromady existující evidenci, nic se nevyplňuje ručně:
  data/svazky.json      knihy (svazek, portál, počet snímků),
  data/zaznamy.json     zápisy nalezené v knize (počet, snímky),
  data/research_log.md  hledání v knize (rozsah, hledáno, výsledek) – i neúspěšná.
Řádek deníku patří ke knize, když sloupec „zdroj“ obsahuje název svazku (bez závorky na konci).
Hledání, která ke knize ze svazky.json nepatří, jsou na konci zvlášť.
S příjmením se vypíšou jen hledání a zápisy, kde se příjmení vyskytuje. Než začneš číst knihu, podívej se sem:
kniha prošlá kvůli jedné osobě neznamená, že v ní není jiná – platí jen pro rozsah a hledané ve sloupcích.

Nápad podle data/prosle_knihy.md z
https://github.com/vlastimilvasek/rodokmen-skill/blob/e04b220e8188cac1353a9ba02cf675671098eb27/skills/rodokmen/template/data/prosle_knihy.md
(vlastimilvasek, MIT) – tady se přehled počítá z deníku a záznamů místo ruční tabulky.
"""
import json, os, re, sys
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRUH = {"N": "Narození", "O": "Oddaní", "Z": "Zemřelí"}


def denik(path):
    """Řádky tabulky research_log.md jako dicty podle hlavičky."""
    if not os.path.exists(path):
        return []
    hlav, out = None, []
    for r in open(path, encoding="utf-8"):
        if not r.lstrip().startswith("|"):
            continue
        bunky = [c.strip() for c in r.strip().strip("|").split("|")]
        if hlav is None:
            hlav = [c.lower() for c in bunky]
        elif not all(set(c) <= set("-: ") for c in bunky):
            out.append(dict(zip(hlav, bunky)))
    return out


def zaklad(nazev):
    return re.sub(r"\s*\([^)]*\)\s*$", "", nazev or "").strip().lower()


def druh_svazku(s, zapisy):
    if zapisy:
        return zapisy[0].get("druh", "?")
    m = re.match(r"(Narození|Oddaní|Zemřelí|[NOZ])\b", s.get("svazek", ""))
    return {"Narození": "N", "Oddaní": "O", "Zemřelí": "Z"}.get(m.group(1), m.group(1)) if m else "?"


def main():
    argv = sys.argv[1:]
    data = os.path.join(ROOT, "data")
    if "--data" in argv:
        i = argv.index("--data")
        data = argv[i + 1]
        del argv[i:i + 2]
    hledej = argv[0].lower() if argv else ""

    def jload(name, default):
        p = os.path.join(data, name)
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default

    svazky = jload("svazky.json", {})
    zaz = jload("zaznamy.json", [])
    log = denik(os.path.join(data, "research_log.md"))
    pouzite = set()
    knihy = {}
    for klic, s in svazky.items():
        zap = [z for z in zaz if z.get("svazek") == klic]
        nazev = zaklad(s.get("svazek"))
        hl = []
        for i, r in enumerate(log):
            if nazev and nazev in r.get("zdroj", "").lower():
                hl.append(r)
                pouzite.add(i)
        if hledej:
            zap = [z for z in zap if hledej in json.dumps(z, ensure_ascii=False).lower()]
            hl = [r for r in hl if hledej in " ".join(r.values()).lower()]
        if zap or hl:
            knihy.setdefault(druh_svazku(s, zap), []).append((klic, s, zap, hl))

    L = ["# Prošlé matriční knihy" + (f" – „{argv[0]}“" if hledej else ""), "",
         "Spočítáno z data/svazky.json, data/zaznamy.json a data/research_log.md (tools/prosle_knihy.py).", ""]
    pocet = 0
    for druh in sorted(knihy, key=lambda d: "NOZ?".find(d) if d in "NOZ?" else 9):
        L += [f"## {DRUH.get(druh, druh)} ({druh})", "", "| kniha | portál | snímků | hledání (rozsah → výsledek) | nalezené zápisy |",
              "|---|---|---|---|---|"]
        for klic, s, zap, hl in knihy[druh]:
            pocet += 1
            h = "; ".join(f"{r.get('rozsah', '')}: {r.get('hledáno', '')} → {r.get('výsledek', '')}" for r in hl) or "—"
            z = "; ".join(f"{x.get('nazev', x['klic'])} (sn. {x.get('snimek', '?')})" for x in zap) or "—"
            L.append(f"| {s.get('svazek', klic)} [`{klic}`] | {s.get('portal', '')} | {s.get('snimku', '')} | {h} | {z} |")
        L.append("")
    zbytek = [r for i, r in enumerate(log) if i not in pouzite and (not hledej or hledej in " ".join(r.values()).lower())]
    if zbytek:
        L += ["## Hledání v knihách mimo svazky.json", "", "| zdroj | rozsah | hledáno | výsledek |", "|---|---|---|---|"]
        L += [f"| {r.get('zdroj', '')} | {r.get('rozsah', '')} | {r.get('hledáno', '')} | {r.get('výsledek', '')} |" for r in zbytek]
        L.append("")
    if not pocet and not zbytek:
        L.append("Zatím žádná prošlá kniha.")
    vystup = "\n".join(L)
    print(vystup)
    os.makedirs(os.path.join(ROOT, "pracovni"), exist_ok=True)
    with open(os.path.join(ROOT, "pracovni", "prosle_knihy.md"), "w", encoding="utf-8") as fh:
        fh.write(vystup + "\n")


if __name__ == "__main__":
    main()
