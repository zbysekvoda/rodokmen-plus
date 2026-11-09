# Changelog

## Nevydáno (flow „Nápady z forků rodokmen-skill“)

Nápady a kód z forků původního rodokmen-skill (MIT). Zdrojové forky a commity jsou v README v sekci
„Převzato z forků“, odkaz na původní soubor je v hlavičce převzatých nástrojů.

### Přidáno
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
- Návody v `reference/portaly.md`: Těšínsko, FamilySearch, odsun Němců, Vídeň, Slovensko/Maďarsko/Banát,
  vojáci 1. sv. války, Franziscejský katastr Dolních Rakous, zemské desky, vodnimlyny.cz.

### Změněno
- `slusne.py`: Retry-After a hlavičky RateLimit-*, sdílený limit pro všechny síťové nástroje.
- Ukázkový projekt: křest Jana Nováka 1890 přesunut na snímek 119, aby seděl s orientací svazku ukazka01.
- `novy_projekt.py`: argumenty přes argparse – `--help` vypíše nápovědu a nic nezaloží (dřív vznikla složka
  „--help“), neznámá volba skončí chybou bez zápisu, `--ukazka` funguje před i za cílovou složkou.
  Test `tests/test_novy_projekt.py`.

### Známé problémy
- SOA Třeboň (`trebon.py`) a SOA Praha (`ebadatelna.py`) odmítají skripty (HTTP 403) – smoke FAIL.
- MZA (`mza.py info`) od 11/2026 nenajde seznam snímků – portál změnil stránku.
- SOA Litoměřice ověřuje člověka (proof-of-work); `litomerice.py` to pozná a skončí kódem 5. Hledání v Litoměřicích
  funguje jen v prohlížeči, ověření se neobchází.
- kramerius.army.cz neprojde v Pythonu ověřením certifikátu – použij curl ze `slusne.py` nebo prohlížeč,
  ověření nevypínej.
- FamilySearch a hungaricana.hu odmítají skripty (403), jen návod pro prohlížeč.
- Encyklopedie dějin města Brna má jen návod, bez nástroje.
- Neověřeno živě: `mista.py` s `MAPY_API_KEY` (běh s klíčem nikdo nespustil), stažení karty z Arolsenu
  (`arolsen.py`).
