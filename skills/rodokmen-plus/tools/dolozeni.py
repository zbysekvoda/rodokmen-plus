#!/usr/bin/env python3
"""Doložené vs. kontext v příbězích (reference/pribehy.md, „Doložené vs. kontext“). Volá ho kontrola.py.

Kauzální nebo účastnické spojení osoby s událostí („zemřel kvůli choleře“, „zúčastnil se bitvy“, „padl u…“)
musí mít v téže nebo sousední větě odkaz na zápis: wiki odkaz [[zdroj:…]], nebo zmínku pramene (matrika,
kronika, kmenový list, vojenský záznam…). Kontextové formulace („v těch letech“, „žil v době“) se nekontrolují.
"""
import re

EPIDEMIE = r"(?:choler\w*|tyf\w*|skvrnivk\w*|neštovic\w*|úplavic\w*|mor\b|moru\b|chřipk\w*|španělsk\w* chřipk\w*|epidemi\w*|záškrt\w*|spál\w*)"
SPOUSTE = re.compile(
    r"(?<![^\W\d_])(?:"
    r"kvůli|v\s+důsledku|následkem|"
    r"z?účastnil[aiy]?|"
    r"padl[aiy]?|"
    r"zemřel[aiy]?\s+(?:\w+\s+)?na\s+" + EPIDEMIE +
    r")(?![^\W\d_])", re.I)
ZDROJ = re.compile(
    r"\[\[zdroj:|(?<![^\W\d_])(?:matri\w*|kronik\w*|zápis\w*|záznam\w*|kmenov\w+\s+list\w*|"
    r"úmrtní\w*\s+list\w*|parte|odvodn\w*|voj(?:\.|ensk\w*)\s+(?:záznam|archiv)\w*|VÚA|VHA)", re.I)
VETY = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ\[\"„(])")


def nedolozena_spojeni(text):
    """Věty odstavce, kde je kauzální/účastnické spojení bez odkazu na zápis v té větě ani ve vedlejších."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    vety = [v for v in VETY.split(text) if v.strip()]
    return [v.strip() for i, v in enumerate(vety) if SPOUSTE.search(v)
            and not any(ZDROJ.search(x) for x in vety[max(0, i - 1):i + 2])]


def kontroluj(warn, soubory):
    """soubory: [(název, text)] – příběhy a zajímavosti. Přidá varování (ne chyby)."""
    for f, text in soubory:
        for odst in text.split("\n\n"):
            for v in nedolozena_spojeni(odst):
                m = SPOUSTE.search(v)
                vyrez = ("…" if m.start() > 60 else "") + v[max(0, m.start() - 60):m.end() + 60].strip() + ("…" if m.end() + 60 < len(v) else "")
                warn.append(f"data/{f}: „{vyrez}“ – kauzální/účastnické spojení s událostí bez odkazu na zápis; "
                            "doplň [[zdroj:…]] (matrika, kronika, voj. záznam), nebo přepiš jako kontext "
                            "(„v těch letech…“), viz reference/pribehy.md „Doložené vs. kontext“")
