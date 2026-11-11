#!/usr/bin/env python3
"""Historický kontext: události z osy (tools/udalosti.json) a z projektové vrstvy (data/udalosti.json).

Použití (z kořene projektu):
  python3 tools/udalosti.py rok 1866 [--misto Holice]       # události platné v roce
  python3 tools/udalosti.py rozsah 1914 1920 [--misto X]    # události, které zasahují do intervalu
  python3 tools/udalosti.py osoba jan-novak-1890            # události za života osoby s jejím věkem
  python3 tools/udalosti.py stat 1940 [--misto Holice]      # státní útvar (monarchie, republika…) v roce / místě
  python3 tools/udalosti.py wikidata Holice [--okres] [--klic holice]  # KANDIDÁTI z Wikidat (jen výpis JSON)

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
Wikidata: dotaz SPARQL na query.wikidata.org najde místo podle českého labelu (s --okres okres ČR) a události
vázané přes P276 / P131 s datem P585 / P580 / P582. Vypíše JSON položky ve formátu data/udalosti.json
(zdroj „Wikidata Q…“, jistota "obecne") jen ke kontrole – nic nezapisuje, přepis do projektu je ruční.
Státy (tools/staty.json, projekt přebíjí přes data/staty.json): v jakém státě a režimu místo leželo. Výjimky
z hlavní linie nesou `kde` s oblastí (hlucinsko, sudety, zaolzi, valticko, vitorazsko); místo ji dostane polem "oblast" v mista.json
a pro dobu výjimky pak platí ona místo celostátní položky. `osoba` vypíše i státy za života osoby podle všech
bydlišť (bydliste[].obec s od/do; bez bydliště podle místa narození).
Exit kódy: 0 v pořádku, 1 neznámá osoba / místo nebo chybná data, 2 chyba sítě (Wikidata).
"""
import argparse, datetime, json, os, re, sys, urllib.error, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
OSA = os.path.join(TOOLS, "udalosti.json")
STATY = os.path.join(TOOLS, "staty.json")
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


def svet_kolem(osoby, osa, mista, n=5, minimum=3, dnes=None):
    """Box „Svět kolem“ v knize: nejvýznamnější události za životů skupiny osob (generace), chronologicky.
    Kandidáti = kontext_osob, výběr = nejvyznamnejsi. Když limit na kategorii nechá méně než `minimum`
    a kandidátů je víc, doplní se bez limitu na kategorii; [] = box vynechat."""
    kand = kontext_osob(osoby, osa, mista, dnes)
    vyber = nejvyznamnejsi(kand, n)
    if len(vyber) < minimum and len(kand) > len(vyber):
        vyber = nejvyznamnejsi(kand, minimum, na_kategorii=minimum)
    return vyber


def nacti_staty(projekt=None, staty=STATY):
    """Státní útvary pluginu sloučené s data/staty.json projektu (stejné id přebíjí)."""
    polozky = {e["id"]: e for e in _json(staty) or []}
    if projekt:
        for e in _json(os.path.join(projekt, "data", "staty.json")) or []:
            polozky[e["id"]] = dict(e, projekt=True)
    return list(polozky.values())


def _datum(d, konec=False):
    c = [int(x) for x in str(d).split("-")]
    if len(c) == 1:
        c += [12, 31] if konec else [1, 1]
    elif len(c) == 2:
        c.append(31 if konec and c[1] in (1, 3, 5, 7, 8, 10, 12) else 30 if konec and c[1] != 2 else 28 if konec else 1)
    return datetime.date(*c)


def staty_v_rozsahu(staty, od, do, misto=None, mista=None):
    """Státní útvary, ve kterých místo leželo v letech [od, do], chronologicky: [{od, do, stat, zeme}] (od/do = date).
    Položka s oblastí místa (mista.json "oblast") vytlačí po dobu své platnosti celostátní položky."""
    m = (mista or {}).get(misto) or {}
    oblast, z = m.get("oblast"), zeme_mista(m)
    jeden_den = datetime.timedelta(days=1)
    vyjimky = [s for s in staty if oblast and oblast in s["kde"]]
    useky = [(_datum(s["od"]), _datum(s["do"], True), s) for s in vyjimky]
    for s in staty:
        if s in vyjimky or not set(s["kde"]) & set(ZEME) or (z and z not in s["kde"]):
            continue
        kusy = [(_datum(s["od"]), _datum(s["do"], True))]
        for a2, b2, _ in useky[:len(vyjimky)]:
            kusy = [k for a, b in kusy for k in ((a, min(b, a2 - jeden_den)), (max(a, b2 + jeden_den), b)) if k[0] <= k[1]]
        useky += [(a, b, s) for a, b in kusy]
    return [dict(od=a, do=b, stat=s, zeme=(s.get("zeme") or {}).get(oblast) or (s.get("zeme") or {}).get(z)) for a, b, s in sorted(useky, key=lambda u: u[0])
            if a.year <= do and b.year >= od]


def _bydliste_useky(p, mista, nar, umr):
    """[(misto, od, do)] v letech z bydliste s obcí v mista.json; chybějící od/do doplní narození, další bydliště, úmrtí."""
    b = sorted((x for x in p.get("bydliste", []) or [] if x.get("obec") in mista),
               key=lambda x: x.get("od") or nar)
    useky = []
    for i, x in enumerate(b):
        od = max(nar, x.get("od") or nar)
        do = min(umr, x.get("do") or (b[i + 1].get("od") or umr if i + 1 < len(b) else umr))
        if od <= do:
            useky.append((x["obec"], od, do))
    return useky


def staty_osoby(p, staty, mista, dnes=None):
    """Státy za života osoby podle všech jejích bydlišť (jinak podle místa narození): [{od, do, stat, zeme, misto}],
    chronologicky, stejný stát po sobě sloučený. [] když život nejde určit."""
    z = zivot(p, dnes)
    if not z:
        return []
    nar, umr, _ = z
    useky = _bydliste_useky(p, mista, nar, umr) or [(misto_osoby(p, mista), nar, umr)]
    out = []
    for misto, od, do in useky:
        for u in staty_v_rozsahu(staty, od, do, misto, mista):
            u["misto"] = misto
            if out and out[-1]["stat"]["id"] == u["stat"]["id"]:
                out[-1]["do"] = max(out[-1]["do"], u["do"])
            else:
                out.append(u)
    return out


def stat_pro_web(u, nar=None):
    d = dict(id=u["stat"]["id"], nazev=u["stat"]["nazev"], zrizeni=u["stat"].get("zrizeni", ""), od=u["od"].year,
             do=u["do"].year, zeme=u.get("zeme") or "", misto=u.get("misto") or "", text=u["stat"].get("text", ""))
    if nar is not None:
        d["vek"] = u["od"].year - nar
    return d


def staty_skupiny(osoby, staty, mista, dnes=None):
    """Názvy států za životů skupiny osob (generace v knize), chronologicky podle prvního výskytu, bez opakování."""
    vse = sorted((u for p in osoby for u in staty_osoby(p, staty, mista, dnes)), key=lambda u: u["od"])
    return list(dict.fromkeys(u["stat"]["nazev"] for u in vse))


def radek_statu(u, nar=None):
    do = "" if u["do"].year >= datetime.date.today().year else u["do"].isoformat()
    v = f" (věk {max(0, u['od'].year - nar)})" if nar is not None else ""
    zeme = f", {u['zeme']}" if u["zeme"] else ""
    zeme += f" ({u['misto']})" if u.get("misto") else ""
    return f"{u['od'].isoformat()} – {do:10}{v}  {u['stat']['nazev']}{zeme} [{u['stat'].get('zrizeni', '')}]"


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


WD_URL = "https://query.wikidata.org/sparql"
WD_TIMEOUT = 30


def _verze():
    try:
        with open(os.path.join(ROOT, "VERZE"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "dev"


WD_UA = f"rodokmen-plus/{_verze()} (genealogy tool)"
WD_KATEGORIE = (("bitv", "valka"), ("válk", "valka"), ("obléh", "valka"), ("epidemi", "epidemie"),
                ("mor", "epidemie"), ("cholera", "epidemie"), ("hlad", "hlad"), ("požár", "zivel"),
                ("povodeň", "zivel"), ("povodn", "zivel"), ("zemětřes", "zivel"), ("povstání", "povstani"),
                ("vzpour", "povstani"), ("stávk", "povstani"))


def wd_dotaz(nazev, okres=False, od=1620, limit=50):
    """SPARQL: místo podle českého labelu v ČR (u okresu okres ČR Q548611), události v něm s datem od roku `od`."""
    lit = json.dumps(nazev, ensure_ascii=False)
    typ = "  ?misto wdt:P31 wd:Q548611 .\n" if okres else ""
    vazba = "(wdt:P276|wdt:P131)/wdt:P131*" if okres else "wdt:P276|wdt:P131"
    return f"""SELECT DISTINCT ?e ?eLabel ?popis ?typLabel ?kdy ?zacatek ?konec WHERE {{
  ?misto rdfs:label {lit}@cs ; wdt:P17 wd:Q213 .
{typ}  ?e {vazba} ?misto .
  OPTIONAL {{ ?e wdt:P585 ?kdy }}
  OPTIONAL {{ ?e wdt:P580 ?zacatek }}
  OPTIONAL {{ ?e wdt:P582 ?konec }}
  FILTER NOT EXISTS {{ ?e wdt:P31/wdt:P279* wd:Q39825 }}   # bez sčítání lidu (stovky položek na obec)
  FILTER(BOUND(?kdy) || BOUND(?zacatek))
  FILTER(YEAR(COALESCE(?kdy, ?zacatek)) >= {int(od)})
  OPTIONAL {{ ?e wdt:P31 ?typ }}
  OPTIONAL {{ ?e schema:description ?popis FILTER(LANG(?popis) = "cs") }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "cs,en". }}
}}
ORDER BY COALESCE(?kdy, ?zacatek)
LIMIT {int(limit)}"""


def wd_stahni(dotaz, timeout=WD_TIMEOUT):
    """Odpověď SPARQL (JSON) – jediné místo se sítí, v testech se nahrazuje."""
    url = WD_URL + "?" + urllib.parse.urlencode({"query": dotaz, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": WD_UA, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _wd_datum(v):
    """'1866-07-03T00:00:00Z' → '1866-07-03'; přesnost na rok (01-01) se zkrátí na rok."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", (v or "").lstrip("+"))
    if not m:
        return None
    return m.group(1) if (m.group(2), m.group(3)) == ("01", "01") else m.group(0)


def _wd_kategorie(*texty):
    t = " ".join(x for x in texty if x).lower()
    return next((k for klic, k in WD_KATEGORIE if klic in t), "sprava")


def _slug(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s)[:40].strip("-") or "udalost"


def wd_kandidati(odpoved, kde, okres=False):
    """Řádky SPARQL → položky ve formátu data/udalosti.json (jedna na QID)."""
    vysl = {}
    for b in odpoved.get("results", {}).get("bindings", []):
        g = lambda k: b.get(k, {}).get("value")
        qid = (g("e") or "").rsplit("/", 1)[-1]
        if not re.match(r"^Q\d+$", qid):
            continue
        od = _wd_datum(g("kdy")) or _wd_datum(g("zacatek"))
        if not od or qid in vysl:
            continue
        do = _wd_datum(g("konec")) or od
        nazev = g("eLabel") or qid
        vysl[qid] = {"id": f"{od[:4]}-{_slug(nazev)}", "od": od, "do": do,
                     "uroven": "region" if okres else "obec", "kde": [kde],
                     "kategorie": _wd_kategorie(nazev, g("typLabel"), g("popis")), "nazev": nazev,
                     "text": g("popis") or "", "dopad": {"umrti": False, "vojaci": False},
                     "zdroj": f"Wikidata {qid}", "jistota": "obecne"}
    return list(vysl.values())


def wikidata(a):
    try:
        odp = wd_stahni(wd_dotaz(a.nazev, a.okres, a.od, a.limit))
    except (urllib.error.URLError, OSError, ValueError) as e:
        duvod = getattr(e, "reason", None) or e
        print(f"Wikidata nejsou dostupná ({duvod}). Zkus to později.", file=sys.stderr)
        return 2
    kand = wd_kandidati(odp, a.klic or a.nazev, a.okres)
    print(json.dumps(kand, ensure_ascii=False, indent=1))
    print(f"{len(kand)} kandidátů z Wikidat – jen k ověření, nic se nezapsalo. Zkontroluj datum, kategorii,"
          f" dopad a `kde`, pak ručně přepiš do data/udalosti.json.", file=sys.stderr)
    return 0


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
    t = sub.add_parser("stat", help="státní útvar v roce (s --misto včetně výjimek oblasti)")
    t.add_argument("rok", type=int)
    t.add_argument("--misto")
    o = sub.add_parser("osoba", help="události za života osoby s jejím věkem")
    o.add_argument("id")
    w = sub.add_parser("wikidata", help="kandidáti událostí z Wikidat pro obec / okres (jen výpis JSON)")
    w.add_argument("nazev", help="český název obce (nebo okresu s --okres)")
    w.add_argument("--okres", action="store_true", help="název je okres ČR")
    w.add_argument("--klic", help="klíč místa z data/mista.json pro pole kde (výchozí: název)")
    w.add_argument("--od", type=int, default=1620, help="jen události od roku (výchozí 1620)")
    w.add_argument("--limit", type=int, default=50, help="nejvýš řádků SPARQL (výchozí 50)")
    return p.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    if a.prikaz == "wikidata":
        return wikidata(a)
    projekt = os.path.abspath(a.projekt)
    osa, mista = nacti_osu(projekt), nacti_mista(projekt)
    kat = set(a.kategorie.split(",")) if a.kategorie else None
    misto = getattr(a, "misto", None)
    if misto and misto not in mista:
        print(f"Místo „{misto}“ není v data/mista.json.", file=sys.stderr)
        return 1
    if a.prikaz == "stat":
        for u in staty_v_rozsahu(nacti_staty(projekt), a.rok, a.rok, misto, mista):
            print(radek_statu(u))
        return 0
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
        print("\nStát v místě osoby:")
        for u in staty_osoby(p, nacti_staty(projekt), mista):
            print("  " + radek_statu(u, nar))
    print("\nJe to kontext doby, ne fakt o osobě – vazbu na událost tvrdí jen zápis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
