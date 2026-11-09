#!/usr/bin/env python3
"""Místa předků pro mapu na webu (data/mista.json): souřadnice obcí a domů (čísel popisných) z faktů osob.

Použití:
  mista.py pridej "Název" ["regulární výraz"] ["dotaz pro vyhledání"]
      přidá obec; výraz se hledá v údajích osob (výchozí = prvních 5 písmen, u víceslovných názvů zkrácené
      každé slovo, aby sedělo i skloňování), dotaz pro vyhledání (výchozí = "Název, Česko"; když nic nenajde,
      zkusí Slovensko a další sousední země); u víceznačných názvů (Podolí, Dub) přidej sousední obec:
      "Podolí, Odlochovice" – a ve výpisu vždy zkontroluj okres
  mista.py
      dohledá souřadnice obcí, které je ještě nemají, a bod každého domu („Hořice čp. 477“) z faktů osob
      v data/osoby.py; vypíše seznam a pod ním varování (nenalezeno, není obec, daleko od ostatních, bez souřadnic).
  mista.py znovu
      zahodí dosavadní souřadnice (kromě "rucne": true) a dohledá je znovu – např. po získání klíče Mapy.com.

Zdroj souřadnic:
  - s klíčem Mapy.com v proměnné prostředí MAPY_API_KEY: obce i domy z Mapy.com (geokódování REST API, zdarma
    250 000 kreditů měsíčně; klíč na https://developer.mapy.com/portal-muj-ucet/). Klíč nikdy nepiš do souborů,
    chatu ani commitu – jen do prostředí (např. načtený z Keychainu).
  - bez klíče: obce z OpenStreetMap Nominatim (přednostně sídla, 1 dotaz za sekundu), domy v Česku z RÚIAN (ČÚZK).
Domy jsou v klíči "adresy": {"477": {"lat": …, "lon": …, "zdroj": "Hořice 477, …"}}. Ruční bod (zaniklý dům
podle staré mapy) označ "rucne": true, nástroj ho nepřepíše.
Položka může mít "hypoteza": true a "rod": <Kekulé zakladatele rodu> – pak se na mapě ukáže jako hypotéza bez osob.

Převzato a sloučeno z forků (MIT):
  - Mapy.com, čísla popisná z faktů osob, kontrola vzdálenosti: vmi43/rodokmen-skill, skills/rodokmen/tools/mista.py
    @ 99e238ed18636f9a9fca481071761fefd7dbec66 (repo HEAD b89d5c91d78e61b8e20b9f2eab8b20d2f8e02e06)
  - Nominatim jen sídla (featuretype=settlement, je_sidlo), varování „není obec“ a > 50 km, kmen víceslovných obcí:
    hackra76/rodokmen-skill 0.8.1, skills/rodokmen/tools/mista.py
    @ 59ba1e666208af7888f6dd4dd5dc54e7c2706807 (repo HEAD 532f7b0a2fed99b9003a23a600085659edb741d2)
"""
import json, math, os, re, sys, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti (Nominatim: 1 dotaz za s pro všechny procesy)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "mista.json")
UA = "rodokmen-plus/1.0 (family genealogy map, occasional geocoding)"
MAPY = "https://api.mapy.com/v1/geocode"
VZDALENE_KM = 50   # nový bod dál než tohle od všech ostatních míst = asi jiná obec stejného jména
MAX_KM = 8         # dům dál od středu obce patří jiné obci stejného jména
SIDLA = {"city", "town", "village", "hamlet", "suburb", "quarter", "neighbourhood", "isolated_dwelling", "farm",
         "municipality", "borough", "cadastral_community"}   # place=locality chybí záměrně: neobydlené pojmenované místo


def klic():
    return os.environ.get("MAPY_API_KEY", "").strip()


def km(a, b):
    p = math.pi / 180
    x = math.sin((b[0] - a[0]) * p / 2) ** 2 + math.cos(a[0] * p) * math.cos(b[0] * p) * math.sin((b[1] - a[1]) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))


def bod(e):
    """(lat, lon) jako čísla, nebo None, když chybí nebo jsou nesmyslné."""
    try:
        lat, lon = float(e["lat"]), float(e["lon"])
    except (KeyError, TypeError, ValueError):
        return None
    return (lat, lon) if -90 <= lat <= 90 and -180 <= lon <= 180 else None


def stahni(url, hlavicky=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA} | (hlavicky or {}))
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


# --- Mapy.com (s klíčem) ---

def mapy(query, **par):
    par = {"query": query, "lang": "cs", "limit": 5} | par
    return stahni(MAPY + "?" + urllib.parse.urlencode(par), {"X-Mapy-Api-Key": klic()}).get("items", [])


def mapy_bod(it):
    return round(float(it["position"]["lat"]), 6), round(float(it["position"]["lon"]), 6)


def mapy_obec(q, zeme):
    """(lat, lon, popis, je_obec) nebo None."""
    loc = {"locality": zeme} if zeme else {}
    its = mapy(q, type="regional.municipality,regional.municipality_part", **loc)
    obec = bool(its)
    its = its or mapy(q, **loc)
    if not its:
        return None
    it = its[0]
    return (*mapy_bod(it), f"{it.get('name', '')}, {it.get('location', '')}".strip(", "), obec)


def mapy_dum(obec, cp, stred):
    its = mapy(f"{obec} {cp}", type="regional.address", preferNear=f"{stred[1]},{stred[0]}", limit=10)
    for it in its:
        jm = it.get("name", "")
        if "ev." in jm or not re.search(rf"(?<![\d/]){re.escape(cp)}(?:/|\s|$)", jm):   # ev. č. = chata, ne čp.
            continue
        b = mapy_bod(it)
        if km(stred, b) <= MAX_KM:
            return (*b, f"{jm}, {it.get('location', '')}".strip(", "))
    return None


# --- bez klíče: Nominatim (obce) a RÚIAN (domy) ---

def je_sidlo(r):
    if r.get("class") == "place":
        return r.get("type") in SIDLA
    if (r.get("class"), r.get("type")) != ("boundary", "administrative"):
        return False
    if r.get("addresstype"):   # obec má „municipality“, „village“…; kraj „state“, okres „county“
        return r["addresstype"] in SIDLA | {"city_district"}
    return int(r.get("place_rank") or 0) >= 16


def osm_obec(q, zeme):
    """(lat, lon, popis, je_obec) nebo None; nejdřív jen sídla, pak cokoli."""
    nalez = None
    for sidla in ({"featuretype": "settlement"}, {}):
        par = {"q": q, "format": "json", "limit": 5} | sidla | ({"countrycodes": zeme} if zeme else {})
        res = stahni("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(par))
        obce = [r for r in res if je_sidlo(r)]
        if obce:
            nalez = (obce[0], True)
            break
        nalez = nalez or ((res[0], False) if res else None)
    if not nalez:
        return None
    r = nalez[0]
    return round(float(r["lat"]), 4), round(float(r["lon"]), 4), r["display_name"], nalez[1]


def ruian_dum(obec, cp, stred):
    """Dům podle RÚIAN (ČÚZK, bez klíče; jen Česko). Tvary adres: „Osada 12, PSČ Obec“, „č.p. 12, PSČ Obec“,
    „Ulice 12/3, Část, PSČ Obec“. Ve městě bývá čp. 12 v několika částech obce – pak None (nejednoznačné)."""
    import mista_domy
    o = obec.replace("'", "")
    nalez = {}
    for where in (f"adresa LIKE '{o} {cp},%'", f"adresa LIKE 'č.p. {cp}, % {o}'",
                  f"adresa LIKE '% {cp}, %{o}'", f"adresa LIKE '% {cp}/%, %{o}'"):
        for a in mista_domy.ruian_q(1, where, "adresa", True):
            b = (round(a["geometry"]["y"], 6), round(a["geometry"]["x"], 6))
            if km(stred, b) <= MAX_KM:
                nalez[a["attributes"]["adresa"]] = b
        if len(nalez) == 1 and where.startswith(f"adresa LIKE '{o}"):   # osada s čp. – jednoznačné
            break
    if len(nalez) != 1:
        return None if not nalez else ("víc", list(nalez))
    (adr, b), = nalez.items()
    return (*b, adr)


def geocode(q, zeme="cz"):
    return (mapy_obec if klic() else osm_obec)(q, zeme)


def dum(obec, cp, stred):
    return (mapy_dum if klic() else ruian_dum)(obec, cp, stred)


# --- data projektu ---

def kmen(name):
    w = name.split()
    if len(w) == 1:
        return re.escape(w[0][:5])
    return r"\b" + r"\w*\s+".join(re.escape(x[:max(3, len(x) - 2)]) for x in w) + r"\w*"   # Moravský Písek → Moravsk\w*\s+Pís\w*


def osoby():
    f = os.path.join(ROOT, "data", "osoby.py")
    if not os.path.exists(f):
        return {}
    ns = {}
    exec(open(f, encoding="utf-8").read(), ns)
    return dict(ns.get("OSOBY", {}))   # graf osob: {id: dict(n=…, f=[…], …)}


def adresy_osob(P, name, e):
    """Čísla popisná uvedená ve faktech osob u místa: {„14“, „477“}."""
    rx = re.compile(rf"(?:{e.get('re') or re.escape(name)})\w*\s+čp\.\s*(\d+)")
    return {m for p in P.values() for f in p.get("f", []) for m in rx.findall(f)}


def uloz(cache):
    json.dump(cache, open(OUT, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)


def main():
    cache = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "pridej" and len(sys.argv) > 2:
        name = sys.argv[2]
        cache[name] = dict(cache.get(name, {}), re=sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else kmen(name),
                           dotaz=sys.argv[4] if len(sys.argv) > 4 else f"{name}, Česko")
    print("Zdroj:", "Mapy.com (MAPY_API_KEY)" if klic() else "OpenStreetMap Nominatim + RÚIAN (bez klíče Mapy.com)")
    P = osoby()
    pozor, nove = [], []
    for name, e in cache.items():
        if arg == "znovu" and not e.get("rucne"):
            for k in ("lat", "lon", "osm", "mapy"):
                e.pop(k, None)
        if not bod(e):
            vychozi = f"{name}, Česko"
            g = geocode(e.get("dotaz") or vychozi)
            if not g and e.get("dotaz", vychozi) == vychozi:   # výchozí dotaz: zkus sousední země
                g = geocode(name, "sk,pl,at,de,hu" if not klic() else None)
                if g:
                    pozor.append(f"MIMO ČESKO: {name} → {g[2][:80]} – zkontroluj, že je to ono")
            if not g:
                pozor.append(f"NENALEZENO: {name} – upravte 'dotaz' nebo doplňte lat/lon ručně")
                continue
            e["lat"], e["lon"] = g[0], g[1]
            e.pop("osm", None), e.pop("mapy", None)
            e["mapy" if klic() else "osm"] = g[2]
            if not g[3]:
                pozor.append(f"POZOR: není obec – zkontroluj: {name} → {g[2][:80]}")
            nove.append(name)
        if e.get("hypoteza") or not P:
            continue
        ad = e.get("adresy", {})
        for cp in sorted(adresy_osob(P, name, e), key=int):
            a = ad.get(cp, {})
            if arg == "znovu" and not a.get("rucne"):
                a = {}
            if bod(a):
                continue
            g = dum(name, cp, bod(e))
            if g and g[0] == "víc":
                pozor.append(f"DŮM NEJEDNOZNAČNÝ: {name} čp. {cp} – RÚIAN zná víc domů ({'; '.join(g[1][:3])}); "
                             f"doplňte bod ručně s \"rucne\": true")
            elif g:
                ad[cp] = {"lat": g[0], "lon": g[1], "zdroj": g[2]}
            else:
                pozor.append(f"DŮM NENALEZEN: {name} čp. {cp} – doplňte bod ručně "
                             f"(\"adresy\": {{\"{cp}\": {{\"lat\": …, \"lon\": …, \"rucne\": true}}}}); mapa ukáže střed obce")
        if ad:
            e["adresy"] = ad
        uloz(cache)   # po každém místě, ať se při přerušení nic neztratí
    for name in nove:   # až po celé dávce, ať nezáleží na pořadí
        d = [(km(bod(cache[name]), b), n) for n, o in cache.items() if n != name and (b := bod(o))]
        if d and min(d)[0] > VZDALENE_KM:
            pozor.append(f"POZOR: {name} je {min(d)[0]:.0f} km od nejbližšího místa ({min(d)[1]}) – je to ono?")
    uloz(cache)
    for n, e in cache.items():
        print(f"{n:28} {str(e.get('lat', '?')):>9} {str(e.get('lon', '?')):>9}  hledá „{e.get('re')}“  "
              f"{(e.get('mapy') or e.get('osm') or '')[:60]}")
        for cp, a in e.get("adresy", {}).items():
            print(f"{'':4}čp. {cp:6} {str(a.get('lat', '?')):>10} {str(a.get('lon', '?')):>10}  "
                  f"{a.get('zdroj', 'ručně' if a.get('rucne') else '')[:60]}")
    bez = [n for n, e in cache.items() if not bod(e)]
    for p in pozor:
        print(p)
    if bez:
        print("BEZ SOUŘADNIC:", ", ".join(bez), "– na mapě chybí")


if __name__ == "__main__":
    main()
