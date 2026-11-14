#!/usr/bin/env python3
"""Volitelné strojové čtení výřezu zápisu multimodálním modelem přes OpenRouter (druhý názor, ne náhrada čtení).

Použití:
  cteni_ai.py <klíč zápisu | cesta k výřezu.jpg> [--model gemini|gemini-pro|fable|<openrouter-id>]
              [--jazyk la|de|cs] [--kontext "…"] [--zapsat] [--souhlas] [--max-usd 1]

Výsledek je JSON na stdout; s --zapsat i pracovni/cteni_ai/<klíč>_<model>.json. Do data/prepisy.json nikdy nepíše:
přepis převezmi až po ověření na výřezu a do přepisu přidej "stroj": "<model>, nepotvrzeno" (kontrola.py ho hlásí).

Klíč: proměnná OPENROUTER_API_KEY, jinak soubor ~/.config/rodokmen/openrouter.key. Nikdy ne do složky projektu.
Bez klíče nástroj jen oznámí, jak ho zadat, a skončí kódem 3. Postup a rizika: docs/navrhy/ocr-openrouter.md.
"""
import base64, json, os, re, sys, time, urllib.error, urllib.request
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = os.environ.get("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
SOUBOR_KLICE = os.path.expanduser("~/.config/rodokmen/openrouter.key")
MODELY = {"gemini": "google/gemini-2.5-flash", "gemini-pro": "google/gemini-2.5-pro", "fable": "anthropic/claude-fable-5.1"}
LHUTY = {"N": 100, "O": 75, "Z": 75, "S": 75}   # narození 100 let, sňatek/úmrtí 75 let
JAZYKY = {"la": "latinsky", "de": "německy", "cs": "česky"}
CHYBI_KLIC = 3

PROMPT = """Jsi paleograf. Na obrázku je výřez zápisu z historické matriky nebo knihy ({jazyk}, kurent/latinka).
Přepiš text věrně (diplomaticky, zachovej zkratky) a přelož ho do češtiny. Nehádej: nejisté čtení označ „(?)“,
nečitelné místo „[…]“. Nedoplňuj jména podle pravděpodobnosti. {kontext}
Odpověz jen JSON: {{"prepis": "…", "preklad": "…", "nejista_mista": ["…"]}}"""


def najdi_klic():
    k = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not k and os.path.exists(SOUBOR_KLICE):
        with open(SOUBOR_KLICE, encoding="utf-8") as f:
            k = f.read().strip()
    return k


def klic_v_projektu(root):
    """Najde soubory projektu s klíčem OpenRouteru (sk-or-…); jen textové soubory mimo node_modules a .git."""
    nalezy = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in (".git", "node_modules", "zdroje", "vyrezy", "pracovni", "dist")]
        for fn in files:
            if fn.endswith((".jpg", ".png", ".pdf", ".tif", ".jpeg", ".webp")):
                continue
            p = os.path.join(d, fn)
            try:
                with open(p, encoding="utf-8", errors="ignore") as f:
                    if re.search(r"sk-or-[A-Za-z0-9-]{10,}", f.read()):
                        nalezy.append(os.path.relpath(p, root))
            except OSError:
                pass
    return nalezy


def rok(datum):
    m = re.search(r"\d{4}", str(datum or ""))
    return int(m.group()) if m else None


def lhuta_vadi(zapis, letos):
    """Vrátí důvod, proč zápis nejde bez souhlasu poslat ven (mladší než lhůta), jinak None."""
    r, lhuta = rok(zapis.get("datum")), LHUTY.get(str(zapis.get("druh", ""))[:1].upper(), 75)
    if r is None:
        return "zápis nemá rok, nelze ověřit lhůtu"
    if letos - r < lhuta:
        return f"zápis z roku {r} je mladší než {lhuta} let"
    return None


def nacti_zaznam(klic):
    p = os.path.join(ROOT, "data", "zaznamy.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return next((z for z in json.load(f) if z.get("klic") == klic), None)


def zavolej(klic_api, model, obrazek, prompt, max_usd):
    with open(obrazek, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    telo = {"model": model, "temperature": 0, "usage": {"include": True},
            "provider": {"data_collection": "deny"},
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}]}]}
    req = urllib.request.Request(URL, data=json.dumps(telo).encode(), headers={
        "Authorization": "Bearer " + klic_api, "Content-Type": "application/json",
        "X-Title": "rodokmen-plus"})
    with urllib.request.urlopen(req, timeout=180) as r:
        odp = json.load(r)
    text = odp["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", text, re.S)
    data = json.loads(m.group()) if m else {"prepis": text, "preklad": "", "nejista_mista": []}
    cena = (odp.get("usage") or {}).get("cost")
    if cena is not None and cena > max_usd:
        print(f"Pozor: cena {cena} USD překročila strop {max_usd} USD.", file=sys.stderr)
    return {"model": model, "prepis": data.get("prepis", ""), "preklad": data.get("preklad", ""),
            "nejista_mista": data.get("nejista_mista", []), "cena_usd": cena,
            "stav": "strojové čtení – ověřit na výřezu"}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cil")
    ap.add_argument("--model", default="gemini")
    ap.add_argument("--jazyk", choices=list(JAZYKY), default="la")
    ap.add_argument("--kontext", default="")
    ap.add_argument("--zapsat", action="store_true")
    ap.add_argument("--souhlas", action="store_true", help="poslat i zápis mladší než lhůta (uživatel souhlasil)")
    ap.add_argument("--max-usd", type=float, default=1.0)
    a = ap.parse_args(argv)

    klic_api = najdi_klic()
    if not klic_api:
        print("Strojové čtení je volitelné a chybí klíč OpenRouteru. Uživatel ho zadá sám v terminálu "
              "(ne do konverzace): export OPENROUTER_API_KEY=… nebo soubor ~/.config/rodokmen/openrouter.key "
              "(chmod 600). Bez klíče pokračuj čtením jako obvykle.", file=sys.stderr)
        return CHYBI_KLIC
    if os.path.exists(os.path.join(ROOT, "data", "STAV.md")):
        v_projektu = klic_v_projektu(ROOT)
        if v_projektu:
            print("Klíč OpenRouteru je uložený ve složce projektu (" + ", ".join(v_projektu) +
                  "). Přesuň ho do ~/.config/rodokmen/openrouter.key a z projektu ho smaž.", file=sys.stderr)
            return 2

    if os.path.exists(a.cil):
        obrazek, klic = a.cil, os.path.splitext(os.path.basename(a.cil))[0]
    else:
        klic, obrazek = a.cil, os.path.join(ROOT, "zdroje", a.cil + ".jpg")
        if not os.path.exists(obrazek):
            obrazek = os.path.join(ROOT, "vyrezy", a.cil + ".jpg")
    if not os.path.exists(obrazek):
        print(f"Výřez {a.cil} nenalezen (zdroje/ ani vyrezy/).", file=sys.stderr)
        return 1
    if "dokumenty" in os.path.normpath(os.path.abspath(obrazek)).split(os.sep):
        print("Rodinné dokumenty se ven neposílají.", file=sys.stderr)
        return 2
    zapis = nacti_zaznam(klic)
    if not a.souhlas:
        duvod = lhuta_vadi(zapis, time.localtime().tm_year) if zapis else "výřez není zápis v zaznamy.json, nelze ověřit lhůtu"
        if duvod:
            print(f"Neposláno: {duvod}. Poslat jen se souhlasem uživatele (--souhlas).", file=sys.stderr)
            return 2

    model = MODELY.get(a.model, a.model)
    kontext = f"Kontext: {a.kontext}" if a.kontext else ""
    try:
        vysl = zavolej(klic_api, model, obrazek, PROMPT.format(jazyk=JAZYKY[a.jazyk], kontext=kontext), a.max_usd)
    except (urllib.error.URLError, OSError, KeyError, ValueError) as e:
        print(f"OpenRouter selhal ({e}); pokračuj bez strojového čtení.", file=sys.stderr)
        return 1
    vysl["klic"] = klic
    out = json.dumps(vysl, ensure_ascii=False, indent=1)
    print(out)
    if a.zapsat:
        d = os.path.join(ROOT, "pracovni", "cteni_ai")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"{klic}_{model.replace('/', '_')}.json"), "w", encoding="utf-8") as f:
            f.write(out + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
