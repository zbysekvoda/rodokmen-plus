#!/usr/bin/env python3
"""Domy rodiny: z pole `bydliste` v data/osoby.py sestaví seznam domů (obec, čp.), ve kterých předci žili.

Výstup: data/domy_rodiny.json a data/domy_rodiny.md – fronta pro dějiny domů (skill dejiny-domu).
Priorita domu = počet generací předků v domě × 10 + doložené roky (od nejstaršího do nejmladšího údaje).
Zápisy ze zaznamy.json, které dům zmiňují, ale nepatří k předkovi v něm (sourozenci, svědci),
jsou v poli `souvisejici_zaznamy`.

Použití: python3 -I tools/domy_rodiny.py
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# Domy, které už mají zpracované dějiny (data/domy_zpracovane.json):
#   [{"obec": "Lhotka", "cp": "12", "poznamka": "data/domy.py D[\"Lhotka 12\"] (sčítání 1869–1921)"}, …]
def nacti_zpracovane():
    path = os.path.join(DATA, "domy_zpracovane.json")
    if not os.path.exists(path):
        return {}
    return {(x["obec"], str(x["cp"])): x.get("poznamka", "zpracováno") for x in json.load(open(path, encoding="utf-8"))}


# Jak se obec píše v zápisech (6. pád apod.) – pro dohledání souvisejících zápisů.
def kmen(obec):
    return obec[:-2] if len(obec) > 5 else obec


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import graf
    g = graf.nacti()
    ZPRACOVANE = nacti_zpracovane()
    prvni = {}                                   # id → nejnižší Kekulé od hlavního kořene (jen pro generaci)
    for k, i in g.kekule().items():
        prvni.setdefault(i, k)
    zaz = json.load(open(os.path.join(DATA, "zaznamy.json"), encoding="utf-8"))
    domy = {}
    poradi = lambda i: (prvni.get(g.osoby[i].get("tataz") or i, 10 ** 12), i)
    for i in sorted(g.osoby, key=poradi):
        p = g.osoby[i]
        hlavni = p.get("tataz") or i            # druhý výskyt (tataz) → hlavní osoba
        k = prvni.get(hlavni)
        for b in p.get("bydliste", []):
            d = domy.setdefault((b["obec"], str(b["cp"])), {"osoby": [], "zdroje": set()})
            d["osoby"].append({"osoba": hlavni, "generace": k.bit_length() - 1 if k else None, "jmeno": g.osoby[hlavni]["n"],
                               "roky": g.osoby[hlavni].get("y", ""),
                               "role": b.get("role", ""), "od": b.get("od"), "do": b.get("do"), "zdroj": b.get("zdroj", [])})
            d["zdroje"].update(b.get("zdroj", []))
    out = []
    for (obec, cp), d in domy.items():
        gen = sorted({o["generace"] for o in d["osoby"] if o["generace"] is not None})
        roky = [y for o in d["osoby"] for y in (o["od"], o["do"]) if y]
        rozpeti = (min(roky), max(roky)) if roky else (None, None)
        let = rozpeti[1] - rozpeti[0] if roky else 0
        vzor = re.compile(rf"{re.escape(kmen(obec))}\w*[^.;]*?čp\.\s*{re.escape(cp)}\b")
        souv = sorted(z["klic"] for z in zaz if z["klic"] not in d["zdroje"] and vzor.search(z.get("shrnuti", "")))
        out.append({
            "obec": obec, "cp": cp,
            "zpracovano": ZPRACOVANE.get((obec, cp)),
            "priorita": len(gen) * 10 + let,
            "pocet_generaci": len(gen), "generace": gen,
            "od": rozpeti[0], "do": rozpeti[1], "doloženo_let": let,
            "osoby": d["osoby"],
            "zdroje": sorted(d["zdroje"]),
            "souvisejici_zaznamy": souv,
        })
    out.sort(key=lambda x: (-x["priorita"], x["obec"], x["cp"]))
    json.dump(out, open(os.path.join(DATA, "domy_rodiny.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    md = ["# Domy rodiny – fronta pro dějiny domů", "",
          "Generuje `tools/domy_rodiny.py` z pole `bydliste` v `data/osoby.py` – needitovat ručně.",
          "Priorita = generace předků v domě × 10 + doložené roky. Zdroj „rodina“ = jen údaj od rodiny.", "",
          "| # | dům | priorita | generací | doloženo | předci | stav |", "|---|---|---|---|---|---|---|"]
    for i, d in enumerate(out, 1):
        lidi = "; ".join(f"{o['jmeno']} [{o['osoba']}] ({o['role']})" for o in d["osoby"])
        obd = f"{d['od']}–{d['do']}" if d["od"] else "?"
        md.append(f"| {i} | {d['obec']} čp. {d['cp']} | {d['priorita']} | {d['pocet_generaci']} | {obd} | {lidi} | "
                  f"{'zpracováno: ' + d['zpracovano'] if d['zpracovano'] else ''} |")
    md += ["", "## Zdroje podle domů", ""]
    for d in out:
        md.append(f"- **{d['obec']} čp. {d['cp']}**: {', '.join(d['zdroje'])}"
                  + (f"; související: {', '.join(d['souvisejici_zaznamy'])}" if d["souvisejici_zaznamy"] else ""))
    open(os.path.join(DATA, "domy_rodiny.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"{len(out)} domů → data/domy_rodiny.json, data/domy_rodiny.md")


if __name__ == "__main__":
    sys.exit(main())
