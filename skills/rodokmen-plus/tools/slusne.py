#!/usr/bin/env python3
"""Slušný přístup k webům archivů: společný limit rychlosti a zastavení, když server dá najevo, že ho zatěžujeme.

Archivy (MZA Brno, SOA Litoměřice, ZA Opava…) banují IP adresu po sérii rychlých dotazů. Ban dopadne na uživatele
a archivy pak přitvrzují vůči všem. Proto:
- limit platí pro každý web zvlášť a je SPOLEČNÝ všem procesům (pomocníci/subagenti, dva nástroje najednou),
- dotazy (hledání, API, HTML) přísně – výchozí 1 za 2 s; obrázky a dlaždice volněji – 20 za s
  (ban způsobují rychlé dotazy, ne dlaždice jednoho snímku),
- weby, které skripty zakázaly (ZAKAZ_SKRIPTU: SOA Třeboň a eBadatelna SOA Praha od 2. 11. 2026), se vůbec
  nedotazují – nástroj hned skončí hláškou, co dělat ručně v prohlížeči,
- po HTTP 429 nebo 503 (a po 403 na dotaz uprostřed práce) se web zablokuje na 30 minut pro všechny procesy a nástroj hned skončí –
  žádné další pokusy; chce-li server v Retry-After (sekundy i datum HTTP) delší pauzu, trvá blokace tak dlouho,
- když server hlásí, že dotazy docházejí (RateLimit-Remaining / X-RateLimit-Remaining 0–1, i tvar `RateLimit: r=0;t=30`),
  nebo pošle Retry-After u běžné odpovědi, další požadavek na web počká na obnovení (nejvýš hodinu), pro všechny procesy.

Nástroje v tools/ to mají zapnuté samy (`slusne.instaluj()` na začátku). Vlastní skript nebo curl spouštěj takhle:
  python3 -I tools/slusne.py pracovni/muj_skript.py [argumenty]   -> skript běží se stejným limitem (urllib, requests)
  python3 -I tools/slusne.py curl [argumenty curl]                -> curl se stejným limitem
  python3 -I tools/slusne.py stav                                 -> které weby jsou teď zablokované a do kdy
  python3 -I tools/slusne.py zablokuj <web> [důvod]               -> zablokovat web na 30 min (429/503/403 v prohlížeči)
  python3 -I tools/slusne.py odblokuj <web>                       -> zrušit blokaci (jen když víš, že šlo o omyl)
Stav je ve ~/.cache/dejiny-domu/slusne/ (jinde: proměnná SLUSNE_DIR).
"""
import http.client, json, os, re, subprocess, sys, threading, time, urllib.parse
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

# (s mezi dotazy, s mezi obrázky). Weby, které banují, přísně; velké státní služby volněji.
VYCHOZI = (2.0, 0.05)
LIMITY = {
    "ags.cuzk.gov.cz": (0.5, 0.05), "ags.cuzk.cz": (0.5, 0.05),   # ArcGIS ČÚZK – mapy jsou dotazy na export
    "kramerius5.nkp.cz": (1.0, 0.05), "anno.onb.ac.at": (1.0, 0.05),
    "nominatim.openstreetmap.org": (1.1, 1.1),                       # pravidla OSM: nejvýš 1 dotaz za s
    "gs-pub.praha.eu": (0.5, 0.05),
    # Slovakiana (SNA): robots.txt „Crawl-delay: 10“ – platí pro web, API wcm.… i snímky content.… (podle jozefizso 0.10.0)
    "slovakiana.sk": (10.0, 10.0), "wcm.slovakiana.sk": (10.0, 10.0), "content.slovakiana.sk": (10.0, 10.0),
}
BLOKACE = 30 * 60
# Weby, které skripty zakázaly (HTTP 403 pro všechno kromě prohlížeče). Požadavek se vůbec neodešle – žádné obcházení
# (User-Agent, cookies z prohlížeče, proxy). host → (název, od kdy, co dělat ručně v prohlížeči)
ZAKAZ_SKRIPTU = {
    "digi.ceskearchivy.cz": ("SOA Třeboň (digi.ceskearchivy.cz)", "2. 11. 2026",
                             "otevři https://digi.ceskearchivy.cz v prohlížeči, svazek najdi přes hledání místa "
                             "a snímek si ulož nebo opiš trvalý odkaz https://digi.ceskearchivy.cz/<id_knihy>/<snímek>"),
    "ebadatelna.soapraha.cz": ("SOA Praha – eBadatelna (ebadatelna.soapraha.cz)", "2. 11. 2026",
                               "otevři https://ebadatelna.soapraha.cz v prohlížeči, matriku najdi přes lokalitu "
                               "a snímek si ulož nebo opiš trvalý odkaz https://ebadatelna.soapraha.cz/d/<matrikaId>/<snímek>"),
}
OBRAZEK = re.compile(r"\.(jpe?g|png|gif|webp|tiff?|jp2|dzi)(\?|$)|_files/|iipsrv|IIIF=|Deepzoom=|ximage|zoomify|"
                     r"TileGroup|ImageProperties\.xml|isrv\d*\.cgi|/full/|default\.jpg|/image/|mrimage|/tiles?/", re.I)


class Zablokovano(SystemExit):   # SystemExit: nástroje chytají OSError/Exception – tohle jim neproklouzne do opakování
    pass


class ZakazSkriptu(Zablokovano):
    pass


def zakaz_skriptu(host):
    """Hláška pro web, který skripty zakázal, jinak None."""
    z = ZAKAZ_SKRIPTU.get((host or "").lower())
    if not z:
        return None
    nazev, od, rucne = z
    return (f"STOP: {nazev} od {od} odmítá skripty (HTTP 403) – požadavek se neodeslal. Portál NEOBCHÁZEJ "
            f"(jiný User-Agent, cookies z prohlížeče, proxy, jiný nástroj). Ručně: {rucne}. "
            f"Řekni to uživateli a pokračuj jiným pramenem.")


def adresar():
    d = os.environ.get("SLUSNE_DIR") or os.path.join(os.path.expanduser("~"), ".cache", "dejiny-domu", "slusne")
    os.makedirs(d, exist_ok=True)
    return d


def _soubor(host, co):
    return os.path.join(adresar(), re.sub(r"[^a-z0-9.-]", "_", host.lower()) + "." + co)


def _zamkni(f):
    if os.name == "nt":
        import msvcrt
        f.seek(0)
        while True:
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                return
            except OSError:   # LK_LOCK to zkouší jen 10 s
                pass
    else:
        import fcntl
        fcntl.flock(f, fcntl.LOCK_EX)


def _odemkni(f):
    if os.name == "nt":
        import msvcrt
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(f, fcntl.LOCK_UN)


def host_z(arg):
    """„https://www.mza.cz/x“ i „www.mza.cz“ → „www.mza.cz“."""
    return (urllib.parse.urlsplit(arg).hostname if "://" in arg else arg).lower()


def druh(url):
    return "obr" if OBRAZEK.search(url) else "dotaz"


def blokace(host):
    """(do kdy, proč) nebo None."""
    try:
        with open(_soubor(host, "blok"), encoding="utf-8") as f:
            b = json.load(f)
    except (OSError, ValueError):
        return None
    if b.get("do", 0) <= time.time():
        return None
    return b["do"], b.get("proc", "")


def zablokuj(host, proc, sekund=BLOKACE):
    with open(_soubor(host, "blok"), "w", encoding="utf-8") as f:
        json.dump({"do": time.time() + sekund, "proc": proc}, f, ensure_ascii=False)


def _hlaska(host, do, proc):
    zbyva = max(1, round((do - time.time()) / 60))
    return (f"STOP: web {host} je zablokovaný ještě {zbyva} min ({proc}). Server dal najevo, že ho zatěžujeme – "
            f"NEZKOUŠEJ to znovu ani jinou cestou (jiný nástroj, curl, prohlížeč). Pokračuj jiným pramenem "
            f"a k tomuhle se vrať po {time.strftime('%H:%M', time.localtime(do))}. Řekni to uživateli.")


# Retry-After a RateLimit-* převzato z jozefizso/rodokmen-skill (MIT), upraveno:
# https://github.com/jozefizso/rodokmen-skill/blob/38850a5aa4dbebe3faf1eb6ed5c5e8c9007c2d68/skills/rodokmen/tools/slusne.py
def sekundy(hodnota, ted=None):
    """Retry-After / RateLimit-Reset na sekundy od teď: počet sekund, čas v epoše nebo datum HTTP. Nejde → 0."""
    hodnota = str(hodnota or "").strip()
    ted = ted or time.time()
    if re.fullmatch(r"\d+(\.\d+)?", hodnota):
        n = float(hodnota)
        return max(0.0, n - ted) if n > 1e9 else n   # velké číslo = okamžik (epocha), malé = počet sekund
    try:
        from email.utils import parsedate_to_datetime
        return max(0.0, parsedate_to_datetime(hodnota).timestamp() - ted)
    except (TypeError, ValueError, IndexError, OverflowError):
        return 0.0


def zpomal(host, sekund):
    """Server chce pauzu: další dotaz i obrázek na web nejdřív za `sekund` (nejvýš hodinu), pro všechny procesy."""
    host = (host or "").lower()
    if not host or sekund <= 0:
        return
    do = time.time() + min(sekund, 3600)
    for co in ("dotaz", "obr"):
        with open(_soubor(host, co), "a+", encoding="utf-8") as f:
            _zamkni(f)
            try:
                f.seek(0)
                try:
                    posledni = float(f.read().strip() or 0)
                except ValueError:
                    posledni = 0.0
                if do > posledni:   # rezervace slotu: pockej() přičte rozestup, takže čeká aspoň do `do`
                    f.seek(0)
                    f.truncate()
                    f.write(repr(do))
                    f.flush()
            finally:
                _odemkni(f)


def hlavicky_limitu(host, hlavicka):
    """RateLimit-* (IETF návrh) a X-RateLimit-*: zbývá 0–1 dotaz → počkat na obnovení. Retry-After u běžné odpovědi → počkat.
    hlavicka: funkce jméno → hodnota nebo None."""
    pauza = sekundy(hlavicka("Retry-After"))
    zbyva = hlavicka("RateLimit-Remaining") or hlavicka("X-RateLimit-Remaining")
    if not zbyva:
        m = re.search(r"\br=(\d+)", hlavicka("RateLimit") or "")   # novější tvar: RateLimit: "default";r=0;t=30
        zbyva = m and m.group(1)
    if zbyva and str(zbyva).strip().isdigit() and int(zbyva) <= 1:
        reset = hlavicka("RateLimit-Reset") or hlavicka("X-RateLimit-Reset")
        if not reset:
            m = re.search(r"\bt=(\d+)", hlavicka("RateLimit") or "")
            reset = m and m.group(1)
        pauza = max(pauza, sekundy(reset) or 60)
    zpomal(host, pauza)


class Fronta(SystemExit):
    pass


def _zkontroluj_blokaci(host):
    z = zakaz_skriptu(host)
    if z:
        raise ZakazSkriptu(z)
    b = blokace(host)
    if b:
        raise Zablokovano(_hlaska(host, *b))


def pockej(host, co, nejdele=None):
    """Počká, až je na webu volno (společně pro všechny procesy). Zablokovaný web → Zablokovano.
    nejdele: kolik s nejvýš čekat (hook má časový limit) – jinak Fronta a termín se nezabere."""
    host = (host or "").lower()
    _zkontroluj_blokaci(host)
    rozestup = LIMITY.get(host, VYCHOZI)[0 if co == "dotaz" else 1]
    with open(_soubor(host, co), "a+", encoding="utf-8") as f:
        _zamkni(f)
        try:
            f.seek(0)
            try:
                posledni = float(f.read().strip() or 0)
            except ValueError:
                posledni = 0.0
            ted = time.time()
            slot = max(ted, posledni + rozestup)   # rezervace termínu – další proces dostane až ten po něm
            if nejdele is not None and slot - ted > nejdele:
                raise Fronta(f"{host}: na web čeká fronta dotazů ({slot - ted:.0f} s) – zkus to za chvíli")
            f.seek(0)
            f.truncate()
            f.write(repr(slot))
            f.flush()
        finally:
            _odemkni(f)
    if slot > ted:
        time.sleep(slot - ted)
        _zkontroluj_blokaci(host)   # mezitím mohl jiný proces dostat 429


def _byl_uspech(host):
    """Odpověděl web v posledních 30 min v pořádku (kterémukoli procesu)? Pak 403 není špatný User-Agent, ale zátěž."""
    try:
        return time.time() - os.path.getmtime(_soubor(host, "ok")) < BLOKACE
    except OSError:
        return False


def posoudit(host, co, kod, retry_after=None):
    """Po odpovědi: 429/503 (a 403 na dotaz) → zablokovat web a skončit.
    403 hned na první dotaz bývá špatný User-Agent nebo neveřejná stránka, ne zátěž – skončí bez blokace."""
    host = host.lower()
    if kod == 403 and zakaz_skriptu(host):   # sem se běžně nedojde (pockej neodešle), ale 403 nikdy neopakovat
        raise ZakazSkriptu(zakaz_skriptu(host))
    if kod < 400:
        with open(_soubor(host, "ok"), "w"):
            pass
        return
    if kod == 403 and co == "dotaz" and not _byl_uspech(host):
        raise SystemExit(f"{host} odmítl dotaz (HTTP 403) – buď chybí prohlížečový User-Agent / stránka není veřejná, "
                         "nebo web zablokoval IP adresu (v prohlížeči „Sorry, you have been blocked“ → vypni VPN nebo "
                         "zkus jinou síť). Neopakuj dotaz ve smyčce.")
    if kod in (429, 503) or (kod == 403 and co == "dotaz"):
        sekund = max(BLOKACE, sekundy(retry_after))
        proc = f"HTTP {kod}" + (f", Retry-After {retry_after}" if retry_after else "")
        zablokuj(host, proc, sekund)
        raise Zablokovano(_hlaska(host, time.time() + sekund, proc))


def po_odpovedi(host, co, kod, hlavicka):
    """Společně pro http.client i curl: posoudit kód (s Retry-After) a pak hlášení o docházejících dotazech.
    hlavicka: funkce jméno → hodnota nebo None."""
    posoudit(host, co, kod, hlavicka("Retry-After"))
    hlavicky_limitu(host, hlavicka)


_lokalni = threading.local()
_instalovano = False


def instaluj():
    """Zapne limit pro všechno, co v procesu jde přes http.client (urllib, requests, http.client)."""
    global _instalovano
    if _instalovano:
        return
    _instalovano = True
    put, get = http.client.HTTPConnection.putrequest, http.client.HTTPConnection.getresponse

    def putrequest(self, method, url, *a, **k):
        co = druh(url)
        pockej(self.host, co)
        _lokalni.posledni = (self.host, co)
        return put(self, method, url, *a, **k)

    def getresponse(self, *a, **k):
        r = get(self, *a, **k)
        host, co = getattr(_lokalni, "posledni", (self.host, "dotaz"))
        po_odpovedi(host, co, r.status, r.getheader)
        return r

    http.client.HTTPConnection.putrequest = putrequest
    http.client.HTTPConnection.getresponse = getresponse


HODNOTOVE = {"-e", "--referer", "-x", "--proxy", "-H", "--header", "-b", "--cookie", "-A", "--user-agent",
             "-u", "--user", "-d", "--data", "--data-urlencode", "-F", "--form"}   # volby curl, jejichž hodnota může být adresa


def hlavicky_ze_souboru(cesta):
    """Hlavičky poslední odpovědi ze souboru curl -D (při -L je v něm víc odpovědí za sebou) → funkce jméno → hodnota."""
    try:
        with open(cesta, encoding="latin-1") as f:
            radky = f.read().splitlines()
    except OSError:
        radky = []
    hlavicky = {}
    for radek in radky:
        if radek.startswith("HTTP/"):   # začátek další odpovědi – platí jen hlavičky té poslední
            hlavicky = {}
        elif ":" in radek:
            k, v = radek.split(":", 1)
            hlavicky[k.strip().lower()] = v.strip()
    return lambda jmeno: hlavicky.get(jmeno.lower())


def curl(args, **kw):
    """Spustí curl s limitem: počká podle první adresy, po odpovědi posoudí kód a hlavičky (Retry-After, RateLimit-*).
    Vrací CompletedProcess (stderr jako text)."""
    urls = [a for i, a in enumerate(args) if re.match(r"https?://", a) and (i == 0 or args[i - 1] not in HODNOTOVE)]
    host = urllib.parse.urlsplit(urls[0]).hostname if urls else ""
    co = druh(urls[0]) if urls else "dotaz"
    if host:
        pockej(host, co)
    kw.setdefault("stderr", subprocess.PIPE)
    kw.setdefault("text", True)
    kw.setdefault("encoding", "utf-8")
    kw.setdefault("errors", "replace")
    args, znacka = list(args), "%{stderr}\nSLUSNE %{http_code}\n"
    for i, x in enumerate(args[:-1]):
        if x in ("-w", "--write-out"):   # vlastní -w nechat, značku připojit za něj (curl bere jen poslední -w)
            args[i + 1] += znacka
            break
    else:
        args += ["-w", znacka]
    # Hlavičky odpovědi: vlastní -D <soubor> přečíst, jinak přidat svůj dočasný. „-D -“ (na stdout) nechat být –
    # druhé -D by ho přebilo; pak se posoudí jen kód.
    soubor_hlavicek, docasny = None, False
    for i, x in enumerate(args[:-1]):
        if x in ("-D", "--dump-header"):
            soubor_hlavicek = None if args[i + 1] == "-" else args[i + 1]
            break
    else:
        import tempfile
        fd, soubor_hlavicek = tempfile.mkstemp(prefix="slusne_hlavicky_")
        os.close(fd)
        docasny = True
        args += ["-D", soubor_hlavicek]
    try:
        p = subprocess.run(["curl", *args], **kw)
        hlavicka = hlavicky_ze_souboru(soubor_hlavicek) if soubor_hlavicek else (lambda jmeno: None)
    finally:
        if docasny:
            try:
                os.remove(soubor_hlavicek)
            except OSError:
                pass
    kody = re.findall(r"SLUSNE (\d+)", p.stderr or "")
    p.stderr = re.sub(r"\n?SLUSNE \d+\n", "", p.stderr or "")
    if host and kody:
        po_odpovedi(host, co, int(kody[-1]), hlavicka)
    return p


def main(a):
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    if a[0] == "stav":
        nic = True
        for fn in sorted(os.listdir(adresar())):
            if fn.endswith(".blok"):
                b = blokace(fn[:-5])
                if b:
                    nic = False
                    print(f"{fn[:-5]}: zablokováno do {time.strftime('%H:%M', time.localtime(b[0]))} ({b[1]})")
        if nic:
            print("Žádný web není zablokovaný.")
    elif a[0] == "zablokuj" and len(a) > 1:
        host = host_z(a[1])
        zablokuj(host, " ".join(a[2:]) or "ručně")
        print(f"{host}: zablokováno na {BLOKACE // 60} min")
    elif a[0] == "odblokuj" and len(a) > 1:
        host = host_z(a[1])
        p = _soubor(host, "blok")
        if os.path.exists(p):
            os.remove(p)
        print(f"{host}: odblokováno")
    elif a[0] == "curl":
        try:
            p = curl(a[1:])
        except Zablokovano as e:
            print(e, file=sys.stderr)
            sys.exit(22)
        sys.stderr.write(p.stderr)
        sys.exit(p.returncode)
    else:
        import runpy
        sys.modules.setdefault("slusne", sys.modules[__name__])   # `import slusne` ve skriptu = tenhle modul, ne druhá kopie
        instaluj()
        sys.argv = a
        sys.path.insert(0, os.path.dirname(os.path.abspath(a[0])))
        runpy.run_path(a[0], run_name="__main__")


if __name__ == "__main__":
    main(sys.argv[1:])
