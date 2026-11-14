#!/usr/bin/env python3
"""Snímek matriky ve formátu Zoomify (SOA Litoměřice, VadeMeCum NA) v plném rozlišení – bez prohlížeče a bez cookies.

ZA Opava (images.archives.cz) od listopadu 2026 nástroje nepouští (robots.txt, obrázky HTTP 403/404) – snímky
odtud ukládej z prohlížeče snímků (reference/portaly.md, ZA Opava; nejlépe Playwright).

Použití (z kořene projektu):
  soal_zoomify.py <cesta nebo adresa> <zmenseni> <vystup.jpg>
    cesta     = SOA Litoměřice: část adresy obrázku za „…/CZ-214000010/matriky/“ (konec typicky „….jpg“), vezmi ji jednou
                z prohlížeče: v digitální badatelně otevři snímek a v síťovém provozu najdi požadavek na
                https://images.soalitomerice.cz/ximage/matriky/zoomify/cz/archives/CZ-214000010/matriky/<cesta>/ImageProperties.xml
                (další snímky téže knihy mají stejnou cestu, liší se jen číslem obrázku)
    adresa    = celá adresa obrázku začínající https:// (s „/ImageProperties.xml“ na konci i bez), např.
                https://images.soalitomerice.cz/ximage/matriky/zoomify/cz/archives/CZ-214000010/NAD-<číslo>/dao/images/<složka>/<uuid>.jpg
    zmenseni  = 0 plné rozlišení (na čtení a výřez), 1 poloviční (na orientaci), 2 čtvrtinové
POZOR: aplikace digi.soalitomerice.cz po ~100 rychlých požadavcích zablokuje přístup na 30 minut. Prohlížečem jen
najdi knihu a cestu k obrázkům, snímky pak stahuj tímto nástrojem po jednom.
"""
import glob, math, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.parse, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti k webům archivů (slusne.py)
import cache   # sdílená mezipaměť snímků (cache.py) – stejný snímek se stáhne jen jednou

BASE = "https://images.soalitomerice.cz/ximage/matriky/zoomify/cz/archives/CZ-214000010/matriky/"
HOSTS = ("images.soalitomerice.cz", "vademecum.nacr.cz")   # jen obrázkové servery archivů (snímky zpracovává ImageMagick); ZA Opava ne (výše)


def magick():
    """Cesta k ImageMagicku; když chybí, skončí hned (před stahováním) srozumitelnou hláškou."""
    m = (shutil.which("magick") or next(iter(sorted(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe"))), None)
         or (os.name != "nt" and shutil.which("convert")))   # ImageMagick 6 bez magick; na Windows je convert.exe jiný program
    if not m:
        sys.exit("Chybí ImageMagick (příkaz magick). Nainstaluj ho (macOS: brew install imagemagick, "
                 "Windows: winget install ImageMagick.ImageMagick a restart Claude Code) a spusť nástroj znovu.")
    return m


def get(url):
    err = None
    for _ in range(3):
        try:
            return urllib.request.urlopen(url, timeout=30).read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 503):   # archiv odmítá – nezkoušet znovu, web v brzdě zastavit (i u obrázků)
                host = urllib.parse.urlsplit(url).hostname
                slusne.zablokuj(host, f"HTTP {e.code} u snímku")
                sys.exit(f"Archiv odmítl snímek (HTTP {e.code}) – web {host} je v brzdě zastavený. Dnes s ním přestaň "
                         "a zkus to jindy; snímky, které teď potřebuješ, ať uloží uživatel v prohlížeči.")
            if e.code == 404:   # neopakovat: špatná cesta, nebo archiv nástroj odmítá (prohlížeč ten snímek načte)
                sys.exit(f"Snímek nenalezen (HTTP 404): {url[:160]}\nZkontroluj, že je to celá adresa obrázku z prohlížeče "
                         "(cesty se mění, i přípona .JPG). Když ji prohlížeč načte a nástroj ne, archiv nástroj odmítá – "
                         "skonči a snímek ulož z prohlížeče (reference/portaly.md).")
            time.sleep(1)
            err = e
        except Exception as e:
            time.sleep(1)
            err = e
    raise err


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    arg = sys.argv[1].strip().removesuffix("/ImageProperties.xml").strip("/")
    base = arg if arg.startswith("http") else BASE + arg
    if urllib.parse.urlsplit(base).hostname in ("images.archives.cz", "digi.archives.cz"):
        sys.exit("ZA Opava od listopadu 2026 nástroje nepouští (robots.txt, obrázky HTTP 403/404). Snímek ulož "
                 "z prohlížeče snímků – Playwright složí dlaždice, které prohlížeč načetl (reference/portaly.md, ZA Opava).")
    if urllib.parse.urlsplit(base).scheme != "https" or urllib.parse.urlsplit(base).hostname not in HOSTS:
        sys.exit(f"Adresa musí být https:// na serveru archivu ({', '.join(HOSTS)}), ne {base[:80]}")
    red, out = int(sys.argv[2]), sys.argv[3]
    MAGICK = magick()
    x = get(base + "/ImageProperties.xml").decode()
    W, H, T = (int(re.search(fr'{k}="(\d+)"', x).group(1)) for k in ("WIDTH", "HEIGHT", "TILESIZE"))
    dims, w, h = [], W, H   # úrovně Zoomify od nejmenší po plné rozlišení
    while True:
        dims.append((w, h))
        if w <= T and h <= T:
            break
        w, h = (w + 1) // 2, (h + 1) // 2
    dims = dims[::-1]
    counts = [math.ceil(a / T) * math.ceil(b / T) for a, b in dims]
    L = len(dims) - 1 - red
    w, h = dims[L]
    nx, ny = math.ceil(w / T), math.ceil(h / T)
    start = sum(counts[:L])
    d = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(out)))
    try:   # dočasnou složku uklidit i při výpadku sítě nebo chybě ImageMagicku
        def tile(yx):
            y, xx = yx
            g = (start + y * nx + xx) // 256
            f = os.path.join(d, f"{y:03d}_{xx:03d}.jpg")
            with open(f, "wb") as fh:
                fh.write(cache.ziskej(f"{base}/TileGroup{g}/{L}-{xx}-{y}.jpg", get))
        for yx in [(y, xx) for y in range(ny) for xx in range(nx)]:   # sekvenčně: v sandboxu vlákna padají, archiv nedostane souběh
            tile(yx)
        # řádky dlaždic +append, pak řádky pod sebe -append (montage na ImageMagicku 7.1.2 padá bez písma);
        # krátká jména (cwd=d) a po řádcích: celá stránka v jednom příkazu by na Windows přesáhla limit příkazové řádky
        rows = []
        for y in range(ny):
            rows.append(f"row{y:03d}.miff")   # MIFF zachová vlastnosti JPEG (podvzorkování barev)
            subprocess.run([MAGICK, *[f"{y:03d}_{xx:03d}.jpg" for xx in range(nx)], "+append", rows[-1]], check=True, cwd=d)
        subprocess.run([MAGICK, *rows, "-append", "-crop", f"{w}x{h}+0+0", "+repage", "-quality", "88",
                        os.path.abspath(out)], check=True, cwd=d)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print(out, w, h)


if __name__ == "__main__":
    main()
