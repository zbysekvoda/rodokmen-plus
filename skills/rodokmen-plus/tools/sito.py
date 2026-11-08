#!/usr/bin/env python3
"""Síto – systematické procházení knihy bez rejstříku po dávkách náhledů, se zápisem prošlých snímků a nálezů.

Myšlenka převzata z „Síta Jev“ forku xsigik (změny #21–#24):
  https://github.com/xsigik/rodokmen-skill/blob/9aa2c189892885f579df3043a2da04ed245f23e6/skills/rodokmen/tools/sito.py
  https://github.com/xsigik/rodokmen-skill/blob/9aa2c189892885f579df3043a2da04ed245f23e6/skills/rodokmen/reference/sito_jev.md
Licence: MIT (původní © Jakub Valenta, xsigik; úpravy rodokmen-plus).
Rozdíl: originál třídí pásy placeným modelem TypeSafe Jev (jen v OMP). Tady síto čte Claude (nebo pomocník) mřížky
z tools/nahledy.py; převzaté jsou pojistky – pevný rozsah, žádná díra, průběžný zápis, navázání po přerušení,
„nenalezeno“ jen pro skutečně prošlé snímky.

Použití (z kořene projektu):
  sito.py zaloz <hledání> <archiv> <kniha> <od> <do> [--vynechat 1,2,240] [--vyrez x0,y0,x1,y1] [--po N] [--otazka "…"]
  sito.py zaloz <hledání> <archiv> <kniha> --rok <klíč svazku> <rok> [volby]    (rozsah z orientace svazku)
  sito.py dalsi <hledání>                 -> mřížka další neprošlé dávky (nahledy.py, přes cache.py a slusne.py)
  sito.py proslo <hledání> <od> [<do>]    -> snímky přečtené a hotové (i bez nálezu)
  sito.py nalez <hledání> <snímek> "<co>" -> kandidát k přečtení v plném rozlišení
  sito.py stav <hledání>                  -> pokrytí, díry, nálezy (kód 1, dokud není rozsah prošlý celý)

Deník: pracovni/sito/<hledání>.json. Nález je jen stopa – do dat jde, až je přečtený na snímku (SKILL.md).
Hledání, které nic nenašlo, patří do research_log.md jako „síto: snímky od–do prošlé, nic“ s otázkou.
"""
import json, os, re, subprocess, sys
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
DIR = os.path.join(ROOT, "pracovni", "sito")
ARCHIVY = ("aron", "pf", "mza", "ahmp")


def cesta(h):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", h):
        sys.exit("hledání pojmenuj jen písmeny bez diakritiky, číslicemi, _ a - (např. novak_jan_krest)")
    return os.path.join(DIR, h + ".json")


def nacti(h):
    p = cesta(h)
    if not os.path.exists(p):
        sys.exit(f"hledání „{h}“ není založené (sito.py zaloz …)")
    return json.load(open(p, encoding="utf-8"))


def uloz(h, d):
    os.makedirs(DIR, exist_ok=True)
    p = cesta(h)
    with open(p + ".tmp", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(p + ".tmp", p)   # atomicky – přerušení nenechá napůl zapsaný deník


def cisla(s):
    return sorted({int(x) for x in s.split(",") if x.strip()}) if s else []


def zbyva(d):
    hotovo = set(d["proslo"]) | set(d["vynechat"])
    return [n for n in range(d["od"], d["do"] + 1) if n not in hotovo]


def zaloz(a):
    volby, rest, i = {}, [], 0
    while i < len(a):
        if a[i] == "--rok" and i + 2 < len(a):
            volby["rok"] = (a[i + 1], int(a[i + 2])); i += 3
        elif a[i] in ("--vynechat", "--vyrez", "--po", "--otazka") and i + 1 < len(a):
            volby[a[i][2:]] = a[i + 1]; i += 2
        else:
            rest.append(a[i]); i += 1
    if len(rest) < 3 or rest[1] not in ARCHIVY:
        sys.exit(__doc__)
    h, archiv, kniha = rest[:3]
    if os.path.exists(cesta(h)):
        sys.exit(f"hledání „{h}“ už existuje – pokračuj sito.py dalsi {h}")
    if "rok" in volby:
        import nahledy
        od, do = nahledy.rozsah_roku(*volby["rok"])
    elif len(rest) == 5 and rest[3].isdigit() and rest[4].isdigit():
        od, do = int(rest[3]), int(rest[4])
    else:
        sys.exit("zadej rozsah <od> <do>, nebo --rok <klíč svazku> <rok>")
    if od < 1 or od > do:
        sys.exit("rozsah: 1 ≤ od ≤ do")
    d = {"archiv": archiv, "kniha": kniha, "od": od, "do": do, "vynechat": cisla(volby.get("vynechat")),
         "vyrez": volby.get("vyrez"), "po": int(volby.get("po", 6)), "otazka": volby.get("otazka", ""),
         "proslo": [], "nalezy": []}
    uloz(h, d)
    print(f"{h}: {archiv} {kniha}, snímky {od}–{do}, {len(zbyva(d))} k prosetí po {d['po']}")


def dalsi(h):
    d = nacti(h)
    z = zbyva(d)
    if not z:
        print(f"{h}: rozsah {d['od']}–{d['do']} je prošlý celý"); return
    davka = [n for n in z if n < z[0] + d["po"]]   # souvislý úsek – díry (vynechané) mřížka přeskočí sama
    od, do = davka[0], davka[-1]
    cmd = [sys.executable, "-I", os.path.join(TOOLS, "nahledy.py"), d["archiv"], d["kniha"], str(od), str(do),
           "--po", str(d["po"]), "-o", os.path.join(DIR, h)]
    if d.get("vyrez"):
        cmd += ["--vyrez", d["vyrez"]]
    if d.get("otazka"):
        print(f"otázka: {d['otazka']}")
    r = subprocess.run(cmd)
    print(f"po přečtení: sito.py proslo {h} {od} {do}  (nález: sito.py nalez {h} <snímek> \"…\"); "
          f"zbývá {len(z)} snímků")
    if r.returncode:
        sys.exit(r.returncode)


def proslo(h, od, do=None):
    d = nacti(h)
    od, do = int(od), int(do or od)
    if not d["od"] <= od <= do <= d["do"]:
        sys.exit(f"mimo rozsah hledání {d['od']}–{d['do']}")
    d["proslo"] = sorted(set(d["proslo"]) | set(range(od, do + 1)))
    uloz(h, d)
    print(f"{h}: prošlo {len(d['proslo'])}, zbývá {len(zbyva(d))}")


def nalez(h, n, co):
    d = nacti(h)
    n = int(n)
    if not d["od"] <= n <= d["do"]:
        sys.exit(f"snímek {n} je mimo rozsah {d['od']}–{d['do']}")
    d["nalezy"].append({"snimek": n, "co": co})
    uloz(h, d)
    print(f"{h}: nález na snímku {n} – přečti ho v plném rozlišení, než cokoli zapíšeš")


def stav(h):
    d = nacti(h)
    z = zbyva(d)
    print(f"{h}: {d['archiv']} {d['kniha']}, snímky {d['od']}–{d['do']}"
          + (f", vynecháno {','.join(map(str, d['vynechat']))}" if d["vynechat"] else ""))
    if d.get("otazka"):
        print(f"otázka: {d['otazka']}")
    print(f"prošlo {len(d['proslo'])}, zbývá {len(z)}" + (f" (od snímku {z[0]})" if z else " – úplné"))
    for x in d["nalezy"]:
        print(f"  nález sn. {x['snimek']}: {x['co']}")
    if z:
        sys.exit(1)


def main(a):
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    sys.path.insert(0, TOOLS)
    p, r = a[0], a[1:]
    if p == "zaloz":
        return zaloz(r)
    if p == "dalsi" and len(r) == 1:
        return dalsi(r[0])
    if p == "proslo" and len(r) in (2, 3):
        return proslo(*r)
    if p == "nalez" and len(r) == 3:
        return nalez(*r)
    if p == "stav" and len(r) == 1:
        return stav(r[0])
    sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
