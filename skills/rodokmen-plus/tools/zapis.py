#!/usr/bin/env python3
"""Přidá nebo nahradí jednu položku v datech projektu – formát souboru zůstane stejný (odsazení 1, české znaky, konce
řádků LF), takže změna v historii je jen ta jedna položka.

Použití (z kořene projektu):
  zapis.py <soubor> <klíč> <vstup.json> [--sloucit]
  zapis.py dokumenty <starý_klíč> --prejmenovat <nový_klíč> [--nahled]
    soubor    zaznamy | svazky | prepisy | zvyrazneni | mista | scitani_mza | dokumenty | mapy | web  (= data/<soubor>.json)
    klíč       zaznamy: „klic“ zápisu; dokumenty, mapy: „img“; web: pole nastavení (uvod, pribeh, prihlaseni,
               zajimavosti_na_uvodu, nazev…); ostatní: klíč ve slovníku (id svazku, klíč zápisu, obec;
               scitani_mza: obec – s --sloucit a {"operaty": {…}} se celé „operaty“ nahradí, tak je uveď všechny)
    vstup.json soubor s jedním objektem JSON (napiš ho nástrojem Write do pracovni/), „-“ = ze vstupu
    --sloucit  jen změní / doplní uvedená pole, ostatní pole položky nechá
    --prejmenovat  přejmenuje „img“ dokumentu včetně výřezů (vyrezy/, zdroje/, web/public/), zvýraznění, web.json
               „uvod.foto“ a odkazů img/…jpg v datech a web/src; --nahled jen vypíše, co by změnil
Položka se stejným klíčem se nahradí, jinak se přidá na konec. Python skripty ani `sed -i` na data nepoužívej.

--prejmenovat převzato z forku xkraust/rodokmen-skill (https://github.com/xkraust/rodokmen-skill),
commit 79d3685 (https://github.com/xkraust/rodokmen-skill/commit/79d36850afaa080b0ebcf70a368cbbb5237d700e).
"""
import json, os, re, sys
import tempfile, unicodedata
from pathlib import Path
from urllib.parse import quote
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "data", "STAV.md")):   # spuštěno ze složky skillu: data projektu tam nejsou, zápis by šel do skillu
    sys.exit(f"{os.path.basename(__file__)}: {ROOT} není složka projektu (chybí data/STAV.md). "
             f"Spusť projektovou kopii z kořene projektu: python3 -I tools/{os.path.basename(__file__)} …")
SEZNAMY = {"zaznamy": "klic", "dokumenty": "img", "mapy": "img"}   # soubory se seznamem: pole, podle kterého se položka pozná
SLOVNIKY = {"svazky", "prepisy", "zvyrazneni", "mista", "scitani_mza", "web"}
LIBOVOLNE = {"web"}   # hodnota nemusí být objekt (web.json: „nazev“ je text, „zajimavosti_na_uvodu“ seznam)
WS = re.compile(r"\s*")


def polozky(text):
    """Položky nejvyšší úrovně: [(klíč nebo None, začátek hodnoty, konec hodnoty)] – pozice v původním textu."""
    dec, i = json.JSONDecoder(), WS.match(text).end()
    otevreni, i, out = text[i], i + 1, []
    while True:
        i = WS.match(text, i).end()
        if text[i] in "]}":
            return out
        klic = None
        if otevreni == "{":
            klic, i = dec.raw_decode(text, i)
            i = WS.match(text, WS.match(text, i).end() + 1).end()   # za dvojtečku
        _, j = dec.raw_decode(text, i)
        out.append((klic, i, j))
        i = WS.match(text, j).end()
        if text[i] == ",":
            i += 1


def jako(text, s, e, v):
    """Hodnota v JSON ve stejném stylu jako text[s:e] (na jednom řádku, nebo odsazená po jedné mezeře)."""
    if "\n" not in text[s:e]:
        return json.dumps(v, ensure_ascii=False)
    odsazeni = text[text.rfind("\n", 0, s) + 1:s]
    odsazeni = odsazeni[:len(odsazeni) - len(odsazeni.lstrip())]
    return json.dumps(v, ensure_ascii=False, indent=1).replace("\n", "\n" + odsazeni)


def _atomic_bytes(path, content):
    """Zápis vedle cíle a atomické nahrazení, bez ponechání rozpracovaného souboru."""
    fd, tmp = tempfile.mkstemp(prefix=".zapis-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def rename_document(root, old, new, preview=False):
    """Přejmenuje dokument (img v data/dokumenty.json), jeho výřezy a známé odkazy; při chybě vrátí provedené změny.

    Převzato z forku xkraust/rodokmen-skill, commit 79d3685
    (https://github.com/xkraust/rodokmen-skill/commit/79d36850afaa080b0ebcf70a368cbbb5237d700e), autor xkraust.
    Úpravy pro rodokmen-plus: kolize hlídá i proti data/mapy.json, chybějící výřez jen ohlásí (dokument bez obrázku
    jde přejmenovat taky)."""
    root = Path(root).resolve()
    def canonical(key):
        return unicodedata.normalize("NFC", key).casefold()

    for key in (old, new):
        if (not key or key in (".", "..") or key[-1] in " ." or
                re.search(r'[<>:"/\\|?*\x00-\x1f]', key) or
                re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", key)):
            raise ValueError(f"Neplatný klíč obrázku: {key!r}; použijte název bez cesty a přípony.")
    if canonical(old) == canonical(new):
        raise ValueError("Nový klíč se musí lišit od původního i bez ohledu na velikost písmen.")

    def inside(path):
        if not path.resolve().is_relative_to(root):
            raise ValueError(f"Cesta vede mimo projekt: {path}")
        return path

    docs_path = inside(root / "data" / "dokumenty.json")
    raw = docs_path.read_bytes()
    text = raw.decode("utf-8-sig")
    docs = json.loads(text)
    if not isinstance(docs, list):
        raise ValueError("dokumenty.json musí být seznam.")
    matches = [i for i, d in enumerate(docs) if isinstance(d, dict) and d.get("img") == old]
    if len(matches) != 1:
        raise ValueError(f"Klíč {old} musí mít právě jednu položku v dokumenty.json.")
    if any(isinstance(d, dict) and canonical(d.get("img", "")) == canonical(new) for d in docs):
        raise ValueError(f"Dokument {new} už existuje.")
    maps_path = inside(root / "data" / "mapy.json")
    if maps_path.exists() and any(isinstance(m, dict) and canonical(m.get("img", "")) == canonical(new)
                                  for m in json.loads(maps_path.read_text(encoding="utf-8-sig"))):
        raise ValueError(f"Klíč {new} už má mapa v mapy.json.")
    records_path = inside(root / "data" / "zaznamy.json")
    if records_path.exists() and any(canonical(r["klic"]) in (canonical(old), canonical(new))
                                     for r in json.loads(records_path.read_text(encoding="utf-8-sig"))):
        raise ValueError("Klíč sdílí matriční zápis; přejmenování dokumentu by změnilo i jeho snímek.")

    idx = matches[0]
    _, s, e = polozky(text)[idx]
    changed = text[:s] + jako(text, s, e, dict(docs[idx], img=new)) + text[e:]
    changes = {docs_path: changed.encode("utf-8")}
    moves = []
    for folder in ("vyrezy", "zdroje", "web/public/img", "web/public/zdroje"):
        directory = inside(root / folder)
        src, dst = inside(directory / (old + ".jpg")), inside(directory / (new + ".jpg"))
        if directory.exists() and any(canonical(p.name) == canonical(new + ".jpg") for p in directory.iterdir()):
            raise ValueError(f"Cílový soubor už existuje: {dst}")
        if src.exists():
            if not src.is_file():
                raise ValueError(f"Očekáván soubor: {src}")
            moves.append((src, dst))
    if not (root / "vyrezy" / (old + ".jpg")).is_file():
        print(f"Pozor: chybí vyrezy/{old}.jpg – přejmenuje se jen evidence a odkazy.")

    def links(value):
        # Relativní cesty i URL, včetně názvů s diakritikou zakódovaných v URL.
        variants = [(old, False)]
        if quote(old, safe="") != old:
            variants.append((quote(old, safe=""), True))
        for before, encoded in variants:
            pattern = r"(?<![\w-])((?:img|vyrezy|zdroje)/)" + re.escape(before) + r"\.jpg(?![\w.-])"
            def replace(match):
                url = encoded or match[1] == "img/" or (match.start() > 0 and value[match.start() - 1] == "/")
                return match[1] + (quote(new, safe="") if url else new) + ".jpg"
            value = re.sub(pattern, replace, value)
        return value

    # Měnit zdrojové odkazy, generované HTML a site.json se obnoví exportem/buildem.
    paths = list((root / "data").rglob("*"))
    src_dir = root / "web" / "src"
    if src_dir.exists():
        paths += [p for p in src_dir.rglob("*") if p.relative_to(src_dir).parts[0] not in ("data", "generated")]
    for path in paths:
        if not path.is_file() or path.suffix not in (".json", ".md", ".py", ".astro", ".js", ".ts", ".html", ".css"):
            continue
        inside(path)
        before = changes.get(path, path.read_bytes()).decode("utf-8-sig")
        after = before
        if path.suffix == ".json":
            data = json.loads(before)
            if path.name == "zvyrazneni.json" and old in data and any(canonical(k) == canonical(new) for k in data):
                raise ValueError(f"Zvýraznění pro {new} už existuje.")
            foto_span, login_span, highlight_span = None, None, None
            if path.name == "zvyrazneni.json" and old in data:
                start = next(s for k, s, e in polozky(before) if k == old)
                highlight_span = re.search(r'("(?:[^"\\]|\\.)*")\s*:\s*$', before[:start]).span(1)
            if path.name == "web.json":
                for field, start, end in polozky(before):
                    if field == "prihlaseni":
                        login_span = (start, end)
                    if field == "uvod" and isinstance(data.get("uvod"), dict):
                        foto_span = next(((start + s, start + e) for k, s, e in polozky(before[start:end]) if k == "foto"), None)
            def token(match):
                if login_span and login_span[0] <= match.start() < login_span[1]:
                    return match[0]
                value = json.loads(match[0])
                rename_key = (match.start(), match.end()) == highlight_span
                rename_value = (match.start(), match.end()) == foto_span
                replacement = new if value == old and (rename_key or rename_value) else links(value)
                return json.dumps(replacement, ensure_ascii=False) if replacement != value else match[0]
            after = re.sub(r'"(?:[^"\\]|\\.)*"', token, before)
            json.loads(after)
        else:
            after = links(before)
        if after != before:
            changes[path] = after.encode("utf-8")

    for src, dst in moves:
        print(f"{src.relative_to(root)} → {dst.relative_to(root)}")
    for path in changes:
        print(f"Aktualizace: {path.relative_to(root)}")
    if preview:
        print("Náhled: nic nezměněno.")
        return

    originals = {p: p.read_bytes() for p in changes}
    moved, written = [], []
    try:
        for src, dst in moves:
            if dst.exists():
                raise FileExistsError(dst)
            os.rename(src, dst)
            moved.append((src, dst))
        for path, content in changes.items():
            _atomic_bytes(path, content)
            written.append(path)
    except BaseException:
        for path in reversed(written):
            _atomic_bytes(path, originals[path])
        for src, dst in reversed(moved):
            os.rename(dst, src)
        raise
    print(f"Přejmenováno: {old} → {new}. Originál v dokumenty/ zachován. "
          "Spusť kontrola.py a export webu (export_web.py), ať se přegeneruje web.")


def main():
    if "--prejmenovat" in sys.argv:
        args = [a for a in sys.argv[1:] if a != "--nahled"]
        if len(args) != 4 or args[0] != "dokumenty" or args[2] != "--prejmenovat":
            sys.exit(__doc__)
        try:
            rename_document(ROOT, args[1], args[3], preview="--nahled" in sys.argv)
        except (OSError, ValueError) as e:
            sys.exit(f"Přejmenování se nezdařilo: {e}")
        return
    args = [a for a in sys.argv[1:] if a != "--sloucit"]
    sloucit = "--sloucit" in sys.argv
    if len(args) != 3 or args[0] not in {*SEZNAMY, *SLOVNIKY}:
        sys.exit(__doc__)
    nazev, klic, vstup = args
    path = os.path.join(ROOT, "data", nazev + ".json")
    try:
        obj = json.load(sys.stdin if vstup == "-" else open(vstup, encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        sys.exit(f"Vstup {vstup} není platný JSON: {e}")
    if not isinstance(obj, dict) and nazev not in LIBOVOLNE:
        sys.exit("Vstup musí být jeden objekt JSON ({…}).")
    if sloucit and not isinstance(obj, dict):
        sys.exit("--sloucit jde jen s objektem JSON ({…}).")
    seznam = nazev in SEZNAMY
    if seznam and obj.setdefault(SEZNAMY[nazev], klic) != klic:
        sys.exit(f"Klíč „{klic}“ nesedí s „{SEZNAMY[nazev]}“ ve vstupu („{obj[SEZNAMY[nazev]]}“).")
    text = open(path, encoding="utf-8-sig").read() if os.path.exists(path) else ""
    try:
        data = json.loads(text) if text.strip() else ([] if seznam else {})
        if not isinstance(data, list if seznam else dict):
            raise ValueError("čekal jsem " + ("seznam [ … ]" if seznam else "slovník { … }"))
    except ValueError as e:
        sys.exit(f"data/{nazev}.json nejde přečíst ({e}) – oprav ho nejdřív (git diff ukáže poslední změnu).")

    poz = polozky(text) if data else []
    if seznam:
        idx = next((n for n, x in enumerate(data) if isinstance(x, dict) and x.get(SEZNAMY[nazev]) == klic), None)
    else:
        idx = next((n for n, (k, _, _) in enumerate(poz) if k == klic), None)
    stare = None if idx is None else (data[idx] if seznam else data[klic])
    nove = {**stare, **obj} if sloucit and isinstance(stare, dict) else obj
    if not poz:   # prázdný nebo nový soubor
        text = json.dumps([nove] if seznam else {klic: nove}, ensure_ascii=False, indent=1) + "\n"
    elif idx is not None:   # nahradit jen text té jedné položky, zbytek souboru zůstane doslova
        _, s, e = poz[idx]
        text = text[:s] + jako(text, s, e, nove) + text[e:]
    else:   # přidat za poslední položku ve stejném stylu
        _, s, e = poz[-1]
        radek = text[text.rfind("\n", 0, s) + 1:s]
        odsazeni = radek[:len(radek) - len(radek.lstrip())]
        text = (text[:e] + ",\n" + odsazeni + ("" if seznam else json.dumps(klic, ensure_ascii=False) + ": ")
                + jako(text, s, e, nove) + text[e:])
    json.loads(text)   # pojistka: výsledek musí být platný JSON

    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)   # celý soubor naráz – při chybě nezůstane rozepsaný
    print(f"data/{nazev}.json: {'přidáno' if idx is None else 'změněno'} „{klic}“")


if __name__ == "__main__":
    main()
