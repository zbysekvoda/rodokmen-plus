#!/usr/bin/env python3
"""Významné osobnosti rodokmenu: najde osoby s výjimečným povoláním nebo postavením.

Použití: python3 -I tools/osobnosti.py [--vse]
Prochází data/osoby.py (OSOBY): vlastní fakta `f` (ne poznámky – ty popisují i rodiče) a ruční pole `vyz`
(krátký popis, proč osoba vyčnívá). Boční souhrny (druh="bocni") podle textu `t`.
Vypíše je po kategoriích s tipy, kde hledat víc (noviny, ročenky, slovníky). --vse vypíše i slabé shody (sedlák, mlynář, mistr…).
Stejné kategorie používá web (stránka /osobnosti/): export_web.py k osobě uloží první silnou shodu (funkce zarad),
ruční `vyz` má vždy přednost. Slova se hledají jako začátky slov (farář = i farářem) a malými písmeny (velké jen na začátku
věty), aby se nechytala příjmení jako Kaplan, Starosta, Major, Sládek nebo Mlynář u manželů a kmotrů ve faktech.

Převzato a přepsáno na graf (OSOBY) z hnizdiljan/rodokmen-skill@d172316 (MIT):
https://github.com/hnizdiljan/rodokmen-skill/blob/d172316bc190d0f44894fa67115505729d587c6a/skills/rodokmen/tools/osobnosti.py
(starší varianta: https://github.com/Brunobeee/rodokmen-skill/blob/7ad48a869981282ab815520bfa295ee534290b3b/skills/rodokmen/tools/osobnosti.py;
původně PR #23 od oskar-stierand v sarsonj/rodokmen-skill).
"""
import os
import re
import sys

for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

# kategorie: (název, kmeny slov, tip kde hledat). „obecní“ záměrně chybí (obecní pastýř, obecní sluha),
# „sokol“ jen jako sokolský/v Sokole/člen Sokola (Sokol, Sokolová bývá příjmení); tituly (MUDr., Ing.) v jakékoli velikosti.
KATEGORIE = [
    ("Vzdělanci a duchovní", r"farář|kaplan|kněz|děkan|vikář|kanovník|biskup|páter|učitel|řídící|profesor|ředitel škol|doktor|(?i:mudr|judr|phdr|rndr|dr|ing)\.|lékař|"
     r"ranhojič|chirurg|advokát|notář|soudce|inženýr|architekt|lékárník|studoval|absolvent|maturit|univerzit",
     "Katalogy duchovenstva (Catalogus cleri), školní výroční zprávy, Kramerius, NDK"),
    ("Vědci a vynálezci", r"vědec|badatel|vynález|patent|astronom|chemik|fyzik|botanik|přírodověd|historik|archivář|akademi",
     "Ottův slovník naučný, Biografický slovník českých zemí (biography.hiu.cas.cz)"),
    ("Umělci", r"malíř|sochař|hudebník|muzikant|kapelník|varhaník|ředitel kůru|regenschori|skladatel|zpěvák|herec|herečka|spisovatel|"
     r"básník|fotograf|kreslíř|řezbář",
     "Kramerius (noviny), Abart (databáze umělců), Český hudební slovník"),
    ("Funkcionáři a úředníci", r"starosta|purkmistr|rychtář|radní|poslanec|senátor|úředník|správce|vrchní|hejtman|purkrabí|důchodní|"
     r"direktor|předseda|místopředseda|jednatel|okresní|zemský|četník|četnick|celník|poštmistr|přednosta",
     "Úřední listy, Hof- und Staatshandbuch, schematismy, obecní kroniky"),
    ("Vojáci a důstojníci", r"důstojník|poručík|nadporučík|setník|kapitán|major|plukovník|generál|šikovatel|legionář|legie|vyznamenán|medail",
     "VÚA – kartotéky legionářů (legie100.com), kvalifikační listiny, Verlustliste"),
    ("Sportovci", r"sportov|sokolsk|v Sokole|člen Sokola|závodník|reprezent|olympi|mistr republiky|fotbal|hokej|lyžař|atlet|gymnast|cvičitel",
     "Kramerius (sportovní rubriky), Sokolské věstníky, archivy klubů"),
    ("Podnikatelé a velcí hospodáři", r"továrník|majitel továrny|podnikatel|statkář|velkostatk|stavitel|firma|pivovarník|majitel pivovaru",
     "Adresáře (Compass), živnostenské rejstříky, noviny"),
    ("Mistři, sedláci a živnostníci", r"sedlák|mlynář|sládek|hostinsk|obchodník|kupec|mistr",
     "Gruntovní knihy, adresáře, cechovní knihy"),
]
SLABE = {"Mistři, sedláci a živnostníci"}  # běžné na vsi – vypisuje se jen s --vse, na web nejde
# začátek slova i u písmen s diakritikou (\b v regulárních výrazech JavaScriptu by u „řídící“ nefungovalo – proto se počítá tady)
RX = [(n, re.compile(rf"(?<!\w)(?:{rx})"), tip) for n, rx, tip in KATEGORIE]


def male(text):
    """Velké písmeno jen na začátku textu a věty -> malé (Farář v Holicích = farář v Holicích); jinde zůstane (příjmení)."""
    return re.sub(r"(^|[.!?;]\s+)(\w)", lambda m: m.group(1) + m.group(2).lower(), text)


def kategorie(text):
    text = male(text)
    return [(n, m.group(0), tip) for n, rx, tip in RX if (m := rx.search(text))]


def zarad(fakta):
    """Pro web: první silná kategorie a fakt, který ji určil -> {"kat", "poradi", "fakt"}, nebo None."""
    for i, (n, rx, _) in enumerate(RX):
        if n in SLABE:
            continue
        for f in fakta:
            if rx.search(male(f)):
                return {"kat": n, "poradi": i, "fakt": f}
    return None


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
    import graf
    vse = "--vse" in sys.argv
    g = graf.nacti()
    kandidati = []
    for i, p in g.osoby.items():
        if p.get("druh") == "bocni":
            kandidati.append((i, p.get("n", "?"), "", p.get("vyz", ""), p.get("t", "")))
        elif p.get("st") != "unk" or p.get("vyz"):
            # jen vlastní údaje; poznámky zmiňují i rodiče
            kandidati.append((i, p.get("n", "?"), p.get("y", ""), p.get("vyz", ""), " ".join(p.get("f", []))))

    po_kat = {}
    for i, jm, y, vyz, text in kandidati:
        if vyz:
            po_kat.setdefault("Ručně označení (vyz)", []).append((i, jm, y, vyz))
            continue
        for n, slovo, tip in kategorie(text):
            if n in SLABE and not vse:
                continue
            po_kat.setdefault(n, []).append((i, jm, y, f"„{slovo}“ – {text.strip()[:110]}"))
    if not po_kat:
        print("Žádný předek s výjimečným povoláním zatím v datech není." + ("" if vse else " (--vse ukáže i sedláky, mlynáře, mistry…)"))
        return
    tipy = {n: tip for n, _, tip in KATEGORIE}
    for n, lidi in po_kat.items():
        print(f"\n## {n} ({len(lidi)})")
        if n in tipy:
            print(f"   kde hledat víc: {tipy[n]}")
        for i, jm, y, co in lidi:
            print(f" {i}  {jm} {y}: {co}")
    print("\nJen náměty podle slov v datech. Ověř v zápisu; potvrzeným doplň do osoby pole vyz=\"krátký popis\" (pak jsou na webu nahoře).")


if __name__ == "__main__":
    main()
