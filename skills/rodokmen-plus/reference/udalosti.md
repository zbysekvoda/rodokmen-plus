# Historický kontext – regionální události projektu (data/udalosti.json)

Osa pluginu (`tools/udalosti.json`) nese jen celostátní a zemské události 1620–1990. Co se stalo **v obci,
farnosti nebo regionu předků** (požár, povodeň, mor, průchod vojsk, odvody, stavba kostela, oddělení farnosti),
zapisuj do projektové vrstvy `data/udalosti.json`. Nový projekt ji dostane prázdnou (`[]`) ze šablony.
Čte ji `tools/udalosti.py` (`rok`, `rozsah`, `osoba`) i `tools/napady.py`; kontroluje `tools/kontrola.py`.

## Formát

Pole položek se **stejnými poli jako osa pluginu**:

```json
[
  {
    "id": "1834-pozar-dolni-ves",
    "od": "1834-04-12",
    "do": "1834-04-12",
    "uroven": "obec",
    "kde": ["dolni-ves"],
    "kategorie": "zivel",
    "nazev": "Velký požár obce",
    "text": "Oheň od kovárny zničil 23 z 41 domů a faru. Farní kronika uvádí dva mrtvé.",
    "dopad": {"umrti": true, "vojaci": false},
    "zdroj": "Farní kronika Dolní Ves 1780–1880, fol. 54r (SOA …, fond Farní úřad Dolní Ves, inv. č. 1)",
    "jistota": "doc"
  }
]
```

(Příklad je vymyšlený, jen ukazuje tvar – do pluginu nepatří žádná skutečná rodinná ani obecní data.)

| pole | povinné | význam |
|---|---|---|
| `id` | ano | `RRRR-kratky-popis` (malá písmena, číslice, pomlčky). **Stejné id jako v ose pluginu ji přebije** – tak opravíš nebo zpřesníš celostátní položku pro svůj region (např. lokální průběh cholery 1866). Jinak volit unikátní id. |
| `od`, `do` | ano | `RRRR`, `RRRR-MM` nebo `RRRR-MM-DD`; `od` ≤ `do`. Jednodenní událost má obě stejné. |
| `nazev` | ano | krátký název |
| `kategorie` | ano | jedna z kategorií osy: `valka`, `epidemie`, `hlad`, `zivel`, `reforma`, `sprava`, `mena`, `rezim`, `povstani`, `hospodarstvi`, `migrace`, `cirkev` |
| `zdroj` | **ano** | konkrétní pramen: kronika + svazek + folio/strana + archiv a fond, nebo kniha + strana. Bez zdroje položku nezapisuj. |
| `uroven` | ne | `obec` / `farnost` / `region`; `cr` jen při přebití celostátní položky |
| `kde` | ne | klíče z `data/mista.json` – podle nich filtruje `udalosti.py --misto` |
| `text` | ne | 1–3 věty, co se stalo a jaký to mělo dopad na obyvatele |
| `dopad` | ne | `{"umrti": bool, "vojaci": bool}` – `umrti` zapíná srovnání se shluky úmrtí v `napady.py` |
| `jistota` | ne | `doc` (přímo z pramene), `lit` (z literatury), `obecne` (obecný odhad) |

Ověření: `python3 tools/kontrola.py` hlásí neplatný JSON, chybějící povinné pole, neznámou kategorii,
duplicitní id a `od` po `do`. Chybějící soubor chybou není.

## Odkud regionální události brát

- **Obecní a farní kroniky** (SOA/SOkA, digitalizované na portálech archivů – `reference/portaly.md`):
  nejlepší zdroj požárů, povodní, neúrody, epidemií, průchodů vojsk a válečných ztrát obce. Farní kronika
  (Memorabilienbuch, Liber memorabilium) bývá starší než obecní (ta povinně od 1920). Zapisuj folio/stranu,
  `jistota: "doc"`. Úmrtní matrika ve stejném roce je dobrá kontrola (shluk úmrtí, poznámky faráře).
- **NDK – Národní digitální knihovna** (ndk.cz, Kramerius): regionální vlastivědy, sborníky, místopisy,
  dobové noviny (zprávy o požárech a povodních). Cituj titul, rok, stranu a ideálně uuid stránky.
- **Gregor Wolny: Die Markgrafschaft Mähren** (1835–1842, 6 svazků po krajích) a **Kirchliche Topographie
  von Mähren** (1855–1863): ke každé moravské obci vrchnost, fara, počty domů a obyvatel, často požáry,
  morové roky a stavby kostelů. Online v NDK / Google Books. Cituj díl, kraj a stranu; `jistota: "lit"`.
- **Ladislav Hosák: Historický místopis země Moravskoslezské** (1938) a pro Čechy obdobně Sedláček (Hrady,
  zámky a tvrze), Profous (Místní jména): první zmínky, změny vrchností, zaniklé obce. Cituj stranu.
- Lexikony obcí a statistiky (Retrospektivní lexikon obcí, sčítání) – dopad změn správy na obec
  (`kategorie: "sprava"`).

Zásady: jedna událost = jedna položka; nevymýšlej data ani počty, které pramen neuvádí; když se prameny
liší, uveď oba ve `zdroj` a rozdíl v `text`. Kauzalitu k osobám (zemřel *kvůli* epidemii) z osy
nevyvozuj – to musí stát v matrice nebo jiném pramenu.

## Státní útvar místa (tools/staty.json)

`udalosti.py stat <rok> --misto X` a výpis `osoba` řeknou, v jakém státě místo leželo (Habsburská monarchie →
Rakouské císařství → Rakousko-Uhersko → ČSR → Protektorát → … → ČR), před rokem 1918 i s korunní zemí.
Místo mimo hlavní linii označ v `data/mista.json` polem `"oblast"`: `hlucinsko` (Prusko 1742–1920),
`sudety` (Německá říše 1938–45), `zaolzi` (Polsko 1938–39), `valticko` a `vitorazsko` (Dolní Rakousy do 31. 7. 1920, Německá říše 1938–45).
Osoba s více bydlišti (`bydliste[]` s `od`/`do`) dostane státy postupně podle nich. Jiné výjimky zapiš do
`data/staty.json` ve stejném formátu s vlastní oblastí v `kde`. I stát je kontext, ne fakt ze zápisu.
