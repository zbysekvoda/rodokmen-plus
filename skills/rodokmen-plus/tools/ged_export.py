#!/usr/bin/env python3
"""Export grafu osob (data/osoby.py + data/zaznamy.json + data/prepisy.json) do GEDCOM 5.5.1 (UTF-8).

Použití (z kořene projektu):
  python3 -I tools/ged_export.py [vystup.ged] [--data <složka>]     (výchozí vystupy/rodokmen.ged, data/)

Každá osoba z OSOBY je INDI (@<id>@ podle trvalého id). Rodiny (FAM) vznikají z hran „manzele“ a z dvojic
rodičů společných dětí (i jen s jedním známým rodičem). Fakta „*“, „×“, „†“ jdou do BIRT/MARR/DEAT
(datum + místo), ostatní fakta, stav doložení a poznámka do NOTE. Zápisy z matrik (pole r) jsou zdroje
(SOUR) s českým překladem přepisu. Zpětně čte strom tools/ged_import.py.

Převzato a přepsáno na graf z
https://github.com/vlastimilvasek/rodokmen-skill/blob/e04b220e8188cac1353a9ba02cf675671098eb27/skills/rodokmen/tools/ged_export.py
(vlastimilvasek, MIT) – původní verze pracovala s Kekulého čísly (P).
"""
import json, os, re, sys
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graf

MES = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
STAV = {"doc": "doloženo matrikou", "prob": "pravděpodobné", "fam": "údaj od rodiny",
        "mh": "z cizího rodokmenu (neověřeno)", "unk": "neznámé"}
DATUM = re.compile(r"^(?:(asi|před|po)\s+)?(?:(\d{1,2})\.\s*(\d{1,2})\.\s*|(\d{1,2})/)?(\d{4})\s*(\(\?\))?\s*")


def ged_datum(text):
    """'3. 9. 1905 Komín č. 19' → ('3 SEP 1905', 'Komín č. 19')."""
    m = DATUM.match(text)
    if not m:
        return "", text.strip()
    pred, den, mes, mes2, rok, _ = m.groups()
    if den and 1 <= int(mes) <= 12:
        d = f"{int(den)} {MES[int(mes) - 1]} {rok}"
    elif mes2 and 1 <= int(mes2) <= 12:
        d = f"{MES[int(mes2) - 1]} {rok}"
    else:
        d = rok
    d = {"asi": "ABT ", "před": "BEF ", "po": "AFT "}.get(pred, "") + d
    return d, text[m.end():].strip()


def jmeno(n):
    n = n.strip()
    if n.startswith("(?)"):
        return "", n[3:].strip()
    casti = n.split()
    if len(casti) == 1:
        return casti[0], ""
    if casti[-1] == "(?)" and len(casti) >= 3:
        return " ".join(casti[:-2]), casti[-2] + " (?)"
    return " ".join(casti[:-1]), casti[-1]


def xref(s):
    return "@" + re.sub(r"[^A-Za-z0-9_-]", "_", s) + "@"


def main():
    argv = sys.argv[1:]
    data = os.path.join(graf.ROOT, "data")
    if "--data" in argv:
        i = argv.index("--data")
        data = argv[i + 1]
        del argv[i:i + 2]
    out = argv[0] if argv else os.path.join(graf.ROOT, "vystupy", "rodokmen.ged")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

    def jload(name, default):
        p = os.path.join(data, name)
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default

    g = graf.nacti(os.path.join(data, "osoby.py"))
    zaz = {z["klic"]: z for z in jload("zaznamy.json", [])}
    pre = jload("prepisy.json", {})
    web = jload("web.json", {})
    zdroj = {k: f"@S{i}@" for i, k in enumerate(zaz, 1)}

    L = ["0 HEAD", "1 SOUR RODOKMEN-PLUS", "2 NAME " + (web.get("nazev") or "Rodokmen"), "1 GEDC", "2 VERS 5.5.1",
         "2 FORM LINEAGE-LINKED", "1 CHAR UTF-8", "1 LANG Czech"]

    def text(tag, s, lvl):
        """Dlouhý text rozdělený na CONC/CONT."""
        for i, r in enumerate(str(s).split("\n")):
            kusy = [r[j:j + 200] for j in range(0, len(r), 200)] or [""]
            for k, kus in enumerate(kusy):
                if i == 0 and k == 0:
                    L.append(f"{lvl} {tag} {kus}".rstrip())
                elif k == 0:
                    L.append(f"{lvl + 1} CONT {kus}".rstrip())
                else:
                    L.append(f"{lvl + 1} CONC {kus}")

    # rodiny: klíč = (muž nebo první, žena nebo druhý); z hran manzele a z rodičů dětí
    rodiny = {}

    def rodina(a, b):
        if a and b and g.osoby[a].get("sex") == "F" and g.osoby[b].get("sex") != "F":
            a, b = b, a
        klic = (a, b)
        if klic not in rodiny:
            rodiny[klic] = {"id": f"@F{len(rodiny) + 1}@", "deti": []}
        return rodiny[klic]

    for e in g.vztahy:
        if e["t"] == "manzele" and e["a"] in g.osoby and e["b"] in g.osoby:
            rodina(e["a"], e["b"])
    for i in g.osoby:
        rod = [r for r in g._rod.get(i, []) if r in g.osoby]
        if rod:
            rodina(rod[0], rod[1] if len(rod) > 1 else None)["deti"].append(i)
    famc, fams = {}, {}
    for (a, b), r in rodiny.items():
        for p in (a, b):
            if p:
                fams.setdefault(p, []).append(r["id"])
        for d in r["deti"]:
            famc.setdefault(d, r["id"])

    for i, o in g.osoby.items():
        kr, pr = jmeno(o.get("n", ""))
        L += [f"0 {xref(i)} INDI", f"1 NAME {kr} /{pr}/".replace("  ", " ")]
        if kr:
            L.append(f"2 GIVN {kr}")
        if pr:
            L.append(f"2 SURN {pr}")
        if o.get("sex") in ("M", "F"):
            L.append(f"1 SEX {o['sex']}")
        poznamky = []
        partneri = [g.osoby[m]["n"] for m in g.manzele(i) if m in g.osoby]
        for f in o.get("f", []):
            znak = f[:1]
            if znak in "*†" and f[1:2] == " ":
                dat, misto = ged_datum(f[2:])
                if not dat and not misto:
                    poznamky.append(f)
                    continue
                L.append("1 " + ("BIRT" if znak == "*" else "DEAT"))
                if dat:
                    L.append(f"2 DATE {dat}")
                if misto:
                    L.append(f"2 PLAC {misto}")
            elif znak == "×" and any(f.rstrip().endswith(p) for p in partneri):
                continue   # sňatek s osobou v grafu jde do FAM jako MARR
            else:
                poznamky.append(f)   # ostatní fakta i sňatky s osobou mimo graf
        poznamky.append("Stav: " + STAV.get(o.get("st"), o.get("st", "")))
        if o.get("note"):
            poznamky.append(o["note"])
        text("NOTE", "\n".join(poznamky), 1)
        for r in o.get("r", []):
            if r in zdroj:
                L.append(f"1 SOUR {zdroj[r]}")
        if i in famc:
            L.append(f"1 FAMC {famc[i]}")
        for fid in fams.get(i, []):
            L.append(f"1 FAMS {fid}")

    for (a, b), r in rodiny.items():
        L.append(f"0 {r['id']} FAM")
        for p, vychozi in ((a, "HUSB"), (b, "WIFE")):
            if p:
                pohl = g.osoby[p].get("sex")
                L.append(f"1 {'WIFE' if pohl == 'F' else 'HUSB' if pohl == 'M' else vychozi} {xref(p)}")
        for d in r["deti"]:
            L.append(f"1 CHIL {xref(d)}")
        if not (a and b):
            continue
        for k, partner in ((a, b), (b, a)):   # sňatek z fakt manžela, jinak manželky
            pn = g.osoby[partner]["n"]
            fx = next((f for f in g.osoby[k].get("f", []) if f.startswith("× ") and f.rstrip().endswith(pn)), None)
            if not fx:
                continue
            dat, zbytek = ged_datum(fx[2:])
            zbytek = zbytek.rstrip()[: -len(pn)].strip()
            L.append("1 MARR")
            if dat:
                L.append(f"2 DATE {dat}")
            if zbytek:
                L.append(f"2 PLAC {zbytek}")
            break

    for klic, z in zaz.items():
        L.append(f"0 {zdroj[klic]} SOUR")
        L.append(f"1 TITL {z.get('nazev', klic)} ({z.get('datum', '')})")
        text("NOTE", (z.get("shrnuti", "") + "\n" + (pre.get(klic) or {}).get("cs", "")).strip(), 1)
        if z.get("odkaz"):
            L.append(f"1 WWW {z['odkaz']}")

    L.append("0 TRLR")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    nrod = sum(len(r["deti"]) for r in rodiny.values())
    print(f"uloženo: {out} ({len(g.osoby)} osob, {len(rodiny)} rodin, {nrod} vazeb dítě–rodina, {len(zaz)} zdrojů)")


if __name__ == "__main__":
    main()
