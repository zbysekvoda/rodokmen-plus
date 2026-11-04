# Osoby a vztahy rodokmenu jako GRAF. Identita osoby = trvalé id (slug), ne Kekulého číslo.
# Kekulého čísla („č. 64“ v poznámkách) se počítají z grafu pro zvolený kořen (KORENY) – jen pro zobrazení
# (vějíř, rody, přehled předků). Výpis čísel: python3 tools/graf.py cisla [koren]
#
# OSOBY = {id: dict(n=…, sex="M"/"F", y=…, st=…, f=[…], r=[…], note=…, bydliste=[…])}
#   id   malými písmeny bez diakritiky: jmeno-prijmeni-rok (např. "jan-novak-1890"); po založení se NEMĚNÍ
#        (je v URL /osoba/<id>/). Kolize → přidat pomlčku a číslo.
#   n    jméno; ženy rodným příjmením („Anna Dvořáková“), u nejistého čtení otazník („Marie Špalková (?)“)
#   sex  "M" / "F" – povinné (dřív plynulo z čísla)
#   y    roky života pro přehledy: "* 1931" (žije / úmrtí neznámé), "1850–1910", "asi 1720–1785", "1680 – před 1740"
#   st   stav doložení:  doc  = doloženo matrikou (čteno přímo ze snímku)
#                        prob = pravděpodobné (shoda údajů, ale ne přímý doklad)
#                        fam  = údaj od rodiny / z rodinného dokumentu
#                        mh   = jen z cizího rodokmenu na internetu (MyHeritage, Geni…) – neověřeno
#                        unk  = neznámé (jen místo v rodokmenu)
#   f    fakta jako krátké věty: "* 12. 3. 1873 Hořice čp. 477", "kovář", "× 28. 1. 1897 Anna Stejskalová", "† 14. 5. 1902"
#        (* narození, × sňatek, † úmrtí – podle těchto značek web pozná sňatky a místa pro mapu)
#   r    klíče zápisů z data/zaznamy.json, které osobu dokládají
#   note poznámka: proč je údaj nejistý, rozpory, odkud se vzal
#   bydliste  volitelně: kde osoba žila – seznam dict(obec, cp, od, do, role, zdroj=[klíče ze zaznamy.json]);
#        jen z doložených faktů, nejisté s (?); zdroj "rodina" = údaj od rodiny (udaje_od_rodiny.md).
#        Klíč (obec, cp) propojuje rodokmen s dějinami domů (tools/domy_rodiny.py).
#   druh "bocni" = souhrnný záznam o bočních příbuzných (dřív SIDE): n = nadpis, t = text; na webu
#        se ukáže u osoby, ke které vede vztah t="pribuzny". Lepší je zakládat boční příbuzné jako
#        normální osoby s hranami rodic/manzele (sourozenec = stejní rodiče).
#   tataz id jiné osoby: tentýž člověk zapsaný podruhé (předek v rodokmenu vícekrát, dřív SAME) –
#        nese jen údaje k druhému výskytu; hrany vedou z hlavní osoby.
# Žijící lidé: jen jméno a rok narození (soukromí), note="Žijící – údaje jen základní."
# Neznámý otec nemanželského dítěte: osoba n="otec neuveden", st="unk" s hranou rodic (na webu bez stránky).

KORENY = {
    "hlavni": "",   # id výchozí osoby rodokmenu (č. 1), např. "jan-novak-1990"
    # "manzelka": "<id>",            # druhý kořen – doplní se, až budou data o manželce
}

OSOBY = {
}

# Hrany grafu. Pořadí nehraje roli; jedna hrana na řádek.
#   dict(t="rodic", a=<rodič>, b=<dítě>)                       – otec/matka podle sex rodiče
#   dict(t="manzele", a=<muž>, b=<žena>)                       – manželství (rodiče společného dítěte)
#   dict(t="kmotr", a=<kmotr>, b=<křtěnec>) / dict(t="svedek", a=<svědek>, b=<ženich nebo nevěsta>)
#   dict(t="pribuzny", a=<boční záznam>, b=<osoba>)            – volná vazba (dřív SIDE k=…)
# Volitelně u každé hrany: st="doc"/"prob"/… (jistota vazby; bez st platí jistota osob),
# r=[klíče zápisů], datum="…", note="…". Sourozenci, strýcové ap. se NEZAPISUJÍ – plynou z rodičů.

VZTAHY = [
]

# Rody = větve podle pradědečků a prababiček výchozí osoby: slug rodu → název, popis, zakladatel (id osoby).
RODY = {
}

# Rozpory a otevřené otázky (na web do „Co hledáme“) jako dvojice (otázka, odpověď). Odpověď začněte
# „Vyřešeno: …“ (na webu se skryje), „Hypotéza: …“ nebo „Otevřené: …“. Jde na web – nic citlivého.
# ("Kdy se narodil Jan Novák?", "Otevřené: rodina říká 1850, v Holicích 1848–1852 nenalezen.")
# Volitelně třetí prvek dict(osoby=["id"], rody=["slug rodu"]) – otázka se pak ukáže i na stránce osoby / rodu.
ISSUES = [
]

# Hypotézy o původu rodu nad rámec doložené linie (zobrazí se na stránce rodu); rod = id osoby (zakladatel větve):
# dict(rod="jan-novak-1890", nadpis="Hypotéza: …", text="…", polozky=[("Jan Novák", "kmotr 1681…")], zaznamy=["klic"])
HYPOTEZY = [
]
