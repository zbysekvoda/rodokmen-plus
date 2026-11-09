#!/usr/bin/env python3
"""Fronta hledání: předci, kterým chybí aspoň jeden rodič, a rody, které ještě nejsou uzavřené.

Převzato a přepsáno na graf (data/osoby.py: OSOBY, VZTAHY, RODY, KORENY) z
  https://github.com/srameko/rodokmen-skill/blob/5f25edb9a201f8ac03b79293bbcb79b5109d022e/skills/rodokmen/tools/fronta.py
  (autor srameko, licence MIT – viz LICENSE).

Použití (z kořene projektu):  python3 -I tools/fronta.py [koren] [--vse]  -> výpis + pracovni/fronta.md
  koren  klíč z KORENY (výchozí „hlavni“); bere se kořen a všichni jeho předci
  --vse  vypsat i osoby z rodů, které uživatel uzavřel
Body (vyšší = dřív):
  +3  jméno rodiče už je ve faktech/poznámce („syn Jana Nováka“) – stačí ho založit jako osobu
  +2  narozen po 1784 (josefínské matriky: dům, rodiče, prarodiče)  /  +1 po 1750
  +2  známe číslo domu,  +1 známe obec narození
  +1  osoba je doložená (st="doc")
  −5  rod uzavřený uživatelem – bez --vse se nevypisuje
Rody: osoba patří do rodu, je-li jeho zakladatelem nebo jeho předkem. Rody mohou ležet v libovolné
generaci (zakladatel se hledá podle id, ne podle Kekulého čísla 8–15).
Uzavřené rody: v data/web.json klíč "fronta_uzavrene": [slugy z RODY], např. {"fronta_uzavrene": ["pokorni"]}.
Osoby st="unk" s n="otec neuveden" se za chybějící rodiče nepovažují (konec větve je známý).
"""
import json, os, re, sys

for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import graf

VELKE = "A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"
RODIC_RE = re.compile(rf"\b(syn|dcera)\s+(?:†\s*)?(?:domkáře|sedláka|mlynáře|chalupníka|kováře|pololáníka)?\s*([{VELKE}]\w+\s+[{VELKE}]\w+)")
MISTO_RE = re.compile(rf"^\*\s*(?:asi\s*)?(?:\d{{1,2}}\.\s*\d{{1,2}}\.\s*)?\d{{4}}\s+[{VELKE}]")   # „* 1852 Obec“
ROK_RE = re.compile(r"\*\s*(?:asi\s*)?(?:\d{1,2}\.\s*\d{1,2}\.\s*)?(1[5-9]\d\d)")


def rok(o):
    m = ROK_RE.search(o.get("y", "") + " " + " ".join(o.get("f", [])))
    if not m:
        m = re.search(r"\b(1[5-9]\d\d)", o.get("y", ""))   # „1850–1910“, „asi 1720–1785“
    return int(m.group(1)) if m else None


def uzavrene_rody(path):
    try:
        with open(path, encoding="utf-8") as fh:
            u = json.load(fh).get("fronta_uzavrene", [])
    except FileNotFoundError:
        return set()
    except ValueError as e:
        sys.exit(f"{path}: neplatný JSON ({e})")
    if not isinstance(u, list):
        sys.exit(f'{path}: "fronta_uzavrene" musí být seznam slugů rodů, např. ["pokorni"].')
    return {str(x) for x in u}


def spocitej(g, koren=None, uzavrene=(), vse=False):
    """→ (radky, rody): radky = [(body, kek, id, jméno, rok, rod, důvod)], rody = {slug: dict(...)}."""
    k0 = g.koren(koren)
    if k0 not in g.osoby:
        sys.exit(f"kořen {koren or g.hlavni_koren()!r} → {k0!r} není v OSOBY")
    kek = {}
    for c, i in g.kekule(koren).items():
        kek.setdefault(i, c)
    clenove = {}
    for slug, r in g.rody.items():
        z = r.get("zakladatel")
        if z in g.osoby:
            for i in [z] + g.predci(z):
                clenove.setdefault(i, []).append(slug)
    zakonceni = lambda i: i and g.osoby[i].get("st") == "unk" and "neuveden" in g.osoby[i].get("n", "")
    radky = []
    for i in [k0] + g.predci(k0):
        o = g.osoby[i]
        if o.get("druh") == "bocni" or o.get("tataz"):
            continue
        ot, ma = g.rodice(i)
        if ot and ma:
            continue
        duvod = ["chybí oba rodiče" if not (ot or ma) else "chybí " + ("otec" if not ot else "matka")]
        if zakonceni(ot) and not ma:
            duvod = ["chybí matka (otec neuveden)"]
        b = 0
        fakta = o.get("f", [])
        t = " ".join(fakta) + " " + o.get("note", "")
        m = RODIC_RE.search(t)
        if m:
            b += 3; duvod.append("rodič v datech: " + m.group(0))
        y = rok(o)
        if y and y >= 1784:
            b += 2; duvod.append("po 1784")
        elif y and y >= 1750:
            b += 1
        if re.search(r"čp\.\s*\d+", t):
            b += 2; duvod.append("dům")
        if any(MISTO_RE.match(x) for x in fakta):
            b += 1
        if o.get("st") == "doc":
            b += 1
        rody_i = clenove.get(i, [])
        if rody_i and all(r in uzavrene for r in rody_i):
            b -= 5
            if not vse:
                continue
        radky.append((b, kek.get(i, ""), i, o.get("n", i), y or "", ", ".join(rody_i), "; ".join(duvod)))
    radky.sort(key=lambda x: (-x[0], -(x[4] or 0)))
    rody = {}
    for slug, r in g.rody.items():
        okraj = [x for x in radky if slug in x[5].split(", ")]
        rody[slug] = dict(nazev=r.get("nazev", slug), zakladatel=r.get("zakladatel"),
                          kek=kek.get(r.get("zakladatel"), ""), uzavreny=slug in uzavrene, okraj=len(okraj),
                          nejstarsi=min((x[4] for x in okraj if x[4]), default=""))
    return radky, rody


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    vse = "--vse" in sys.argv
    g = graf.nacti()
    uz = uzavrene_rody(os.path.join(graf.DATA, "web.json"))
    radky, rody = spocitej(g, args[0] if args else None, uz, vse)
    neuzavrene = {s: r for s, r in rody.items() if not r["uzavreny"] and r["okraj"]}
    out = ["# Fronta hledání (tools/fronta.py)", "",
           "## Neuzavřené rody", "", "| rod | zakladatel | č. | osob na okraji | nejstarší * |", "|---|---|---|---|---|"]
    out += [f"| {r['nazev']} ({s}) | {r['zakladatel']} | {r['kek']} | {r['okraj']} | {r['nejstarsi']} |" for s, r in neuzavrene.items()]
    if uz:
        out += ["", "Uzavřené: " + ", ".join(sorted(uz))]
    out += ["", "## Chybějící rodiče", "", "| body | č. | id | osoba | * | rod | proč |", "|---|---|---|---|---|---|---|"]
    out += [f"| {b} | {k} | {i} | {n} | {y} | {r} | {d} |" for b, k, i, n, y, r, d in radky]
    os.makedirs("pracovni", exist_ok=True)
    with open(os.path.join("pracovni", "fronta.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"Neuzavřené rody ({len(neuzavrene)}):")
    for s, r in neuzavrene.items():
        print(f"  {r['nazev']} ({s}): {r['okraj']} osob na okraji, nejstarší * {r['nejstarsi'] or '?'}")
    print(f"{len(radky)} osob s chybějícím rodičem (uzavřené rody {'zahrnuty' if vse else 'vynechány'}); pracovni/fronta.md")
    for b, k, i, n, y, r, d in radky[:25]:
        print(f"  {b:>3}  č. {k or '-':<5} {n} (* {y or '?'}) [{r or 'mimo rody'}] – {d}")


if __name__ == "__main__":
    main()
