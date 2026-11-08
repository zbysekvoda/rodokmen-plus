#!/usr/bin/env python3
"""Síť kmotrů a svědků jako stopy: kdo se opakuje u více zápisů (kmotři bývali příbuzní).

Převzato a přepsáno na graf (data/osoby.py: OSOBY, VZTAHY) z
  https://github.com/srameko/rodokmen-skill/blob/5f25edb9a201f8ac03b79293bbcb79b5109d022e/skills/rodokmen/tools/kmotri.py
  (autor srameko; původně z https://github.com/micl79/rodokmen-skill/blob/11cf9bad06c454f8415625a23a7b9e49d13c75e3/skills/rodokmen/tools/kmotri.py,
  autor micl79; licence MIT – viz LICENSE).

Použití (z kořene projektu):  python3 -I tools/kmotri.py [--min N]  -> výpis + pracovni/kmotri.md
Dva zdroje:
  1. graf – hrany t="kmotr" (a=kmotr, b=křtěnec) a t="svedek" (a=svědek, b=ženich/nevěsta) ve VZTAHY;
     u každého kmotra/svědka vypíše, u koho stál, a jestli je s ním v grafu pokrevně spřízněný.
  2. text – z `shrnuti` v data/zaznamy.json vezme část za slovem Kmotr/Svědek/Družba/Porodní bába
     (do konce věty) a vytáhne jména „Jméno Příjmení“. Příjmení sjedná na mužský tvar (-ová → -).
Vypíše příjmení, která se objeví u ≥ N zápisů/osob (výchozí 2) – kandidáti na příbuzné, které stojí za dohledání.
"""
import json, os, re, sys
from collections import defaultdict

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import graf

VELKE = "A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"
MALE = "a-záčďéěíňóřšťúůýž"
JMENO = re.compile(rf"\b([{VELKE}][{MALE}]+)\s+(?:roz\.\s+)?([{VELKE}][{MALE}]+)")
ROLE = re.compile(r"(Kmotr\w*|kmotr\w*|Svěd\w*|svěd\w*|Družb\w*|družb\w*|Porodní bab\w*|porodní bab\w*)[^.]*", re.S)
KRESTNI = set("Josef Jan Václav Tomáš Vojtěch Jakub Matěj František Jiří Martin Ludmila Anna Marie Marianna Kateřina "
              "Barbora Dorota Alžběta Rozálie Rosalie Magdalena Karel Antonín Ondřej Pavel Petr Matouš Šimon Vít Lukáš "
              "Mikuláš Kristián Adam Eva Terezie Veronika Johana Josefa Františka Markéta Ignác Bernard Augustin Leopold "
              "Filip Prokop Bartoloměj Řehoř Štěpán Emanuel Wenzel Joseph Johann".split())
NEJMENA = {"Horní", "Dolní", "Nový", "Nové", "Malá", "Velká", "Svatý", "Panna", "Čteno", "Ověřeno"}
ROLE_HRANY = {"kmotr": "kmotr", "svedek": "svědek"}


def zaklad(p):
    for a, b in (("ová", ""), ("á", "ý")):
        if p.endswith(a) and len(p) > 4:
            return p[: -len(a)] + b
    return p


def prijmeni(n):
    slova = [s for s in re.sub(r"\(.*?\)", "", n).split() if s[:1].isupper()]
    return zaklad(slova[-1]) if len(slova) >= 2 else None


def z_grafu(g):
    """→ [(kmotr_id, role, osoba_id, příbuzný: bool, datum, r)] z hran kmotr/svedek."""
    out = []
    for e in g.vztahy:
        if e["t"] in ROLE_HRANY and e["a"] in g.osoby and e["b"] in g.osoby:
            a, b = e["a"], e["b"]
            pa, pb = set(g.predci(a)) | {a}, set(g.predci(b)) | {b}
            out.append((a, ROLE_HRANY[e["t"]], b, bool(pa & pb), e.get("datum", ""), e.get("r", [])))
    return out


def z_textu(path):
    """→ {příjmení: [(klíč zápisu, „Jméno Příjmení“, role)]} ze shrnutí zápisů."""
    try:
        with open(path, encoding="utf-8") as fh:
            Z = json.load(fh)
    except FileNotFoundError:
        return {}
    except ValueError as e:
        sys.exit(f"{path}: neplatný JSON ({e})")
    Z = Z if isinstance(Z, list) else list(Z.values())
    vyskyt = defaultdict(list)
    for z in Z:
        if not isinstance(z, dict) or "klic" not in z:
            continue
        for m in ROLE.finditer(z.get("shrnuti", "")):
            usek = m.group(0)[len(m.group(1)):]   # jména až za slovem Kmotr/Svědek
            for j, p in JMENO.findall(usek):
                if j in NEJMENA or p in NEJMENA or p in KRESTNI:
                    continue
                vyskyt[zaklad(p)].append((z["klic"], f"{j} {p}", m.group(1).lower()[:6]))
    return vyskyt


def main():
    mn = 2
    if "--min" in sys.argv:
        try:
            mn = int(sys.argv[sys.argv.index("--min") + 1])
        except (IndexError, ValueError):
            sys.exit("--min potřebuje číslo")
    g = graf.nacti()
    jm = lambda i: g.osoby[i].get("n", i)
    hrany = z_grafu(g)
    text = z_textu(os.path.join(graf.DATA, "zaznamy.json"))

    # spojit podle příjmení: graf (osoby) + text (zápisy)
    podle = defaultdict(lambda: dict(graf=[], text=[]))
    for h in hrany:
        p = prijmeni(jm(h[0]))
        if p:
            podle[p]["graf"].append(h)
    for p, v in text.items():
        podle[p]["text"].extend(v)
    def vaha(v):
        return len({h[2] for h in v["graf"]}) + len({k for k, _, _ in v["text"]})
    rad = sorted(((p, v) for p, v in podle.items() if vaha(v) >= mn), key=lambda x: (-vaha(x[1]), x[0]))

    out = ["# Síť kmotrů a svědků (tools/kmotri.py)", "", "## Kmotři a svědci v grafu", ""]
    po_kmotrech = defaultdict(list)
    for h in hrany:
        po_kmotrech[h[0]].append(h)
    for a, hs in sorted(po_kmotrech.items(), key=lambda x: -len(x[1])):
        out.append(f"- **{jm(a)}** ({a}) – " + "; ".join(
            f"{r} u {jm(b)}{' ' + d if d else ''}{' – příbuzný' if pr else ''}" for _, r, b, pr, d, _ in hs))
    if not hrany:
        out.append("(žádné hrany kmotr/svedek)")
    out += ["", f"## Příjmení u ≥ {mn} zápisů/osob", ""]
    for p, v in rad:
        out.append(f"### {p} – {vaha(v)}")
        out += [f"- {jm(a)} ({r} u {jm(b)}) – graf" for a, r, b, _, _, _ in v["graf"]]
        out += [f"- {kdo} ({r}) – {k}" for k, kdo, r in v["text"]]
        out.append("")
    os.makedirs("pracovni", exist_ok=True)
    with open(os.path.join("pracovni", "kmotri.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")

    print(f"Kmotři/svědci v grafu: {len(po_kmotrech)} osob, {len(hrany)} hran")
    for a, hs in sorted(po_kmotrech.items(), key=lambda x: -len(x[1]))[:20]:
        print(f"  {jm(a)}: " + "; ".join(f"{r} u {jm(b)}{' (příbuzný)' if pr else ''}" for _, r, b, pr, _, _ in hs))
    print(f"{len(rad)} příjmení u ≥ {mn} zápisů/osob; pracovni/kmotri.md")
    for p, v in rad[:40]:
        print(f"  {p} {vaha(v)}: " + ", ".join(sorted({jm(h[2]) for h in v["graf"]} | {k for k, _, _ in v["text"]})))


if __name__ == "__main__":
    main()
