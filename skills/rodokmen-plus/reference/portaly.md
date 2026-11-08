# Portály archivů a jak z nich dostat snímky

Matriky jsou online u osmi státních archivů – podle toho, **kde předci žili** (dnešní kraje zhruba odpovídají):

| Archiv | Oblast | Portál s matrikami | Vyzkoušeno se skillem |
|---|---|---|---|
| SOA Zámrsk | východní Čechy (Hradecký a Pardubický kraj) | ARON – aron.vychodoceskearchivy.cz | **ano – hotové nástroje** |
| SOA Praha | střední Čechy | eBadatelna – ebadatelna.soapraha.cz | **ano – nástroj `ebadatelna.py`** (i urbáře a gruntovní knihy) |
| SOA Plzeň | západní Čechy | Porta fontium – portafontium.eu | **ano – nástroj `portafontium.py`** |
| SOA Třeboň | jižní Čechy | digi.ceskearchivy.cz | **ano – nástroj `trebon.py`** |
| SOA Litoměřice | severní Čechy | Digitální badatelna – digi.soalitomerice.cz | **částečně – `litomerice.py`, `soal_zoomify.py`** (portál ověřuje člověka → knihu najdi v prohlížeči) |
| AHMP | hl. m. Praha | katalog.ahmp.cz (Pragapublica) | **ano – `ahmp_search.sh`, `ahmp_scan.py`** |
| MZA Brno | jižní Morava, Vysočina z části | Acta Publica – www.mza.cz/actapublica | částečně – v prohlížeči (postup níže) |
| ZA Opava | severní Morava a Slezsko, Olomoucko a Litovelsko | Digitální badatelna – digi.archives.cz/da/ | **částečně – `soal_zoomify.py`** (jen s prohlížečem, CAPTCHU řeší uživatel) |
| Národní archiv | židovské matriky (HBMa), soupisy; pražské policejní přihlášky 1850–1914 | badatelna.eu; digi.nacr.cz/prihlasky2 | židovské matriky **ano – `vademecum.py`**; přihlášky **ano – `policie_prihlasky.py`** |

Adresy u nevyzkoušených portálů ověř při prvním použití (portály se mění). Pro pohraničí a mimo ČR viz `playbook.md` §2
(Matricula pro Rakousko/Německo, Geneteka pro Polsko, FamilySearch pro Slovensko) a níže.

## ARON (SOA Zámrsk) – hotové nástroje
- **Hledání svazků:** `python3 -I tools/aron_search.py "Holice"` → řádky `apu_id | signatura, roky | druh, obce`.
  Popis obsahuje druh knihy (NAROZENÝCH / ODDANÝCH / ZEMŘELÝCH, index) a všechny obce farnosti.
- **Informace o svazku:** `python3 -I tools/aron_img.py <apu_id> info` → název a počet snímků.
- **Stažení snímku:** `python3 -I tools/aron_img.py <apu_id> <snímek> 1 pracovni/holice_n_57.jpg`
  (úroveň 1 = poloviční rozlišení – stačí na orientaci; 0 = plné rozlišení – na čtení a výřez).
  Jen část stránky v plném rozlišení: `… <snímek> 0 pracovni/detail.jpg 0.0,0.4,1.0,0.7`.
- **Odkaz na snímek** (pole `odkaz` v `zaznamy.json`): `python3 -I tools/aron_img.py <apu_id> link <snímek>`.
- **Svazek do dat:** `python3 -I tools/aron_img.py <apu_id> svazek` (klíč = prvních 8 znaků apu_id → pole `svazek` v zápisu).
- V ARON jsou i další fondy (sčítání lidu, některé gruntovní knihy, kroniky) – `aron_search.py "Obec" "název fondu"`.
- Stejnojmenných obcí bývá víc (Vinice u Hořic × Vinice u Velké Jesenice). Výsledky jsou seřazené podle farnosti;
  zúžit jde víc slovy oddělenými čárkou, která musí být v popisu všechna: `aron_search.py "Vinice,Hořice"`
  (nebo hledej sousední obec či farní obec).
- U starých far hledej nejdřív **souhrnné indexy** (popis „index NAROZENÝCH…“ přes mnoho let), často sahají do 17. století.
- Obec nenalezena? Zkus název **bez přívlastku** („Lhota“ místo „Horní Lhota“) a starý název. Starší matriky
  (před ~1784) bývají ve faře sousedního města; indexy fary mají oddíly po vesnicích
  („Copulati Gross Lhota“).
- Ber ohled na server: stahuj jen to, co čteš; žádné hromadné stahování celých svazků.

## SOA Třeboň (digi.ceskearchivy.cz) – `tools/trebon.py`, bez prohlížeče
- `trebon.py misto "Obec"` → id místa. Diakritiku a mezery nástroj odstraní sám (portál zná jen „RatiborskeHory“).
  Portál vrátí vždy jen jedno místo – **zkontroluj vypsaný název a okres**: u stejnojmenných obcí jinou (Buk → Bukovka),
  u měst i okres nebo synagogu (Jindřichův Hradec → okres 1949–1960). Správné id pak najdi na portálu a pracuj s ním.
  Malé osady portál jako místo nezná vůbec (Malá Chyška) – hledej farní nebo sousední obec (Chyšky) a osadu v popisu knih.
  Občasná chyba 500 bývá výpadek portálu – nástroj zkouší znovu; když trvá, zkus to později.
- `trebon.py svazky <id|"Obec">` → knihy místa (id knihy, druh, roky, obce).
- `trebon.py rejstrik <id_knihy> <písmeno>` → **dobrovolnický jmenný rejstřík** knihy se snímkem, obrovská úspora.
  Ne každá kniha ho má; prázdný výsledek = rejstřík chybí, ne „osoba tam není“.
- `trebon.py snimek <id_knihy> <snímek> pracovni/x.jpg [nahled]`, `trebon.py svazek <id_knihy>` (do `svazky.json`).
- Trvalý odkaz: `https://digi.ceskearchivy.cz/<id_knihy>/<snímek>`.
- Některé fary mají knihy po vesnicích, které nejsou v seznamu svazků místa (Vacov → Žár) – hledej podle titulků knih fary.
- **Civilní matriky (1920–1945) lidí bez vyznání** jsou v knihách okresních úřadů (např. Tábor, kniha 12304) a mají
  dobrovolnický rejstřík (`trebon.py rejstrik 12304 N`). Dobrá cesta, když farní matrika mlčí. V `svazky "Obec"`
  se neukážou (patří okresu, ne obci) – id knihy najdi na portálu.

## SOA Plzeň (Porta fontium, portafontium.eu) – `tools/portafontium.py`, bez prohlížeče
- `portafontium.py fara <fara>` → knihy fary: kniha | obce | roky a druhy (`*` N, `oo` O, `+` Z, `i` index) | popis.
  `<fara>` je název římskokatolické fary („Dolní Bělá“, „Mýto“ – diakritiku nástroj odstraní) nebo přímo část
  její adresy (`dolni-bela` =
  `…/contents/register/soap-pn/cirkev-rimskokatolicka/dolni-bela`). Obec → faru nástroj nehledá: faru zjisti ve vyhledávání
  matrik na portálu (pole Místo, v prohlížeči) nebo v popisech knih okolních far. Bez prohlížeče: stránka
  `https://www.portafontium.eu/searching/register?search_api_views_fulltext_1=<obec>` vypíše odkazy
  `/register/soap-pn/<kniha>` – `<kniha>` (např. `kdyne-29`) rovnou použij v `portafontium.py info`.
- `portafontium.py info <kniha>` (`dolni-bela-17`) → signatura, druh, text desky a **obsah** – u knih psaných po vesnicích
  vypíše, na kterých foliích je která obec („Ves X z let 1862–1901 = fol. 121–200“).
- `portafontium.py snimek <kniha> <snímek> pracovni/x.jpg [nahled] [x0,y0,x1,y1]` → celá stránka v plném rozlišení jedním
  požadavkem (IIIF), `nahled` = 1/4. Číslo snímku = pořadí náhledu v prohlížeči; soubory nesou číslo folia
  (`dolni-bela-17_0951` = fol. 95), takže u knih se souvislou foliací je **snímek ≈ folio**.
- `link <kniha> <snímek>` → trvalý odkaz, `svazek <kniha>` → `svazky.json` (klíč `pf_<kniha>`).
- Bez prohlížečového User-Agentu portál vrací 403 (nástroj ho posílá). Jmenné hledání portál nemá – indexy jsou jen uvnitř knih
  (`*i`, `ooi`, `+i` v seznamu knih fary).

## SOA Praha (eBadatelna, ebadatelna.soapraha.cz) – `tools/ebadatelna.py`, bez prohlížeče
- `ebadatelna.py hledat "Obec"` → celé názvy lokalit („Lhota - obec X - okres Y“); `matriky "Obec"` (nebo celý název)
  → matrikaId | kniha | druh | roky | fara | počet snímků. U stejnojmenných obcí vypíše možnosti.
- `ebadatelna.py info <matrikaId>` → obsah knihy včetně **rozvržení stran po vesnicích** (např. „1–48 Ves A, 49–82 Ves B,
  1–30 Ves C …“ – každá ves může mít vlastní stránkování) – u takových knih neodhaduj snímek podle roku, ale podle stran
  dané vsi (číslo strany je nahoře na snímku). Takové knihy bývají řazené po vsích, ne chronologicky – je-li rejstřík,
  začni jím.
- `ebadatelna.py snimek <matrikaId> <snímek> pracovni/x.jpg [nahled] [x0,y0,x1,y1]`; `link`, `svazek` (klíč `ebad_<id>`).
- **Archiválie** (urbáře, gruntovní a pozemkové knihy velkostatků – most přes 17. století): `a-info <archivalieId>`,
  `a-snimek`, `a-link`, `a-svazek` (klíč `ebad_a_<id>`). Archiválii nástroj nehledá – najdi ji na portálu v prohlížeči;
  id je v adrese `…/pages/ArchivaliePage/archivalieId/<id>`.
- Starší snímky bývají z mikrofilmu nebo silně vybledlé – čti se zvýšeným kontrastem:
  `magick x.jpg -colorspace Gray -contrast-stretch 2%x30% x_k.jpg` (výřez pak dělej z kontrastní verze a poznamenej to v přepisu).
  Víc variant najednou (CLAHE, odečtené pozadí, kanál inkoustu): `tools/vylepsi_snimek.py`. Detekce hran a
  černobílé prahování kurentu škodí – vlasové tahy zdvojí nebo smažou.
- Portál dává vždy celý snímek (nedlaždicuje); náhled a výřez dělá nástroj po stažení přes ImageMagick (`magick`).
  Denní údržba kolem 4:44 (asi 2 minuty).

## AHMP Praha – `tools/ahmp_search.sh`, `tools/ahmp_scan.py`
- `bash tools/ahmp_search.sh "Smíchov"` → svazky Sbírky matrik: popis | farnost | (XID, id, počet snímků).
- `python3 -I tools/ahmp_scan.py <XID> <snímek> pracovni/x.jpg [1] [x0,y0,x1,y1]` → snímek (1 = poloviční rozlišení).
- Trvalý odkaz `https://katalog.ahmp.cz/pragapublica/permalink?xid=<XID>&scan=<N>`.
- Nový portál digi.ahmp.cz má ochranu proti robotům – nepoužívat. Pražské matriky 1890–1940 většinou **nemají rejstříky**
  a farností je mnoho – bez přesného data a farnosti (z úmrtí/sňatku nebo od rodiny) je hledání velmi drahé.

## Národní archiv – židovské matriky (Archivní VadeMeCum) – `tools/vademecum.py`
- vademecum.nacr.cz: fondy HBMa / Židovské kontrolní matriky 1784–1949. **Nejsou indexované po jménech** – hledá se podle obce
  (kniha je po židovských obcích a letech; rejstříková hesla v `info` vyjmenují všechny obce, které kniha pokrývá).
- `python3 -I tools/vademecum.py hledat "Dambořice" [--stran N] [--jen-snimky]` → xid | druh | název | NAD | roky | popis | snímků
- `vademecum.py info <xid>`, `snimek <xid> <n> pracovni/x.jpg [nahled]` (Zoomify přes `soal_zoomify.py`, sdílená cache),
  `link <xid> <n>` (trvalý odkaz do `zaznamy.json`), `svazek <xid>` (klíč `nacvm_<xid8>` v `svazky.json`).
- Podmínky: veřejně přístupné bez registrace; lhůty 100/75/30 let jako u církevních matrik. Síť jde přes `slusne.py`.

## SOA Litoměřice (severní Čechy) – `tools/litomerice.py`, `tools/soal_zoomify.py`
- `litomerice.py hledat "Obec" [slovo …]` / `info` / `snimek` / `link` / `svazek` – knihy Sbírky matrik podle obce.
  Dokud portál ověřuje člověka (proof-of-work v prohlížeči), nástroj skončí kódem 5 a nic neobchází – postupuj níže.
- Digitální badatelna digi.soalitomerice.cz má na vstupu automatické ověření (asi 15 s „počítání“) → knihu a snímek
  najdi v prohlížeči. V síťovém provozu pak najdi adresu `…/zoomify/cz/archives/CZ-214000010/matriky/<cesta>/ImageProperties.xml`.
- Snímky stahuj nástrojem: `python3 -I tools/soal_zoomify.py <cesta> 0 pracovni/x.jpg` (0 = plné rozlišení, 1 = poloviční).
  Obrázkový server neomezuje a cookies nepotřebuje.
- **POZOR: po zhruba 100 rychlých požadavcích na stránky aplikace (prohlížení snímků, detail výsledku) archiv zablokuje
  přístup na 30 minut.** V prohlížeči proto jen najdi knihu a cestu k obrázkům, pak už jen nástroj. Pomocníkům to napiš do zadání.

## ZA Opava (severní Morava, Slezsko, Olomoucko, Litovelsko) – `tools/soal_zoomify.py`
- Pozor na hranici: obce na Litovelsku a Olomoucku patří pod **ZA Opava**, ne pod MZA Brno.
- **Bez prohlížeče to nejde.** Badatelna `https://digi.archives.cz/da/` (stará adresa matriky.archives.cz jen přesměruje)
  má ochranu proti robotům – curl ani WebFetch se nedostanou ani na hledání. Potřebuješ připojený prohlížeč (Claude in
  Chrome – uživatel ho připojí příkazem `/chrome` – nebo Playwright); jinak ať knihu najde a snímky uloží uživatel.
  Úvodní ověření projde samo, ale hledání často skončí **CAPTCHou: tu vyřeší uživatel** v okně prohlížeče, ty nikdy.
- Hledej obec a vyfiltruj Matriky (ikona, potom znovu lupa). Hledání vrací i civilní matriky (u obce stovky svazků) –
  filtr „Datum od – do“ (podle začátku svazku, např. 1680–1873) nechá jen církevní. Knihy bývají řazené po obcích
  a na konci mají rejstřík. Vedle farních knih bývají i **druhopisy** („T“ v signatuře, viz `matriky.md`).
- **Seznam svazků a ID snímků si hned ulož** do `pracovni/<svazek>/` – relace po pár hodinách vyprší a výsledky
  hledání platí jen v ní. Na detailu svazku: entita `document.querySelector('[entityuuid]').getAttribute('entityuuid')`
  (u svazků uložených v jiném archivu nemá tvar UUID – nehledej ji regexem), ID snímků jsou hodnoty
  `select.getScanSelect option` (tvar „N%20uuid“). Snímek pak otevřeš kdykoli bez hledání:
  `/da/showZoomifySeparate?imageNumberSeparate=N&myEntityUuid=<entita>&myImageUuid=<uuid>`.
- Adresa obrázku: `fetch('/da/showZoomify/<id svazku z URL>/<část option.value za „%20“>')` vrátí HTML s cestou
  `…/images/<složka>/<uuid>.jpg`. Cesta se u svazků liší (`…/CZ-217000010/NAD-165/dao/images/…`, `…/zao/matriky/dao/images/…`)
  a přípona bývá i `.JPG` – nástroji dej vždy **celou adresu z HTML**:
  `python3 -I tools/soal_zoomify.py "<adresa>" 2 pracovni/x.jpg` (2 = čtvrtinové rozlišení na orientaci podle záhlaví
  stránek, 0 = plné jen u nalezeného zápisu). Obrázkový server images.archives.cz neomezuje a cookies nepotřebuje.
- **POZOR na blokování** (jen stránky aplikace, obrázky ne): rychlé dotazy → CAPTCHA, „operace vyhodnoceny jako
  nestandardní“ nebo „Access blocked“ na 30 minut; po desítkách dotazů za den vrací showZoomify „Server Exception“
  (denní limit – pokračuj až další den). Pauza 3–6 s mezi stránkami, dávky do ~80 stránek, žádné rychlé `fetch` hned
  po hledání a stránky výsledků neprocházej za sebou. Delší smyčku pusť v prohlížeči na pozadí, výsledky ukládej do
  `window` nebo `localStorage` a vyzvedávej po částech (nástroj pro JavaScript má limit asi 45 s). Pomocníkům to napiš do zadání.

## Těšínsko (Jablunkovsko, Třinecko, Karvinsko) – ZA Opava a prameny za hranicí
- **Katolické matriky** české části jsou v ZA Opava (postup výše: prohlížeč, CAPTCHU řeší uživatel). Stejné knihy uvádí
  i katalog FamilySearch ve sbírce „Czech Republic, Church Books, 1552-1981“ (např. Jablunkov 1617–1937) – když
  digi.archives.cz blokuje, zkus je tam v uživatelově přihlášeném prohlížeči (nevyzkoušeno).
- **Evangelíci a. v.** tu tvořili velkou část obyvatel: k jejich zápisům hledej vždy i evangelický sbor. Po toleranci
  (1781) vedly vlastní matriky toleranční sbory (u Jablunkova Návsí). Do té doby (1709–1781) byl pro luterány celého
  Těšínského knížectví i okolních panství jediný sbor – Ježíšův kostel v Cieszyně; kde jsou jeho matriky online, neověřeno.
- **Hranice se měnila** (1920 rozdělení Těšínska, 1938 polský zábor, 1939–1945 německá správa) a fara či sbor mohou
  být za dnešní hranicí: filiální sbor v Istebné patřil k Návsí do roku 1932.
- **Polská strana** (Istebna, Jaworzynka, Wisła, Cieszyn): Geneteka, vojvodství `12sl` (slezské), má indexy farností
  včetně evangelických sborů a u řady zápisů odkaz na sken (dotaz viz Polsko – Geneteka níže). Archivní skeny:
  `https://szukajwarchiwach.gov.pl/` (Archiwum Państwowe w Katowicach).
- **Slovenská strana** (Kysuce: Čadca, Svrčinovec, Čierne, Skalité, Turzovka): uherské matriky na FamilySearch – oddíl
  „FamilySearch v Chromu uživatele“ níže.
- **1939–1945** (neověřeno): muži z Těšínska často s Deutsche Volksliste a ve Wehrmachtu. Stopy jsou v poválečných
  spisech o vrácení československého občanství a u mimořádných lidových soudů (ZA Opava, fondy Okresní úřad Těšín,
  Landrát Těšín, ONV) a v agendě DVL v archivu v Katovicích (szukajwarchiwach, německý i polský název obce
  a „Volksliste“). Jsou to citlivé údaje – na web jen se souhlasem rodiny (`soukromi.md`).

## MZA Brno (jižní Morava, Acta Publica) – bez nástroje
- Portál `https://www.mza.cz/actapublica/`, bez přihlášení. Adresa actapublica.eu bývá za Cloudflare zablokovaná
  („Sorry, you have been blocked“ – podle IP, i v běžném prohlížeči); když blokuje i mza.cz, ať uživatel vypne VPN
  nebo zkusí jinou síť.
- Knihu najdi v prohlížeči podle obce nebo fary. Snímky jsou IIIF: adresu obrázku najdi v síťovém provozu a stáhni ji
  přes `curl` (Python dostane HTTP 426). Dál podle „Ostatní portály“ níže.

### MZA – ARON (pozemkové knihy, tereziánský katastr, urbáře)
- **ARON MZA** (`https://www.mza.cz/aron/`) má veřejné JSON API bez ALTCHA: `GET …/aron/api/aron/apu/<id>` (pole `parts`:
  „Digitální“, inv. č., `parent` = cesta fond > panství > obce) a `POST …/aron/api/aron/apu/listview?listType=SEARCH`
  s filtry `{"field":"type","operation":"EQ","value":"ARCH_DESC"}` + `{"operation":"FTXF","field":"name","value":"<obec>"}`.
  Podle `parent` filtrovat nejde – ber `size=100` a filtruj u sebe. **Dotazů málo** (přes `slusne.py`): MZA po ~20
  dotazech za sebou přestala přijímat spojení.
- **Pozemkové (gruntovní) knihy panství**: fond „Pozemkové knihy“ > <panství> > Jednotlivé obce. Mnoho knih je
  digitalizovaných („Digitální: Ano“, originál nepřístupný). Kniha 18. století má rejstřík podle pořadí zápisů,
  19. století podle čp. – dává předání gruntu, jméno manželky a výměnek, tedy vazbu mezi generacemi, kterou matrika
  nedá. Před dotazem do archivu se vždy podívej, jestli kniha není online.
- **Tereziánský katastr moravský (fond D 4, 1750–1768)** je online (digitální kopie); jednotky se jmenují často jen
  „Tereziánský katastr“ – obec hledej ve stromu panství, ne fulltextem. Josefský katastr = fond D 6.
- Opisy moravských urbářů (17. stol.) jsou v ARON taky, hledej „<panství> urbář“.
- **„Connection refused“ z mza.cz** (prohlížeč i nástroje) = přetížení nebo odmítnutá adresa. Hned
  `slusne.py zablokuj www.mza.cz "…"`, všem pomocníkům zastav MZA a pokračuj jinými prameny. Neobcházej proxy ani
  scrapovacími službami (Apify apod.) – ať uživatel ověří mza.cz z jiné sítě; je-li odmítnutá jen jeho adresa,
  navrhni omluvný dopis archivu (odešle uživatel).
- **Evangelické matriky na Moravě**: katalog Acta Publica je po obcích, ale evangelická kniha se objeví jen u obce
  sídla sboru (a obcí, které sbor výslovně uvádí), ne u vsi, kde evangelík bydlel. `mza.py matriky "<obec>"` ukáže
  jen katolické → hledej sbory podle původce „evangelická církev …“ a podle literatury (sbory h. v. na Vysočině).

## Encyklopedie dějin města Brna (`https://encyklopedie.brna.cz/home-mmb/`) – bez nástroje
- Fulltext přes osobnosti, ulice, objekty a spolky; portál vrací jen první stránku (~30 zásahů), proto zužuj dalšími
  slovy (příjmení, ulice, povolání: „Novák klempíř Králova“). Heslo osobnosti uvádí narození, úmrtí, **bydliště
  s adresou**, vzdělání, zaměstnání a **hrob (hřbitov, skupina, číslo)**. Bez prohlížeče jen přes `slusne.py curl`.
- Je to encyklopedie významných osob a míst, ne evidence obyvatel – běžní předkové tu být nemusí. U brněnských řemeslníků
  a úředníků ale často dá adresu, povolání a hrob na Ústředním hřbitově; dál matriky MZA (`mza.py`). Zdroj cituj jako
  „Encyklopedie dějin města Brna“ (zdroj `J`).

## Pražské policejní přihlášky 1850–1914 (Národní archiv) – `tools/policie_prihlasky.py`
- Karty pražských rodin: hlava rodiny, manželka s rokem a místem narození, děti s roky, adresy, někdy místo sňatku.
  Výborné, když rodina žila v Praze a nevíš farnost (pražské matriky nemají rejstříky).
- `python3 -I tools/policie_prihlasky.py Kolar [Jan] [1850] [1870]` – příjmení bez diakritiky (začátek jména), jméno a roky
  narození volitelně. Bez prohlížeče vrátí jen prvních 20 výsledků, proto hledej co nejúžeji.
  Kartu stáhni `policie_prihlasky.py karta <pořadí> pracovni/karta.jpg Kolar [Jan] [1850] [1870]` (stejné hledání; jde i pořadí
  nad 20) – vypíše citaci a trvalý odkaz (`index.php?action=link&ref=czarch:CZ-100000010:874&karton=K&folium=F`).
- **Nepokrývá Smíchov, Vinohrady, Žižkov, Karlín a další předměstí před 1922** (byla to samostatná města). Náboženství karty neuvádějí.

## Matricula (Rakousko, Bavorsko, Polsko…; data.matricula-online.eu) – `tools/matricula_*.sh`
- Bez přihlášení. Seznam knih: `…/de/oesterreich/<diecéze>/<farnost>/?page=N`; snímek knihy `…/<id>/?pg=<snímek>`
  (zároveň trvalý odkaz).
- URL obrázku obsahuje `csrf` a `ctrl` počítané JavaScriptem → je potřeba prohlížeč (Playwright / Claude in Chrome):
  otevři knihu, klikni na stránku (`.docview-pagelink`), URL obrázku vezmi z `performance.getEntriesByType('resource')`
  a stáhni `bash tools/matricula_dl.sh "<url>" pracovni/x.jpg`. Víc stránek: soubor řádků „<snímek> <url>“ → `matricula_batch.sh`.
- Rejstřík najdeš bez prohlížeče: HTML stránky knihy má seznam `labels` s popisky snímků („04-Index Taufe_0001“).
- Vojenské matriky (např. Štýrský Hradec) tam nejsou – jsou v Kriegsarchivu ve Vídni (offline).
- **Vídeň:** 567 farností pod `https://data.matricula-online.eu/de/oesterreich/wien/` (`<obvod>-<farnost>`, např.
  `01-am-hof`). Oddací a úmrtní knihy bývají online do 1938, křty do 1922 (mladší se otevírají – ověř na portálu).
  Židovské matriky Vídně: Israelitische Kultusgemeinde a mikrofilmy ve Wiener Stadt- und Landesarchiv (WStLA);
  bydliště 1904–1975 (Meldezettel) jen placeným písemným dotazem na WStLA. Hroby: `https://www.friedhoefewien.at/`
  → Verstorbenensuche, jen v prohlížeči (brána vyžaduje přihlášení – neobcházet). Vídeňští Češi se často „ztratí“
  ve Vídni – hledej křty dětí a sňatek ve farnosti bydliště.
- **GenTeam** (`https://www.genteam.at/`, zdarma po registraci – účet zakládá uživatel sám): jmenný rejstřík vídeňských
  katolických křtů, sňatků a úmrtí a dalších rakouských pramenů; najde i další děti téže matky. Zápis pak ověř na
  Matricule. Aktivační odkaz z e-mailu otevřený přes Outlook (Safe Links) se „spotřebuje“ – ať ho uživatel zkopíruje
  do prohlížeče.

## Slovensko, Maďarsko, Rumunsko (Banát, Sedmihradsko) – bez nástroje, jen návod
Slovenské, maďarské a rumunské archivní servery bývají pro skripty nedostupné nebo za Cloudflare (ověřeno 11/2026:
hungaricana.hu HTTP 403, arhivelenationale.ro HTTP 503) – neobcházej, hledej v prohlížeči uživatele.
- **FamilySearch** je hlavní cesta (postup „FamilySearch v Chromu uživatele“ níže): katalog podle místa → „Church Books /
  Anyakönyvek / Cirkevná matrika“. Kolekce Slovakia Church and Synagogue Books má zindexované i sňatky a úmrtí
  (`q.spouseSurname`, datum úmrtí); sňatek najde index i ve farnosti nevěsty. Slovenské vesnice často nemají vlastní faru –
  katalog podle obce ukáže jen fary se sídlem v obci; faru poznáš ze sloupce bydliště v knihách okolních far.
- **Rozsah:** Slovensko – církevní matriky zhruba 1590–1895 (snímky online), jména často maďarsky nebo latinsky.
  Maďarsko – církevní matriky do 1895, občanské od 1895. Rumunský Banát a Sedmihradsko – farní matriky Banátu
  mikrofilmované 1939–40 (zhruba 1760–1850), latinsky a německy.
- **Maďarské matriky (1850–1895):** Lakhely = bydliště, zsellér = domkář bez půdy, földész = rolník, telkes = sedlák,
  árva = sirotek, néhai = zesnulý, törv. = manželské, H. H. = reformovaný; Mihály = Michal, Pál = Pavel, Erzsébet = Alžběta,
  Borbála = Barbora, András = Ondřej, Ferenc = František, József = Josef, János = Jan.
- **Hranice a jména:** do 1918 bylo Slovensko, Banát i Sedmihradsko v Uhrách – obce mají **maďarské názvy** (i německé,
  rumunské); hledej pod tím, co platilo v době zápisu.
- **Státní archivy** (Slovenský národný archív a štátne archívy; Magyar Nemzeti Levéltár `https://mnl.gov.hu/`;
  Arhivele Naționale – pobočka Timiș má občanské matriky 1717–1951; adatbazisokonline.hu `https://adatbazisokonline.hu/`):
  většina knih není online, žádost o výpis podle obce a roku → `archivni_dotazy.md`. Mladší matriky jen na matričním úřadě.
- **Čeští reemigranti z Banátu** (Svatá Helena, Gerník, Eibentál, Bígr, Rovensko…) se po 1945 vraceli hlavně 1946–1950
  a usazovali v pohraničí. Zapiš obec v Banátu, vyznání a jméno rodiny tam; cesta: rodina → FamilySearch (farní matriky
  obce) → spisy o osídlení a reemigraci v okresním archivu nového bydliště.
- Zápisy v maďarštině, slovenštině a latině čti pomalu; nejistá místa označ „(?)“.

## Polsko – Geneteka (geneteka.genealodzy.pl)
- Zdarma dobrovolnické indexy křtů, sňatků a úmrtí po farnostech; hledej ve webovém rozhraní (vojvodství → farnost →
  příjmení). Index je vodítko – skeny často online nejsou (farní nebo diecézní archiv), pak zápis žádej tam.
- **Farní příslušnost se měnila**: obec mohla patřit k sousední faře (Lipowa → Radziechowy do 1896) – hledej i tam.
- Nestahuj hromadně: PTG uvádí „linkujemy, nie pobieramy danych“ (odkazujeme, nestahujeme) a po desítkách rychlých dotazů
  server vrací nefiltrovaná data. Dotazy dávkuj, s pauzami, a výsledky si ověř.
- Jednotlivý dotaz jde i bez prohlížeče: `https://geneteka.genealodzy.pl/api/getAct.php?draw=1&start=0&length=10&bdm=B&rid=B&w=12sl&search_lastname=<příjmení>&search_name=&search_lastname2=&search_name2=&from_date=1850&to_date=1900&exac=1`
  (`bdm`/`rid` B křty, S sňatky, D úmrtí; `w` vojvodství, např. 12sl slezské, 08op opolské) → JSON. Past: `recordsTotal` > 0
  a prázdné `data` – zkus jen jedno příjmení bez křestního jména a užší roky. Stránkování opakuje řádky.
- Skeny některých polských far jsou i na Matricule (výše) nebo FamilySearch (níže).

## FamilySearch (přes uživatelův přihlášený prohlížeč)
- Přihlášení je potřeba i na hledání v indexech. České matriky tam skoro zindexované nejsou (Slovensko ano, hlavně křty).
- Jen když ho má uživatel otevřený a sám nabídne. Z kontextu stránky lze volat JSON API
  `https://www.familysearch.org/service/search/hr/v2/personas?q.surname=…&q.givenName=…&q.fatherGivenName=…&count=20`
  (`fetch(…, {credentials:'include'})`); výsledky v `entries[].content.gedcomx`.
- Užitečné na indexy matrik a hroby (BillionGraves, Find a Grave). Výsledek je vodítko – ověř v matrice.
- Neměň uživateli otevřené karty (po hledání vrať původní adresu). Stránky za Cloudflare neobcházej – ať je uživatel
  otevře sám a pošle snímek obrazovky.
- Snímky filmu (DGS): seznam přes `POST /search/filmdatainfo/image-data` s `{"type":"film-data","args":{"dgsNum":"00…","state":{"i":"0"},"locale":"cs"}}`
  (`images[]` = ARK). Snímek: `https://www.familysearch.org/service/records/storage/deepzoomcloud/dz/v1/<ARK 3:1:…>/$dist`
  (plné rozlišení), malé náhledy `…/image_files/8/0_0.jpg`. **Po ~1000 rychlých požadavcích přijde HTTP 429** a blokace
  na desítky minut – stahuj jen konkrétní snímky, nanejvýš pár za sekundu, hromadné procházení knih nedělej.

## FamilySearch v Chromu uživatele (slovenské a uherské matriky)
Ověřený postup pro sbírku „Slovakia Church and Synagogue Books, 1592–1935“ a jiné uherské matriky v uživatelově
skutečném Chromu s rozšířením Claude in Chrome. Automatizovaný prohlížeč (Playwright, chrome-devtools) i dotazy mimo
prohlížeč (curl, i na veřejný katalog) dostanou „Access Denied – Error 15“ nebo HTTP 403 a každý pokus se zapisuje k IP
uživatele – nezkoušej je. Bez takového Chromu hledá uživatel sám a posílá snímky obrazovky.
**Předem, jednou:** uživatel je ve FamilySearch přihlášený a složku stahování v Chromu má nastavenou do projektu
(`pracovni/familysearch/`) – na macOS Terminál do `~/Downloads` bez plného přístupu k disku nevidí.
1. **Rejstřík napřed, listování až nakonec.** Hledej adresou
   `https://www.familysearch.org/search/record/results?q.surname=…&q.givenName=…&q.birthLikePlace=…&q.birthLikeDate.from=…&q.birthLikeDate.to=…&count=100`
   (podle potřeby i `q.fatherGivenName`, `q.spouseSurname`, `q.marriageLikePlace`), s přesnou shodou i bez ní – křty
   i sňatky bývají zindexované i tam, kde to nečekáš. Odkaz „Zobrazit původní dokument“ v detailu záznamu vede rovnou
   na snímek (dál bod 4). Ke katalogu (bod 3) přejdi, až obě hledání nic nenajdou – typicky úmrtí po ~1852.
   Index slovenských křtů uvádí jako místo jen faru („Raková, Čadca“), obec a dům jsou až na snímku:
   `q.birthLikePlace=<obec>` vrátí celou faru i cizí podobné záznamy – výsledky filtruj podle příjmení a fary.
2. **Výsledky čti levně:** JavaScriptem z řádků tabulky (`javascript_tool`) místo snímků obrazovky:
   `[...document.querySelectorAll('tr')].map(r => [r.innerText.replace(/\s+/g, ' ').trim(), r.querySelector('a[href*="1:1:"]')?.href]).filter(r => r[1])`
   → jméno, událost, datum, rodiče a odkaz na záznam (`…/1:1:…`).
3. **Katalog:** místo hledej v uherské podobě („Turzovka, Trencsén, Maďarsko“). Film otevřeš adresou
   `https://www.familysearch.org/search/film/<číslo DGS>`, číslo doplněné nulami zleva na 9 číslic (`004567890`).
4. **Prohlížeč snímků:** po otevření zavři spodní panel a dej „přizpůsobit“ (jinak vidíš jen horní část dvoustrany).
   Na snímek skoč polem „Snímek“ vlevo nahoře: trojklik, číslo, Enter a počkej, až se snímek načte (~5 s). Šipky po
   stranách = další / předchozí. Parametr `?i=N` v adrese snímek nezmění.
5. **Stažení:** ikona stažení v liště prohlížeče → **„Pouze JPG“** (výchozí je PDF se zvýrazněním) → Stáhnout. Soubor
   (ark-id nebo `image.jpg`) hned přejmenuj na `<DGS>_<snímek>.jpg`; obě čísla patří i do zápisu.
6. **Čtení:** zápis čti ze staženého JPG v plném rozlišení. Limit HTTP 429 z oddílu výše platí i tady.

## Hroby a hřbitovy
- Kde jsou předci pohřbeni, víš z rozhovoru s rodinou (Fáze 1). Fotky náhrobků (jména, data, rodná příjmení) jsou
  cenný pramen hlavně pro 20. století, kde matriky ještě nejsou přístupné.
- Evidence hrobových míst: správa hřbitova (kdo je v hrobě uložen, kdo platí nájem – často žijící potomek);
  řada měst má online vyhledávání hrobů. Mezinárodně BillionGraves a Find a Grave.

## Noviny a ročenky – `tools/anno.py`, `tools/anno_snap.py`, `tools/kramerius.py`
**Kdy se vyplatí:** státní a vrchnostenští úředníci, soudci, učitelé, faráři, důstojníci, vojenští lékaři, notáři,
poštmistři, starostové, podnikatelé – noviny otiskovaly jmenování, přeložení, vyznamenání, penze, konkurzy, oznámení
sňatků a parte (zhruba od 1860). Z toho plyne, **kde člověk kdy žil** → kde hledat křty dětí, sňatek, úmrtí.
A když osoba „chybí“ v očekávaných matrikách (stěhovala se se službou). **Spíš ne:** sedláci a řemeslníci na vsi.
- ANNO (rakouské noviny 1700–1950, i Prager Zeitung, Wiener Zeitung): `python3 -I tools/anno.py '"Johann Nowak"' 1860 1915 [stran] [--snip]`
  – jména **německy** („Johann Nowak“, „Wenzel Dworschak“). Výřez místa: `tools/anno_snap.py <docId> "<dotaz>" pracovni/x.jpg`.
  ALEX a annoshow jsou za Cloudflare – neobcházet.
- Kramerius NK ČR (české noviny, ročenky, adresáře): `python3 -I tools/kramerius.py 'text_ocr:"Jan Novák" AND datum_begin:[1900 TO 1910]'`.
- Vojenské schematismy: fulltext na archive.org (např. `militrschematis13kriegoog` = 1850).
- **Rizika:** jména se opakují a fulltext šumí („Winter“ = i zima, „Novák“ = nový obyvatel). Ztotožni jen při shodě víc údajů (bydliště,
  funkce navazující na matriku, časová posloupnost). Zdroj je „J“ (jiný pramen) – vodítko a příběh, ne náhrada matriky.
- Výstřižky jsou skvělé na web: ulož do `dokumenty/noviny/`, přes `vyrez.py` a do `dokumenty.json`.
- **Soudní a úřední vyhlášky** (Úřední list Brněnských novin, Brünner Zeitung, Brünner Morgenpost; v Čechách Pražské
  noviny / Prager Zeitung) jsou nejvýnosnější pro venkov: dražby usedlostí s čp., opatrovnictví, výmazy pohledávek,
  vypsání učitelských míst, obchodní rejstřík. OCR bývá bez diakritiky, čísla domů špatně („40“ místo „4“).
- **Dotazy:** Solr skládá diakritiku, ne pády – hledej obec v 6. a 2. pádě („v Horní Lhotě“, „z Horní Lhoty“).
  Filtr `datum_begin:[od TO do]` vyřadí čísla bez data – hledej bez filtru a rok čti z výstupu. Obec se jménem shodným
  s křestním jménem (např. Lukov, Bohdalov) dává šum – přidej druhé slovo. Facet `root_title` nefunguje, použij `root_pid`.
- `dnnt.py ocr klic=uuid:…` stáhne text veřejné strany; `dnnt.py kontext` bere slova jako AND (víc než 2–3 slova = 0).
  Úryvek z OCR je `lit`, ne `doc`.
- **Regionální periodika** malých okresů v Krameriu často chybí – čti je přes celozemské listy (Moravská orlice,
  Lidové noviny, Našinec, Venkov, Národní listy…). Školní ročenky (programy gymnázií, seznamy žáků) levně potvrdí,
  kdo z obce studoval.
- **Literatura o toleranci a skrytých evangelících** (DNNT) jde prohledat po úryvcích bez přihlášení: příjmení + ves
  ukáže rody z tajné církve → pak hledej v tolerančních matrikách.
- Pořadí: nejdřív matriky; noviny, když chybí stopa kvůli stěhování, nebo když jde o úředníka/vojáka a chceme příběh.

## Ručně stažené knihy (složka s `obsah.txt`) – kterýkoli archiv
Když archiv skripty nepouští (ALTCHA, blokace) nebo je rychlejší stáhnout celou knihu, stáhne ji uživatel tlačítkem
na portálu do `pracovni/<původní název>/` spolu s **`obsah.txt`** (popis knihy, na konci odkaz s číslem knihy).
Na stránku svazku v archivu kvůli tomu **nechoď** – vše je v `obsah.txt`.
1. Klíč svazku vezmi z čísla v odkazu: eBadatelna `ebad_<matrikaId>`, ARON `<apu>`, Porta fontium `pf_<kniha>`.
2. Složku přejmenuj na `pracovni/<klíč>_<název>_manual/` (název = část názvu svazku před první čárkou, bez
   diakritiky, malými, mezery a `-` jako `_`, např. `ebad_12345_horni_lhota_3_manual`); klíč ve `svazky.json` je bez přípony.
3. Snímky přejmenuj na `s<n>.jpg` podle pořadí (bez úvodních nul).
4. Do složky napiš `obsah.md` (roky, co kniha obsahuje, rejstříky a jejich snímky); kotvy rok → snímek rovnou do
   `orientace` svazku (`reference/data.md`).
5. Svazek zapiš `zapis.py svazky …` s polem `"upload": "manual"`.
6. Je-li svazek stažený i strojově, ponech verzi s vyšším rozlišením, druhou smaž a zapiš to do deníku.
Složka bez `obsah.txt` → do `todo.md`, ať ho uživatel doplní.

## Ostatní portály – obecný postup
Nástroje pro ně hotové nejsou. Postupuj takto a výsledek zapiš do `STAV.md`, ať to příště víš:
1. Otevři portál v prohlížeči (Claude in Chrome / Playwright, pokud jsou k dispozici; jinak požádej uživatele).
   Najdi fond „Sbírka matrik“ / „Matriky“ a svazek podle obce a let.
2. **Snímek:** většina prohlížečů má tlačítko ke stažení obrázku – ulož do `pracovni/`. Když ne, podívej se v síťovém
   provozu, odkud se načítají dlaždice/obrázky (IIIF, DeepZoom, Zoomify), a stáhni celý obrázek touto cestou – jednotlivě,
   jen snímky, které čteš. Krajní možnost: požádej uživatele, ať snímek uloží a dá do `pracovni/`.
3. **Trvalý odkaz** na snímek (tlačítko „trvalý odkaz“/permalink, jinak URL svazku + číslo snímku) dej do `odkaz` v zápisu.
4. Svazek zapiš do `data/svazky.json` ručně: `"klic": {"archiv": "SOA Třeboň", "portal": "digi.ceskearchivy.cz",
   "svazek": "N Volary 1784–1820, sign. …", "popis": "obce…", "url": "<odkaz na svazek>"}`.
5. Dál stejně jako u ARON: `vyrez.py`, `ramecek.py`, přepis, osoby, deník.
6. Když se postup osvědčí, napiš pro portál vlastní malý nástroj podle `trebon.py` (bez prohlížeče, pokud to jde)
   a postup zapiš do `STAV.md`. Poznatek zapiš i do `poznamky_pro_skill.md` (pro správce skillu).

## Starší prameny (17.–18. století)
- **Soupis poddaných podle víry 1651** – celé rodiny s věkem, po krajích; edice Národního archivu jako PDF
  (nacr.cz, hledej „Soupis poddaných podle víry“ + kraj). Fulltext v PDF, příjmení často bez diakritiky / s jinou ortografií
  (Šaršoun → „Šaroun“, dlouhé ſ jako f). Ves je v rámci panství; poznamenej si stránku edice.
- **Berní rula 1654** – jen hospodáři s půdou; edice a rejstříky v knihovnách (Kramerius/DNNT).
- **Gruntovní (pozemkové) knihy** – převody domů z otce na syna; online jen část (SOA Plzeň téměř vše, SOA Praha část,
  ostatní spíš badatelna). Fond „Velkostatek <panství>“.
- **Zemské desky** (Národní archiv; Morava MZA Brno) – evidence **deskových statků**: šlechta, svobodníci, majitelé
  deskových dvorů a některá města. Poddaní sedláci a chalupníci v nich nejsou (ti jsou v gruntovních knihách).
  Vyplatí se jen u předka-svobodníka nebo majitele statku; středověké a raně novověké zápisy částečně jako edice
  v Czech Medieval Sources (`https://sources.cms.flu.cas.cz/`, kategorie „Desky zemské“). Originály jen v badatelně.
- **Mlýny a mlynáři – vodnimlyny.cz** (`https://www.vodnimlyny.cz/mlyny/objekty/`; `databaze.vodnimlyny.cz` neexistuje).
  Karta mlýna má sekci **Historie** s držiteli mlýna v chronologickém sledu (z gruntovních knih, urbářů, katastrů),
  prameny a fotky. Vyplatí se, když je předek mlynář nebo se narodil „ve mlýně“: rod na mlýně přes generace, příběh
  a obrázky na web. Hledá se podle obce, katastru, toku i jména mlynáře (pole jsou dobrovolná – „nenalezeno“ nic
  nedokazuje). Bez prohlížeče (přes `slusne.py`): GET `/mlyny/objekty/` (cookies), pak POST tamtéž s hlavičkou
  `X-Requested-With: XMLHttpRequest` a poli `_do=filter-form-submit`, `city=<Obec>` (nebo `miller=<Příjmení>`),
  `send=Filtrovat` → JSON, výsledky v `snippets["snippet--items"]`; přesný název obce dá `?do=citySuggestions&q=<Obec>`.
  Údaje z karty jsou odkaz na pramen, ne doklad – předka ověř v matrice nebo gruntovní knize.
- **Mapy stabilního katastru (1824–43)** – kde stál dům s číslem popisným: archivnimapy.cuzk.cz (Archiv ČÚZK).
  Na **císařských otiscích** chybí u části listů barvy a čísla domů. Lepší jsou **indikační skici**: mají čísla domů
  a u pozemků jméno majitele („N. 13“ = patří k domu čp. 13). Dům bez pozemků mimo ves = domkář bez polí.
  Jméno majitele samotného domu bývá jen v písemném operátu (archiv, ne online). Výřezy map patří na web k rodině.
- **Obce, které byly do roku 1920 v Dolních Rakousích** (Valticko: Valtice/Feldsberg, Hlohovec/Bischofswarth,
  Poštorná/Unter-Themenau, Charvátská Nová Ves/Ober-Themenau, Úvaly/Garschönthal…, i část Vitorazska) indikační skici
  v MZA nemají. Rakouský stabilní katastr („Franziszeischer Kataster“, kolem 1821) je online v NÖ Landesarchiv:
  `https://www.noela.findbuch.net/` (hledej německý název obce):
  - **FK Mappen UM <č.>**: barevná mapa obce (~5600 × 4600 px), stavební parcely černě, pozemky červeně; čísla domů
    ani jména na ní nejsou.
  - **FK Prot UM <č.>** (protokol stavebních parcel): u parcely majitel, stav (Halblehner = půlláník, Häusler = domkář),
    bydliště a **číslo domu** – číslo parcely z mapy tak vede k domu a majiteli.
  - **BG <okresní soud> …**: pozemkové knihy (Grundbuch, Gewährbuch od 18. stol.) a pozůstalostní inventáře
    (Inventurprotokolle), často naskenované.
  - Bez prohlížeče (přes `slusne.py`): cookie z `…/php/view.php?link=…`, pak `php/gtpc.php?be_id=<fond>&ve_id=<id>&count=<0..n>`
    (fond 4092 = mapy, 4091 = Prot, 4094 = Operate; prázdná odpověď = konec nebo bez skenů). `id` vrátí hledání
    `php/rech_start.php?rech_nr=1` (POST `words=<obec>&max=500&…`, po načtení `main.php`; JSON, signatura v klíči hexadecimálně).
    Server obrázků `augias.noel.gv.at` je dostupný jen přes `gtpc.php`.
- **Dnešní adresa domu** podle čísla popisného: RÚIAN (ČÚZK, vrstva AdresniMisto). Pozor, staré centrum mívá od 19. století
  stejná čp., ale předměstí a vesnice čísla přečíslovávaly. Hodí se na „procházku po stopách předků“.
  Stavbu podle obce a čísla popisného najde i nahlizenidokn.cuzk.gov.cz (ověření adresy z dokladu); vlastník je za
  CAPTCHou a je to údaj o žijícím člověku – nezjišťuj ho.

## Vojenské prameny (1. světová válka, kmenové listy)
Pro muže narozené ~1865–1900. Starší: matriky, Musterlisten, Kriegsarchiv Vídeň.
- **Seznamy ztrát (Verlustlisten) 1914–1918** – ANNO (`tools/anno.py`) a Kramerius MO `https://kramerius.army.cz`
  (veřejné API v5 `…/search/api/v5.0/search?q=text_ocr:"…" AND fedora.model:page`). Zápis: „Příjmení Jméno, hodnost,
  IR. Nr., rota, Mähren/Böhmen, okres a obec německy, rok narození; verw. / kriegsgef. / gefallen (datum)“.
  Hledej **obec** v několika německých a OCR tvarech, nejen jméno. Doplňovací okrsek okresu = číslo pluku, další
  vodítko. Rodiče tam nejsou → ztotožnění jen `prob` (rok + obec + okres + pluk).
- **Databáze VHA** (`https://www.vuapraha.cz/databaze-vha/`): padlí v 1. sv. válce (~186 tis.), legionáři, padlí
  ve 2. sv. válce. Formulář je JS; jde volat REST `POST https://www.vuapraha.cz/wp-json/mo/v1/archive-database/html`
  s JSON `{"page":1,"surname":"…","name":"","place":"","date":"","database":"fallen-first"}`
  (`legio`, `fallen-first`, `fallen-second`, `abroad-second`) přes `slusne.py curl`. Příjmení = podřetězec, místa
  bývají zkomolená (jiná ves téhož okresu) → kontroluj rok, okres a pluk.
- **Bílá kartotéka a úmrtní matriky pluků** (`/kartoteky/`, `/vojenske-matriky/`): originální zápis o smrti vojáka;
  pluk zjisti ze seznamu ztrát.
- **Kmenové listy** (VHA Praha) online nejsou, jen placená rešerše (jméno + rok narození). **Ročníky 1887–1900
  a 1903–1910 jsou skartované** – smysl mají pro ročníky 1865–1886.
- **Seznamy ztrát v ANNO** hledej podle **domovské obce v německém tvaru** – účinnější než příjmení:
  `ANNO_TITLE=vll python3 -I tools/anno.py '"Oberdorf"' 1914 1919 3 --snip` (zkratky titulů `vll`, `vlv`, `nvv`).
  Přehled všech digitalizací dává VHÚ (`https://www.vhu.cz/`, knihovna → „Seznamy ztrát rakousko-uherské armády“).
- **Vojenské úmrtní matriky 1. sv. války** (podle VHÚ přes 160 000 padlých) jsou v Digitální studovně MO
  (`https://digitalnistudovna.mo.gov.cz/`), mj. „Matriky pěšího pluku N“ (N = číslo čs. pluku, který převzal c. a k. pluk).
  Fulltext přes Kramerius v5: `python3 -I tools/kramerius.py 'text_ocr:"Horní Lhota"' 10 --server https://kramerius.army.cz`.
  Když Python neověří certifikát serveru (CERTIFICATE_VERIFY_FAILED), **kontrolu nevypínej** – stejný dotaz pusť přes
  `slusne.py curl` (systémové certifikáty) nebo hledej v prohlížeči.
- **Kriegsarchiv Vídeň** (offline): Grundbuchblätter starších ročníků, vojenské matriky po plucích, kartotéky ztrát
  a zajatců. Do `archivni_dotazy.md` jméno, datum a místo narození, **domovskou obec** (Heimatrecht ≠ rodiště) a pluk –
  bez pluku se vojenská matrika hledat nedá.
- **Pomníky a hroby** (nevyzkoušeno): pomník padlých v obci bývá jediný záznam o nezvěstném – `https://www.vets.cz/`
  (pietní místa, pamětní desky s fotografiemi), Centrální evidence válečných hrobů `https://valecnehroby.army.cz/`;
  příběhy legionářů `https://www.legie100.com/`. V datech pluk, hodnost a osud slovy („voják c. a k. pěšího pluku 28,
  padl 1915 v Haliči“), zdroj `J`; jména padlých na web se souhlasem rodiny.

## Oběti a vězni 2. světové války – `tools/obeti.py`, `arolsen.py`, `mauthausen.py`, `vezni.py`
Kdy: předek (nebo sourozenec) zmizí z pramenů 1939–1945, rodina mluví o deportaci, koncentráku, gestapu, Terezíně či
nuceném nasazení, nebo je v matrice/sčítání židovská či romská rodina. Pořadí: `obeti.py` (Židé z českých zemí, Lety) →
`vezni.py` (čeští političtí i rasově pronásledovaní vězni) → `mauthausen.py` (zemřelí v Mauthausenu) → `arolsen.py`
(kartotéky táborů, transporty, nucené práce, DP po válce – i přeživší).

**Souhlas s podmínkami (`tools/souhlas.py`).** Databáze obsahují citlivé údaje; holocaust.cz a Arolsen žádají při vstupu
potvrzení podmínek, u Mauthausenu a Památníku Terezín ukazuje nástroj vlastní upozornění. Nástroj bez zapsaného souhlasu
**nic nestahuje** (skončí kódem 4 a řekne, co spustit). Souhlas potvrzuje **jen uživatel** sám v terminálu:
`python3 -I tools/<nástroj>.py souhlas` (v Claude Code `!…`), přečte znění a napíše „ano“. Claude ho nikdy nepotvrzuje
za uživatele, ani přes `SOUHLAS_STAV`. Platí 30 dní na počítači a jen pro dané znění (změní-li se, zeptá se znovu);
`python3 -I tools/souhlas.py stav` vypíše platné souhlasy. Na pojistce se neptej opakovaně – když souhlas platí, nástroj jede.

- `obeti.py hledat --prijmeni Nováková [--jmeno] [--bydliste] [--misto-narozeni] [--rok] [--stran N]`; `obeti.py detail <odkaz>`
  – databáze obětí holocaust.cz (Terezínská iniciativa): narození, transporty, osud, dokumenty. Příjmení i v ženském tvaru.
- `vezni.py hledat --prijmeni Novák [--jmeno] [--narozeni "15. 3. 1910"] [--misto] [--cislo] [--stran N]`; `vezni.py detail <odkaz>`
  – Památník Terezín: Buchenwald, Dachau, Flossenbürg, Mauthausen, Ravensbrück, ghetto a Malá pevnost Terezín, Pankrác.
  Zkus s diakritikou i bez.
- `mauthausen.py hledat "Novak 1905" [--stran N]` – Raum der Namen: jen zemřelí v Mauthausenu a pobočkách, jména v místním tvaru.
- `arolsen.py hledat "Novák Josef 1905" [--misto-narozeni] [--rodne] [--cislo] [--narodnost] [--vyznani] [--podrobne] [--max N]`;
  `arolsen.py karta <id> pracovni/arolsen.jpg` – obrázek karty (přes sdílenou mezipaměť `cache.py`). Datum v databázi je m/d/r,
  nástroj ho převádí. Údaje jen pro osobní, vědecké a genealogické účely (podmínky Arolsen); dokumenty před zveřejněním
  podle jejich Terms of Use.

Všechny jdou přes brzdu `slusne.py`; neprocházej databáze hromadně. Shoda jména není ztotožnění – ověř datum a místo
narození v matrice a v rodině. Nalezené údaje jsou citlivé: do dat projektu ano, na web jen se souhlasem rodiny (`soukromi.md`).
Kdyby portál začal vyžadovat přihlášení, captchu nebo vracel 403, nástroj to ohlásí – hledej ručně v prohlížeči, neobcházej to.

## Odsun Němců z pohraničí 1945–1946 a Češi vysídlení v roce 1938
Pro předky z pohraničí (Sudety, Slezsko, jižní Morava, Šumava), kteří byli Němci a po válce museli odejít, a pro Čechy,
kteří odešli z pohraničí po záboru 1938. **Bez nástroje – dopisy, prohlížeč a návštěva archivu; skriptem se nic nestahuje.**
- **Dvě fáze.** Léto 1945 = takzvaný divoký odsun (vyhánění bez seznamů, zápisy chybí nebo jsou neúplné). 1946 =
  organizovaný odsun v transportech do americké a sovětské okupační zóny. Zachované **transportní listiny** (kdo odjel,
  kterým transportem a kdy) jsou **z roku 1946, ne z roku 1945**.
- **Matriky zůstaly v českých archivech** (SOA Litoměřice, SOA Plzeň, ZA Opava – oddíly výše). Narození, sňatky a úmrtí
  do odsunu tam najdeš, **odsun sám a osud po něm ne**. Po 1945 se místa přejmenovala – hledej německý i český název obce
  i farnosti (pomůže GOV, `https://gov.genealogy.net/`, jen v prohlížeči – kontrola Anubis).
- **Transportní listiny 1946** – Sudetendeutsches Museum (Mnichov) má kopie asi 1290 listin s kolem milionem jmen
  (55–60 % transportů, asi 80 % transportů do americké zóny; originály ve Vojenském ústředním archivu v Praze):
  `https://www.sudetendeutsches-archiv.de/transportlisten-der-vertreibung-1946/`. **Chybí** transporty do sovětské zóny
  a divoký odsun 1945. **Hledání podle jména jen na přístroji v muzeu** (z právních důvodů ne online). Muzeum za vás
  nehledá; na písemný dotaz (přesné datum a místo transportu, příjmení, jméno, věk, poslední bydliště, poštovní adresa
  odesílatele) pošle sken jednoho vagonu – kontakt na stránce výše. Datum a nakládací stanici zjistíš z přehledu
  transportů 1946 (W. Jun, nekompletní):
  `https://sudetendeutsche-familienforscher.de/wp-content/uploads/2020/05/Verzeichnis_Vertreibungstransporte_1946_V9.pdf`.
  **Skoro úplné listy bývají v okresních archivech podle místa odjezdu** (adresy `https://www.cesarch.cz/archivnictvi/adresar-archivu/`).
- **České úřední spisy o odsunu a konfiskacích**: fondy ONV a MNV 1945–1948 (referáty pro odsun, konfiskace,
  osídlování), např. dílčí inventář „Okresní národní výbor Ústí nad Labem (odsun Němců), 1945–1948“ (SOA Litoměřice).
  Seznamy Němců podle transportů a čísel domů hledej v inventáři okresního archivu podle obce → `archivni_dotazy.md`.
  Archiv bezpečnostních složek (`https://www.abscr.cz/`) má regionální spisy „Odsun Němců 1946“ (obsah neprověřen).
  Část Němců z odsunu vyňali (smíšená manželství, specialisté, antifašisté) – ti jsou v matrikách i po 1946.
- **Německá strana**: Lastenausgleichsarchiv Bayreuth (Bundesarchiv, `https://www.bundesarchiv.de/`) – akta o vyrovnání
  škod vyhnanců, Ostdokumentation, Heimatortskartei. Jen písemně; **od 16. 1. 2026 do 31. 12. 2027 vyřizuje jen naléhavé
  dotazy, rodinné bádání ne** (znovu od 1. 1. 2028). Dál Arolsen (`arolsen.py`), matriky nové obce v Německu/Rakousku,
  Suchdienst Červeného kříže (nevyzkoušeno).
- **Češi a odpůrci nacismu, kteří odešli z pohraničí 1938–1939** (nevyzkoušeno): uprchlické spisy v okresních archivech,
  policejní spisy (Národní archiv, Policejní ředitelství Praha), literatura J. Benda, *Útěky a vyhánění z pohraničí
  českých zemí 1938–1939*, a M. Frankl, *Občané země nikoho*. Nejdřív se zeptej rodiny na doklady (uprchlická legitimace).
- **Rodina:** doklady z odsunu (seznam zavazadel, odsunový list, Vertriebenenausweis) bývají doma; číslo transportu
  a stanice nakládky (Verladestation) zkrátí hledání. Údaje jsou citlivé – na web jen se souhlasem rodiny (`soukromi.md`).

## Příjmení dnes a DNA
- **Rozšíření příjmení dnes**: kdejsme.cz (počty nositelů po okresech). Rychle ukáže, jestli je příjmení vzácné a kde
  jsou jeho „hnízda“. Při hledání vzdálených příbuzných vyškrtni vlastní rodinu.
- **DNA** (jen když o to uživatel stojí, a jeho rozhodnutí): autosomální test (MyHeritage, Ancestry) najde bratrance
  do ~5. kolene. **Y-DNA** (FamilyTreeDNA, Y-37 až Big Y) se dědí po meči beze změny. Ověří, jestli dvě linie stejného
  příjmení mají společného předka, a u nemanželského dítěte může shoda s jiným příjmením ukázat otce. Kontakt se žijícími
  příbuznými vždy jen přes uživatele.
Všechno, co jde jen v badatelně, zapisuj do `data/archivni_dotazy.md` (archiv, fond, inventární číslo, co hledat).
