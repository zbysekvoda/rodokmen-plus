#!/usr/bin/env python3
"""Archivní VadeMeCum Národního archivu (vademecum.nacr.cz) bez prohlížeče – hlavně židovské matriky 1784–1949
(fondy HBMa a HBM), ale i jiné inventární záznamy se snímky.

Použití (z kořene projektu):
  vademecum.py hledat "text" [--stran N] [--jen-snimky]
        -> fulltext (např. „Dambořice“, „Hustopeče“, „FÚ Hodonín“); N stran po 12 záznamech (výchozí 3).
           Výpis: xid | druh | název | č. NAD | roky | popis | počet snímků
  vademecum.py info <xid|odkaz>
        -> údaje o záznamu (název, datace, obsah, rejstříková hesla = obce, které kniha pokrývá)
  vademecum.py snimek <xid|odkaz> <snímek> <vystup.jpg> [nahled]
        -> snímek v plném rozlišení (Zoomify); "nahled" = 1/4 rozlišení; snímek jde do sdílené cache
           (tools/cache.py), výřez zápisu pak udělá tools/vyrez.py
  vademecum.py link <xid|odkaz> <snímek>  -> trvalý odkaz na snímek (pole `odkaz` v zaznamy.json)
  vademecum.py svazek <xid|odkaz>         -> zapíše svazek do data/svazky.json (klíč nacvm_<xid>)
<xid> je identifikátor záznamu z prvního sloupce výpisu (nebo celý „Přímý odkaz na záznam“ z portálu).
<snímek> je pořadí od 1. Ber ohled na server: stahuj jen snímky, které čteš.
Židovské matriky nejsou po jménech indexované – hledá se podle obce (kniha je po židovských obcích a letech).
Pro studium matrik mladších než 100/75/30 let platí stejné lhůty jako u církevních matrik.

Převzato a upraveno z forku (licence MIT, © hnizdiljan):
  https://github.com/hnizdiljan/rodokmen-skill/blob/d172316bc190d0f44894fa67115505729d587c6a/skills/rodokmen/tools/vademecum.py
Rozdíly: síť jen přes slusne.py (žádné vlastní pauzy a opakování), snímky přes soal_zoomify.py a cache.py,
běží jen v projektu (data/STAV.md), svazek zachová ruční pole v svazky.json.
"""
import html, http.cookiejar, json, os, re, subprocess, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # noqa: E402 – společný limit rychlosti k webům archivů (slusne.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://vademecum.nacr.cz"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if not os.path.exists(os.path.join(ROOT, "data", "STAV.md")):   # spuštěno ze složky skillu: zápis by šel do skillu
    sys.exit(f"{os.path.basename(__file__)}: {ROOT} není složka projektu (chybí data/STAV.md). "
             f"Spusť projektovou kopii z kořene projektu: python3 -I tools/{os.path.basename(__file__)} …")
_op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
_op.addheaders = [("User-Agent", "Mozilla/5.0 (rodokmen-plus)")]


def get(url, data=None):
    """Stránka portálu. Rychlost a blokace hlídá slusne.py (429/503 = konec, žádné další pokusy)."""
    try:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data, doseq=True).encode() if data else None)
        with _op.open(req, timeout=90) as r:
            return r.read().decode("utf-8", "replace")
    except OSError as e:
        sys.exit(f"Portál neodpověděl ({type(e).__name__}: {str(e)[:100]}). Zkus to později nebo hledej v prohlížeči.")


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")).strip()


def xid_z(arg):
    m = re.search(r"xid=([0-9a-fA-F-]{16,})", arg) or re.fullmatch(r"([0-9a-fA-F-]{16,})", arg.strip())
    if not m:
        sys.exit("Zadej xid záznamu (první sloupec výpisu `hledat`) nebo celý „Přímý odkaz na záznam“.")
    return m.group(1)


def hledat(dotaz, stran, jen_snimky):
    home = get(BASE + "/vademecum/")
    f = re.search(r'<form method="post" action="([^"]+)" id="searchBar">(.*?)</form>', home, re.S)
    if not f:
        sys.exit("Portál změnil stránku (nenašel jsem hledací formulář). Hledej v prohlížeči.")
    data = dict(re.findall(r'name="(_sourcePage|__fp)" value="([^"]*)"', f.group(2)))
    sf = re.search(r'name="searchFrom" type="hidden" value="([^"]*)"', f.group(2))
    if not sf:
        sys.exit("Portál změnil stránku (v hledacím formuláři chybí pole searchFrom). Hledej v prohlížeči.")
    data.update({"patternFulltext": dotaz, "wordPosition0": "ANYWHERE", "wordOperator0": "AND",
                 "searchFrom": sf.group(1), "searchFulltext": "Search"})
    page = get(BASE + html.unescape(f.group(1)), data)
    celkem = re.search(r"([\d\s\xa0]+)&nbsp;záznamů|([\d\s\xa0]+)\s*záznamů", page)
    out, videno = [], set()
    for p in range(stran):
        for blok in re.findall(r"<art?icle class=\"contentRecordList.*?</art?icle>", page, re.S):   # portál má v HTML překlep „aricle“
            m = re.search(r"xid=([0-9a-f-]+)&amp;entityType=(\d+)", blok)
            if not m or m.group(1) in videno:
                continue
            videno.add(m.group(1))
            druh = text(re.search(r'class="database">(.*?)</span>', blok, re.S).group(1)) if "database" in blok else ""
            titul = re.search(r'<p class="title[^>]*>(.*?)</p>', blok, re.S)
            nad = re.search(r'<p class="cNAD">(.*?)</p>', blok, re.S)
            roky = re.search(r'<p class="years">(.*?)</p>', blok, re.S)
            popis = re.search(r'<p class="descr">(.*?)</p>', blok, re.S)
            sk = re.search(r"plné kvalitě (\d+) sken", blok)
            if jen_snimky and not sk:
                continue
            out.append((m.group(1), druh, text(titul.group(1)) if titul else "", text(nad.group(1)) if nad else "",
                        text(roky.group(1)) if roky else "", text(popis.group(1)) if popis else "", sk.group(1) if sk else "0"))
        nxt = re.search(r'<a href="(/vademecum/PaginatorResult\.action\?[^"]+)"><i class="icon-next', page)
        if not nxt or p == stran - 1:
            break
        page = get(BASE + html.unescape(nxt.group(1)))
    for r in out:
        print(" | ".join(r[:6]) + f" | {r[6]} snímků")
    if not out:
        print("Nic nenalezeno (zkus jiný tvar jména obce, bez „u“/okresu).", file=sys.stderr)
    elif celkem and len(out) < int(re.sub(r"\D", "", celkem.group(1) or celkem.group(2)) or 0):
        print(f"… celkem je víc záznamů než {len(out)}; zúžit jde dalším slovem nebo --stran", file=sys.stderr)


def zaznam(xid):
    return get(f"{BASE}/vademecum/permalink?xid={xid}")


def info(xid):
    page = zaznam(xid)
    t = text(re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S))
    i = t.find("Název pomůcky")
    if i < 0:
        i = t.find("Název")
    j = t.find("Výběr Související")
    print(t[i:j if j > i else i + 3000][:3500])
    sk = re.search(r"(\d+) skenů", t)
    print(f"Snímků: {sk.group(1) if sk else 0}")


def prohlizec(xid):
    """Stránka prohlížeče (Zoomify) pro záznam + odkaz na přepínání snímků."""
    page = zaznam(xid)
    z = re.search(r'href="(/vademecum/Zoomify\.action[^"]+)"', page)
    if not z:
        sys.exit("Záznam nemá digitalizované snímky.")
    zp = get(BASE + html.unescape(z.group(1)))
    pg = re.search(r'href="(/vademecum/PaginatorMedia\.action\?_sourcePage=[^"&]+)&amp;row=\d+"', zp)
    n = re.search(r'<span class="number">(\d+)</span>', zp)
    return zp, (html.unescape(pg.group(1)) if pg else None), int(n.group(1)) if n else 1


def snimek_stranka(xid, n):
    zp, pg, celkem = prohlizec(xid)
    if not 1 <= n <= celkem:
        sys.exit(f"Snímek musí být číslo 1–{celkem}.")
    if n > 1 and not pg:
        sys.exit("Portál změnil přepínání snímků (nenašel jsem odkaz na další snímky) – nástroj by stáhl špatný snímek. Stáhni ho v prohlížeči.")
    page = get(BASE + pg + f"&row={n - 1}") if n > 1 else zp
    cesta = re.search(r'zoomifyImgPath = "([^"]+)"', page)
    if not cesta:
        sys.exit("Cestu k obrázku se nepodařilo najít (portál změnil stránku?). Stáhni snímek v prohlížeči.")
    aktivni = re.search(r'<li class="active" id="scan([0-9a-f]+)"', page)
    return cesta.group(1), (aktivni.group(1) if aktivni else None), celkem


def cislo(s):
    if not (s.isascii() and s.isdigit()):
        sys.exit("Snímek musí být číslo.")
    return int(s)


def odkaz_snimku(xid, sken):
    return f"{BASE}/vademecum/permalink?xid={xid}" + (f"&scan={sken}&parentType=9019" if sken else "")


def link(xid, n):
    return odkaz_snimku(xid, snimek_stranka(xid, n)[1])


def snimek(xid, n, out, nahled=False):
    cesta, sken, _ = snimek_stranka(xid, n)
    cesta = urllib.parse.urljoin(BASE + "/", cesta)   # i kdyby portál dal cestu relativně
    if urllib.parse.urlsplit(cesta).hostname != "vademecum.nacr.cz":
        sys.exit(f"Neočekávaný server obrázků: {cesta[:80]}")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    zoom = [sys.executable, "-I", "-X", "utf8", os.path.join(HERE, "soal_zoomify.py"), cesta, "2" if nahled else "0", out]
    r = subprocess.run(zoom, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr.strip() or r.stdout.strip())
    print(out, "odkaz:", odkaz_snimku(xid, sken))


def svazek(xid):
    page = zaznam(xid)
    t = text(re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S))

    def pole(a, b):
        m = re.search(re.escape(a) + r":\s*(.*?)\s*(?=" + re.escape(b) + r":)", t)
        return m.group(1).strip() if m else ""
    fond, inv, dat, nazev, obsah = (pole("Název fondu", "Inv./přír. číslo"), pole("Inv./přír. číslo", "Datace"),
                                     pole("Datace", "Název"), pole("Název", "Obsah"), pole("Obsah", "Druh ukládací jednotky"))
    nazev = f"{fond}, inv. č. {inv}: {nazev}, {obsah}" + (f" ({dat})" if dat and dat not in obsah else "")
    m = re.search(r"Rejstříková hesla(.*?)(?:Výběr Související|$)", t)
    path = os.path.join(ROOT, "data", "svazky.json")
    d = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    d[f"nacvm_{xid[:8]}"] = {**d.get(f"nacvm_{xid[:8]}", {}),   # ruční pole zůstanou
                             "archiv": "Národní archiv – Archivní VadeMeCum", "portal": "vademecum.nacr.cz",
                             "svazek": nazev, "popis": (m.group(1).strip() if m else "")[:400],
                             "url": f"{BASE}/vademecum/permalink?xid={xid}"}
    tmp = path + ".tmp"   # zápis přes dočasný soubor: přerušení nesmí zkrátit svazky.json
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    print(f"nacvm_{xid[:8]} -> {nazev}")



if __name__ == "__main__":
    a = sys.argv[1:]
    stran, jen = 3, False
    if "--jen-snimky" in a:
        a.remove("--jen-snimky")
        jen = True
    if "--stran" in a:
        i = a.index("--stran")
        if i + 1 >= len(a) or not a[i + 1].isdigit() or int(a[i + 1]) < 1:
            sys.exit("--stran chce kladné číslo (kolik stran výsledků načíst).")
        stran = int(a[i + 1])
        del a[i:i + 2]
    if not a:
        sys.exit(__doc__)
    if a[0] == "hledat" and len(a) == 2:
        hledat(a[1], stran, jen)
    elif a[0] == "info" and len(a) == 2:
        info(xid_z(a[1]))
    elif a[0] == "snimek" and len(a) >= 4:
        rest = a[4:]
        snimek(xid_z(a[1]), cislo(a[2]), a[3], "nahled" in rest)
    elif a[0] == "link" and len(a) == 3:
        print(link(xid_z(a[1]), cislo(a[2])))
    elif a[0] == "svazek" and len(a) == 2:
        svazek(xid_z(a[1]))
    else:
        sys.exit(__doc__)
