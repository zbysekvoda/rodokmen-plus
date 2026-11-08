#!/usr/bin/env python3
"""Kontrola konzistence dat rodokmenu a dějin domů (osoby.py, domy.py, zápisy, křížové odkazy osoba↔dům). Spouštějte po každé větší změně a před stavbou webu.

Použití: kontrola.py
Vypíše CHYBY (rozbijí web nebo jsou věcně špatně) a UPOZORNĚNÍ (něco chybí, doplnit).
Návratový kód 1, pokud jsou chyby.
"""
import datetime, json, os, re, sys, unicodedata
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import kontrola_domy  # noqa: E402


def jload(name, default):
    p = os.path.join(DATA, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def slugify(text):   # stejně jako export_web.py
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def wiki_odkazy(err, warn, g, O, LINES, kek, keys, D, obec_domu, dum_id, cfg):
    """Wiki odkazy [[typ:cíl]] / [[typ:cíl|popisek]] v příbězích a zajímavostech – stejné cíle jako v export_web.py
    (neplatný cíl tam zastaví export). Osoby, zápisy a příběhy přesně; domy, rody a místa podle dat (export je skládá složitěji)."""
    soubory = ["zajimavosti.md", "zajimavosti_domy.md", "pribeh.md", "pribeh_domy.md"]
    pribehy = set()
    for x in cfg.get("pribehy", []) if isinstance(cfg.get("pribehy"), list) else []:
        if isinstance(x, dict) and x.get("soubor") and os.path.exists(os.path.join(DATA, x["soubor"])):
            soubory.append(x["soubor"])
            pribehy.add(x.get("slug", ""))
    placeholder = lambda p: (p.get("n") or "").startswith(("otec neuveden", "matka neuvedena")) or p.get("n") in ("", "?", None)
    osoby = {i for i, p in O.items() if not (placeholder(p) or p.get("druh") == "bocni" or p.get("tataz"))}
    domy = {slugify(" ".join(dum_id(k, d))) for k, d in D.items()}
    obce = {d.get("obec") or obec_domu for d in D.values()}
    for d in jload("domy_rodiny.json", []):
        if isinstance(d, dict) and d.get("obec"):
            domy.add(slugify(f"{d['obec']} {d.get('cp', '')}"))
            obce.add(d["obec"])
    obce |= {n for n, e in jload("mista.json", {}).items() if isinstance(e, dict) and "lat" in e}
    rody = {slugify(v[0] if isinstance(v, (list, tuple)) else str(v)) for k, v in LINES.items() if k in kek}
    rx = re.compile(r"\[\[([^\]|:]+):([^\]|]+?)(?:\|([^\]]+))?\]\]")
    for f in dict.fromkeys(soubory):
        path = os.path.join(DATA, f)
        if not os.path.exists(path):
            continue
        text = re.sub(r"<!--.*?-->", "", open(path, encoding="utf-8").read(), flags=re.S)   # komentáře export zahodí
        for m in rx.finditer(text):
            typ, x, odkaz = m.group(1).strip(), m.group(2).strip(), m.group(0)
            kde = f"data/{f}: odkaz {odkaz}"
            if typ == "osoba":
                if x not in osoby:
                    hl = O.get(x, {}).get("tataz")
                    err.append(f"{kde} – osoba {x!r} nemá stránku" + (f" (druhý výskyt, piš [[osoba:{hl}]])" if hl else
                               " (není v osoby.py, nebo je to boční souhrn / neuvedený rodič)"))
            elif typ == "zdroj":
                if x not in keys:
                    err.append(f"{kde} – zápis {x!r} není v zaznamy.json")
            elif typ == "pribeh":
                if x not in pribehy:
                    err.append(f"{kde} – příběh {x!r} není ve web.json „pribehy“ (nebo chybí jeho soubor)")
            elif typ == "dum":
                if x not in domy:
                    err.append(f"{kde} – dům {x!r} není v domy.py ani domy_rodiny.json (adresa je obec-cp, např. horni-lhota-12)")
            elif typ == "rod":
                if x not in rody:
                    err.append(f"{kde} – rod {x!r} neexistuje (adresy rodů: {', '.join(sorted(rody)) or 'žádné'})")
            elif typ == "misto":
                if slugify(x) not in {slugify(o) for o in obce if o}:
                    warn.append(f"{kde} – obec {x!r} nemá souřadnice v mista.json ani dům; export ji asi nenajde a zastaví se")
            else:
                warn.append(f"{kde} – neznámý typ {typ!r} (osoba, dum, zdroj, rod, misto, pribeh); na webu zůstane jako text")


def main():
    err, warn = [], []
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import graf
        g = graf.nacti()
        if not g.osoby:
            print("Rodokmen je zatím prázdný – založte první osobu do OSOBY a její id do KORENY['hlavni'].")
            return
        ns = g.legacy()
    except Exception as e:  # noqa: BLE001
        sys.exit(f"CHYBA: data/osoby.py nejde načíst: {e}")
    O, LINES = g.osoby, ns.get("LINES", {})
    kek = g.kekule()                                    # Kekulé jen pro rody a přehledy
    err += [f"graf osob: {e}" for e in g.chyby()]
    hlavni = lambda i: O[i].get("tataz") or i                  # druhý výskyt → hlavní osoba
    zaz = jload("zaznamy.json", [])
    svazky, prep, hl = jload("svazky.json", {}), jload("prepisy.json", {}), jload("zvyrazneni.json", {})
    keys = [z.get("klic") for z in zaz]
    dup = {k for k in keys if keys.count(k) > 1}
    if dup:
        err.append(f"zápisy se stejným klíčem: {sorted(dup)}")
    keys = set(keys)

    for k, p in O.items():
        st = p.get("st", "unk")
        bydliste = p.get("bydliste", [])
        if not isinstance(bydliste, list):
            err.append(f"osoba {k}: 'bydliste' musí být seznam")
            bydliste = []
        for b in bydliste:
            kde = f"osoba {k} ({p.get('n')}), bydliště {b.get('obec')} čp. {b.get('cp')}"
            if not b.get("obec") or not str(b.get("cp") or "").strip():
                err.append(f"{kde}: chybí obec nebo číslo popisné")
            zdroj = b.get("zdroj") or []
            if not zdroj:
                err.append(f"{kde}: chybí zdroj (klíč ze zaznamy.json, nebo \"rodina\")")
            for r in zdroj:
                if r != "rodina" and r not in keys:
                    err.append(f"{kde}: zdroj '{r}' není v zaznamy.json")
            od, do = b.get("od"), b.get("do")
            for v in (od, do):
                if v is not None and not isinstance(v, int):
                    err.append(f"{kde}: od/do musí být rok (celé číslo) nebo None, ne {v!r}")
            if isinstance(od, int) and isinstance(do, int) and od > do:
                err.append(f"{kde}: od ({od}) je později než do ({do})")
        if st == "doc" and not p.get("r"):
            warn.append(f"osoba {k} ({p.get('n')}) je 'doc' (doloženo), ale necituje žádný zápis")
    gen_rodu = {k.bit_length() - 1 for k in LINES}
    if len(gen_rodu) > 1:
        err.append(f"LINES: rody {sorted(LINES)} nejsou v jedné generaci – zakladatelé rodů mají být např. všichni pradědečci a prababičky")
    for k in LINES:
        if k < 4:
            err.append(f"LINES: rod {k} – zakladatel rodu má být nejméně prarodič výchozí osoby (č. 4 a výš)")

    cited = {r for p in O.values() for r in p.get("r", [])} | {r for e in g.vztahy for r in e.get("r", [])}

    # Dějiny domů (data/domy.py) a křížové odkazy osoba ↔ dům
    nsd, cited_domy, souhrn_domy = kontrola_domy.kontrola(err, warn)
    cited |= cited_domy
    OBEC, D = nsd.get("OBEC", {}), nsd.get("D", {})
    obec_domu = OBEC.get("nazev", "")

    def zije(k):
        return "Žijící" in O.get(k, {}).get("note", "")

    def dum_id(key, d):   # (obec, čp.): dům jiné obce má pole obec= a cp= (klíč „Obec čp“), jinak OBEC a klíč
        return d.get("obec") or obec_domu, str(d.get("cp") or key)
    for key, d in D.items():
        obec, cp = dum_id(key, d)
        if d.get("obec") and key != f"{obec} {cp}":
            err.append(f"dům {key!r}: dům jiné obce má mít klíč „{obec} {cp}“ (podle polí obec a cp)")
        if " " in key and not d.get("obec"):
            err.append(f"dům {key!r}: klíč s mezerou = dům jiné obce, chybí pole obec= a cp=")
        for role, seznam in (("držitel", d.get("drzitele", [])), ("obyvatel", d.get("obyvatele", []))):
            for o in seznam:
                if o.get("o") is None:
                    continue
                kde = f"dům {obec} čp. {cp}, {role} {o.get('n')}"
                if isinstance(o["o"], int) or str(o["o"]).isdigit():
                    k = g.id_osoby(o["o"])
                    err.append(f"{kde}: o={o['o']!r} je Kekulého číslo – odkaz na osobu musí být id z osoby.py"
                               + (f", tady o=\"{k}\"" if k else " (najdi ho: python3 -I tools/graf.py osoba <číslo>; hromadně tools/prevod_odkazu_id.py)"))
                    continue
                k = g.id_osoby(o["o"])
                if k is None:
                    err.append(f"{kde}: odkaz o={o['o']!r} na osobu, která v osoby.py není")
                    continue
                prijmeni = {w[:5] for w in re.findall(r"\w{4,}", O[k].get("n", ""))}
                if not prijmeni & {w[:5] for w in re.findall(r"\w{4,}", o.get("n", ""))}:
                    warn.append(f"{kde}: o={k}, ale osoba {k} se jmenuje {O[k].get('n')} – je to opravdu tatáž osoba?")
                if not zije(k) and not any(b.get("obec") == obec and str(b.get("cp")) == cp for b in O[k].get("bydliste", []) + [b for t in O.values() if t.get("tataz") == k for b in t.get("bydliste", [])]):
                    warn.append(f"{kde}: osoba {k} ({O[k].get('n')}) nemá v 'bydliste' tento dům – doplň (obec, čp.)")
    domy_id = {dum_id(key, d) for key, d in D.items()}
    odkazy = {dum_id(key, d) + (g.id_osoby(o.get("o")),) for key, d in D.items() for o in d.get("drzitele", []) + d.get("obyvatele", [])}
    for k, p in O.items():
        for b in p.get("bydliste", []):
            bid = (b.get("obec"), str(b.get("cp")))
            if bid in domy_id and bid + (hlavni(k),) not in odkazy:
                warn.append(f"osoba {k} ({p.get('n')}) bydlela v {bid[0]} čp. {bid[1]}, dům je v domy.py, "
                            f"ale nemá ji mezi držiteli/obyvateli s o=\"{hlavni(k)}\"")
        if zije(k) and (p.get("bydliste") or p.get("r")):
            warn.append(f"SOUKROMÍ: osoba {k} ({p.get('n')}) je žijící – jen jméno a rok narození, bez bydliště a zápisů")
    # Zápis může volitelně odkazovat na osoby a domy: "osoby": [id osoby] (jen id, ne Kekulé č.), "domy": [{"obec": …, "cp": …}]
    for dk in jload("dokumenty.json", []):   # dokumenty: "osoby": [id osoby]
        for x in dk.get("osoby", []) if isinstance(dk, dict) else []:
            if isinstance(x, int) or str(x).isdigit():
                k = g.id_osoby(x)
                err.append(f"dokument {dk.get('soubor') or dk.get('nazev')!r}: v 'osoby' je Kekulého číslo {x!r} – piš id z osoby.py"
                           + (f" (tady \"{k}\")" if k else " (najdi ho: python3 -I tools/graf.py osoba <číslo>; hromadně tools/prevod_odkazu_id.py)"))
            elif g.id_osoby(x) is None:
                err.append(f"dokument {dk.get('soubor') or dk.get('nazev')!r}: osoba {x!r} v 'osoby' není v osoby.py")
    for z in zaz:
        for x in z.get("osoby", []):
            k = g.id_osoby(x)
            if isinstance(x, int) or str(x).isdigit():
                err.append(f"zápis {z.get('klic')}: v 'osoby' je Kekulého číslo {x!r} – piš id z osoby.py"
                           + (f" (tady \"{k}\")" if k else " (najdi ho: python3 -I tools/graf.py osoba <číslo>; hromadně tools/prevod_odkazu_id.py)"))
            elif k is None:
                err.append(f"zápis {z.get('klic')}: osoba {x!r} v 'osoby' není v osoby.py")
            elif z.get("klic") not in O[k].get("r", []) + [r for t in O.values() if t.get("tataz") == k for r in t.get("r", [])]:
                warn.append(f"zápis {z.get('klic')}: uvádí osobu {k}, ale ta zápis necituje v 'r'")
        for dm in z.get("domy", []):
            if not isinstance(dm, dict) or not dm.get("obec") or not str(dm.get("cp") or "").strip():
                err.append(f"zápis {z.get('klic')}: položka v 'domy' musí být {{\"obec\": …, \"cp\": …}}, ne {dm!r}")
    for z in zaz:
        k = z.get("klic", "?")
        for f in ("klic", "druh", "datum", "nazev", "shrnuti"):
            if not z.get(f):
                err.append(f"zápis {k}: chybí pole '{f}'")
        if z.get("svazek") and z["svazek"] not in svazky:
            err.append(f"zápis {k}: svazek '{z['svazek']}' není v data/svazky.json")
        if z.get("ukazka"):   # vymyšlený zápis ukázkové rodiny – nemá snímek ani přepis
            continue
        if not z.get("odkaz") and not svazky.get(z.get("svazek", ""), {}).get("url"):
            warn.append(f"zápis {k}: chybí odkaz na snímek (pole 'odkaz')")
        if not os.path.exists(os.path.join(ROOT, "vyrezy", k + ".jpg")):
            warn.append(f"zápis {k}: chybí výřez vyrezy/{k}.jpg")
        elif k not in hl and z.get("druh") != "M":   # mapa: rámeček volitelný
            warn.append(f"zápis {k}: chybí rámeček (tools/ramecek.py)")
        if k not in prep and z.get("druh") != "M":   # mapa: stačí shrnutí
            warn.append(f"zápis {k}: chybí přepis a překlad v data/prepisy.json")
        if k not in cited:
            warn.append(f"zápis {k}: necituje ho žádná osoba ani dům (doplnit do 'r' u osoby, bočního příbuzného nebo v domy.py)")

    for name, e in jload("mista.json", {}).items():
        if "lat" not in e:
            warn.append(f"místo {name}: nemá souřadnice (spusťte tools/mista.py)")
        try:
            re.compile(e.get("re") or "")
        except re.error as ex:
            err.append(f"místo {name}: špatný výraz '{e.get('re')}': {ex}")

    cfg = jload("web.json", {})
    if not (cfg.get("prihlaseni") or {}).get("odpoved") and not (cfg.get("prihlaseni") or {}).get("otevreny"):
        warn.append("web.json: není nastavená odpověď na přihlašovací otázku – nasazení webu skončí chybou")

    # ukázka z novy_projekt.py --ukazka (fiktivní Novákovi z Holic); skutečné příjmení Novák varování nespouští
    if "z Holic" in json.dumps(cfg, ensure_ascii=False) or (cfg.get("prihlaseni") or {}).get("odpoved") == "kovář":
        warn.append("web.json: jsou v něm ještě ukázkové texty (Novákovi) – nastav název, příběh a kontakt")

    # Citlivé věci, které jdou na web: ISSUES („Co hledáme“), poznámky a fakta osob, boční příbuzní, texty.
    citlive = re.compile(r"sebevra|vzal[a]? si život|oběsil|zastřelil[a]? se|utopil[a]? se|alkohol|vězen|kriminál|"
                         r"rozvod|rozvedl|psychiatr|léčebn|duševn|rakovin|nemanželsk|cizoložst|dluh|exekuc|interrupc|potrat", re.I)

    hranice = datetime.date.today().year - 100   # posledních ~100 let; staré matriční údaje (nemanželské dítě v 18. stol.) nevadí

    def recent(text):
        return any(int(y) >= hranice for y in re.findall(r"\b(19\d\d|20\d\d)\b", text))
    schvaleno = [s for s in (cfg.get("citlive_schvaleno") if isinstance(cfg.get("citlive_schvaleno"), list) else [])
                 if isinstance(s, str) and len(s.strip()) >= 3]

    def schvalene(text, m):   # uživatel to na web pustil: v web.json „citlive_schvaleno“ je úryvek textu s tímto slovem
        for s in schvaleno:
            i = text.find(s)
            while i >= 0:
                if i <= m.start() and m.end() <= i + len(s):
                    return True
                i = text.find(s, i + 1)
        return False
    texty = [("ISSUES", i if isinstance(i, str) else " ".join(x for x in i if isinstance(x, str))) for i in ns.get("ISSUES", [])]
    blizci = {i for k, i in kek.items() if k < 8} | set(g.koreny.values())
    for k, p in O.items():
        if p.get("druh") == "bocni":
            texty.append((f"boční příbuzný {p.get('n')}", p.get("n", "") + " " + p.get("t", "")))
            continue
        text = " ".join(p.get("f", [])) + " " + p.get("note", "") + " " + json.dumps(p.get("extra") or {}, ensure_ascii=False)   # i vlastní pole extra
        roky = [int(y) for y in re.findall(r"\b1[5-9]\d\d|20\d\d\b", p.get("y", "") + " " + text)]
        texty.append((f"osoba {k}", text + (f" {hranice}" if roky and min(roky) >= 1870 or k in blizci else "")))
    for f in ("zajimavosti.md", "pribeh.md", "pribeh_domy.md", *(x.get("soubor", "") for x in cfg.get("pribehy", []))):
        if os.path.exists(os.path.join(DATA, f)):
            texty += [(f, odst) for odst in open(os.path.join(DATA, f), encoding="utf-8").read().split("\n\n")]
    for kde, text in texty:
        if not recent(text):
            continue
        m = next((m for m in citlive.finditer(text) if not schvalene(text, m)), None)
        if m:
            warn.append(f"CITLIVÉ ({kde}): „…{text[max(0, m.start() - 40):m.end() + 40].strip()}…“ – jde na web; "
                        f"zeptej se uživatele, jestli to tam smí být (reference/soukromi.md); když ano, "
                        f"přidej úryvek textu s tím slovem do web.json „citlive_schvaleno“")

    wiki_odkazy(err, warn, g, O, LINES, kek, keys, D, obec_domu, dum_id, cfg)

    if not os.path.exists(os.path.join(DATA, "pribeh.md")) and LINES:
        hlavni = min(LINES)
        n = max((k.bit_length() for k in kek if k >= 8 and k >> (k.bit_length() - 4) == hlavni), default=0)
        if n >= 6:
            warn.append(f"rod {LINES[hlavni][0]} má už {n} generací – je čas napsat příběh rodu "
                        f"(data/pribeh.md, reference/pribehy.md); koncept nejdřív ukaž uživateli v chatu")

    log = os.path.join(DATA, "research_log.md")
    rows = sum(1 for l in open(log, encoding="utf-8") if re.match(r"^\| \d+ \|", l)) if os.path.exists(log) else 0
    print(f"{sum(1 for d in O.values() if not d.get('druh') and not d.get('tataz'))} osob, {souhrn_domy}, {len(zaz)} zápisů, {len(svazky)} svazků, {rows} řádků deníku")
    for e in err:
        print("CHYBA:", e)
    for w in warn:
        print("upozornění:", w)
    if not err and not warn:
        print("Vše v pořádku.")
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()
