# Changelog

## Nevydáno

### Opraveno
- `staty.json`: revize dat a zdrojů – Slezsko v Rakouském císařství jako „Rakouské Slezsko (od 1849 Vévodství Horní
  a Dolní Slezsko)“, neexistující citace u ČSSR nahrazena ústavním zákonem č. 100/1960 Sb., u ČSFR doplněn zákon
  č. 101/1990 Sb. a mezidobí „Československá federativní republika“, opravený titul Plačkových *Prajzáků*,
  upřesněné texty k Vratislavskému míru (1742) a připojení Zaolzí k Říši (1939).

### Změněno
- Web: pohled Rody u Stromu se jmenuje „Pásy rodů“ (přepínač i nadpis `/pasy/`). Prázdné sloupce prarodičů
  a prázdné řádky generací se nevykreslují, chybějící rody nahradí věta s odkazem na Co hledáme; když zbydou
  méně než dva pásy (kořen doložený jen z jedné strany), pásy se rozpadnou o generaci výš.
- Web: přepínač pohledů u Stromu (`ViewSwitch.astro`) ukazuje jen hlavní pohledy – Generace, Rody, Vějíř, Celý strom
  a Seznam předků (dřív „Předci“); Vějíř v čase a Řeka času jsou schované pod „Další pohledy ▾“ (adresy beze změny,
  aktivní pohled se zvýrazní i v rozbalovací nabídce).
- Web: Osa s vazbami (`/osa-vazby/`) patří pod Časovou osu – obě stránky mají přepínač „Všichni / Přímí předci
  s vazbami“ (`OsaSwitch.astro`) a v menu se zvýrazní „Časová osa“ místo „Strom“.
- Web `/domy/`: domy seskupené po obcích (obce podle počtu předků, uvnitř podle předků a čp.), nahoře hlavní dům (`web_domy.json` → `hlavni_dum`, nově `config.hlavniDum`) a až 5 domů s příběhem; karty vypisují jen nenulové údaje a místo počtu předků rody a rozsah let; filtr obce (tlačítka, u víc než 8 obcí výběr) a přepínač „jen se zpracovanými dějinami“. U jedné obce bez nadpisů skupin.

## 0.13.0

### Přidáno
- Web: stránka příběhu ukazuje výřez rodokmenu – předky z přímé linie, na které text odkazuje, s doplněnými mezigeneracemi a manžely (`lib/vyrez.js`, `components/StoryTree.astro`, test `tests/vyrez_pribehu.test.js`).

## 0.12.1

### Opraveno
- `export_web.py`: syntaktická chyba ve `stats` z 0.12.0 (komentář uprostřed víceřádkového volání).

## 0.12.0

### Opraveno
- Web: jedna definice počtu předků a generací (`lib/predci.js` → `pocty` v `lib/data.js`) pro úvod, `/statistiky/`
  i `/predci/`. Předek = osoba s Kekulého číslem k > 1 (výchozí osobu nepočítáme, implex jednou), generací = nejvyšší
  generace předků. Dřív úvod nepočítal kořen a statistiky ano (rozdíl o 1) a generace se lišily o 1.
- Web: odstavce `uvod.odstavce` v `web.json` umí placeholdery `{predku}`, `{generaci}`, `{osob}` doplněné při buildu –
  místo ručně psaných čísel, která zastarávají.

## 0.11.0

### Změněno
- Web: každá zajímavost (`##` v `data/zajimavosti*.md`) je samostatný „krátký příběh“ na `/pribeh/<slug>/` s perexem,
  štítky rodů a odkazy předchozí / další; rozcestník `/pribehy/` má velké příběhy a krátké příběhy s filtrem podle rodu.
  Stará adresa `/zajimavosti/#kotva` přesměruje na příběh. „Zmíněno v příběhu“ u osob a domů vede na stránku příběhu.
- Web: „Osobnosti“ a „V číslech“ mají vlastní položku v menu; úvod má místo tlačítka na každý příběh jeden odkaz
  „Všechny příběhy“.
- Web: `web.json` → `menu_skryt` schová položky menu (např. `["/osobnosti/"]`, dokud nejsou osobnosti vybrané ručně).

## 0.9.0

### Přidáno
- Historický kontext k životům předků: kurátorovaná osa událostí 1620–1990 (`tools/udalosti.json`) a projektová
  vrstva regionálních událostí `data/udalosti.json` (návod `reference/udalosti.md`).
- `udalosti.py`: `rok`, `rozsah`, `osoba` (události za života s věkem); `wikidata <obec>` vypíše kandidáty k ověření.
- Web: pásy událostí na `/osa/` (přepínač) a řádek „Doba“ na kartě osoby a domu; kniha předků: box „Svět kolem“
  u každé generace.
- `napady.py`: epidemie z osy událostí a shluky úmrtí v obci porovnané s osou.
- `kontrola.py`: upozornění na spojení osoby s událostí bez odkazu na pramen; pravidla doložené vs. kontext v návodu.

### Změněno
- Kniha předků: výřezy 1100 px / JPEG 65 (kniha se zápisy ~10 MB), vějíř jen do hloubky `kniha.generaci`,
  nastavitelný limit a srozumitelná chyba při timeoutu.
- Dokumentace: MZA od 11/2026 jen v prohlížeči (ALTCHA).

## 0.8.1

### Změněno
- Kniha předků: karty osob v jednom sloupci a větší písmo; světlá obálka s rámečkem místo plné tmavé (šetří barvu při tisku).

## Nevydáno (flow „Nápady z forků rodokmen-skill“)

Nápady a kód z forků původního rodokmen-skill (MIT). Zdrojové forky a commity jsou v README v sekci
„Převzato z forků“, odkaz na původní soubor je v hlavičce převzatých nástrojů.

### Přidáno
- Kniha předků (PDF): tisková route `/kniha/<id>/` (Paged.js), `tools/kniha_pdf.py <id> | --vse [--web]`,
  `web.json` → `kniha` (generaci, domy, pribehy, zapisy), odkaz na stránce osoby; `kontrola.py` hlásí `CITLIVÉ`
  i u zápisů a bydlišť (jdou do knihy), brána nginx i Netlify chrání `/kniha/*.pdf` a `/kniha/*/` (test `tests/test_brana.py`).
- Export a přehledy: `ged_export.py` (GEDCOM 5.5.1), `prosle_knihy.py`, `fronta.py`, `kmotri.py`.
- Procházení knih: `nahledy.py` (mřížka náhledů), `sito.py` (síto pro knihy bez rejstříku), `mapa_knihy.py`,
  sdílená mezipaměť snímků `cache.py`, orientace v knize u svazku.
- Místa: `mista.py` – Mapy.com s `MAPY_API_KEY` z prostředí (např. z Keychainu), bez klíče Nominatim + RÚIAN.
- 2. sv. válka: `obeti.py`, `arolsen.py`, `mauthausen.py`, `vezni.py` a `souhlas.py` (souhlas s podmínkami
  portálů zapisuje jen uživatel; bez něj nástroje nedotazují a smoke končí kódem 4).
- Sčítání lidu: `slovakiana.py` (hárky 1930 ze Slovakiany), `portafontium.py scitani/domy/fara`.
- Židovské matriky a Litoměřice: `vademecum.py`, `litomerice.py`.
- `kramerius.py --server` pro jiné knihovny s Kramerius v5.
- Web: osobnosti, statistiky, portréty, věk u událostí, časová návaznost, vějíř s posunem/přibližováním
  a sloučenými sdílenými předky (`fan_chart.py`).
- Kontroly: `audit.py`, `kontrola.py` (čísla domů), `smoke_test.py` (OK/FAIL po portálech).
- `zapis.py dokumenty <klíč> --prejmenovat <nový> [--nahled]`: přejmenování dokumentu i s výřezy a odkazy.
- Návody v `reference/portaly.md`: Těšínsko, FamilySearch, odsun Němců, Vídeň, Slovensko/Maďarsko/Banát,
  vojáci 1. sv. války, Franziscejský katastr Dolních Rakous, zemské desky, vodnimlyny.cz.

### Změněno
- `slusne.py`: Retry-After a hlavičky RateLimit-*, sdílený limit pro všechny síťové nástroje.
- Ukázkový projekt: křest Jana Nováka 1890 přesunut na snímek 119, aby seděl s orientací svazku ukazka01.
- `novy_projekt.py`: argumenty přes argparse – `--help` vypíše nápovědu a nic nezaloží (dřív vznikla složka
  „--help“), neznámá volba skončí chybou bez zápisu, `--ukazka` funguje před i za cílovou složkou.
  Test `tests/test_novy_projekt.py`.
- `slusne.py`: SOA Třeboň (digi.ceskearchivy.cz) a eBadatelna (ebadatelna.soapraha.cz) zakázaly od 2. 11. 2026
  skripty. Požadavek na ně se neodešle a nástroj skončí hláškou s postupem v prohlížeči; 403 se nikdy neopakuje.
  `zdravi.py` to hlásí jako známé omezení. Test `tests/test_slusne_zakaz_skriptu.py`.

### Známé problémy
- SOA Třeboň (`trebon.py`) a SOA Praha (`ebadatelna.py`) od 2. 11. 2026 odmítají skripty (HTTP 403) – nástroje
  portál nedotazují, smoke FAIL. Postup: svazek najít v prohlížeči, uložit snímek nebo trvalý odkaz.
- MZA (`mza.py info`) od 11/2026 nenajde seznam snímků – portál změnil stránku.
- SOA Litoměřice ověřuje člověka (proof-of-work); `litomerice.py` to pozná a skončí kódem 5. Hledání v Litoměřicích
  funguje jen v prohlížeči, ověření se neobchází.
- kramerius.army.cz neprojde v Pythonu ověřením certifikátu – použij curl ze `slusne.py` nebo prohlížeč,
  ověření nevypínej.
- FamilySearch a hungaricana.hu odmítají skripty (403), jen návod pro prohlížeč.
- Encyklopedie dějin města Brna má jen návod, bez nástroje.
- Neověřeno živě: `mista.py` s `MAPY_API_KEY` (běh s klíčem nikdo nespustil), stažení karty z Arolsenu
  (`arolsen.py`).
