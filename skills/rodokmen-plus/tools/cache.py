#!/usr/bin/env python3
"""Sdílená mezipaměť snímků z archivů – každý obrázek (snímek, dlaždice) se z archivu stáhne jen jednou.

Převzato a upraveno z:
  https://github.com/sarsonj/rodokmen-skill/blob/f0f833745d0456dd8644803e1c8708c3e9817f66/skills/rodokmen/tools/cache.py
  https://github.com/hackra76/rodokmen-skill/blob/532f7b0a2fed99b9003a23a600085659edb741d2/skills/rodokmen/tools/cache.py
  (kontrola integrity z verze 0.8.1, commit 59ba1e6)
Licence: MIT (původní © autoři forků sarsonj a hackra76; úpravy rodokmen-plus).

Nástroje archivů (aron_img, soal_zoomify, portafontium, mza, matricula_dl.sh) ukládají každý stažený obrázek podle
adresy; příště ho vezmou z disku bez dotazu na archiv. Z adresy se před uložením odstraní jen části, které obsah
nemění (;jsessionid=, PHPSESSID, utm_…, pojistky proti mezipaměti _=1793…; u Matriculy jednorázový csrf/ctrl).
Neznámé parametry zůstávají – raději stáhnout znovu, než vrátit cizí snímek.

Kontrola integrity: ukládá se jen úspěšná odpověď, která je opravdu celý obrázek (sedí délka ze serveru a soubor má
značku konce). Vedle obrázku leží <soubor>.sha256 s velikostí a hashem; při čtení se obojí ověří a poškozený či
zkrácený soubor se smaže a stáhne znovu.

Mezipaměť je společná pro všechny projekty na počítači: ~/.cache/rodokmen_snimky/ (Windows
%LOCALAPPDATA%\\rodokmen_snimky), jinou složku nastaví proměnná RODOKMEN_SNIMKY. Nejvýš 5 GB (RODOKMEN_SNIMKY_GB),
nejdéle nepoužité soubory se mažou samy. RODOKMEN_SNIMKY=0 mezipaměť vypne. Složku lze kdykoli smazat.

Použití:
  cache.py stav                                   -> kolik místa zabírá
  cache.py soubor <adresa> <vystup> -- <curl …>   -> obrázek z mezipaměti, jinak stáhne curlem přes slusne.py
                                                     (adresu a -o doplní samo) a uloží
Nástroje píšou na stderr „mezipaměť: N z disku, M staženo“.
"""
import atexit, hashlib, os, re, shutil, sys
from urllib.parse import parse_qsl, urlencode, urlsplit

KOREN = os.environ.get("RODOKMEN_SNIMKY") or os.path.join(
    os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".cache"), "rodokmen_snimky")
ZAPNUTO = KOREN != "0"
LIMIT = float(os.environ.get("RODOKMEN_SNIMKY_GB") or 5) * 1024 ** 3
PRIPONY = ((b"\xff\xd8\xff", ".jpg"), (b"\x89PNG\r\n\x1a\n", ".png"), (b"GIF8", ".gif"), (b"II*\x00", ".tif"),
           (b"MM\x00*", ".tif"), (b"\x00\x00\x00\x0cjP  ", ".jp2"), (b"\xffO\xffQ", ".j2k"))
JEDNORAZOVE = {"img.data.matricula-online.eu": {"csrf", "ctrl"}}   # podpis platný jen v jedné session prohlížeče
_pocty = {"disk": 0, "sit": 0}


def _souhrn():
    if _pocty["disk"] or _pocty["sit"]:
        print(f"mezipaměť: {_pocty['disk']} z disku, {_pocty['sit']} staženo ({KOREN})", file=sys.stderr)


atexit.register(_souhrn)


def pripona(data):
    """Přípona podle prvních bajtů; None = není obrázek (chybová stránka, „zablokováno“ …)."""
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return next((p for z, p in PRIPONY if data.startswith(z)), None)


def cely(data, delka=None):
    """Úplný obrázek: sedí délka ze serveru (Content-Length), je-li, a má značku konce."""
    if delka is not None and len(data) != delka:
        return False
    p = pripona(data)
    konec = data[-1024:]
    if p in (".jpg", ".jp2", ".j2k"):
        return b"\xff\xd9" in konec
    if p == ".png":
        return b"IEND" in konec[-64:]
    if p == ".gif":
        return konec.rstrip(b"\x00")[-1:] == b";"
    if p == ".webp":
        return int.from_bytes(data[4:8], "little") + 8 <= len(data)
    return p is not None   # TIFF konec nemá – ohlídá ho délka a hash


def klic_url(url):
    """Klíč podle adresy bez částí, které obsah nemění. Neznámé parametry zůstávají."""
    u = urlsplit(url)
    host = (u.hostname or "").lower()
    path = re.sub(r";jsessionid=[^/?#;]*", "", u.path, flags=re.I)
    q = []
    for k, v in parse_qsl(u.query, keep_blank_values=True):
        kl = k.lower()
        if kl in ("jsessionid", "phpsessid") or kl.startswith("utm_") or kl in JEDNORAZOVE.get(host, ()):
            continue
        if (kl == "_" and v.isdigit()) or (not v and re.fullmatch(r"\d{10,}", k)):
            continue
        q.append((k, v))
    port = f":{u.port}" if u.port and u.port not in (80, 443) else ""
    h = hashlib.sha1(f"{host}{port}{path}?{urlencode(sorted(q))}".encode()).hexdigest()
    return os.path.join(KOREN, "web", host or "_", h[:2], h)


def _smaz(*cesty):
    for p in cesty:
        try:
            os.remove(p)
        except OSError:
            pass


def _overeny(p):
    """Soubor sedí s velikostí a hashem z <p>.sha256 a je celý obrázek; jinak se smaže."""
    try:
        with open(p + ".sha256", encoding="ascii") as f:
            velikost, h = f.read().split()
        with open(p, "rb") as f:
            data = f.read()
        if len(data) == int(velikost) and hashlib.sha256(data).hexdigest() == h and cely(data):
            os.utime(p)   # naposledy použité – úklid maže nejdéle nepoužité
            return data
    except (OSError, ValueError):
        pass
    print(f"mezipaměť: poškozený soubor {p} smazán, stáhne se znovu", file=sys.stderr)
    _smaz(p, p + ".sha256")
    return None


def najdi(url):
    """(cesta, data) uloženého obrázku pro adresu, nebo None."""
    if not ZAPNUTO:
        return None
    k = klic_url(url)
    for p in {pp for _, pp in PRIPONY} | {".webp"}:
        if os.path.exists(k + p):
            data = _overeny(k + p)
            return (k + p, data) if data is not None else None
    return None


def uloz(url, data, delka=None):
    """Uloží obrázek (jen skutečný a úplný). Vrací cestu, nebo None."""
    p = pripona(data)
    if not ZAPNUTO or not p or not cely(data, delka):
        return None
    cil = klic_url(url) + p
    os.makedirs(os.path.dirname(cil), exist_ok=True)
    tmp = f"{cil}.tmp.{os.getpid()}"
    try:
        with open(tmp, "wb") as f:
            f.write(data)
        with open(tmp + ".h", "w", encoding="ascii") as f:
            f.write(f"{len(data)} {hashlib.sha256(data).hexdigest()}\n")
        os.replace(tmp, cil)
        os.replace(tmp + ".h", cil + ".sha256")
    except OSError:
        _smaz(tmp, tmp + ".h")
        return None
    if sum(_pocty.values()) % 50 == 0:
        uklid()
    return cil


def ziskej(url, stahni):
    """Obrázek pro adresu: z mezipaměti, jinak stahni(url) -> bytes (uloží se, je-li to celý obrázek)."""
    hit = najdi(url)
    if hit:
        _pocty["disk"] += 1
        return hit[1]
    data = stahni(url)
    if isinstance(data, (bytes, bytearray)) and uloz(url, bytes(data)):
        _pocty["sit"] += 1
    return data


def do_souboru(url, out, stahni_do):
    """Totéž pro nástroje, které stahují rovnou do souboru (curl): stahni_do(out) -> True/False."""
    hit = najdi(url)
    if hit:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        shutil.copyfile(hit[0], out)
        _pocty["disk"] += 1
        return True
    if not stahni_do(out):
        return False
    try:
        with open(out, "rb") as f:
            if uloz(url, f.read()):
                _pocty["sit"] += 1
    except OSError:
        pass
    return True


def uklid():
    """Nad limitem smaže nejdéle nepoužité obrázky (i s jejich .sha256)."""
    polozky = []
    for d, _, fs in os.walk(KOREN):
        for f in fs:
            if f.endswith(".sha256"):
                continue
            p = os.path.join(d, f)
            try:
                st = os.stat(p)
                polozky.append((st.st_mtime, st.st_size, p))
            except OSError:
                pass
    polozky.sort()
    celkem = sum(s for _, s, _ in polozky)
    while celkem > LIMIT and polozky:
        _, s, p = polozky.pop(0)
        _smaz(p, p + ".sha256")
        celkem -= s


def main(a):
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")
    if a[:1] == ["stav"]:
        n = s = 0
        for d, _, fs in os.walk(KOREN):
            for f in fs:
                if not f.endswith(".sha256"):
                    n += 1
                    s += os.path.getsize(os.path.join(d, f))
        print(f"{KOREN}: {n} obrázků, {s / 1024 ** 2:.0f} MB z {LIMIT / 1024 ** 3:g} GB")
    elif a[:1] == ["soubor"] and len(a) >= 4 and a[3] == "--":
        url, out, args = a[1], a[2], a[4:]
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import slusne

        def stahni_do(cil):
            os.makedirs(os.path.dirname(os.path.abspath(cil)) or ".", exist_ok=True)
            p = slusne.curl([*args, url, "-o", cil])
            sys.stderr.write(p.stderr or "")
            return p.returncode == 0 and os.path.exists(cil)
        try:
            ok = do_souboru(url, out, stahni_do)
        except slusne.Zablokovano as e:
            print(e, file=sys.stderr)
            sys.exit(22)
        sys.exit(0 if ok else 1)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
