#!/usr/bin/env python3
"""Hlídá, aby do veřejného repa nepronikla data ze soukromého projektu rodokmenu.

Použití: python3 -I scripts/kontrola_soukromi.py <složka data/ soukromého projektu>
Vezme příjmení osob (data/osoby.py, pole n=) a názvy obcí (data/mista.json) a hledá je jako celá slova
ve verzovaných souborech repa. Fiktivní ukázková rodina (Novákovi) a jméno autora jsou povolené.
Konec s kódem 1, když něco najde.
"""
import json, os, re, subprocess, sys

POVOLENO = {"Zbyšek", "Voda", "Brno", "Praha", "Vídeň",   # autor pluginu; velká města (archivy, příklady)
            "Petrovice",   # příklad nejednoznačného názvu obce (ztotozneni-mist)
            "Jihlava"}    # krajské město (test osy událostí na zemské hranici)
UKAZKA = "skills/rodokmen-plus/template/ukazka"         # fiktivní rodina – její jména jsou povolená
POVOLENE_RADKY = re.compile(r"Zbyšek Voda|Hradecký a Pardubický kraj|Jakub Valenta|Gregor Wolny|Karlova 190/1|„Chalupa, kde")
# autor; název kraje; autor forku (MIT), autor vlastivědy, pražská adresa v testu RÚIAN, obecné slovo v příkladu
MIN_DELKA = 4                                        # krátká slova („Na“, „Ves“) dávají jen šum


def slova(data):
    out = set()
    osoby = open(os.path.join(data, "osoby.py"), encoding="utf-8").read()
    osoby = "\n".join(r for r in osoby.splitlines() if not r.lstrip().startswith("#"))   # bez návodu v hlavičce
    for jm in re.findall(r'\bn="([^"]+)"', osoby):
        jm = re.sub(r"\(.*?\)|\?", "", jm).split()
        if len(jm) > 1 and jm[-1][:1].isupper():
            out.add(jm[-1])   # příjmení
    mista = os.path.join(data, "mista.json")
    if os.path.exists(mista):
        for k in json.load(open(mista, encoding="utf-8")):
            if not k.startswith("_"):
                out.add(k)
    ukazka = set()
    for base, _, files in os.walk(UKAZKA):
        for f in files:
            if f.endswith((".py", ".json", ".md")):
                ukazka.update(re.findall(r"\w+", open(os.path.join(base, f), encoding="utf-8").read()))
    return {w.strip(",.;") for w in out if len(w.strip(",.;")) >= MIN_DELKA} - POVOLENO - ukazka


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    hledat = slova(os.path.expanduser(sys.argv[1]))
    if not hledat:
        sys.exit("V soukromých datech jsem nenašel žádná jména – špatná cesta?")
    vzor = re.compile(r"(?<!\w)(" + "|".join(map(re.escape, sorted(hledat, key=len, reverse=True))) + r")(?!\w)")
    soubory = subprocess.run(["git", "ls-files", "-z"], capture_output=True, text=True, check=True).stdout.split("\0")
    nalezy = []
    for f in filter(None, soubory):
        try:
            text = open(f, encoding="utf-8").read()
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        for i, radek in enumerate(text.splitlines(), 1):
            if POVOLENE_RADKY.search(radek):
                continue
            for m in vzor.finditer(radek):
                nalezy.append(f"{f}:{i}: {m.group(1)}")
    if nalezy:
        print("Možný únik soukromých dat:\n  " + "\n  ".join(nalezy))
        sys.exit(1)
    print(f"Soukromí OK ({len(hledat)} jmen a obcí, {len(soubory)} souborů).")


if __name__ == "__main__":
    main()
