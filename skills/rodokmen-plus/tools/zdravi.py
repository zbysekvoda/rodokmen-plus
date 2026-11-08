#!/usr/bin/env python3
"""Kontrola portálů: funguje každý nástroj ještě proti živému portálu?

Archivy mění adresy a API bez ohlášení. Nástroj spustí každý nástroj na pevném, známém svazku (čtení + jeden malý
snímek) v dočasné složce – do dat projektu nesahá – a vypíše, co funguje a co ne.

Použití (z kořene projektu i ze složky skillu):
  zdravi.py                 všechny kontroly (~30 požadavků, asi minuta)
  zdravi.py --rychle        bez stahování snímků
  zdravi.py --jen trebon,aron
                            jen vybrané portály (názvy viz výpis)
Návratový kód 1 = aspoň jedna kontrola selhala. Selže-li portál, zkus to za chvíli znovu (výpadky bývají krátké);
trvá-li chyba, změnilo se API – oprav nástroj a zapiš to do poznamky_pro_skill.md.
"""
import os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.request
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti k webům archivů (slusne.py)

TOOLS = os.path.dirname(os.path.abspath(__file__))
PY = [sys.executable, "-I", "-X", "utf8"]

# (portál, popis, příkaz, regex ve výstupu, výstupní obrázek nebo None)
# Pevná id: když portál svazek přečísluje, kontrola selže – to je taky zpráva (odkazy v datech projektů přestanou platit).
KONTROLY = [
    ("trebon", "hledání místa", ["trebon.py", "misto", "Chyšky"], r"407376 \| Chyšky", None),
    ("trebon", "svazky místa", ["trebon.py", "svazky", "407376"], r"^4250 \|", None),
    ("trebon", "snímek", ["trebon.py", "snimek", "4250", "5", "{out}", "nahled"], r"digi\.ceskearchivy\.cz/4250/5", "tr.jpg"),
    ("aron", "hledání svazků", ["aron_search.py", "Holice", "", "500"], r"0dfa5da8-0b8f-49f4-bc13-c2ea70fd100c", None),
    ("aron", "info svazku", ["aron_img.py", "0dfa5da8-0b8f-49f4-bc13-c2ea70fd100c", "info"], r"scans: [1-9]", None),
    ("aron", "snímek", ["aron_img.py", "0dfa5da8-0b8f-49f4-bc13-c2ea70fd100c", "3", "2", "{out}"], r"full size", "ar.jpg"),
    ("portafontium", "knihy fary", ["portafontium.py", "fara", "dolni-bela"], r"^dolni-bela-17 \|", None),
    ("portafontium", "snímek", ["portafontium.py", "snimek", "dolni-bela-17", "5", "{out}", "nahled"], r"odkaz:", "pf.jpg"),
    ("ebadatelna", "matriky lokality", ["ebadatelna.py", "matriky", "Kounice - obec Kounice - okres Nymburk"], r"^4293 \|", None),
    ("ebadatelna", "snímek", ["ebadatelna.py", "snimek", "4293", "5", "{out}", "nahled"], r"soapraha\.cz/d/4293/5", "eb.jpg"),
    ("ahmp", "hledání svazků", ["bash", "ahmp_search.sh", "Smíchov"], r"9A79C81088C94C9DBEA2FC6758FD08E7", None),
    ("ahmp", "snímek", ["ahmp_scan.py", "9A79C81088C94C9DBEA2FC6758FD08E7", "5", "{out}", "1"], r"permalink", "ah.jpg"),
    ("mza", "knihy obce", ["mza.py", "matriky", "1269"], r"^3090 \| 3212 \|", None),
    ("mza", "info knihy", ["mza.py", "info", "3090"], r"snímků: 270", None),
    ("mza", "snímek", ["mza.py", "snimek", "3090", "50", "{out}", "nahled"], r"detail/3090\?image=", "mz.jpg"),
    ("policie", "hledání přihlášek", ["policie_prihlasky.py", "Kolar", "Josef"], r"záznamů", None),
    ("cuzk", "listy stabilního katastru", ["cuzk_archiv.py", "listy", "49.5234,14.4301"], r"TAB082018300", None),
    ("cuzk", "export listu", ["cuzk_archiv.py", "export", "skici", "195567", "{out}", "0,0,1,1", "400"], r"400×", "cz.jpg"),
    ("ruian", "adresa v RÚIAN", ["mista_domy.py", "ruian", "Karlova 190/1"], r"k\. ú\. Staré Město", None),
    ("osm", "hledání v OpenStreetMap", ["mista_domy.py", "hledej", "Chyšky, Písek"], r"lat=49\.5", None),
    ("ipr", "starý plán Prahy", ["ipr_praha.py", "serie", "50.0870,14.4207", "80", "300", "--jen", "herget_1791"],
     r"OK\s+herget_1791", "pracovni/ipr/herget_1791_r80.jpg"),
    ("kramerius", "fulltext", ["kramerius.py", 'text_ocr:"Chyšky"', "1"], r"^found [1-9]", None),
    ("dnnt", "hledání v tisku", ["dnnt.py", "hledej", 'text_ocr:"Chyšky"', "--max", "1"], r"nalezeno [1-9]", None),
    ("anno", "rakouské noviny", ["anno.py", "Chischka", "1880", "1890", "1"], r"ANNOP_", None),
    # databáze obětí a vězňů 2. sv. války: obecné příjmení, kontroluje se jen tvar odkazu, ne osobní údaje
    ("holocaust", "databáze obětí", ["obeti.py", "hledat", "--prijmeni", "Novák", "--stran", "1"], r"holocaust\.cz/databaze-obeti/", None),
    ("arolsen", "hledání osob", ["arolsen.py", "hledat", "Novák", "--max", "1"], r"arolsen-archives\.org/en/document/\d+", None),
    ("mauthausen", "Raum der Namen", ["mauthausen.py", "hledat", "Novak", "--stran", "1"], r"\| nar\. ", None),
    # židovské matriky (Národní archiv, VadeMeCum) a SOA Litoměřice
    ("vademecum", "hledání matrik obce", ["vademecum.py", "hledat", "Dambořice", "--stran", "1"],
     r"^81034f69-dfc6-4de8-ac9c-de097a9bf81f \|", None),
    ("vademecum", "info svazku", ["vademecum.py", "info", "81034f69-dfc6-4de8-ac9c-de097a9bf81f"], r"Snímků: 75", None),
    ("vademecum", "snímek", ["vademecum.py", "snimek", "81034f69-dfc6-4de8-ac9c-de097a9bf81f", "2", "{out}", "nahled"],
     r"permalink\?xid=81034f69", "vm.jpg"),
    ("litomerice", "hledání knih obce", ["litomerice.py", "hledat", "Úštěk"], r"^\S+ \| \d+ \|", None),
    ("terezin", "databáze vězňů", ["vezni.py", "hledat", "--prijmeni", "Novák", "--stran", "1"], r"pamatnik-terezin\.cz/vezen/", None),
]
# Portály, které před vstupem ověřují člověka (výpočet v prohlížeči). Nástroj to neobchází a skončí tímto kódem;
# kontrola pak hlásí OK s poznámkou – server žije, nástroj ověření poznal, hledání jde jen v prohlížeči.
OVERENI_CLOVEKA = {"litomerice": 5}
# Nástroje, které bez souhlasu uživatele (souhlas.py) nedotazují portál: bez souhlasu se kontroluje jen dostupnost serveru.
SOUHLAS = {"holocaust": ("obeti", "https://www.holocaust.cz/databaze-obeti/"),
           "arolsen": ("arolsen", "https://collections.arolsen-archives.org/"),
           "mauthausen": ("mauthausen", "https://raumdernamen.mauthausen-memorial.org/"),
           "terezin": ("vezni", "https://www.pamatnik-terezin.cz/databaze")}


def ma_souhlas(modul):
    import importlib, souhlas
    try:
        m = importlib.import_module(modul)
    except (ImportError, SystemExit):
        return False
    return souhlas.ma_souhlas(m.SOUHLAS_KLIC, m.SOUHLAS_ZNENI)
# Portály bez pevného svazku (cestu k obrázku dává jen prohlížeč): jen „server odpovídá“
DOSTUPNOST = [
    ("soal", "obrázkový server SOA Litoměřice", "https://images.soalitomerice.cz/ximage/matriky/zoomify/"),
    ("opava", "obrázkový server ZA Opava", "https://images.archives.cz/ximage/matriky/zoomify/"),
    ("matricula", "Matricula", "https://data.matricula-online.eu/"),
]


def je_jpeg(path):
    try:
        with open(path, "rb") as f:
            return f.read(3) == b"\xff\xd8\xff" and os.path.getsize(path) > 5000
    except OSError:
        return False


def server_odpovida(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (rodokmen-plus)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, str(r.status)
    except urllib.error.HTTPError as e:   # 404 na kořeni obrázkového serveru je v pořádku – server žije
        return e.code < 500, str(e.code)
    except OSError as e:
        return False, str(getattr(e, "reason", e))
    except SystemExit as e:   # slusne.py: web zablokovaný nebo 403 na první dotaz – kontrola má pokračovat dál
        return False, str(e)[:80]


def main():
    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        sys.exit(__doc__)
    rychle = "--rychle" in args
    jen = None
    if "--jen" in args:
        i = args.index("--jen")
        jen = set(args[i + 1].split(",")) if i + 1 < len(args) else set()
    portaly = {k[0] for k in KONTROLY} | {k[0] for k in DOSTUPNOST}
    if jen is not None and not jen <= portaly:
        sys.exit(f"Neznámý portál: {', '.join(sorted(jen - portaly))}. Známé: {', '.join(sorted(portaly))}")

    tmp = tempfile.mkdtemp(prefix="dejiny_zdravi_")
    selhalo = 0
    try:
        os.makedirs(os.path.join(tmp, "data"))
        open(os.path.join(tmp, "data", "STAV.md"), "w").close()   # nástroje jinak odmítnou běžet mimo projekt
        shutil.copytree(TOOLS, os.path.join(tmp, "tools"), ignore=shutil.ignore_patterns("__pycache__"))
        os.makedirs(os.path.join(tmp, "out"))
        for portal, popis, cmd, vzor, obr in KONTROLY:
            if (jen is not None and portal not in jen) or (rychle and obr):
                continue
            if portal in SOUHLAS and not ma_souhlas(SOUHLAS[portal][0]):
                ok, kod = server_odpovida(SOUHLAS[portal][1])
                print(f"{'OK   ' if ok else 'CHYBA'} {portal:13} {popis:28} (bez souhlasu jen dostupnost, {kod})")
                selhalo += not ok
                continue
            out = os.path.join("out", obr) if obr and "/" not in obr else obr
            cmd = [c.replace("{out}", out or "") for c in cmd]
            cmd = ["bash", "tools/" + cmd[1], *cmd[2:]] if cmd[0] == "bash" else [*PY, "tools/" + cmd[0], *cmd[1:]]
            t = time.time()
            try:
                p = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=180)
                vystup = p.stdout + p.stderr
                ok = p.returncode == 0 and re.search(vzor, p.stdout, re.M) is not None
                if not ok and OVERENI_CLOVEKA.get(portal) == p.returncode:
                    print(f"OK    {portal:13} {popis:28} (portál ověřuje člověka – jen prohlížeč)")
                    continue
                if ok and obr and not je_jpeg(os.path.join(tmp, out)):
                    ok, vystup = False, f"obrázek {obr} chybí nebo není JPEG\n" + vystup
            except subprocess.TimeoutExpired:
                ok, vystup = False, "vypršel čas (180 s)"
            radky = [r for r in vystup.strip().splitlines() if r.strip()]
            print(f"{'OK   ' if ok else 'CHYBA'} {portal:13} {popis:28} {time.time() - t:5.1f} s")
            if not ok:
                selhalo += 1
                for r in radky[-3:]:
                    print("      ", r[:200])
        for portal, popis, url in DOSTUPNOST:
            if jen is not None and portal not in jen:
                continue
            ok, kod = server_odpovida(url)
            print(f"{'OK   ' if ok else 'CHYBA'} {portal:13} {popis:28} (jen dostupnost, {kod})")
            selhalo += not ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'Vše funguje.' if not selhalo else f'Selhalo: {selhalo}.'}")
    sys.exit(1 if selhalo else 0)


if __name__ == "__main__":
    main()
