#!/usr/bin/env python3
"""Podklad pro nezávislý audit zápisu (druhý pohled): kontrola přepisu proti výřezu, jiné výklady, kde hledat dál.

Myšlenka „čtenář na levnějším modelu + nezávislý auditor“ převzata z
  https://github.com/jozefizso/rodokmen-skill/blob/38850a5aa4dbebe3faf1eb6ed5c5e8c9007c2d68/skills/rodokmen/tools/audit.py
  (autor Jozef Izso, verze 0.11; licence MIT – viz LICENSE). Tam audit spouští Codex; tady model nespouštíme:
  auditora pustí agent jako subagenta Claude (jiný model / effort, čistý kontext) – viz skill `paralelni-badani`.

Použití (z kořene projektu):
  python3 -I tools/audit.py zadani <klic> [<klic> …] [--kolo N] [--nazev JMENO]
      → pracovni/audit/<jmeno>_zadani.md: zápis ze zaznamy.json, přepis z prepisy.json, cesty k výřezům,
        osoby z grafu (data/osoby.py), které zápis dokládá, s rodiči, manželi a dětmi, kontrolní seznam
        a JSON schéma odpovědi. S --kolo N přidá hlášení čtenářů z pracovni/kolo_<N>/ a pom_*.
  python3 -I tools/audit.py nacti <odpoved.json|-> [--nazev JMENO]
      → zkontroluje odpověď auditora (JSON, smí být v ```json bloku), uloží pracovni/audit/<jmeno>.json
        a vypíše shrnutí: rozhodnutí, nesoulady, jiné výklady, kde hledat, úkoly.
  python3 -I tools/audit.py schema → JSON schéma odpovědi

Nástroj nic nevolá po síti a nemění data/ – výsledek auditu zapisuje do dat jen hlavní agent po vlastním ověření.
Návratový kód: 0 OK, 1 chyba (neznámý klíč, neplatná odpověď).
"""
import datetime, glob, json, os, re, sys

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import graf

ROOT = graf.ROOT
DATA = graf.DATA
PRACOVNI = os.path.join(ROOT, "pracovni")
AUDIT = os.path.join(PRACOVNI, "audit")

ROZHODNUTI = ["v_poradku", "opravit", "overit_znovu", "zeptat_se_uzivatele"]
ZAVAZNOST = ["chyba", "riziko", "poznamka"]

SCHEMA = {
    "type": "object",
    "required": ["rozhodnuti", "oduvodneni", "nesoulady", "jine_vyklady", "kde_hledat", "otazky_pro_uzivatele",
                 "overeno"],
    "properties": {
        "rozhodnuti": {"type": "string", "enum": ROZHODNUTI},
        "oduvodneni": {"type": "string"},
        "nesoulady": {"type": "array", "items": {
            "type": "object", "required": ["zavaznost", "kde", "problem", "dukaz", "navrh"],
            "properties": {"zavaznost": {"type": "string", "enum": ZAVAZNOST}, "kde": {"type": "string"},
                           "problem": {"type": "string"}, "dukaz": {"type": "string"}, "navrh": {"type": "string"}}}},
        "jine_vyklady": {"type": "array", "items": {
            "type": "object", "required": ["tvrzeni", "proc", "jak_overit"],
            "properties": {"tvrzeni": {"type": "string"}, "proc": {"type": "string"},
                           "jak_overit": {"type": "string"}}}},
        "kde_hledat": {"type": "array", "items": {
            "type": "object", "required": ["priorita", "pramen", "co_tam_najit", "proc"],
            "properties": {"priorita": {"type": "integer"}, "pramen": {"type": "string"},
                           "co_tam_najit": {"type": "string"}, "proc": {"type": "string"},
                           "odkaz": {"type": "string"}}}},
        "otazky_pro_uzivatele": {"type": "array", "items": {"type": "string"}},
        "overeno": {"type": "array", "items": {"type": "string"}},
    },
}

ZADANI = """\
# Nezávislý audit zápisu z matriky

Jsi nezávislý rodopisec (české matriky). Hlavní agent nebo čtenář na levnějším modelu přečetl zápis(y) níže
a zapsal je do dat. Ty jsi druhý pohled s čistým kontextem. Dva úkoly, stejně důležité:
**A) ověř přepis proti výřezu a proti datům**, **B) podívej se na výsledek jinak** a poraď, kde hledat dál.

## Pravidla
- Jen čtení. Nic neměň, nic nestahuj, na weby archivů nechoď. Smíš číst soubory projektu a spustit
  `python3 -I tools/graf.py osoba <id>` nebo `python3 -I tools/kontrola.py`.
- **Výřezy otevři a přečti sám** (nástroj Read na .jpg) dřív, než budeš číst přepis – ať tě neukotví.
  Do `overeno` napiš cesty výřezů, které jsi skutečně viděl. Chybí-li výřez, je to `riziko`.
- Nejisté čtení nehlas jako `chyba`, ale jako `riziko` a napiš, co přesně na výřezu vidíš.
- Ukázková data (příznak `ukazka`, vymyšlený zápis) nejsou chyba výzkumu – jen poznámka.
- Žijící lidé: nehledej je a nepiš o nich víc než jméno a rok narození.
- Piš česky, stručně, konkrétně (klíč zápisu, id osoby, pole).

## A) Kontrolní seznam
1. Přepis × výřez: jméno, datum (den, měsíc, rok), číslo popisné, obec, rodiče, kmotři/svědci, stav, povolání, věk.
2. Přepis × překlad (`orig` × `cs`) × `shrnuti` v zaznamy.json × fakta osob (`f`, `y`, `bydliste`): sedí čísla a jména?
3. Stav doložení: `doc` jen to, co je na výřezu; nejisté čtení („(?)“) nemá být podkladem pro `doc` fakt.
4. Logika: věk rodičů při narození (matka 15–50), věk při sňatku × rok narození, dítě po smrti rodiče,
   dvě rodiny stejného jména v obci, záměna generací (otec a syn stejného jména a domu).
5. Úplnost: má zápis svazek (`svazky.json`), výřez, přepis? Jsou kmotři/svědci ze zápisu v grafu nebo v hypotézách?

## B) Jiný pohled
- `jine_vyklady`: co data připouštějí jinak (jiná rodina stejného jména, jiné čtení obce/čp., přistěhování,
  nemanželský původ, chybně spojené zápisy) – u každého proč a čím ověřit.
- `kde_hledat`: konkrétní prameny (sousední farnosti, indexy, sčítání 1857/1869–1921, pozemkové knihy,
  soupisy poddaných, vojenské a domovské prameny, noviny), seřazené podle priority (1 = nejdřív).

## Rozhodnutí (`rozhodnuti`)
- `v_poradku` – žádná `chyba`.
- `opravit` – v datech je chyba opravitelná z toho, co už je přečtené (napiš návrh opravy).
- `overit_znovu` – údaj `doc` nesedí s výřezem nebo výřez chybí/je nečitelný: hlavní agent musí číst znovu.
- `zeptat_se_uzivatele` – rozhodnutí patří člověku (rozpor s rodinou, dvě stejně pravděpodobné osoby, soukromí).

Odpověz **jen JSON** podle schématu na konci (bez dalšího textu).
"""


def nacti_json(nazev, vychozi):
    try:
        return json.load(open(os.path.join(DATA, nazev), encoding="utf-8"))
    except FileNotFoundError:
        return vychozi


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def vyrezy(klic):
    return [rel(p) for d in ("vyrezy", "zdroje") for p in sorted(glob.glob(os.path.join(ROOT, d, glob.escape(klic) + ".*")))]


def popis_osoby(g, i):
    d = g.osoby[i]
    radky = [f"- `{i}` {d.get('n', '?')} ({d.get('sex', '?')}, {d.get('y', '')}, st={d.get('st', 'unk')})"]
    for k in ("f", "bydliste", "note"):
        if d.get(k):
            radky.append(f"  - {k}: {json.dumps(d[k], ensure_ascii=False)}")
    otec, matka = g.rodice(i)
    pribuzni = [("otec", otec), ("matka", matka)] + [("manžel(ka)", m) for m in g.manzele(i)] + \
               [("dítě", c) for c in g.deti(i)]
    for role, j in pribuzni:
        if j and j in g.osoby:
            o = g.osoby[j]
            radky.append(f"  - {role}: `{j}` {o.get('n', '?')} ({o.get('y', '')}, st={o.get('st', 'unk')})")
    for e in g.hrany(i):
        if e["t"] in ("kmotr", "svedek"):
            radky.append(f"  - hrana {e['t']}: {e['a']} → {e['b']}")
    return "\n".join(radky)


def hlaseni(kolo):
    dirs = [os.path.join(PRACOVNI, f"kolo_{kolo}")] + sorted(glob.glob(os.path.join(PRACOVNI, "pom_*")))
    out = []
    for d in dirs:
        for base, _, files in os.walk(d):
            out += [rel(os.path.join(base, f)) for f in sorted(files) if f.lower().endswith((".md", ".txt", ".json"))]
    return out


def sestav(klice, kolo=None):
    zaznamy = {z.get("klic"): z for z in nacti_json("zaznamy.json", [])}
    prepisy = nacti_json("prepisy.json", {})
    svazky = nacti_json("svazky.json", {})
    g = graf.nacti()
    nezname = [k for k in klice if k not in zaznamy]
    if nezname:
        sys.exit(f"Klíč není v data/zaznamy.json: {', '.join(nezname)}")
    casti = [ZADANI]
    for k in klice:
        z = zaznamy[k]
        casti.append(f"\n## Zápis `{k}`\n```json\n{json.dumps(z, ensure_ascii=False, indent=1)}\n```\n")
        sv = svazky.get(z.get("svazek")) if isinstance(svazky, dict) else None
        casti.append(f"Svazek `{z.get('svazek')}`: " + (json.dumps(sv, ensure_ascii=False) if sv else
                     "**není v svazky.json**") + "\n")
        p = prepisy.get(k)
        casti.append("\n### Přepis (prepisy.json)\n" + (f"orig:\n```\n{p.get('orig', '')}\n```\ncs: {p.get('cs', '')}\n"
                     if p else "**Přepis chybí.**\n"))
        v = vyrezy(k)
        casti.append("\n### Výřezy – otevři je\n" + ("\n".join(f"- `{x}`" for x in v) if v else "**Výřez nenalezen.**") + "\n")
        osoby = [i for i, d in g.osoby.items() if k in d.get("r", [])]
        hrany = [e for e in g.vztahy if k in e.get("r", [])]
        casti.append("\n### Osoby z grafu, které zápis dokládá\n" + ("\n".join(popis_osoby(g, i) for i in osoby)
                     or "Žádná osoba nemá tento klíč v `r`.") + "\n")
        if hrany:
            casti.append("Hrany s tímto zdrojem: " + "; ".join(f"{e['t']} {e['a']}→{e['b']}" for e in hrany) + "\n")
    if kolo is not None:
        h = hlaseni(kolo)
        casti.append(f"\n## Hlášení čtenářů (kolo {kolo}) – přečti je\n" + ("\n".join(f"- `{x}`" for x in h)
                     or "- žádná hlášení") + "\n")
    casti.append("\n## Schéma odpovědi\n```json\n" + json.dumps(SCHEMA, ensure_ascii=False, indent=1) + "\n```\n")
    return "".join(casti)


def platny(v):
    """→ seznam chyb odpovědi (prázdný = platná)."""
    if not isinstance(v, dict):
        return ["odpověď není JSON objekt"]
    err = [f"chybí pole {k}" for k in SCHEMA["required"] if k not in v]
    if v.get("rozhodnuti") not in ROZHODNUTI:
        err.append(f"rozhodnuti musí být jedno z {ROZHODNUTI}")
    for k in ("nesoulady", "jine_vyklady", "kde_hledat", "otazky_pro_uzivatele", "overeno"):
        if k in v and not isinstance(v[k], list):
            err.append(f"{k} musí být seznam")
    for n in v.get("nesoulady", []) if isinstance(v.get("nesoulady"), list) else []:
        if not isinstance(n, dict) or n.get("zavaznost") not in ZAVAZNOST:
            err.append(f"nesoulad bez platné závažnosti: {n}")
    return err


def parsuj(text):
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    s = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1]
    return json.loads(s)


def shrnuti(v):
    print(f"Rozhodnutí auditora: {v['rozhodnuti']}\n  {v['oduvodneni']}")
    for z in ZAVAZNOST:
        n = [x for x in v["nesoulady"] if x["zavaznost"] == z]
        if n:
            print(f"\n{z.upper()} ({len(n)}):")
            for x in n:
                print(f"  - [{x.get('kde', '')}] {x.get('problem', '')}\n      důkaz: {x.get('dukaz', '')}"
                      f"\n      návrh: {x.get('navrh', '')}")
    if v["jine_vyklady"]:
        print("\nJiné výklady:")
        for h in v["jine_vyklady"]:
            print(f"  - {h.get('tvrzeni', '')}\n      proč: {h.get('proc', '')}\n      ověřit: {h.get('jak_overit', '')}")
    if v["kde_hledat"]:
        print("\nKde hledat:")
        for k in sorted(v["kde_hledat"], key=lambda k: k.get("priorita", 99)):
            print(f"  {k.get('priorita', '?')}. {k.get('pramen', '')}: {k.get('co_tam_najit', '')} – {k.get('proc', '')}"
                  + (f"\n      {k['odkaz']}" if k.get("odkaz") else ""))
    if v["otazky_pro_uzivatele"]:
        print("\nOtázky pro uživatele:")
        for q in v["otazky_pro_uzivatele"]:
            print(f"  - {q}")
    print(f"\nAuditor viděl výřezy: {', '.join(v['overeno']) or 'žádné'}")


def arg(name):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 >= len(sys.argv):
            sys.exit(f"Chybí hodnota za {name}.")
        hodnota = sys.argv[i + 1]
        del sys.argv[i:i + 2]
        return hodnota
    return None


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    kolo, nazev = arg("--kolo"), arg("--nazev")
    if kolo is not None and not kolo.isdigit():
        sys.exit(f"--kolo čeká číslo, ne „{kolo}“.")
    prikaz, rest = sys.argv[1], sys.argv[2:]
    if prikaz == "schema":
        print(json.dumps(SCHEMA, ensure_ascii=False, indent=1))
        return 0
    if prikaz == "zadani" and rest:
        text = sestav(rest, int(kolo) if kolo is not None else None)
        os.makedirs(AUDIT, exist_ok=True)
        jmeno = nazev or (rest[0] if len(rest) == 1 else f"kolo_{kolo}" if kolo else rest[0] + f"_a_{len(rest) - 1}")
        p = os.path.join(AUDIT, f"{jmeno}_zadani.md")
        open(p, "w", encoding="utf-8").write(text)
        print(f"Zadání auditu: {rel(p)}\nDej ho subagentovi s čistým kontextem (jen čtení) a jeho odpověď načti:\n"
              f"  python3 -I tools/audit.py nacti <odpoved.json> --nazev {jmeno}")
        return 0
    if prikaz == "nacti" and len(rest) == 1:
        text = sys.stdin.read() if rest[0] == "-" else open(rest[0], encoding="utf-8").read()
        try:
            v = parsuj(text)
        except ValueError as e:
            print(f"Odpověď auditora není platný JSON: {e}")
            return 1
        err = platny(v)
        if err:
            print("Neplatná odpověď auditora:\n  " + "\n  ".join(err))
            return 1
        v["cas"] = datetime.datetime.now().isoformat(timespec="seconds")
        os.makedirs(AUDIT, exist_ok=True)
        jmeno = nazev or (os.path.splitext(os.path.basename(rest[0]))[0] if rest[0] != "-" else "audit")
        out = os.path.join(AUDIT, f"{jmeno}.json")
        json.dump(v, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        shrnuti(v)
        print(f"\nUloženo: {rel(out)}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
