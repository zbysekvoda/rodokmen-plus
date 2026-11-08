# Formát dat projektu

Všechna data jsou v `data/`. Web se z nich generuje (`npm run data`), nikdy needituj `web/src/data/site.json` ručně.
Po změnách spusť `python3 -I tools/kontrola.py`. Ukázku vyplněných dat má `SKILL_DIR/template/ukazka/`.
Položky do JSON souborů přidávej a měň přes `python3 -I tools/zapis.py` (zachová formát souboru, viz SKILL.md).

## `osoby.py` – předci
Kekulého čísla: 1 = výchozí osoba, otec osoby n = 2n, matka = 2n+1.
| číslo | kdo |
|---|---|
| 1 | výchozí osoba (u ženy `sex="F"`) |
| 2, 3 | otec, matka |
| 4–7 | prarodiče (4, 5 otcovi rodiče; 6, 7 matčini) |
| 8–15 | pradědečci a prababičky = obvykle **8 rodů** (`LINES`); rody smí být i v jiné generaci (např. 16–31, když je kořenem dítě), ale všechny v jedné |
| 16–31, 32–63 … | každá další generace dvojnásobek |

Otec předka 22 je 44, matka 45; dítě předka 45 je 22 (45 // 2). Muži mají sudá čísla.

```python
P = {
 8: dict(n="Jan Novák", y="1890–1944", st="doc",
         f=["* 14. 2. 1890 Holice čp. 112", "kovář", "× 20. 6. 1919 Holice Josefa Pokorná", "† 1944 Holice"],
         r=["holice_krest_jan_novak_1890", "holice_snatek_jan_novak_josefa_pokorna_1919"],
         note="Proč nejistota / rozpor / odkud údaj"),
 9: dict(n="Josefa Pokorná", y="* 1895", st="doc", f=[...], r=[...]),
 33: dict(n="otec neuveden", st="unk", f=[], note="Nemanželský syn; otec v matrice není."),
}
```
- `n` jméno (ženy rodným příjmením), `y` roky pro přehledy (`"* 1895"`, `"1890–1944"`, `"asi 1720–1785"`, `"1680 – před 1740"`,
  `"† 1940"` když známe jen úmrtí; nic nevíme → `""`).
- `f` fakta: začínají `*` (narození), `×` (sňatek), `†` (úmrtí) nebo jsou volný text (řemeslo, bydliště).
  Názvy obcí ve faktech používá mapa (`mista.json` → `re`).
- `r` klíče zápisů ze `zaznamy.json`. `st` viz `matriky.md`: `doc` přečteno v matrice, `prob` pravděpodobné,
  `fam` od rodiny (i strom, který si rodina vede sama, např. GEDCOM z jejího MyHeritage), `mh` cizí strom z internetu, `unk`.
- `LINES = {8: ("Novákové", "Kováři z Holic…"), …}` – všechna čísla v jedné generaci (obvykle 8–15); název rodu = příjmení v množném čísle.
- `vyz` (volitelné) – krátký popis, proč osoba vyčnívá; web ji ukáže nahoře na stránce „Osobnosti“ (`/osobnosti/`).
  Bez `vyz` ji tam zařadí `tools/osobnosti.py` podle slov ve faktech (farář, starosta, legionář…; sedlák a mistr ne).
  V datech webu `p.vyz` a `p.osobnost` (`{kat, poradi, fakt}` nebo `null`). Kontroluje `tools/kontrola.py` (musí být text).
- `SIDE` – sourozenci a další příbuzní: `dict(k=<číslo předka>, n="Josef Novák (1865–1920)", t="text", r=[klíče])`.
- `ISSUES` – dvojice `("Otázka", "Vyřešeno: … / Hypotéza: … / Otevřené: …")` → stránka „Co hledáme“ (vyřešené se skryjí).
  Jde na web – nepiš sem citlivé věci (příčiny úmrtí, rodinné spory) bez souhlasu.
- `HYPOTEZY` – `dict(rod=8, nadpis="…", text="…", polozky=[("jméno", "text")], zaznamy=[klíče])` → stránka rodu.
- `SAME = {350: 140}` – předek, který je v rodokmenu dvakrát (alias → hlavní číslo; alias v `P` může mít `f=["TÁŽ OSOBA jako 140"]`).

## `zaznamy.json` – zápisy
```json
[{"klic": "holice_krest_jan_novak_1890", "svazek": "1a0b2337", "snimek": 57, "druh": "N",
  "datum": "14. 2. 1890", "nazev": "Křest Jana Nováka",
  "shrnuti": "Jan, syn Václava Nováka, kováře v Holicích čp. 112, a Barbory roz. Malé z Ostřetína.",
  "odkaz": "https://aron.vychodoceskearchivy.cz/apu/…/dao/…/file/…"}]
```
- `klic`: malá písmena bez diakritiky, `obec_druh_kdo_rok` (druh: krest, snatek, umrti, index, scitani…). Je to i název obrázku.
- `druh`: N, O, Z, I (index/rejstřík), S (sčítání), J (jiný pramen).
- `datum` jako v češtině („14. 2. 1890“, „3/1867“, „1797“) – web podle něj řadí.

## `svazky.json`
`{"1a0b2337": {"archiv": "SOA Zámrsk – Sbírka matrik…", "portal": "ARON", "svazek": "N Holice 1880–1900, sign. …",
"popis": "obce", "url": "odkaz na svazek", "orientace": {…}}}` – u ARON zapisuje `aron_img.py <apu> svazek`.
- `orientace` (nepovinné, jen pro tebe a pomocníky, web ho neukazuje): rozvržení knihy ověřené na snímku –
  `{"popis": "N 1884–1891 po obcích; Cheznovice fol. 290–338; snímek ≈ fol + 3 (ověřeno fol. 290–338); rejstřík na konci",
  "roky": {"1884": 3, "1885": 41}}`. `roky` jsou kotvy rok → první snímek roku; `mapa_knihy.py rok <klíč> <rok>` z nich
  vrátí rozsah snímků. Posun snímek ↔ folio se v knize mění – každý zapiš s rozsahem, kde jsi ho ověřil. Starší
  textová `orientace` (řetězec) platí dál, jen z ní nejde skočit na rok.
  Jediné místo pravdy o rozvržení: svazek nejdřív zapiš nástrojem `… svazek` (ruční pole jako `orientace` nechá),
  pak doplň `zapis.py svazky <klíč> pracovni/x.json --sloucit` (v `x.json` jen `{"orientace": …}`); deník odkazuje sem.

## `prepisy.json`
`{"<klic>": {"orig": "[Datum] 14. února 1890\n[Dům] 112\n[Otec] …", "cs": "Český překlad celou větou…"}}`
- `orig` věrný přepis po sloupcích, `[Název sloupce]` v hranatých závorkách, nejisté „(?)“, nečitelné „[…]“, zkratky ponechat.
- `cs` srozumitelný překlad pro rodinu; vysvětli staré pojmy (domkář, podruh).

## `zvyrazneni.json`
`{"<klic>": {"boxes": [[x0, y0, x1, y1]], "status": "ok", "note": ""}}` – zlomky šířky/výšky obrázku `vyrezy/<klic>.jpg`.
Zapisuje `ramecek.py`. Rámeček má obepnout celý čtený zápis (ne jen jméno).

## `mista.json`
`{"Holice": {"re": "Holic", "dotaz": "Holice, Česko", "lat": 50.066, "lon": 15.986}}` – `re` je regulární výraz hledaný
ve faktech osob (kmen slova, aby sedělo skloňování: „Holic“ najde Holice i v Holicích). Spravuje `mista.py`.
Pozor na kolize (Hradec Králové × Nový Hradec Králové – použij `(?<!Nový )Hradec`; krátká jména jako `\bBuku?\b`).
Hypotéza: `"hypoteza": true, "rod": 8`. Když OpenStreetMap obec nenajde („Žár“, malé osady), zkus třetí parametr – dotaz: `mista.py pridej "Žár" "Žár" "Žár, Zdíkov, okres Prachatice"`
nebo dotaz s větší obcí či okresem. U **víceznačných názvů** (Podolí, Dub, Lhota) vezme OpenStreetMap kteroukoli ves
(„Podolí, Česko“ = Podolí u Brna) – v posledním sloupci výpisu zkontroluj okres a dej dotaz se sousední obcí
(`mista.py pridej "Podolí" "Podol" "Podolí, Odlochovice"`). Místopis nejlíp zná rodina – když si nejsi jistý, zeptej se.

## `dokumenty.json` – rodinné fotky a dokumenty na webu
`[{"img": "foto_svatba_1919", "popis": "Svatba Jana a Josefy, Holice 1919.", "osoby": [8, 9]}]`
Obrázek ulož přes `vyrez.py dokumenty/<sken>.jpg foto_svatba_1919` (vznikne `vyrezy/` i `zdroje/`).

### Portréty osob
Podle [xkraust/rodokmen-skill@79d3685](https://github.com/xkraust/rodokmen-skill/blob/79d36850afaa080b0ebcf70a368cbbb5237d700e/skills/rodokmen/reference/data.md).
Samostatnou fotku jedné osoby nabídni jako portrét; skupinová fotka, koláž ani tvář v dokumentu hotový portrét nejsou
(výřez domluv zvlášť). Identitu neodhaduj z obličeje – vezmi ji z evidence nebo se zeptej. Nabídka např.: „Na fotce
`IMG_1234.jpg` je jedna osoba. Chcete ji použít jako portrét na stránce Jana Nováka? Mezi dokumenty pak nebude.“
Možnosti: ano / nechat mezi dokumenty / odložit. Před souhlasem nic nepřejmenovávej ani nepřesouvej.

Po souhlasu oznam klíč a vytvoř webové kopie (originál v `dokumenty/` zůstane pod svým názvem):
```text
python3 -I tools/vyrez.py dokumenty/IMG_1234.jpg jan_novak_1890_portret
python3 -I tools/zapis.py dokumenty jan_novak_1890_portret pracovni/portret.json
```
`pracovni/portret.json`: `{"img": "jan_novak_1890_portret", "popis": "Jan Novák kolem roku 1920.", "osoby": ["jan-novak-1890"]}`.
Do `data/udaje_od_rodiny.md` zapiš datum, původní soubor, osobu, rozhodnutí a klíč.

Export (`export_web.py`) pozná portrét podle podřetězce `portret` v klíči `img` bez ohledu na diakritiku a velikost
písmen. Portrét musí mít právě jednu známou osobu, jinak ho přeskočí s varováním; na osobu bere první existující
v pořadí `dokumenty.json` a na další upozorní. Portréty se nezobrazují v galerii dokumentů ani u osoby mezi dokumenty.
Při odmítnutí použij klíč bez `portret`. **Osoba už portrét má:** nabídni ponechání, nebo nahrazení – starému pak
dej klíč bez `portret` (`vyrez.py` s novým klíčem a úprava položky přes `zapis.py`), vrátí se mezi dokumenty.

## `web.json` – nastavení webu
Viz `web.md`.

## Markdown poznámky
- `research_log.md` – tabulka `| # | datum | zdroj | rozsah | hledáno | výsledek | citace |`, nové řádky na konec, i negativní.
  Web ji zobrazuje jako „Výzkumný deník“.
- `zajimavosti.md` – `## Nadpis` + text, odkazy `[Jméno](/osoba/<slug>/)`.
- `pribeh.md` – „Příběh <hlavního rodu>“: frontmatter `title`, `lead` + kapitoly `##`; když soubor neexistuje,
  položka menu se skryje. Jak psát: `pribehy.md`.
- Poznámky pro Clauda v markdownu piš jako `<!-- … -->` – na web nejdou.
- `archivni_dotazy.md`, `udaje_od_rodiny.md` – volný text.

## Odkazy na osoby (slug)
Slug = jméno bez diakritiky + rok, např. `jan-novak-1890`; při kolizi přidá číslo osoby. Přesné slugy po `npm run data`
v `web/src/data/site.json` (`people`). Při přejmenování osoby se slug změní – oprav odkazy v textech.
