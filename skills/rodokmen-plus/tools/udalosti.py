#!/usr/bin/env python3
"""Historický kontext: události z osy (tools/udalosti.json) a z projektové vrstvy (data/udalosti.json).

Použití (z kořene projektu):
  python3 tools/udalosti.py rok 1866 [--misto Holice]       # události platné v roce
  python3 tools/udalosti.py rozsah 1914 1920 [--misto X]    # události, které zasahují do intervalu
  python3 tools/udalosti.py osoba jan-novak-1890            # události za života osoby s jejím věkem

Volby: --projekt <složka> (výchozí: kořen projektu, ve kterém leží tools/), --kategorie epidemie,hlad

Osa pluginu nese jen celostátní (uroven "cr") a zemskou úroveň (kde = cechy / morava / slezsko).
Projekt může mít vlastní data/udalosti.json ve stejném formátu; jeho `kde` jsou klíče z data/mista.json.
Při shodě id má přednost projektová položka. Chybějící soubor není chyba.

Filtr podle místa (--misto = klíč z data/mista.json): celostátní události + zemské pro zemi místa + projektové
s tím místem v `kde`. Země místa: pole "zeme" v mista.json, jinak odhad z kraje v poli "osm" (kraje, které
leží ve dvou zemích – Vysočina, Moravskoslezský, okres Svitavy – odhadnout nejde). U neznámé země se zemské
události nefiltrují.

Osoba: život = rok narození až rok úmrtí (z faktů * a †, jinak z pole y). Když úmrtí chybí, bere se
narození + 80 let, nejvýš letošní rok (žijící). Když chybí narození, bere se úmrtí − 80. Věk je
rok začátku události − rok narození (u události začaté před narozením 0). Místo osoby: první bydliště
(bydliste[0].obec), jinak místo narození, které se najde podle regulárního výrazu "re" v mista.json.

Knihovna:  import udalosti; osa = udalosti.nacti_osu(projekt)  → seznam položek (plugin + projekt)
           udalosti.v_rozsahu(osa, od, do, misto=None, mista=None)
Jsou to KONTEXT, ne fakta o osobě – vazbu na událost tvrdí jen zápis (viz docs/navrhy/historicky-kontext.md).
Exit kódy: 0 v pořádku, 1 neznámá osoba / místo nebo chybná data.
"""
import argparse, datetime, json, os, re, sys
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
OSA = os.path.join(TOOLS, "udalosti.json")
ZEME = ("cechy", "morava", "slezsko")
KRAJE = {"Jihomoravský": "morava", "Zlínský": "morava", "Olomoucký": "morava", "Praha": "cechy",
         "Hlavní město Praha": "cechy", "Středočeský": "cechy", "Jihočeský": "cechy", "Plzeňský": "cechy",
         "Karlovarský": "cechy", "Ústecký": "cechy", "Liberecký": "cechy", "Královéhradecký": "cechy",
         "Pardubický": "cechy"}
NEJASNE_OKRESY = ("Svitavy",)   # okres v kraji jedné země, ale částečně v druhé
DOZITI = 80


def _json(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def nacti_osu(projekt=None, osa=OSA):
    """Osa pluginu sloučená s data/udalosti.json projektu (projektová položka přebíjí stejné id), seřazená podle od."""
    polozky = {e["id"]: e for e in _json(osa) or []}
    if projekt:
        for e in _json(os.path.join(projekt, "data", "udalosti.json")) or []:
            polozky[e["id"]] = dict(e, projekt=True)
    return sorted(polozky.values(), key=lambda e: (e["od"], e["id"]))


def nacti_mista(projekt):
    return _json(os.path.join(projekt, "data", "mista.json")) or {}


def rok(d):
    return int(str(d)[:4])


def zeme_mista(m):
    """Země (cechy/morava/slezsko) záznamu z mista.json, nebo None, když ji nelze určit."""
    if not m:
        return None
    if m.get("zeme") in ZEME:
        return m["zeme"]
    osm = m.get("osm", "")
    if any(f"okres {o}" in osm for o in NEJASNE_OKRESY):
        return None
    for kraj, z in KRAJE.items():
        if re.search(rf"\b{kraj}( kraj)?\b", osm):
            return z
    return None


def plati_v_miste(e, misto, mista):
    if misto is None:
        return True
    if e.get("projekt"):
        return e.get("uroven") == "cr" or misto in e.get("kde", []) or zeme_mista(mista.get(misto)) in e.get("kde", [])
    if e["uroven"] == "cr":
        return True
    z = zeme_mista(mista.get(misto))
    return z is None or z in e["kde"]


def v_rozsahu(osa, od, do, misto=None, mista=None, kategorie=None):
    """Události, jejichž roky [od, do] se překrývají s intervalem; volitelně filtr podle místa a kategorií."""
    mista = mista or {}
    return [e for e in osa if rok(e["od"]) <= do and rok(e["do"]) >= od
            and (not kategorie or e["kategorie"] in kategorie) and plati_v_miste(e, misto, mista)]


def _rok_faktu(p, znak):
    for f in p.get("f", []):
        if f.strip().startswith(znak):
            m = re.search(r"\b(1[5-9]\d\d|20\d\d)\b", f)
            if m:
                return int(m.group(1))
    return None


def zivot(p, dnes=None):
    """(narození, úmrtí, odhad_úmrtí) v letech. Fallback viz docstring modulu; None, když nejde určit nic."""
    dnes = dnes or datetime.date.today().year
    roky = [int(x) for x in re.findall(r"\b(1[5-9]\d\d|20\d\d)\b", p.get("y", ""))]
    nar = _rok_faktu(p, "*") or (roky[0] if roky and not p.get("y", "").strip().startswith("†") else None)
    umr = _rok_faktu(p, "†") or (roky[1] if len(roky) > 1 else None)
    if nar and umr:
        return nar, umr, False
    if nar:
        return nar, min(nar + DOZITI, dnes), True
    if umr:
        return umr - DOZITI, umr, True
    return None


def misto_osoby(p, mista):
    for b in p.get("bydliste", []) or []:
        if b.get("obec") in mista:
            return b["obec"]
    for f in p.get("f", []):
        if f.strip().startswith("*"):
            for k, m in mista.items():
                if re.search(m.get("re") or re.escape(k), f):
                    return k
    return None


# Významnost pro výběr „Doba“ (web, kniha): kolik událostí z kategorie zasáhlo běžný život; dopad na úmrtí / odvody přidá.
VAHA_KATEGORIE = {"valka": 6, "epidemie": 5, "hlad": 5, "rezim": 4, "povstani": 3, "mena": 3, "reforma": 3,
                  "migrace": 3, "zivel": 3, "hospodarstvi": 2, "sprava": 1, "cirkev": 1}


def vaha(e):
    d = e.get("dopad") or {}
    trvani = min(5, rok(e["do"]) - rok(e["od"]))
    return (VAHA_KATEGORIE.get(e.get("kategorie"), 1) + 3 * bool(d.get("umrti")) + 2 * bool(d.get("vojaci"))
            + 2 * bool(e.get("projekt")) + trvani / 5)


def doba(p, osa, mista, n=5, dnes=None):
    """Nejvýznamnějších n událostí za života osoby, chronologicky: [(událost, věk na začátku)]; [] když život nejde určit.
    Místně vázané filtruje podle misto_osoby jako příkaz `osoba`."""
    z = zivot(p, dnes)
    if not z:
        return []
    nar, umr, _ = z
    kand = v_rozsahu(osa, nar, umr, misto_osoby(p, mista), mista)
    return [(e, rok(e["od"]) - nar) for e in nejvyznamnejsi(kand, n)]   # záporný věk = začalo před narozením


def nejvyznamnejsi(kand, n=5, na_kategorii=2):
    """n událostí podle váhy, chronologicky. Pestrost: nejvýš na_kategorii z jedné kategorie a nic, co leží celé uvnitř
    už vybrané události stejné kategorie (totální nasazení uvnitř 2. světové války)."""
    vyber = []
    for e in sorted(kand, key=lambda e: (-vaha(e), e["od"], e["id"])):
        stejne = [x for x in vyber if x["kategorie"] == e["kategorie"]]
        if len(stejne) >= na_kategorii or any(rok(x["od"]) <= rok(e["od"]) and rok(e["do"]) <= rok(x["do"]) for x in stejne):
            continue
        vyber.append(e)
        if len(vyber) == n:
            break
    return sorted(vyber, key=lambda e: (e["od"], e["id"]))


def kontext_osob(osoby, osa, mista, dnes=None):
    """Události, které se překrývají se životem aspoň jedné osoby (místně vázané jen pro místo té osoby)."""
    ids = set()
    for p in osoby:
        z = zivot(p, dnes)
        if z:
            ids.update(e["id"] for e in v_rozsahu(osa, z[0], z[1], misto_osoby(p, mista), mista))
    return [e for e in osa if e["id"] in ids]


def pro_web(e):
    """Položka osy pro data webu (bez zdrojových poznámek navíc); od/do jako roky pro osu."""
    return dict(id=e["id"], od=rok(e["od"]), do=rok(e["do"]), datum=[e["od"], e["do"]], nazev=e["nazev"], text=e.get("text", ""),
                kategorie=e.get("kategorie", ""), uroven=e.get("uroven", ""), kde=e.get("kde", []), zdroj=e.get("zdroj", ""),
                projekt=bool(e.get("projekt")), vaha=round(vaha(e), 1))


def radek(e, vek=None):
    kdy = e["od"][:4] if rok(e["od"]) == rok(e["do"]) else f"{e['od'][:4]}–{e['do'][:4]}"
    kde = "ČR" if e["uroven"] == "cr" else ", ".join(e["kde"])
    v = f" (věk {vek})" if vek is not None else ""
    return f"{kdy:>9}{v}  {e['nazev']} [{e['kategorie']}; {kde}]{' *projekt' if e.get('projekt') else ''}"


def vypis(udalosti, vek_od=None):
    if not udalosti:
        print("Žádné události.")
    for e in udalosti:
        print(radek(e, None if vek_od is None else max(0, rok(e["od"]) - vek_od)))


def parse_args(argv):
    popis, _, epilog = __doc__.partition("\n\n")
    p = argparse.ArgumentParser(prog="udalosti.py", description=popis.strip(), epilog=epilog.strip(),
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--projekt", default=ROOT, help="složka projektu (s data/)")
    p.add_argument("--kategorie", help="jen tyto kategorie, oddělené čárkou (např. epidemie,hlad)")
    sub = p.add_subparsers(dest="prikaz", required=True)
    r = sub.add_parser("rok", help="události platné v roce")
    r.add_argument("rok", type=int)
    r.add_argument("--misto")
    s = sub.add_parser("rozsah", help="události zasahující do intervalu let")
    s.add_argument("od", type=int)
    s.add_argument("do", type=int)
    s.add_argument("--misto")
    o = sub.add_parser("osoba", help="události za života osoby s jejím věkem")
    o.add_argument("id")
    return p.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    projekt = os.path.abspath(a.projekt)
    osa, mista = nacti_osu(projekt), nacti_mista(projekt)
    kat = set(a.kategorie.split(",")) if a.kategorie else None
    misto = getattr(a, "misto", None)
    if misto and misto not in mista:
        print(f"Místo „{misto}“ není v data/mista.json.", file=sys.stderr)
        return 1
    if a.prikaz == "rok":
        vypis(v_rozsahu(osa, a.rok, a.rok, misto, mista, kat))
    elif a.prikaz == "rozsah":
        if a.od > a.do:
            print("Začátek intervalu je po konci.", file=sys.stderr)
            return 1
        vypis(v_rozsahu(osa, a.od, a.do, misto, mista, kat))
    else:
        sys.path.insert(0, TOOLS)
        import graf
        g = graf.nacti(os.path.join(projekt, "data", "osoby.py"))
        i = g.id_osoby(a.id)
        if not i:
            print(f"Osoba „{a.id}“ není v data/osoby.py.", file=sys.stderr)
            return 1
        p = g.osoby[i]
        z = zivot(p)
        if not z:
            print(f"{p.get('n', i)}: chybí rok narození i úmrtí.", file=sys.stderr)
            return 1
        nar, umr, odhad = z
        m = misto_osoby(p, mista)
        print(f"{p.get('n', i)} ({i}), {nar}–{umr}{' (konec odhadem)' if odhad else ''}"
              f"{', místo ' + m if m else ', místo neurčeno'}")
        vypis(v_rozsahu(osa, nar, umr, m, mista, kat), vek_od=nar)
    print("\nJe to kontext doby, ne fakt o osobě – vazbu na událost tvrdí jen zápis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
