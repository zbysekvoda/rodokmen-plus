#!/usr/bin/env python3
"""Raum der Namen – zemřelí v koncentračním táboře Mauthausen a pobočkách (Gusen, Ebensee, Melk…), bez prohlížeče.

Použití (z kořene projektu):
  mauthausen.py souhlas -> uživatel (ne Claude!) jednou za 30 dní potvrdí, že s citlivými údaji o obětech zachází odpovědně
                           (v Claude Code `!python3 -I tools/mauthausen.py souhlas`). Bez souhlasu nástroj nic nestahuje.
  mauthausen.py hledat "text" [--stran N]
        -> příjmení nebo jméno (i „Novak 1905“); N stran po 20 osobách (výchozí 2).
           Výpis: jméno | roky | narozen (místo) | zemřel (místo) | odkaz na stránku osoby (s fotkami a životopisem, je-li)
Jen osoby, které v táboře zemřely; přeživší tu nejsou (hledej v `arolsen.py`). Jména bývají v místním tvaru (Novak, Nowak).
Údaje o obětech jsou citlivé – na web jen se souhlasem rodiny (soukromi.md).

Převzato a upraveno z forku (licence MIT, © srameko):
  https://github.com/srameko/rodokmen-skill/blob/5f25edb9a201f8ac03b79293bbcb79b5109d022e/skills/rodokmen/tools/mauthausen.py
  (varianta: https://github.com/hnizdiljan/rodokmen-skill/blob/d172316bc190d0f44894fa67115505729d587c6a/skills/rodokmen/tools/mauthausen.py)
"""
import os, html, re, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # noqa: E402 – společný limit rychlosti k webům archivů (slusne.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

import souhlas  # noqa: E402 – souhlas s podmínkami (tools/souhlas.py)

BASE = "https://raumdernamen.mauthausen-memorial.org/"
SOUHLAS_KLIC, SOUHLAS_PORTAL, SOUHLAS_PRIKAZ = "mauthausen", "Raum der Namen (KZ-Gedenkstätte Mauthausen)", "tools/mauthausen.py souhlas"
SOUHLAS_ZNENI = ("Raum der Namen je pamětní databáze lidí zavražděných v koncentračním táboře Mauthausen a jeho pobočkách. Obsahuje "
                 "citlivé údaje o obětech (jméno, narození, místo a datum smrti, někdy fotografie a životopis). Údaje používám jen "
                 "k osobnímu a genealogickému bádání, s respektem k obětem a pozůstalým, a zveřejním je jen se souhlasem rodiny. "
                 "(Upozornění nástroje rodokmen-plus; portál vlastní okno se souhlasem nemá, platí jeho podmínky užití.)")
SOUHLAS_URL = "https://www.mauthausen-memorial.org/de/Impressum"


def get(url):
    err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (rodokmen)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except OSError as e:
            err = e
            if getattr(e, "code", 0) in (403, 404):
                break
            time.sleep(2 * (attempt + 1))
    sys.exit(f"Portál neodpověděl ({type(err).__name__}: {str(err)[:100]}). Zkus to později.")


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ")).strip()


def hledat(dotaz, stran):
    q = urllib.parse.quote(dotaz)
    n, videno, celkem = 0, set(), None
    for p in range(1, stran + 1):
        page = get(f"{BASE}?txtFullSearch={q}&L=0&id=5&page={p}&count=20")   # strany portálu jsou číslované od 1
        celkem = celkem or re.search(r'(\d[\d.\s\xa0]*) Personen', page)   # počet bereme z první stránky, která ho má
        osoby = re.findall(r'<div class="entry">.*?<h1><a href="([^"]+)">(.*?)</a></h1>\s*(?:<p class="subtext">(.*?)</p>)?', page, re.S)
        osoby = [o for o in osoby if o[0] not in videno]
        videno |= {o[0] for o in osoby}
        for href, jm, sub in osoby:
            roky = re.search(r'<span class="years">(.*?)</span>', jm)
            jmeno = text(re.sub(r'<span class="years">.*?</span>', "", jm))
            radky = [text(x) for x in re.split(r"<br\s*/?>", sub) if text(x)]
            nar = next((r.replace("Geboren ", "") for r in radky if r.startswith("Geboren")), "-")
            zem = next((r.replace("Gestorben ", "") for r in radky if r.startswith("Gestorben")), "-")
            print(f"{jmeno} | {text(roky.group(1)) if roky else '-'} | nar. {nar} | zem. {zem} | {html.unescape(href)}")
            n += 1
        if not osoby:
            break
        time.sleep(0.7)
    if n == 0:
        print("Nic nenalezeno (zkus jiný pravopis nebo jen příjmení).", file=sys.stderr)
    elif celkem and n < int(re.sub(r"\D", "", celkem.group(1)) or 0):
        print(f"… celkem {celkem.group(1).strip()} osob, zobrazeno {n}; zúžit jde křestním jménem nebo rokem, víc dá --stran", file=sys.stderr)


if __name__ == "__main__":
    a = sys.argv[1:]
    stran = 2
    if a == ["souhlas"]:
        souhlas.potvrd(SOUHLAS_KLIC, SOUHLAS_PORTAL, SOUHLAS_ZNENI, SOUHLAS_URL, SOUHLAS_PRIKAZ)
        sys.exit(0)
    if "--stran" in a:
        i = a.index("--stran")
        if i + 1 >= len(a) or not (a[i + 1].isdigit() and int(a[i + 1]) >= 1):
            sys.exit("--stran chce kladné číslo.")
        stran = int(a[i + 1])
        del a[i:i + 2]
    if len(a) == 2 and a[0] == "hledat" and a[1].strip():
        souhlas.vyzaduj(SOUHLAS_KLIC, SOUHLAS_PORTAL, SOUHLAS_ZNENI, SOUHLAS_PRIKAZ)
        hledat(a[1], stran)
    else:
        sys.exit(__doc__)
