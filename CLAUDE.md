# rodokmen-plus – pokyny pro vývoj pluginu

Tohle repo je plugin pro Claude Code (skilly v `skills/`, nástroje v `skills/rodokmen-plus/tools/`, šablona projektu
a webu v `skills/rodokmen-plus/template/`). `skills/rodokmen-plus/template/CLAUDE.md` patří do rodokmenového projektu
uživatele, ne sem – při vývoji pluginu se jím neřiď. Píše se česky, včetně commitů, komentářů a CHANGELOGu.

## Příkazy (z kořene repa)

Python testy (unittest, ~15 s):

    python3 -m unittest discover tests

JS testy (logika webu, `bun:test`):

    bun test tests

Dva testy mimo discover, spouštějí se samostatně s argumentem:

    python3 -I tests/brzda/test_curl.py skills/rodokmen-plus/tools/slusne.py
    python3 -I tests/mapa/test_sloupce.py skills/rodokmen-plus/tools    # potřebuje ImageMagick (magick)

`test_curl.py` chce cestu ke `slusne.py`, ne ke složce `tools` – se složkou projde 0 z 10 a vypadá to jako regrese.

Build webu na ukázkových datech (do dočasné složky, ne do repa):

    python3 -I skills/rodokmen-plus/tools/novy_projekt.py --ukazka <dir>
    cd <dir> && python3 -I tools/export_web.py
    cd web && bun install && bun run build

Bez `export_web.py` build spadne na chybějícím `../generated/denik.md`. Samostatný lint repo nemá; kontrolou je
test suite a kontrola soukromí.

Kontrola soukromí (před každým pushem):

    python3 -I scripts/kontrola_soukromi.py ~/Projects/personal/genealogy/data

Release (jen s výslovným souhlasem člověka, z větve `main`):

    scripts/release.sh X.Y.Z           # kontrola soukromí, verze v plugin.json + VERZE, commit a tag lokálně
    scripts/release.sh X.Y.Z --push    # push main + tagu a GitHub Release přes gh

Python nástroje se spouštějí s `-I` (izolovaný režim), stejně jako v dokumentaci skillu.

## Soukromí

Repo je veřejné, skutečná rodina autora do něj nepatří. V testech, příkladech, dokumentaci i commitech se používá
jen fiktivní rodina Novákových z `skills/rodokmen-plus/template/ukazka/`. Když potřebuješ nové jméno nebo obec,
přidej je do ukázky, ne ze soukromých dat.

`kontrola_soukromi.py` bere příjmení a obce ze soukromého projektu (`~/Projects/personal/genealogy/data`, jinde
přes `RODOKMEN_SOUKROMA_DATA`) a hledá je ve verzovaných souborech. Výjimky (autor, velká města, autoři forků) jsou
v `POVOLENO` a `POVOLENE_RADKY`; rozšiřuj je jen o slova, která prokazatelně nejsou z rodiny. Soukromá data se
nekopírují ani necitují – stačí výstup skriptu. Implex a podobné jevy, které ukázka nemá, ověřuj na kopii
soukromých dat mimo repo.

## Git a GitHub

- Repo: https://github.com/zbysekvoda/rodokmen-plus. Práce jde na pojmenovanou větev a do PR.
- Do `main` se nepushuje ani nemerguje bez souhlasu člověka; totéž platí pro release a tagy.
- Před pushem proběhne kontrola soukromí a obě test suite.
- Změna chování pluginu dostane záznam do `CHANGELOG.md` pod `## Nevydáno`.

## Převzaté nápady z forků a upstreamu

Plugin navazuje na `sarsonj/rodokmen-skill` a `vzoha/dejiny-domu-skill` (MIT). Když přebíráš nápad nebo kód
z forku či upstreamu, cituj ho v README v sekci „Převzato z forků“: nástroj, odkaz na konkrétní commit
(`<autor>/rodokmen-skill@<sha>` s permalinkem na soubor), jméno nebo login autora a případně číslo issue/PR.
Kód se přepisuje na graf osob, ne kopíruje 1:1; v hlavičce souboru uveď původ. Forky jdou stáhnout přes
`git fetch https://github.com/<autor>/rodokmen-skill.git`.

## Pasti

- Archivní portály často odmítají skripty nebo ověřují člověka (ALTCHA, kód 5). To není chyba nástroje, ochrana
  se neobchází; čtení jde přes skill `matriky-v-prohlizeci` v Chromu uživatele.
- Živé dotazy na portály, Wikidata a Slovakianu pouštěj střídmě – testy pracují s fixtures v `tests/fixtures/`
  a nic nestahují. Nový test má zůstat offline.
- Testy, které importují `kontrola.py`, nesmí volat jeho `main` (končí `sys.exit`); pracují nad dočasným projektem.
- Názvy vztahů ve webu (`template/web/src/lib/pribuzni.js`) se musí shodovat s `tools/graf.py`; hlídá to
  `tests/pribuzni.test.js`.
- Web je Astro; `package.json` šablony volá `npm`/`node`, lokálně funguje i `bun run`.
