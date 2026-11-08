# Rodokmen plus – skill pro Claude Code

Průvodce, se kterým si v [Claude Code](https://claude.com/claude-code) uděláte **rodokmen z českých matrik** a **dějiny
domů, ve kterých vaše rodina žila**, a z obojího jeden rodinný web. Claude stahuje a čte snímky matrik, sčítání lidu
a katastrů, zapisuje nálezy s výřezy a přepisy a staví web. Vy dodáváte znalost rodiny, rozhodujete sporná místa
a schvalujete, co jde ven. Zkušenosti s genealogií ani programováním nejsou potřeba.

Mluví česky a míří na české a moravské archivy (ARON, SOA Třeboň, Porta fontium, eBadatelna, AHMP, MZA Brno, Archiv ČÚZK…).

## Odkud to je
Plugin navazuje na dva skilly a velkou část z nich přebírá. Patří jim za to dík:
- **[rodokmen](https://github.com/sarsonj/rodokmen-skill)** od Jindřicha Šaršona (verze 0.5.0) – postup od rozhovoru
  s rodinou přes matriky k webu, nástroje pro archivní portály, šablona webu, metodika čtení matrik,
- **[dejiny-domu](https://github.com/vzoha/dejiny-domu-skill)** od Vojtěcha Žohy (verze 0.3.7) – dějiny domu a vsi
  z gruntovních knih, katastrů a sčítání, společný limit rychlosti k archivům (`slusne.py`, `hlidac.py`), RÚIAN, Archiv ČÚZK.

Pokud vám stačí jen rodokmen, nebo jen dějiny jednoho domu, použijte klidně původní skilly – jsou jednodušší.

### Co je tu navíc
- **Graf osob místo čísel.** Osoby mají trvalé id a vazby jsou hrany (rodič, manželé, kmotr, svědek). Kekulého čísla
  se dopočítají od libovolného kořene, takže jde mít víc kořenů (vy i partner), sourozence a boční příbuzné jako
  plnohodnotné osoby a ptát se „jak je X příbuzný s Y“ (volitelně přes Prolog). Starý formát převede `migrace_graf.py`.
- **Jeden projekt pro osoby i domy.** Pole `bydliste` u osoby a odkaz z domu na osobu; z bydlišť předků vznikne fronta
  domů, jejichž dějiny se vyplatí zpracovat. Kontrola hlídá křížové odkazy, web má stránky domů.
- **Čtení portálů za ověřením (ALTCHA)** v Chromu uživatele – šetrně, s limity a bez obcházení ochrany
  (skill `matriky-v-prohlizeci`, včetně MZA Brno: Acta Publica, sčítací operáty a indikační skici Moravy).
- **Ztotožnění míst a příjmení** – německé a zkomolené názvy obcí, homonyma, slovníky tvarů (skill `ztotozneni-mist`).
- **Paralelní bádání** – víc pomocníků na vlastních větvích, fronta úkolů, šablona zadání, ověřovací vlna,
  hledání příběhů ve vlnách a skrytých vazeb z kmotrů a svědků (skill `paralelni-badani`).
- **Web v2** – strom po generacích i celý strom, rodové pásy, časová osa, odkazy mezi osobami se zpětnými zmínkami,
  příběhy, stránky domů, světlý i tmavý vzhled, přihlášení jen pro rodinu.

### Převzato z forků
Nápady z forků původního skillu, přepsané na graf osob (licence MIT):
- `tools/fronta.py` – fronta hledání (chybějící rodiče, neuzavřené rody) ze
  [srameko/rodokmen-skill@5f25edb](https://github.com/srameko/rodokmen-skill/blob/5f25edb9a201f8ac03b79293bbcb79b5109d022e/skills/rodokmen/tools/fronta.py) (srameko),
- `tools/kmotri.py` – kmotři a svědci jako stopy ze
  [srameko/rodokmen-skill@5f25edb](https://github.com/srameko/rodokmen-skill/blob/5f25edb9a201f8ac03b79293bbcb79b5109d022e/skills/rodokmen/tools/kmotri.py),
  původně z [micl79/rodokmen-skill@11cf9ba](https://github.com/micl79/rodokmen-skill/blob/11cf9bad06c454f8415625a23a7b9e49d13c75e3/skills/rodokmen/tools/kmotri.py) (micl79),
- pravidla hledání (víc předků jedním průchodem, okno ±5 let, sourozenci, kmotři jako stopy, ručně stažené knihy
  s `obsah.txt`) v `SKILL.md` a `reference/portaly.md` ze
  [vmi43/rodokmen-skill@b89d5c9](https://github.com/vmi43/rodokmen-skill/blob/b89d5c91d78e61b8e20b9f2eab8b20d2f8e02e06/skills/rodokmen/SKILL.md) (Vasek M.),
- `tools/nahledy.py` – mřížka náhledů pro rychlé procházení rozsahu snímků ze
  [xsigik/rodokmen-skill@6a62def](https://github.com/xsigik/rodokmen-skill/blob/6a62def5e10ab169018282a124f033fe4280be71/skills/rodokmen/tools/nahledy.py) (Jakub Valenta, xsigik, #10),
- `tools/sito.py` – síto pro knihy bez rejstříku (dávky náhledů s deníkem prošlých snímků), myšlenka „Síta Jev“ ze
  [xsigik/rodokmen-skill@9aa2c18](https://github.com/xsigik/rodokmen-skill/blob/9aa2c189892885f579df3043a2da04ed245f23e6/skills/rodokmen/tools/sito.py) (xsigik, #21–#24; fork ve verzi
  [c262de7](https://github.com/xsigik/rodokmen-skill/tree/c262de702464b9743d4782abe1b296aa77bd34d4)),
- `tools/mista.py` – geokódování obcí a čísel popisných z faktů osob: Mapy.com s klíčem `MAPY_API_KEY` ze
  [vmi43/rodokmen-skill@99e238e](https://github.com/vmi43/rodokmen-skill/blob/99e238ed18636f9a9fca481071761fefd7dbec66/skills/rodokmen/tools/mista.py) (Vasek M.),
  bez klíče Nominatim jen sídla a varování na vzdálenou obec ze
  [hackra76/rodokmen-skill@59ba1e6](https://github.com/hackra76/rodokmen-skill/blob/59ba1e666208af7888f6dd4dd5dc54e7c2706807/skills/rodokmen/tools/mista.py) (hackra76, 0.8.1),
  domy bez klíče z RÚIAN.

## Co je v repozitáři
```
.claude-plugin/                 instalace jako plugin
skills/rodokmen-plus/           jádro: SKILL.md (režimy osoba a dům), tools/, template/ (projekt a web), reference/
skills/matriky-v-prohlizeci/    čtení portálů za ALTCHA v prohlížeči, reference MZA
skills/ztotozneni-mist/         ztotožnění obcí a příjmení
skills/paralelni-badani/        pomocníci, větve, briefy, vlny příběhů
```

## Co budete potřebovat
- Claude Code s předplatným, které unese delší práci (velké kolo hledání stojí dost kreditů).
- Python 3.9+, Node.js 20+ (nebo Bun), ImageMagick 7 a git – Claude vám s instalací pomůže.
- Pro portály za ověřením (MZA Brno) Chrome s rozšířením Claude in Chrome. Bez něj zbytek funguje, jen Morava hůř.
- Volitelně SWI-Prolog (`swipl`) na dotazy o příbuzenství.

## Instalace
V Claude Code napište:
```
/plugin marketplace add zbysekvoda/rodokmen-plus
/plugin install rodokmen-plus@rodokmen-plus
```
a Claude Code restartujte. Aktualizace: `/plugin marketplace update rodokmen-plus`.

Ručně: zkopírujte čtyři složky ze `skills/` do `~/.claude/skills/` a restartujte Claude Code.

Máte-li zároveň nainstalované původní skilly `rodokmen` nebo `dejiny-domu`, pro jeden projekt používejte jen jeden
z nich – formát osob se liší.

## První spuštění
Napište třeba:
> Chci udělat rodokmen své rodiny.

nebo
> Koupili jsme starou chalupu v Horní Lhotě čp. 12 a zajímá mě, kdo v ní žil.

Claude zkontroluje programy, založí složku projektu a začne se ptát. Ukázkový projekt s fiktivními daty si můžete
nechat založit předem, ať vidíte, jak web vypadá.

## Soukromí a šetrnost
- Data zůstávají ve složce projektu na vašem počítači. Na web jde jen to, co schválíte; žijící lidé jen jménem a rokem
  narození. Web je ve výchozím stavu za přihlášením pro rodinu.
- Archivy blokují IP adresy po sérii rychlých dotazů. Nástroje mají společný limit a projekt nastaví hook, který zastaví
  vlastní skripty jdoucí mimo něj. Ověření typu ALTCHA ani CAPTCHA skill neobchází a smyčkové stahování zakazuje.
- Projekt po založení obsahuje hook `tools/hlidac.py` (kontroluje síťové příkazy v Bashi). Plugin sám žádné hooky
  ani MCP servery nemá. Nechte zapnuté schvalování příkazů, dokud si nezvyknete, co Claude dělá.
- Skripty chodí jen na archivní portály, Wikipedii, Kramerius a ANNO, RÚIAN a ČÚZK, OpenStreetMap a při instalaci
  webu na registr npm; na hosting jen když web sami zveřejníte.

## Verze a aktualizace
Verze je v `.claude-plugin/plugin.json` a `skills/rodokmen-plus/VERZE` (projekt si ji pamatuje v `.skill_verze` a skill
při neshodě nabídne aktualizaci). Aktualizace pluginu: `claude plugin marketplace update rodokmen-plus` a
`claude plugin update rodokmen-plus@rodokmen-plus`; pak v projektu `novy_projekt.py` na stejnou složku (data zůstanou).

Vydání (správce): `scripts/release.sh X.Y.Z` – kontrola, že v repu nejsou jména a obce ze soukromého rodokmenu
(`scripts/kontrola_soukromi.py`, cesta v `RODOKMEN_SOUKROMA_DATA`), zvednutí verze, commit a tag `vX.Y.Z`;
`scripts/release.sh X.Y.Z --push` ho pošle na GitHub.

## Převzato z forků
Nápady a kód z forků původního skillu (MIT):
- významné osobnosti `tools/osobnosti.py` (pole `vyz`, stránka `/osobnosti/`) a stránka Statistiky (`/statistiky/`,
  výpočet přepsaný do `web/src/lib/statistiky.js`):
  [hnizdiljan/rodokmen-skill@d172316](https://github.com/hnizdiljan/rodokmen-skill/tree/d172316bc190d0f44894fa67115505729d587c6a/skills/rodokmen) (hnizdiljan),
  starší varianta [Brunobeee/rodokmen-skill@7ad48a8](https://github.com/Brunobeee/rodokmen-skill/blob/7ad48a869981282ab815520bfa295ee534290b3b/skills/rodokmen/tools/osobnosti.py) (Brunobeee),
  původně PR #23 od oskar-stierand v sarsonj/rodokmen-skill
- brzda `tools/slusne.py` – Retry-After (sekundy i datum HTTP) a hlavičky RateLimit-*/X-RateLimit-*:
  [jozefizso/rodokmen-skill@38850a5](https://github.com/jozefizso/rodokmen-skill/blob/38850a5aa4dbebe3faf1eb6ed5c5e8c9007c2d68/skills/rodokmen/tools/slusne.py) (Jozef Izso);
  sdílený limit pro všechny síťové nástroje a dlaždice sekvenčně podle
  [vmi43/rodokmen-skill@b89d5c9](https://github.com/vmi43/rodokmen-skill/blob/b89d5c91d78e61b8e20b9f2eab8b20d2f8e02e06/skills/rodokmen/tools/slusne.py) (Vasek M.)
- nezávislý audit zápisu `tools/audit.py` (podklad pro auditora-subagenta Claude místo Codexu) a postup
  „čtenář na levnějším modelu + auditor“ v `paralelni-badani` podle verze 0.11:
  [jozefizso/rodokmen-skill@38850a5](https://github.com/jozefizso/rodokmen-skill/blob/38850a5aa4dbebe3faf1eb6ed5c5e8c9007c2d68/skills/rodokmen/tools/audit.py)
  a [rodokmen-orchestrace](https://github.com/jozefizso/rodokmen-skill/blob/38850a5aa4dbebe3faf1eb6ed5c5e8c9007c2d68/skills/rodokmen-orchestrace/SKILL.md) (Jozef Izso)
- `tools/smoke_test.py` – podle
  [hnizdiljan/rodokmen-skill@d172316](https://github.com/hnizdiljan/rodokmen-skill/blob/d172316bc190d0f44894fa67115505729d587c6a/skills/rodokmen/tools/smoke_test.py) (hnizdiljan)
  a [srameko/rodokmen-skill@5f25edb](https://github.com/srameko/rodokmen-skill/blob/5f25edb9a201f8ac03b79293bbcb79b5109d022e/skills/rodokmen/tools/smoke_test.py) (Ondrej Sramek)
- vlastní pole osoby (`p.extra`) a doplňky webu ve `web/src/local`, které aktualizace nepřepíše:
  [xsigik/rodokmen-skill@318a965](https://github.com/xsigik/rodokmen-skill/commit/318a965d6a5df9a5078657747377f16ccc83f345) (Jakub Valenta, xsigik)
- sdílená mezipaměť snímků `tools/cache.py` a mapa knihy `tools/mapa_knihy.py`:
  [sarsonj/rodokmen-skill@f0f8337](https://github.com/sarsonj/rodokmen-skill/tree/f0f833745d0456dd8644803e1c8708c3e9817f66) (Jindřich Šaršon, sarsonj);
  kontrola integrity mezipaměti (verze 0.8.1):
  [hackra76/rodokmen-skill@59ba1e6](https://github.com/hackra76/rodokmen-skill/commit/59ba1e666208af7888f6dd4dd5dc54e7c2706807) (hackra76)
- orientace v knize u svazku (`svazky.json` → `orientace`, #6):
  [xsigik/rodokmen-skill@bca63e4](https://github.com/xsigik/rodokmen-skill/commit/bca63e401b02bde5e4ea644930292f547189d63f) (Jakub Valenta, xsigik)
- `tools/kontrola.py` – čísla domů ve faktech a bydlištích proti citovaným zápisům podle
  [sarsonj/rodokmen-skill@f0f8337](https://github.com/sarsonj/rodokmen-skill/blob/f0f833745d0456dd8644803e1c8708c3e9817f66/skills/rodokmen/tools/kontrola.py#L154-L188)
  (Jindřich Šaršon, pavelzbornik); automatické kontroly dat jako směr podle
  [xsigik/rodokmen-skill@9d4df44](https://github.com/xsigik/rodokmen-skill/commit/9d4df4466fdc6741612675bb5aeb2fd694f39c22) (Jakub Valenta)
- věk osoby u sňatku a úmrtí na stránce osoby a rodiny (`web/src/lib/data.js`: `ageAt`, `factWithAge`, verze 0.7.1):
  [xkraust/rodokmen-skill@79d3685](https://github.com/xkraust/rodokmen-skill/blob/79d36850afaa080b0ebcf70a368cbbb5237d700e/skills/rodokmen/template/web/src/lib/data.js) (xkraust)
- upozornění na časovou návaznost v časové ose (`web/src/lib/navaznost.js`, ⚠ u pruhu a seznam „Co časově nesedí“) podle
  [mplisek/rodokmen-skill@cc35533](https://github.com/mplisek/rodokmen-skill/blob/cc35533cda7753a31e87f915fef6555542df1798/skills/rodokmen/tools/chronologie.py) (Martin Plíšek, mplisek)

## Zpětná vazba
Chyby a nápady (bez údajů o rodině) zakládejte jako issue v tomto repozitáři. Týká-li se věc převzatých částí,
zvažte poslat ji i autorům původních skillů.

## Licence
[MIT](LICENSE). Původní části © Jindřich Šaršon a Vojtěch Žoha, nové části © Zbyšek Voda. Výjimkou je metodická
příručka `reference/playbook.md` (převzatá rešeršní zpráva bez uvedeného autora, MIT se na ni nevztahuje).
