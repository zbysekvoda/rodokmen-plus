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

## Zpětná vazba
Chyby a nápady (bez údajů o rodině) zakládejte jako issue v tomto repozitáři. Týká-li se věc převzatých částí,
zvažte poslat ji i autorům původních skillů.

## Licence
[MIT](LICENSE). Původní části © Jindřich Šaršon a Vojtěch Žoha, nové části © Zbyšek Voda. Výjimkou je metodická
příručka `reference/playbook.md` (převzatá rešeršní zpráva bez uvedeného autora, MIT se na ni nevztahuje).
