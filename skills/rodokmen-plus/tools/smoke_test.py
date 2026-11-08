#!/usr/bin/env python3
"""Smoke test portálů: krátce projde stávající síťové nástroje proti živým portálům a vypíše OK/FAIL po portálech.

Nápad a tvar výstupu převzaty z forků (MIT):
  https://github.com/hnizdiljan/rodokmen-skill/blob/d172316bc190d0f44894fa67115505729d587c6a/skills/rodokmen/tools/smoke_test.py
  https://github.com/srameko/rodokmen-skill/blob/5f25edb9a201f8ac03b79293bbcb79b5109d022e/skills/rodokmen/tools/smoke_test.py
Tady je to tenký obal nad zdravi.py --rychle (bez stahování snímků), takže kontroly (pevné svazky, očekávaný výstup)
jsou na jednom místě. Každý nástroj jde přes brzdu slusne.py – pouštěj ručně, ne ve smyčce ani z pomocníků.

Použití:
  smoke_test.py                  všechny portály, jen dotazy (~1–2 min)
  smoke_test.py trebon aron      jen vybrané portály
  smoke_test.py --plny           včetně stahování jednoho snímku od portálu
Návratový kód 1 = aspoň jeden portál FAIL.
"""
import os, re, subprocess, sys
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ZDRAVI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zdravi.py")


def main(args):
    if "-h" in args or "--help" in args:
        sys.exit(__doc__)
    cmd = [sys.executable, "-I", "-X", "utf8", ZDRAVI]
    if "--plny" not in args:
        cmd.append("--rychle")
    portaly = [a for a in args if not a.startswith("-")]
    if portaly:
        cmd += ["--jen", ",".join(portaly)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    vysledky, detail, posledni = {}, {}, None
    for radek in p.stdout.splitlines():
        m = re.match(r"(OK|CHYBA)\s+(\S+)\s+(.*)", radek)
        if m:
            posledni = m.group(2)
            ok = m.group(1) == "OK"
            vysledky[posledni] = vysledky.get(posledni, True) and ok
            if not ok:
                detail.setdefault(posledni, []).append(m.group(3).strip())
        elif radek.startswith("       ") and posledni and not vysledky.get(posledni, True):
            detail.setdefault(posledni, []).append("  " + radek.strip()[:160])
    if not vysledky:   # zdravi.py skončil dřív (neznámý portál, chyba) – ukázat proč
        sys.exit((p.stdout + p.stderr).strip() or f"zdravi.py skončil s kódem {p.returncode}")
    for portal, ok in vysledky.items():
        print(f"{'OK  ' if ok else 'FAIL'} {portal}")
        for r in detail.get(portal, []):
            print("     ", r)
    fail = sum(not ok for ok in vysledky.values())
    print(f"\n{len(vysledky) - fail}/{len(vysledky)} portálů OK")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
