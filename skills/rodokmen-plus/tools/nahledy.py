#!/usr/bin/env python3
"""Mřížka náhledů (contact sheet): rozsah snímků knihy jako několik celých snímků v jednom obrázku – rychlé
procházení knihy bez rejstříku, hledání oddílu, ověření, kde začíná rok.

Převzato a upraveno z:
  https://github.com/xsigik/rodokmen-skill/blob/6a62def5e10ab169018282a124f033fe4280be71/skills/rodokmen/tools/nahledy.py
  (fork xsigik, změna #10; ve forku později nahrazeno mapa_knihy.py, tady obojí: mapa = pruhy, mřížka = celé snímky)
Licence: MIT (původní © Jakub Valenta, xsigik; úpravy rodokmen-plus).

Použití (z kořene projektu):
  nahledy.py <archiv> <kniha> <od> <do> [volby]
  nahledy.py <archiv> <kniha> --rok <klíč svazku> <rok> [volby]   -> rozsah z data/svazky.json → orientace.roky
    archiv  = aron | pf | mza | ahmp (kniha jako u mapa_knihy.py; pf i id domu ze sčítání)

Volby:
  --vyrez x0,y0,x1,y1  jen část každého snímku (zlomky 0–1), např. sloupec se jmény 0,0,0.5,1
  --ostre              vyšší rozlišení (drobné písmo ve výřezu); výchozí náhled
  --po N               snímků na jeden obrázek (výchozí 6, nejvýš 12)
  --sloupce N          dlaždic vedle sebe (výchozí 3)
  --sirka PX           šířka dlaždice (výchozí 700)
  -o <složka>          výchozí pracovni/nahledy/

Vytvoří <složka>/<archiv>_<kniha>_<od>-<do>_<i>.jpg, každá dlaždice nese číslo snímku, a vypíše cesty.
Snímky stahuje nástroj archivu (stahni() z mapa_knihy.py) přes sdílenou mezipaměť tools/cache.py a brzdu
tools/slusne.py, postupně, bez vlastního souběhu. Podruhé jde celý rozsah z disku. Nejvýš 60 snímků na běh;
delší knihu procházej po dávkách, systematicky s evidencí prošlých snímků přes tools/sito.py.
"""
import json, os, re, shutil, subprocess, sys, tempfile
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import mapa_knihy   # stahni() přes nástroje archivu → cache.py → slusne.py; magick(), PISMO, snimek_pro_rok()

ROOT = os.path.dirname(TOOLS)
NEJVIC = 60
ARCHIVY = ("aron", "pf", "mza", "ahmp")


def rozsah_roku(svazek, rok, cesta=None):
    """(od, do) z orientace svazku; do = konec roku (snímek před další kotvou), jinak +30 snímků."""
    cesta = cesta or os.path.join(ROOT, "data", "svazky.json")
    sv = json.load(open(cesta, encoding="utf-8")) if os.path.exists(cesta) else {}
    if svazek not in sv:
        sys.exit(f"svazek „{svazek}“ není v {cesta}")
    v = mapa_knihy.snimek_pro_rok(sv[svazek], rok)
    if not v:
        sys.exit(f"{svazek}: orientace nemá kotvu roku ≤ {rok} – udělej mapu knihy (mapa_knihy.py) a kotvy doplň")
    od, do, pozn = v
    if pozn:
        print(pozn, file=sys.stderr)
    return od, do or od + 29


def dlazdice(M, src, n, sirka, out):
    cmd = [M, src + "[0]", "-resize", f"{sirka}x", "-background", "white", "-gravity", "North",
           "-splice", "0x48", "-fill", "#B00000", "-pointsize", "36"]
    cmd += ["-font", mapa_knihy.PISMO] if mapa_knihy.PISMO else []
    cmd += ["-annotate", "+0+4", f"sn. {n}", "-bordercolor", "#888", "-border", "2", out]
    return subprocess.run(cmd, capture_output=True).returncode == 0


def mrizka(M, dily, sloupce, out):
    """Dlaždice po řádcích (sloupce vedle sebe), řádky pod sebe."""
    radky = []
    for k in range(0, len(dily), sloupce):
        r = out + f".r{k}.png"
        subprocess.run([M, *dily[k:k + sloupce], "-background", "white", "-gravity", "North", "+append", r], check=True)
        radky.append(r)
    subprocess.run([M, *radky, "-background", "white", "-append", "-quality", "85", out], check=True)
    for r in radky:
        os.remove(r)


def main(a):
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    volby = {"--po": 6, "--sloupce": 3, "--sirka": 700}
    vyrez, ostre, outdir, rok, rest = (0, 0, 1, 1), False, None, None, []
    i = 0
    while i < len(a):
        x = a[i]
        if x in volby and i + 1 < len(a):
            volby[x] = int(a[i + 1]); i += 2
        elif x == "--vyrez" and i + 1 < len(a):
            try:
                vyrez = tuple(float(v) for v in a[i + 1].split(","))
            except ValueError:
                vyrez = ()
            if len(vyrez) != 4 or not (0 <= vyrez[0] < vyrez[2] <= 1 and 0 <= vyrez[1] < vyrez[3] <= 1):
                sys.exit(f"--vyrez „{a[i + 1]}“ zadej jako x0,y0,x1,y1 (zlomky 0–1)")
            i += 2
        elif x == "--rok" and i + 2 < len(a) and a[i + 2].isdigit():
            rok = (a[i + 1], int(a[i + 2])); i += 3
        elif x == "--ostre":
            ostre = True; i += 1
        elif x == "-o" and i + 1 < len(a):
            outdir = a[i + 1]; i += 2
        else:
            rest.append(x); i += 1
    if len(rest) < 2 or rest[0] not in ARCHIVY:
        sys.exit(__doc__)
    archiv, kniha = rest[0], rest[1]
    if rok:
        od, do = rozsah_roku(*rok)
    elif len(rest) == 4 and rest[2].isdigit() and rest[3].isdigit():
        od, do = int(rest[2]), int(rest[3])
    else:
        sys.exit("zadej rozsah <od> <do>, nebo --rok <klíč svazku> <rok>")
    po, sloupce = max(1, min(volby["--po"], 12)), max(1, volby["--sloupce"])
    if od < 1 or od > do:
        sys.exit("rozsah: 1 ≤ od ≤ do")
    if do - od + 1 > NEJVIC:
        sys.exit(f"{do - od + 1} snímků je moc (nejvýš {NEJVIC}) – procházej po dávkách (tools/sito.py dalsi)")
    M = mapa_knihy.magick()
    outdir = outdir or os.path.join(ROOT, "pracovni", "nahledy")
    os.makedirs(outdir, exist_ok=True)
    nazev = f"{archiv}_{re.sub(r'[^A-Za-z0-9-]', '', kniha)[:24]}_{od}-{do}"
    print(f"mřížka {archiv} {kniha}, snímky {od}–{do} …", file=sys.stderr)
    tmp = tempfile.mkdtemp(prefix="nahledy_")
    try:
        dily, cisla = [], []
        for n in range(od, do + 1):
            s, d = os.path.join(tmp, f"s{n:05d}.jpg"), os.path.join(tmp, f"d{n:05d}.png")
            if mapa_knihy.stahni(archiv, kniha, n, vyrez, ostre, s) and dlazdice(M, s, n, volby["--sirka"], d):
                dily.append(d); cisla.append(n)
        if not dily:
            sys.exit("žádný snímek nevznikl")
        chybi = sorted(set(range(od, do + 1)) - set(cisla))
        for k in range(0, len(dily), po):
            cil = os.path.join(outdir, f"{nazev}_{k // po + 1}.jpg")
            mrizka(M, dily[k:k + po], sloupce, cil)
            print(cil, "– snímky", ", ".join(map(str, cisla[k:k + po])))
        if chybi:
            print("chybí snímky:", ", ".join(map(str, chybi)), file=sys.stderr)
            sys.exit(2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
