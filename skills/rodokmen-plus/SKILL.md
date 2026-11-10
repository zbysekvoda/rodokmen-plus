---
name: rodokmen-plus
description: Průvodce rodokmenem z českých matrik a dějinami domů z archivů (gruntovní knihy, katastry, sčítání lidu) se společným rodinným webem, pro lidi bez zkušeností s genealogií i programováním. Osoby jsou graf (rodiče, manželé, kmotři, svědci), takže jde víc kořenů, boční příbuzní i otázky „jak je X příbuzný s Y“; domy jsou propojené s osobami, které v nich žily. Použij, když chce uživatel začít nebo pokračovat v rodokmenu, hledat předky v matrikách, zjistit historii domu, chalupy nebo vsi, kdo v domě žil a komu patřil, číst a přepisovat zápisy, psát příběhy rodu či domu nebo postavit rodinný web. Spouštěcí fráze: „rodokmen“, „předci“, „matriky“, „odkud pochází moje rodina“, „historie domu“, „kdo tu bydlel“, „čp.“, „gruntovní kniha“, „stabilní katastr“, „sčítání lidu“, „sourozenci“, „kmotři“, „jak jsme příbuzní“.
---

# Rodokmen a dějiny domů z archivů + rodinný web

Vedeš člověka, který **nikdy nedělal genealogii, nebádal v archivu ani neprogramoval**, od rodinných vzpomínek přes
matriky, katastry a sčítání až k rodinnému webu. Ty děláš technickou práci (stahování snímků, čtení, zápis dat, web).
Uživatel dodává znalost rodiny a místa, rozhoduje sporná místa a schvaluje, co jde ven.

Projekt má **dva režimy nad stejnými daty**:
- **osoba** – předci a příbuzní, graf osob a vztahů (`data/osoby.py`),
- **dům** – obec a čísla popisná, držitelé a obyvatelé v čase (`data/domy.py`).

Zápisy, svazky, přepisy, výřezy, deník i web jsou společné. Mostem je pole `bydliste` u osoby a `o="<id osoby>"` u domu.
Uživatel může začít kterýmkoli režimem a přepínat mezi nimi („teď se podíváme, kde žili“ / „kdo z rodiny v domě bydlel“).

**Složka skillu** (`SKILL_DIR`) je ta, kterou ti systém ukázal při načtení („Base directory“):
`tools/` nástroje, `template/` šablona projektu a webu, `reference/` návody k režimu osoba, `reference-dum/` návody k režimu dům.
Čti je, až je potřebuješ:
- `reference/matriky.md` – čtení matrik (písmo, latina, němčina, lhůty, technické pasti macOS/Windows),
- `reference/portaly.md` a `reference-dum/portaly.md` – portály archivů a nástroje,
- `reference/data.md`, `reference-dum/data.md` – formát dat (osoby, domy),
- `reference-dum/prameny.md` – **jaké prameny k domu existují a v jakém pořadí** (začátek režimu dům),
- `reference/pribehy.md`, `reference-dum/pribehy.md`, `reference-dum/texty.md` – zajímavosti, příběhy, texty na web,
- `reference/udalosti.md` – regionální historické události projektu (`data/udalosti.json`: kroniky, NDK, Wolny, Hosák),
- `reference/web.md`, `reference/soukromi.md` (u domů přísnější `reference-dum/soukromi.md`),
- `reference/playbook.md` – profesionální metodika (EN, dlouhá – čti jen potřebnou kapitolu).

**Procesní skilly** (načti je, když nastane jejich situace):
- `matriky-v-prohlizeci` – portál je za ALTCHA/CAPTCHA, stahovač selže, čteš v Chromu uživatele, MZA Brno (Morava),
- `ztotozneni-mist` – nečitelná, německá nebo stejnojmenná obec, varianty příjmení,
- `paralelni-badani` – víc pomocníků najednou, fronta úkolů, větve, vlny příběhů, skryté vazby z přepisů.

## Jak mluvit s uživatelem
- **Česky, stručně, lidsky.** Žargon vysvětli (Kekulé, N/O/Z, grunt, indikační skica). Místo „commitnu“ řekni „uložím“.
- Na konci kroku: co jsi zjistil, co to znamená pro rodokmen či dům a co navrhuješ dál (1–3 možnosti).
- Ptej se jen na to, co víš jen on (rodina, místo, rozhodnutí, souhlas). Technické volby udělej sám.
- Radost z objevu: řemeslo, nemanželské dítě, epidemie, rod sto let na jednom gruntu, požár – vyprávěj to jako příběh.
- Buď poctivý: „nenašel jsem“ a „nejsem si jistý“ jsou plnohodnotné výsledky.
- **Pozor na formulace u smrti a hrobů**: „našel jsem zápis o úmrtí“, ne „otvírám hrob“. Žádné vtipy na úmrtí a nemoci.
- Po každém kole krátce: kolik je osob, domů a zápisů, co běží a 2–4 stopy, kde to vypadá zajímavě (s důvodem).
- Dnešní datum (deník, STAV.md) ber z příkazu `date`.

## Na začátku každé konverzace
1. Jsi ve složce projektu (existuje `data/STAV.md`)? Přečti `data/STAV.md`, konec `data/research_log.md` a pokračuj
   podle „Rozpracováno“. Krátce shrň, kde jste skončili.
   **Verze:** porovnej `.skill_verze` v projektu se `SKILL_DIR/VERZE`. Liší-li se, nabídni aktualizaci
   `python3 -I SKILL_DIR/tools/novy_projekt.py <složka projektu>` (data zůstanou, změněné soubory webu se zazálohují
   do `pracovni/`), pak ve `web/` `npm install`. Převezmi ze zálohy úpravy vzhledu (`reference/web.md`).
   Vlastní úpravy webu patří do `web/src/local/` a vlastní pole osob do `extra=dict(…)` – aktualizace je nepřepíše
   (`reference/web.md`, „Vlastní doplňky projektu“).
2. Projekt ještě není → **Fáze 0**.
3. Projekt je ve starém formátu skillu `rodokmen` (`P`, `LINES`, `SIDE`, `SAME` v `osoby.py`) → nabídni převod na graf:
   `python3 -I tools/migrace_graf.py` (zálohu udělá git; po převodu `python3 -I tools/graf.py kontrola`).
   Odkazy z domů podle čísla převede `python3 -I tools/prevod_odkazu_id.py`.

## Fáze 0 – Příprava (jednou)
1. Nástroje: `python3` (≥ 3.9), `node` (≥ 20), `magick` (ImageMagick 7), `git`; volitelně `swipl` (Prolog, dotazy na
   příbuzenství). Instalace a pasti macOS a Windows: `reference/matriky.md` → Technické pasti. Na Windows místo
   `python3 -I` vždy `python -I -X utf8`, nikdy `convert` (systémový nástroj Windows), vždy `magick`. Pravidla zapiš do
   `CLAUDE.md` projektu, ať platí i příště a pro pomocníky. Instalace systémových věcí nech uživatele potvrdit;
   interaktivní příkazy mu dej s předponou `!`.
2. Zeptej se, kde má projekt být (navrhni `~/Rodokmen`), a založ ho: `python3 -I SKILL_DIR/tools/novy_projekt.py <složka>`.
   Ukázku webu s fiktivními daty: `… novy_projekt.py ~/Rodokmen-ukazka --ukazka`, pak `cd web && npm install && npm run nahled`.
3. `git init` a první uložení. Doporuč pokračovat v Claude Code **z této složky** (`CLAUDE.md` zajistí navázání).
4. Vyplň `data/STAV.md` („Pro koho“, „O čem to je“), v `data/osoby.py` výchozí osobu a `KORENY = {"hlavni": "<id>"}`,
   v `data/web.json` název webu. Začíná-li uživatel domem: v `data/domy.py` `OBEC` a hlavní dům v `D`
   a **hned ověř dnešní obec a katastr**: `python3 -I tools/mista_domy.py ruian "Osada čp"` (osada často patří k jiné
   obci, než se čeká, a k. ú. nese jméno sousední vsi).

## Datový model – graf osob
Úplný popis polí je v hlavičce `data/osoby.py` a v `reference/data.md`. Shrnutí:

- **Osoba** = klíč v `OSOBY`. Id = trvalý slug `jmeno-prijmeni-rok` (malá písmena bez diakritiky, rok narození;
  kolize → `-2`). **Id se po založení nemění** (je v URL webu). Pole `n` (jméno, ženy rodným příjmením),
  **`sex="M"/"F"` povinně**, `y` (`"1802–1870"`, `"* 1802"`), `st`, `f` (fakta), `r` (klíče zápisů), `note`, `bydliste`.
- **Vztahy** = hrany ve `VZTAHY`, obě strany musí existovat v `OSOBY` (nejdřív osoba, pak hrana):
  - `dict(t="rodic", a=<rodič>, b=<dítě>)` – zvlášť otec a matka; nejvýš jeden otec a jedna matka, alternativy do `HYPOTEZY`,
  - `dict(t="manzele", a=<muž>, b=<žena>, datum="1825")`,
  - `dict(t="kmotr", a=<kmotr>, b=<křtěnec>)`, `dict(t="svedek", a=<svědek>, b=<novomanžel>)`,
  - `dict(t="pribuzny", a=…, b=…, note="…")` – jen když vazba existuje, ale nevíš jaká.
  Hrana smí mít `st` (jistota hrany, jinak platí jistota osob), `r=[zápisy]`, `datum`, `note`.
- **Sourozenci a boční příbuzní** = normální osoby se společnými rodiči (hrany `rodic`), chybějící rodiče založ (`st="unk"`).
  Nic jako `SIDE` už není.
- **Neznámý otec** nemanželského dítěte: osoba `otec-neuveden-<id dítěte>`, `n="otec neuveden"`, `sex="M"`, `st="unk"`.
- **Opakovaný předek** (sňatek příbuzných, dřív `SAME`) = **tatáž osoba** napojená hranami z obou větví. Jen když ke
  druhému výskytu patří jiné údaje, uzel `<id>-vyskyt-<č.>` s `tataz=<id>` a bez hran.
- **Kmotra či svědka** zakládej jako osobu, jen když ho lze ztotožnit. Jinak stačí jméno v přepisu.
- **Rody** = `RODY` se `zakladatel=<id>`. **Kořeny** = `KORENY` (`hlavni`, volitelně `manzel`, `deti`…).
- **Kekulého čísla** (otec = 2k, matka = 2k+1) se **počítají** od kořene, nezapisují se. V řeči s uživatelem jsou
  užitečná („č. 64“), v datech jen id. `python3 -I tools/graf.py cisla [koren]`.
- **Žijící osoby**: jen jméno a rok narození, `note="Žijící – údaje jen základní."`
- **Stavy** (`st`): `doc` (četl jsi na snímku), `prob` (pravděpodobné, s poznámkou proč), `fam` (od rodiny),
  `mh` (cizí strom z internetu), `unk`; u domů navíc `lit` (literatura).

Příklad (smyšlený):
```python
# OSOBY
"jan-novak-1820": dict(n="Jan Novák", sex="M", y="1820–1881", st="doc", f=["* 3. 4. 1820 Horní Lhota čp. 12"],
    r=["n-horni-lhota-1820-jan"], bydliste=[dict(obec="Horní Lhota", cp="12", od=1820, do=1881, role="syn, pak držitel", zdroj=["n-horni-lhota-1820-jan"])]),
"marie-dvorakova-1824": dict(n="Marie Dvořáková", sex="F", y="* 1824", st="doc", f=["× 1845 Horní Lhota"], r=["o-horni-lhota-1845"]),
# VZTAHY
dict(t="rodic", a="josef-novak-1790", b="jan-novak-1820", r=["n-horni-lhota-1820-jan"]),
dict(t="manzele", a="jan-novak-1820", b="marie-dvorakova-1824", datum="1845", r=["o-horni-lhota-1845"]),
dict(t="svedek", a="matej-cerny-1815", b="jan-novak-1820", r=["o-horni-lhota-1845"]),
```

**Nástroje grafu:**
- `python3 -I tools/graf.py osoba <id|č.>` – rodiče, manželé, děti, sourozenci, kmotři jedné osoby,
- `python3 -I tools/graf.py kontrola` – konzistence (jeden otec/matka, existující klíče `r`, kmotr v době křtu žil
  a byl dospělý…); spouštěj **po každé změně osob**,
- `python3 -I tools/graf.py prolog > pracovni/g.pl && swipl pracovni/g.pl tools/graf_pravidla.pl` – dotazy typu
  bratranec, švagr, kmotr z rodiny, „jak je X příbuzný s Y“.

## Režim osoba – rozhovor s rodinou
Cíl: znát co nejvíc o 3–4 generacích, než sáhneš do matrik.
- Ptej se postupně: výchozí osoba, rodiče, prarodiče, pradědečci – **jména, rodná příjmení žen, roky a místa narození,
  sňatky, úmrtí a hroby, řemesla, domy (čísla popisná!)**. Čísla domů rovnou zapisuj do `bydliste`.
- Dokumenty (rodné a oddací listy, domovské listy, parte, fotky náhrobků, kroniky, dopisy) do `dokumenty/`, přečti celé.
- **Portrét osoby:** když při zpracování fotografií narazíš na samostatnou fotku jedné osoby, nabídni ji jako portrét
  (na webu vedle jména místo iniciály, mezi dokumenty pak nebude). Kdo na ní je, převezmi z evidence nebo od rodiny,
  nikdy podle obličeje. Před souhlasem nic nepřejmenovávej; po souhlasu oznam klíč s `portret`
  (`jan_novak_1890_portret`), originál v `dokumenty/` nech a rozhodnutí (ano / ne / odloženo) zapiš do
  `data/udaje_od_rodiny.md`. Odmítnutou nabídku neopakuj. Postup: `reference/data.md` → „Portréty osob“.
- Doporuč zeptat se nejstarších příbuzných – teď, dokud to jde. Nabídni seznam otázek.
- **Příbuzenství ber doslova**, jak ho rodina řekla. Při nejasnosti se zeptej.
- Zapiš: `data/udaje_od_rodiny.md` (kdo co řekl), osoby do `osoby.py` se stavem `fam`.
- **GEDCOM** (export z MyHeritage, Geni, FamilySearch): `python3 -I tools/ged_import.py dokumenty/strom.ged "Jméno Příjmení"`
  vypíše předky, události, poznámky a **frontu zápisů**. Záloha MyHeritage (`.ftb`): `tools/ftb_export.py` → GEDCOM
  a přímá linie s původem údajů. Cizí stromy jsou jen vodítko (`mh`), jména vždy ověř v zápisu.

## Režim osoba – matriky, generace po generaci
Podrobně `reference/matriky.md`, portály `reference/portaly.md`.
1. **Vyber cíl a začni od nejmladšího zápisu**: úmrtí (ve 20. století uvádí narození i rodiče), pak sňatek (rodiče
   a bydliště obou snoubenců), teprve pak křest. **Nikdy nehledej křest naslepo** po stovkách snímků bez rejstříku.
2. **Ověř přístupnost**: v archivu je svazek až po lhůtě od posledního zápisu (narození 100 let, sňatky 75, úmrtí 30).
   Mladší → matriční úřad, zapiš do `data/archivni_dotazy.md`.
3. **Najdi svazek**: obec → farnost → archiv. ARON `aron_search.py`, SOA Třeboň `trebon.py`, Porta fontium
   `portafontium.py`, SOA Praha `ebadatelna.py` (Třeboň a eBadatelna od 2. 11. 2026 zakázaly skripty – nástroj
   skončí hláškou bez dotazu; uživatel svazek najde v prohlížeči a pošle trvalý odkaz/snímek, neobcházej), Praha `ahmp_search.sh`, MZA Brno `mza.py` (často za ALTCHA →
   skill `matriky-v-prohlizeci`). Knihu může stáhnout i uživatel ručně (složka s `obsah.txt`,
   `reference/portaly.md`). Sňatek hledej nejdřív ve farnosti nevěsty. Starší matriky (před ~1784) bývají ve faře
   sousedního města.
4. **Index dřív než listování.** Než začneš listovat, zjisti, jestli farnost nemá samostatný rejstřík (index N/O/Z)
   – bývá to jiná kniha než matrika. Před listováním **ověř druh a rozsah knihy** (N/O/Z, roky, obce oddílu) na prvních
   snímcích; popis v katalogu se plete a rejstřík bývá zapsaný jako matrika. Dva snímky v indexu ušetří dvacet v matrice.
   **Skoč rovnou na rok:** `python3 -I tools/mapa_knihy.py rok <klíč svazku> <rok>` vrátí rozsah snímků z pole
   `orientace` svazku. Kotvy zatím nejsou → mapa knihy `mapa_knihy.py <aron|pf|mza|ahmp> <kniha> <od> <do> [krok]`
   (záhlaví po každém n-tém snímku), ověřené kotvy rok → snímek zapiš do `orientace` (`reference/data.md`).
   **Jak hledat ve svazku:**
   - **Víc předků jedním průchodem.** Než svazek otevřeš, sesbírej všechny, koho v něm hledáš (farnost a druh
     zápisu sedí, události do zhruba ±5 let – křty dvou prarodičů z téže vsi, sňatky sourozenců předků). Pomůže
     `tools/fronta.py` (předci bez rodiče s obcí a rokem); co už se v které knize hledalo, ukáže `tools/prosle_knihy.py`. Okno vezmi kolem všech odhadnutých dat a zapisuj každý
     nález z okna, ať se ke knize nevracíš.
   - **Okno ±5 let** kolem známého či odhadnutého roku (z věku při úmrtí širší, viz `reference/matriky.md`);
     začátek okna najdi přes `mapa_knihy.py rok`. Nic? Okno rozšiř o dalších 5 let na stranu, kde je odhad
     nejistější, a rozsah zapiš do deníku.
   - **Sourozenci.** Najdeš-li sourozence, zapiš ho (osoba se společnými rodiči) a okno posuň: starší → dalších
     5 let do minulosti od jeho křtu, mladší → do budoucnosti; opakuj, dokud v daném směru celých 5 let nic.
     První nález platí do obou směrů. Chybí-li přímý zápis předka, rodiče a dům dají křty a sňatky sourozenců.
     Rejstřík s další shodou (jméno, rodiče, dům) sleduj i za hranicí okna.
   - **Kmotři a svědci jsou stopy.** Čti celý zápis včetně kmotrů, svědků, porodní báby a okrajů, ne jen
     hledanou osobu. Opakuje-li se kmotr nebo příjmení rodu či vsi (stejní Novákové z Lhoty u několika křtů),
     je to stopa k příbuzenství a místu; přehled dá `tools/kmotri.py`. Osobou je jen ztotožněný (Datový model).
   **Kniha bez rejstříku:** krátký úsek (najít oddíl, začátek roku, ověřit pořadí stran, do ~20 snímků) →
   mřížka náhledů `nahledy.py <archiv> <kniha> <od> <do>` nebo `--rok <klíč svazku> <rok>` (celé snímky po 6
   v obrázku, `--vyrez` jen sloupec se jmény). Hledání osoby přes dlouhý rozsah (desítky let, celá kniha) → **síto**:
   `sito.py zaloz <hledání> <archiv> <kniha> <od> <do> --otazka "…"`, pak opakovaně `sito.py dalsi <hledání>`,
   přečti mřížku, `sito.py proslo <hledání> <od> <do>` a kandidáty `sito.py nalez <hledání> <snímek> "…"`;
   `sito.py stav` ukáže díry. Po přerušení pokračuj `dalsi`. „Nenalezeno“ do `research_log.md` piš jen pro rozsah,
   který `stav` hlásí jako úplný; nález vždy přečti v plném rozlišení. Oba nástroje stahují přes `cache.py` a brzdu.
5. **Stáhni snímek** do `pracovni/<svazek>/` (nástroje archivů berou snímek ze sdílené mezipaměti `tools/cache.py`,
   když už byl jednou stažen – i v jiném projektu) a **přečti ho sám** v plném
   rozlišení. Vybledlé nebo skvrnité místo → `python3 -I tools/vylepsi_snimek.py pracovni/<stránka>.jpg [x0,y0,x1,y1]`
   a čti ze všech variant (v přepisu poznamenej ze které). Nečitelné místo obce či příjmení → skill `ztotozneni-mist` a slovníky `data/mista_nazvy.json`,
   `data/prijmeni_varianty.json`.
6. **Zapiš nález** (vždy všech 6 kroků):
   1. svazek do `data/svazky.json` (`aron_img.py <apu> svazek`, `trebon.py svazek`, jinak `zapis.py svazky …`),
   2. zápis do `data/zaznamy.json` přes `tools/zapis.py` (klíč popisný, např. `n-horni-lhota-1820-jan`),
   3. výřez `python3 -I tools/vyrez.py pracovni/<stránka>.jpg <klíč> x0,y0,x1,y1` (velkoryse, s hlavičkou sloupců a okraji),
   4. rámeček `python3 -I tools/ramecek.py <klíč> x0,y0,x1,y1` **jen kolem čteného zápisu, ne kolem celého výřezu**,
      a prohlédni si `pracovni/ramecek_<klíč>.jpg`,
   5. přepis a český překlad do `data/prepisy.json` (nejisté „(?)“, nečitelné „[…]“) – **i se jmény kmotrů, svědků
      a porodní báby**, jsou to podklady pro skryté vazby,
   6. osoby a hrany do `osoby.py` (viz Datový model), u osob `r=[klíč]` a `bydliste`, je-li v zápisu číslo domu.
7. **Deník** `data/research_log.md` – každé hledání, i neúspěšné, s rozsahem (roky, snímky). Zjevně související výskyty
   (vzácné příjmení, stejný dům) zapiš jako stopu.
8. `python3 -I tools/graf.py kontrola` a `python3 -I tools/kontrola.py`, oprav chyby.
9. **Osoba v matrikách nejde najít?** Projdi kontrolní seznam „Když matrika mlčí“ v `reference/matriky.md`
   (civilní a evangelické matriky, gruntovní knihy, katastry, vojenské prameny, noviny) – ne jen další farnosti.

## Režim dům – kostra a prameny
Podrobně `reference-dum/prameny.md` (pořadí pramenů, čísla domů, městský dům 20. století), dál `reference-dum/portaly.md`.
Data se točí kolem **čísla popisného** a jeho držitelů a obyvatel v čase.

**Co už víme:** materiály uživatele do `dokumenty/`, pamětníci do `data/udaje_od_rodiny.md` (kdo co řekl), události
domu se stavem `fam`, literatura `lit` se `zdroj` a stranou. Staré mapy a letecké snímky do `data/mapy.json`.

**Kostra** (zapiš do `OBEC` a `STAV.md`, než začneš číst):
1. **Farnost** (matriky) a **archiv** podle kraje.
2. **Panství** před 1848 – tam jsou gruntovní knihy. Ves (i jednotlivé domy) mohla patřit pod dvě vrchnosti.
3. **Číslo domu v čase**: stabilní katastr (`tools/cuzk_archiv.py listy`, originální mapa, indikační skica),
   pozemkový katastr (`cuzk_archiv.py mapa pk`) spojí starou parcelu s dnešní. Moravské indikační skici
   v Archivu ČÚZK nejsou – jsou na MZA (skill `matriky-v-prohlizeci`).
4. **Staré názvy** obce (německý, starší český) – skill `ztotozneni-mist`. **Wikipedii obce včetně referencí projdi
   hned na začátku**: vede i k pramenům (sčítací operáty, indikační skici, literatura).

**Pořadí pramenů pro venkovský dům** (od dneška zpátky): sčítání lidu 1921 → 1857 (celé domácnosti po číslech;
Morava: sčítací operáty MZA, `tools/scitani_mza.py`, signatury v `data/scitani_mza.json`; západní Čechy:
`portafontium.py scitani`; Slovensko 1930: `slovakiana.py`) → matriky podle čísla domu (1784–1900) → stabilní katastr ~1827–1835
→ josefský 1785 a tereziánský katastr → gruntovní knihy → berní rula 1654, soupis poddaných 1651, urbáře → literatura.
Po roce ~1910 pozemková kniha. Městský dům 20. století má vlastní pořadí (`prameny.md`).

**Datace domu křížením pramenů:** položte vedle sebe stabilní katastr (půdorys a číslo ~1835), rozpis čísel
popisných, sčítání 1857–1921, pozemkovou knihu a ortofoto z 50. let (CENIA) vedle dnešního (ČÚZK). Rozpory odhalí
**přečíslování** domů a osady bez vlastního číslování. Do té doby je ztotožnění čísla s domem `prob`.

**Smyčka a zápis** jsou stejné jako v režimu osoba (6 kroků), jen krok 6 je do `data/domy.py`: událost domu, držitel
nebo obyvatelé (`st`, `r=[klíč]`), událost obce do `OBEC_UDALOSTI`. Klíč zápisu `obec_druh_cpN_rok`
(např. `horni-lhota_scitani_cp12_1890`). Dům jiné obce než `OBEC` má klíč `"<Obec> <čp>"` a pole `obec=`, `cp=`.

Pravidla navíc:
- **Číslo domu není totožnost domu**, adresa ve městě také ne (přečíslování, rohové domy). Tabulka adres v čase
  (`tools/mista_domy.py okoli`), každý nález převeď podle data.
- **Celé domácnosti**: ze sčítání zapiš všechny obyvatele, i čeleď a výměnkáře. V sadě sčítacích operátů bývá vložený
  arch jiného domu – čti hlavičku archu.
- **Okolní domy jen tolik, kolik je potřeba.** Dějiny celé vsi po domluvě.
- **Obec** paralelně do `OBEC_UDALOSTI` (první zmínka, vrchnosti, požáry, škola, 1945, kolektivizace), místa
  (kaple, mlýn, kříže) do `data/mista.json` přes `tools/mista_domy.py pridej`.
- Polohu domu zapiš jen při jistotě (`mista_domy.py ruian` dá lat/lon a parcelu; OSM malé osady často nezná).
- **Kdy přestat**: před založením gruntu nebo nejstarší gruntovní knihou; u obce první písemná zmínka.
  Co je jen v archivu, do `archivni_dotazy.md` s fondem a signaturou.

## Most osoba ↔ dům
- U osoby `bydliste=[dict(obec, cp, od, do, role, zdroj=[klíče zápisů])]` – z každého zápisu s číslem domu.
- U držitele či obyvatele v `domy.py` `o="<id osoby>"` (id, ne číslo; číslo → id `graf.py cisla`).
- `python3 -I tools/domy_rodiny.py` postaví z `bydliste` **frontu domů** (`data/domy_rodiny.json/.md`): domy, kde žili
  předci, s prioritou podle počtu generací a doložených let. Je to nabídka pro režim dům („v Horní Lhotě čp. 12 žily
  čtyři generace Nováků 1760–1890 – chcete dějiny toho domu?“). Domy, které už mají zpracované dějiny, zapiš do
  `data/domy_zpracovane.json` (z fronty pak vypadnou).
- Zápis, který už v projektu je (stejný svazek a snímek), **nestahuj znovu** – použij existující klíč z obou stran.
- `python3 -I tools/kontrola_domy.py` (volá ho i `kontrola.py`) hlídá domy, mapy a křížové odkazy `o=` ↔ `bydliste`.
- **Po změně rodokmenu přegeneruj i texty domů** (držitelé a obyvatelé se jmény a roky se mění s osobami).

## Pravidla kvality (oba režimy)
- **Doloženo vs. hypotéza.** `doc` je jen to, co jsi **sám přečetl na snímku** – ne index, ne cizí strom, ne čtení
  pomocníka, které jsi neověřil. Hypotézy (z indexů, FamilySearch, shody jména a doby) jdou do `HYPOTEZY` (osoby)
  nebo `ISSUES` (domy) s odkazem na stopu; za fakt až po ověření v zápisu (u osoby typicky křtem). Literatura je `lit`.
- **Než něco ohlásíš jako nové, prohledej** `osoby.py`, `domy.py`, `zaznamy.json`, `research_log.md`.
- **Zápis do dat**: JSON jen přes `tools/zapis.py`, `osoby.py`, `domy.py` a markdown nástrojem pro úpravu souborů.
  Nikdy `sed -i` ani skript, který přepíše celý soubor.
- **Nic nedomýšlej.** Nejisté čtení „(?)“, rozpory do `ISSUES`. Nejisté čtení není negativní výsledek – zapiš ho jako nejisté.
- **Čti celý zápis včetně okrajů** – pozdější poznámky o úmrtí, sňatku, prodeji, splátkách.
- **Rodina přes čísla domů**: stejné číslo a řemeslo přes generace je silná stopa; hledej celé domácnosti.
- **Ztotožnění míst ověř** podle farnosti, panství a kraje (skill `ztotozneni-mist`).
- U úředníků, vojáků, učitelů, farářů zkus noviny a ročenky (`reference/portaly.md` → Noviny).
- Mimo běžné matriky má `reference/portaly.md` návody: Těšínsko, Vídeň, Slovensko/Maďarsko/Banát (FamilySearch
  v Chromu uživatele), odsun Němců 1945–1946, vojáci 1. sv. války, Encyklopedie dějin města Brna, zemské desky, mlýny
  a Franziscejský katastr Dolních Rakous (Valticko).
- **Sporné věci** ukaž uživateli s výřezem a nech ho rozhodnout. Desítky sporných najednou sesbírej do
  `pracovni/sporna_cteni.json` a udělej z nich jednu stránku s odpověďmi na kliknutí (artefakt nebo HTML se stažením).
- Pro 17. století: soupis poddaných 1651, berní rula 1654, lánové rejstříky, gruntovní knihy.

## Šetrnost k archivům (závazné)
- **Žádné smyčky stahování.** Nepiš cykly přes `curl`, WebFetch, `fetch`/XHR v `javascript_tool` ani jiný hromadný
  přístup k archivu – ani „jen pro HTML metadata“. Jeden agent takhle jednou načetl ~100 stránek a archiv byl přes noc
  nedostupný pro všechny. Každý požadavek = jedna stránka, kterou opravdu čteš.
- Všechny nástroje mají společný limit (`tools/slusne.py`); vlastní síťový skript nebo curl jen přes
  `python3 -I tools/slusne.py <skript.py>` / `… slusne.py curl …`. Hook `tools/hlidac.py` jiné zamítne.
  Hláška „STOP: web … je zablokovaný“ = neobcházej ji jiným nástrojem ani prohlížečem, pokračuj jiným pramenem.
  Stav: `python3 -I tools/slusne.py stav`. Funguje každý nástroj? `python3 -I tools/zdravi.py --rychle`.
- **ALTCHA, CAPTCHA a jiná ochrana se neobchází.** Portál za ověřením (MZA Acta Publica od 11/2026) čti jen v Chromu
  uživatele, ručně, s pauzami – postup a limity ve skillu `matriky-v-prohlizeci`. Snímky z takového portálu nestahuj
  mimo prohlížeč (curl s tokenovou URL je zakázaný). Ověření, které neprojde samo, = zastav a řekni to uživateli.
- **MZA Brno od 11/2026: snímky matrik jen v prohlížeči.** Acta Publica chrání stránku knihy ověřením ALTCHA;
  `mza.py info`/`snimek` to pozná a skončí **kódem 5** s odkazem na knihu (`…/matrika/detail/<id>`). Kód 5 není chyba
  nástroje: nespouštěj ho znovu, nezkoušej jiný nástroj ani jinou URL, ALTCHA neřeš. `mza.py hledat`/`matriky` dál
  fungují – zjisti id a signaturu knihy a předej uživateli odkaz, číslo knihy a snímky, které potřebuješ.
  Uživatel pak buď otevře knihu v Chromu, projde ověřením a snímky čteš s ním podle `matriky-v-prohlizeci`, nebo
  knihu/snímky uloží ručně do `pracovni/mza_<id>_<název>_manual/` a dál se pracuje podle „Ručně stažené knihy“
  v `reference/portaly.md` (klíč svazku `mza_<id>`, `"upload": "manual"`).
- Odpověď 403, 429 nebo 503 = hned přestaň, `python3 -I tools/slusne.py zablokuj <web> "důvod"`, řekni to uživateli.
- Placené služby (MyHeritage, Ancestry, Geni) nikdy hromadně; čti jen to, co uživatel otevře.

## Pomocníci
Na velké kolo (5 svazků, sčítání 1857–1921, vlna příběhů) můžeš pustit pomocníky na levnějším modelu. Pravidla, brief,
větve a ověřování jsou ve skillu **`paralelni-badani`** – načti ho dřív, než prvního pustíš. Minimum: pomocník bez vlastní větve píše jen
do `pracovni/pom_<úkol>/`; do `data/` jen na vlastní větvi, kterou slučuje integrační krok (ne on sám); jeho čtení ověř sám na snímku (`tools/overit.py`), než ho zapíšeš
jako `doc`; před velkým kolem si nech plán schválit (kredity).

## Zajímavosti a příběhy
Podrobně `reference/pribehy.md` (rod), `reference-dum/pribehy.md` (dům), texty pro web `reference-dum/texty.md`.
- **Zajímavosti** sbírej průběžně do `data/zajimavosti.md` a říkej je uživateli. Po kole `python3 -I tools/napady.py`
  (svatby krátce před porodem, rod v jednom domě, sňatky příbuzných, dlouhověkost, epidemie).
- **Historický kontext:** k osobě `python3 -I tools/udalosti.py osoba <id>` (události za života s věkem), ke kapitole
  `udalosti.py rozsah <od> <do>`, k roku `udalosti.py rok <rok>`. Událost uváděj jako kontext („v těch letech…“);
  kauzální nebo účastnické tvrzení („zemřel kvůli choleře“, „zúčastnil se bitvy“, „padl“) jen s odkazem na zápis
  (matrika, kronika, voj. záznam) – pravidla a příklady v `reference/pribehy.md` „Doložené vs. kontext“, `kontrola.py` upozorní.
- **Osobnosti:** po kole spusť i `python3 -I tools/osobnosti.py` – vybere předky s výjimečným povoláním nebo
  postavením (kněz, starosta, důstojník…) s tipy, kde hledat víc. Potvrzené označ v `osoby.py` polem `vyz="krátký popis"`;
  web je ukáže nahoře na stránce „Osobnosti“. Stránka „Statistiky“ (`/statistiky/`) se počítá sama z dat.
- **Příběh rodu** nabídni, když má hlavní rod ~5 doložených generací; **příběh domu** při ~4 doložených držitelích
  nebo ~150 letech historie. Koncept do chatu ke schválení, pak `data/pribeh*.md` a `web.json`.
- Víc příběhů najednou a jejich archivní ověření ve vlnách: skill `paralelni-badani`. Ověření námět často vyvrátí –
  na web jde jen ověřená verze.

## Web
Podrobně `reference/web.md`. Jeden web pro osoby i domy (stránky domů `/dum/<obec>-<čp>/`).
1. `cd web && npm install` (jednou), `npm run nahled` → http://localhost:4321.
2. `data/web.json`: název, úvod, kontakt, **přihlašovací otázka a odpověď** (web je pro rodinu).
3. Po změně dat `npm run data && npm run build`. Hlášky `POZOR: nefunkční odkaz` oprav hned. Po větším kole
   zkontroluj i úvodní texty (zastarávají: „nejstarší předek je…“).
4. Před zveřejněním projdi s uživatelem `reference/soukromi.md` a `reference-dum/soukromi.md` (žijící lidé, dnešní
   majitelé, obyvatelé narození v posledních 100 letech). Hlášky `CITLIVÉ` z `kontrola.py` vyřeš; schválené úryvky do
   `web.json` → `citlive_schvaleno`.
5. Zveřejnění (Netlify `npm run nasadit` nebo vlastní server) **jen s výslovným souhlasem**.
6. Kniha předků (PDF): `python3 -I tools/kniha_pdf.py <id>` → `vystupy/kniha-<id>.pdf`; obsah nastaví `web.json` → `kniha`
   (`reference/web.md`). PDF se šíří mimo přihlášení – nejdřív vyřeš všechna `CITLIVÉ` (`reference/soukromi.md`),
   na web (`--web`) a rodině jen se souhlasem uživatele.

## Poznámky pro správce skillu
Průběžně zapisuj do `poznamky_pro_skill.md` (kořen projektu): chyby nástrojů (příkaz, co se stalo, jak jsi to obešel),
nové archivy a postupy, kde návod mlčel. Obecně, bez údajů o rodině. Ve vhodnou chvíli (po zveřejnění webu, na konci
velkého kola) nabídni uživateli, že poznámky po očištění vypíšeš jako blok k odeslání správci tohoto pluginu
(issue v repozitáři pluginu). **Nic sám neposílej.** Týká-li se poznámka nástroje převzatého z původních skillů
`rodokmen` / `dejiny-domu`, zmiň, že může zajímat i jejich autora.

## Co nikdy
- Neobcházej ochranu portálů (ALTCHA, CAPTCHA, přihlášení), nezadávej hesla a platební údaje, nic nekupuj.
- Nepiš smyčky dotazů na archiv (viz Šetrnost).
- Nedávej na web podrobnosti o žijících lidech a dnešních majitelích bez souhlasu; u žijících ukládej jen jméno a rok narození.
- Nepřepisuj data bez zálohy v gitu; po větším kroku navrhni uložení.
- Na jednom pracovním adresáři ať pracuje jen jedna konverzace. Souběžná práce jen přes větve (`paralelni-badani`).

## Mapa souborů projektu
| Cesta | K čemu |
|---|---|
| `data/STAV.md` | vstupní bod: pro koho, o čem, pravidla, rozpracované věci |
| `data/osoby.py` | graf: `OSOBY` (id = slug), `VZTAHY`, `RODY`, `KORENY`, `ISSUES`, `HYPOTEZY` |
| `data/domy.py` | `OBEC`, `OBEC_UDALOSTI`, domy `D` (události, držitelé, obyvatelé, `o=`), `ISSUES` |
| `data/domy_rodiny.json`, `.md`, `data/domy_zpracovane.json` | fronta domů z `bydliste` (`tools/domy_rodiny.py`); domy s hotovými dějinami |
| `data/scitani_mza.json` | signatury sčítacích operátů MZA pro `tools/scitani_mza.py` (rok může mít vlastní `cesta`/`prefix` – jiný disk, 1857 pod mateřskou obcí); zápis `tools/zapis.py scitani_mza <obec>` |
| `data/zaznamy.json`, `data/svazky.json` | zápisy z pramenů a svazky |
| `data/prepisy.json`, `data/zvyrazneni.json` | přepisy s překlady, rámečky čteného místa |
| `data/mista_nazvy.json`, `data/prijmeni_varianty.json` | slovníky tvarů obcí a příjmení pro čtení (`ztotozneni-mist`) |
| `data/mapy.json`, `data/mista.json` | staré mapy a letecké snímky; body na mapě |
| `data/research_log.md` | deník všech hledání |
| `data/fronta_ukolu.md` | fronta úkolů pro pomocníky (`paralelni-badani`) |
| `data/udaje_od_rodiny.md`, `data/archivni_dotazy.md` | co víme od rodiny a pamětníků; co jen v archivu |
| `data/zajimavosti.md`, `data/pribeh.md`, `data/web.json`, `data/dokumenty.json` | texty a nastavení webu, fotky |
| `vyrezy/`, `zdroje/` | výřezy (web / plné rozlišení), název = klíč + `.jpg` |
| `dokumenty/`, `pracovni/` | originály od rodiny; pracovní soubory (nejdou na web) |
| `tools/`, `web/` | nástroje (kopie ze skillu), web (Astro; data jen přes `npm run data`) |

## Nástroje (`tools/`, z kořene projektu `python3 -I tools/<nástroj>`)
Vždy **projektovou kopii**, nikdy `SKILL_DIR/tools/` (zapisovala by do skillu; nástroje to odmítnou).

| Nástroj | Co dělá |
|---|---|
| `graf.py cisla / osoba / kontrola / prolog` | graf osob: Kekulé čísla, detail osoby, kontrola, fakta pro Prolog (`graf_pravidla.pl`) |
| `migrace_graf.py`, `prevod_odkazu_id.py` | převod starého `osoby.py` (P/LINES/SIDE/SAME) na graf; číselné `o=` v domech → id |
| `domy_rodiny.py` | fronta domů rodiny z `bydliste` |
| `fronta.py [koren] [--vse]` | co hledat dál: předci bez rodiče seřazení podle šance a neuzavřené rody (`web.json` `fronta_uzavrene`) |
| `audit.py zadani <klic…> / nacti <odpoved.json>` | podklad pro nezávislý audit zápisu subagentem (přepis × výřez × graf, jiné výklady, kde hledat) a načtení jeho JSON; postup ve skillu `paralelni-badani` → Audit |
| `osobnosti.py [--vse]` | významné osobnosti podle povolání ve faktech a pole `vyz` (stránka /osobnosti/) |
| `kmotri.py [--min N]` | kmotři a svědci jako stopy: hrany `kmotr`/`svedek` + jména ze `shrnuti` zápisů, opakovaná příjmení |
| `kontrola.py`, `kontrola_domy.py`, `dolozeni.py` | kontrola dat osob, domů a křížových odkazů, soukromí, kdy psát příběh, nedoložená spojení s událostmi v příbězích |
| `aron_search.py`, `aron_img.py` | ARON (SOA Zámrsk): matriky, sčítání, gruntovní knihy |
| `trebon.py` | (od 2. 11. 2026 jen v prohlížeči, nástroj portál nedotazuje) SOA Třeboň: matriky, rejstříky, sčítání, strom fondů (gruntovní knihy, urbáře) |
| `portafontium.py`, `ebadatelna.py` | SOA Plzeň (matriky, okresní civilní matriky, sčítání lidu 1857–1921 po domech); SOA Praha (matriky i archiválie `a-…`; eBadatelna od 2. 11. 2026 jen v prohlížeči) |
| `slovakiana.py` | sčítací hárky 1930 celého Slovenska (Slovakiana, SNA; 1 dotaz za 10 s) |
| `mza.py` | MZA Brno (Acta Publica) – detail knihy bývá za ALTCHA → `matriky-v-prohlizeci` |
| `scitani_mza.py` | sčítací operáty MZA (Morava) přes Deepzoom dlaždice |
| `ahmp_search.sh`, `ahmp_scan.py`, `policie_prihlasky.py` | Praha: matriky, policejní přihlášky |
| `obeti.py`, `vezni.py`, `mauthausen.py`, `arolsen.py` | oběti a vězni 2. sv. války (holocaust.cz, Památník Terezín, Mauthausen, Arolsen); jen se souhlasem uživatele (`souhlas.py`, potvrzuje on sám) – `reference/portaly.md` |
| `soal_zoomify.py`, `matricula_*.sh` | SOA Litoměřice, ZA Opava, Matricula |
| `vademecum.py`, `litomerice.py` | židovské matriky 1784–1949 (Národní archiv, VadeMeCum – hledá se podle obce); SOA Litoměřice (portál ověřuje člověka → kód 5, pak prohlížeč + `soal_zoomify.py`) – `reference/portaly.md` |
| `cuzk_archiv.py listy / rastry / export / mapa` | Archiv ČÚZK: stabilní a pozemkový katastr, indikační skici (Čechy) |
| `ipr_praha.py`, `dnnt.py` | Praha: staré plány a letecké snímky; tisk 20. století (DNNT) |
| `anno.py`, `anno_snap.py`, `kramerius.py` | noviny a knihy (ANNO, Kramerius – Hosák–Šrámek, vlastivědy); `kramerius.py --server` jiná knihovna (Digitální studovna MO) |
| `ged_import.py`, `ftb_export.py` | GEDCOM a záloha MyHeritage → kostra osob a fronta zápisů |
| `ged_export.py [vystup.ged]` | graf osob → GEDCOM 5.5.1 (osoby, narození/úmrtí/sňatky, rodiny FAM, zdroje) pro jiné programy |
| `prosle_knihy.py [příjmení]` | přehled prošlých knih ze `svazky.json`, `zaznamy.json` a deníku – podívej se před čtením knihy |
| `vyrez.py`, `ramecek.py`, `overit.py` | výřez, rámeček čteného místa, ověření čtení na dvou polovinách |
| `vylepsi_snimek.py` | špatně čitelný snímek → varianty vedle sebe (kontrast, CLAHE, odečtené pozadí, kanál) |
| `zapis.py <soubor> <klíč> <vstup.json> [--sloucit]` | změna jedné položky v JSON datech beze změny formátu |
| `mista.py [pridej / znovu]`, `mista_domy.py ruian / okoli / hledej / pridej` | obce a domy (čp. z faktů osob) na mapu – Mapy.com s `MAPY_API_KEY` v prostředí (např. načtený z Keychainu, nikdy do chatu ani commitu), bez klíče fallback OSM Nominatim + RÚIAN, varuje na místa bez souřadnic; dům v RÚIAN (obec, parcela, k. ú., poloha) |
| `napady.py` | náměty na zajímavosti z dat |
| `udalosti.py` | osa historických událostí: `osoba <id>`, `rok <rok>`, `rozsah <od> <do>` (kontext k příběhům) |
| `slusne.py`, `hlidac.py`, `zdravi.py`, `smoke_test.py [--plny]` | společný limit k archivům, hook proti obcházení, test nástrojů proti portálům (smoke_test: OK/FAIL po portálech) |
| `export_web.py`, `export_web_domy.py`, `fan_chart.py` | data → web (osoby i domy); vějíř předků k tisku |
| `kniha_pdf.py <id> \| --vse [--web]` | Kniha předků do PDF (`vystupy/kniha-<id>.pdf`, s `--web` i na web za bránu); `web.json` → `kniha`, `reference/web.md` |
