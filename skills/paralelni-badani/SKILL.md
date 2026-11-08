---
name: paralelni-badani
description: Orchestrace víc pomocníků (subagentů) při bádání v archivech pro rodokmen a dějiny domů – fronta úkolů, levnější model pro pomocníky, každý na vlastní git větvi s integrační větví, deník s předem přidělenými čísly řádků, šablona briefu (doloženo vs. hypotéza, limity portálů), ověřovací vlna, hledání příběhů ve vlnách a hledání skrytých vazeb z hotových přepisů (kmotři, svědci, sousedé) a nezávislý audit zápisů subagentem (tools/audit.py). Použij, když chce uživatel „velké kolo“, pustit víc agentů najednou, projít víc svazků nebo rodů souběžně, autonomní noční bádání, najít příběhy pro web nebo skryté příbuzenské vazby. Spouštěcí fráze: „pusť pomocníky“, „paralelně“, „velké kolo“, „projdi všechny“, „najdi příběhy“, „kdo byl kmotr“, „skryté vazby“, „audit“, „druhý pohled“.
---

# Paralelní bádání s pomocníky

Pomocníci zrychlí velké kolo, ale bez pravidel si přepisují soubory, tlučou do stejného archivu a jejich nejistá čtení
se dostanou do dat jako fakta. Tenhle skill to drží v pořádku. Patří ke skillu `rodokmen-plus`.

Před velkým kolem řekni uživateli, co plánuješ (kolik pomocníků, na co, odhad času) a nech si to schválit. Pomocníci
stojí kredity.

## Role
- **Koordinátor (ty, hlavní model)**: fronta, briefy, integrace, ověření čtení na snímku, zápis `doc`, komunikace s uživatelem.
- **Pomocník** (Agent s levnějším modelem, např. `model: "sonnet"`): hledání a první čtení. Do `data/` zapisuje jen
  na své větvi podle briefu, nebo vůbec (varianta „jen pracovni“ – viz níže). Nikdy nemerguje, nenasazuje, neposílá ven.
  Uživateli vysvětli: pomocník nečte hůř, je to princip čtyř očí – nemá kontext (dvě rodiny téhož jména ve vsi).

## Fronta úkolů – `data/fronta_ukolu.md`
- Oddíly: **Otevřené online** (s prioritou), **Rozpracováno** (kdo, větev), **Hotovo**, **Mimo internet**
  (→ `archivni_dotazy.md`), **Slepé uličky** (s důvodem, ať se nezkoušejí znovu).
- Bod fronty = jedna otázka + kde hledat: „křest Jana Nováka ~1820, N Horní Lhota sv. 3, nejdřív index N“.
  **U každého bodu ověř druh knihy** (matrika × rejstřík, N/O/Z, roky) – fronta zapsaná podle katalogu se plete
  (rejstřík zapsaný jako matrika pošle pomocníka listovat nesprávnou knihu).
- Pomocník po skončení označí svůj bod `[x]` (hotovo) nebo `[!]` (zaseknuto, s důvodem) a připíše nové stopy.

## Rozdělení práce
- **Po portálech, ne po osobách.** Pomocníci na stejném portálu sdílí jeho limit – tři pomocníci na jednom archivu
  nejsou rychlejší než jeden. Pro portály za ověřením v prohlížeči nejvýš 2 současně (`matriky-v-prohlizeci`).
- Offline úkoly (čtení už stažených snímků, analýza přepisů) jdou souběžně bez limitu.
- Rozsah jednoho briefu ~1–2 h práce. Typicky 3–4 pomocníci najednou.

## Větve a integrace
- Každý pomocník pracuje ve **vlastním worktree a větvi** (`pom/<úkol>`) z aktuální hlavní větve. Neměl by sahat do
  cizích worktree ani do sdíleného scratchpadu (screenshoty a skripty do `pracovni/pom_<úkol>/`).
- Pomocník commituje atomicky na svou větev a **nemerguje**.
- Koordinátor vytvoří **integrační větev** (`integrace/<datum>`), postupně do ní merguje větve pomocníků, po každém
  merge spustí kontroly a teprve celek jde do hlavní větve.
- Data se jen přidávají (nové zápisy, osoby, hrany, řádky deníku), takže **konflikt = ponechat obě strany** a pak
  zkontrolovat duplicity (stejná osoba založená dvakrát pod různým id, stejný zápis pod dvěma klíči).
- Po integraci: `python3 -I tools/graf.py kontrola`, `python3 -I tools/kontrola.py`, build webu.

## Deník – předem přidělená čísla
Souběžně píše do `data/research_log.md` víc agentů. Koordinátor **přidělí každému briefu rozsah čísel řádků deníku
předem** (např. pomocník A 600–619, B 620–639), aby po integraci nevznikly duplicitní čísla. Nepoužitá čísla se nechají
prázdná, to nevadí. Stejně tak u předem přidělených id nových osob, pokud hrozí kolize.

## Šablona briefu
Brief je jediný kontext, který pomocník má. Vlož do něj:
```
Úkol: <otázka z fronty, bod č.>  Rozsah: ~1–2 h.
Repo: <cesta>. Začni: git fetch && git worktree add ../<úkol> -b pom/<úkol> origin/<hlavní větev>.
Přečti: CLAUDE.md, data/STAV.md (pravidla), data/fronta_ukolu.md bod <č.>, konec data/research_log.md.
Skilly: rodokmen-plus (zápis nálezu, graf osob), matriky-v-prohlizeci (je-li portál za ověřením), ztotozneni-mist.
Kde hledat: <portál, kniha, snímky / index nejdřív>. Co už víme: <fakta s klíči zápisů>. Co je vyloučené: <…>.

Pravidla:
- doc jen to, co sám přečteš na snímku. Neověřené a vše, co z něj plyne, označ prob/fam a „(?)“;
  hypotézy do HYPOTEZY (osoby) / ISSUES (domy). Index (rejstřík, FamilySearch) = jen hypotéza do ověření ve zdroji.
- Nejisté čtení není negativní výsledek – zapiš ho jako nejisté. Neúspěšné hledání zapiš s rozsahem.
- U každého prošlého snímku zapiš, co na něm skutečně je (rok, první jméno, čp.).
- Ke každému nálezu: výřez, rámeček jen kolem zápisu, přepis + překlad (i kmotři a svědci), zaznamy, svazky;
  osoby a hrany podle grafového modelu (id = slug, sex povinně), bydliste s čp.
- Deník: tvoje čísla řádků <od–do>. Fronta: svůj bod [x]/[!] + nové stopy.
- Limit <portál>: 1 snímek / <N> s. Čekej: python3 -c "import time; time.sleep(<N>)". Kratší mezery nejsou OK.
- ZAKÁZÁNO: smyčky fetch/XHR/curl, hromadné načítání stránek (ani HTML), obcházení ALTCHA/CAPTCHA, stahování snímků
  mimo prohlížeč z portálu za ověřením. 403/429/503 nebo ověření, které neprojde → přestaň a napiš to v reportu.
- Prohlížeč: vlastní nová záložka, tabId si pamatuj, před každým snímkem ověř URL, cizí záložky nech, svou zavři.
- Na konci: graf.py kontrola, kontrola.py bez chyb; commity atomicky na svou větev. NEMERGOVAT, NENASAZOVAT.
Report: větev a sha, doloženo × pravděpodobné (s klíči zápisů), počet snímků, otevřené otázky, nové stopy.
```
Doplň technické pasti prostředí (macOS zsh; Windows `python -I -X utf8`, `magick`) z `reference/matriky.md`.

Varianta **„jen pracovni“** pro méně zkušené prostředí nebo citlivá data: pomocník nepíše do `data/` vůbec, výsledky
dává do `pracovni/pom_<úkol>/vysledky.json` (klíč, snímek, souřadnice zápisu, přepis, návrh osob a hran) a zapisuje
koordinátor.

## Ověřovací vlna
Žádné čtení pomocníka nejde do dat jako `doc` bez ověření koordinátorem:
1. Projdi report a diff větve. U každého nového `doc` otevři výřez (nebo `tools/overit.py <snímek> x0,y0,x1,y1 pracovni/over`)
   a přečti jména, data a čísla domů sám.
2. Zkontroluj rámeček (jen kolem zápisu), správnost svazku a snímku, a že ztotožnění osoby není jen shoda jména.
3. Co nesedí, sniž na `prob` s poznámkou nebo vrať pomocníkovi (nový brief s přesným snímkem).
4. Do deníku zapiš „ověřeno koordinátorem“ s datem.

## Audit – nezávislý druhý pohled
Po ověřovací vlně (nebo po kole, které přineslo nové `doc` údaje) pusť **auditora**: subagenta s čistým kontextem,
který dostane jen podklad z `tools/audit.py`. Hlídá přepis proti výřezu, nabízí jiné výklady a radí, kde hledat dál.
Koordinátor i pomocník mají kontext a závěry, které je ukotví; auditor ne. (Převzato z `tools/audit.py` forku
jozefizso/rodokmen-skill 0.11, kde audit dělá Codex; tady je to subagent Claude – viz README „Převzato z forků“.)

**Kdy:** po kole s novými `doc` zápisy; u sporného ztotožnění (dvě rodiny stejného jména); než se staví další
generace na jednom zápisu; u kurentu a německých formulářů, kde čtenáři chybují. Ne u každého drobného zápisu –
stačí každé druhé kolo nebo jen klíčové zápisy linie.

**Modely:**
| role | model / effort | proč |
|---|---|---|
| čtenář (hledání, první čtení) | levnější – `model: "sonnet"`, běžný effort | stačí na hledání a první čtení; Haiku na rukopis ne |
| koordinátor (ověření, zápis) | hlavní model | ověřuje na výřezu a píše do `data/` |
| auditor | **jiný model, než který zápis četl**, vyšší effort (`opus` po čtenáři na Sonnetu; `sonnet` po čtení koordinátorem na Opusu), vždy čistý kontext | nezávislost = jiný model + žádný kontext koordinátora |

**Postup:**
1. Změny kola ulož do gitu (ať audit vidí uložený stav).
2. `python3 -I tools/audit.py zadani <klic> [<klic> …] [--kolo N]` → `pracovni/audit/<jméno>_zadani.md`
   (zápis, přepis, svazek, cesty k výřezům, osoby z grafu s rodiči a manželi, kontrolní seznam, schéma odpovědi).
3. Pusť subagenta (Agent, `model` podle tabulky): „Přečti `pracovni/audit/<jméno>_zadani.md` a splň ho. Jen čtení,
   výřezy otevři nástrojem Read, žádná síť. Odpověď (jen JSON) zapiš do `pracovni/audit/odpoved_<jméno>.json`.“
   Do briefu nepiš svůj názor na zápis – zadání stačí.
4. `python3 -I tools/audit.py nacti pracovni/audit/odpoved_<jméno>.json --nazev <jméno>` – zkontroluje schéma,
   uloží `pracovni/audit/<jméno>.json` a vypíše shrnutí.

**Jak naložit s výsledkem** (pole `rozhodnuti`):
- `v_poradku` → pokračuj; `kde_hledat` zařaď do `data/fronta_ukolu.md`.
- `opravit` → oprav po vlastním ověření na výřezu, ne slepě podle auditora.
- `overit_znovu` → přečti zápis znovu sám (`tools/overit.py`); do té doby údaj na `prob`.
- `zeptat_se_uzivatele` → otázky z `otazky_pro_uzivatele` polož uživateli.
- `jine_vyklady` → do `HYPOTEZY` (s tím, čím je ověřit), ne do grafu. Auditor nic nedokládá – je to další čtenář,
  ne zdroj. Do deníku zapiš: audit <jméno>, rozhodnutí, co se s ním udělalo.
- Auditor bez otevřeného výřezu (prázdné `overeno`) = audit jen nad texty; řekni to a nepovažuj přepis za ověřený.

## Hledání příběhů ve vlnách
Pro web (příběh rodu, domu, zajímavosti):
1. **Vlna námětů** – 4–5 pomocníků offline nad daty, každý jinak: podle rodů, podle domů, podle témat (války,
   epidemie, řemesla, migrace, nemanželské děti, dlouhověkost, sňatky příbuzných). Výstup: náměty s klíči zápisů,
   co je doložené a co by bylo potřeba ověřit. Pomůže `tools/napady.py`.
2. **Vlna archivního ověření** – na nejlepší náměty pusť pomocníky do pramenů (úmrtí, noviny, sčítání).
   **Ověření původní námět často vyvrátí** – „voják z Itálie“ je jmenovec, „vyhořelý statek“ je jiné čp.
   Na web jde jen ověřená verze, vyvrácené náměty zapiš do deníku, ať se nevracejí.
3. Koncept příběhu dej uživateli ke schválení (viz `rodokmen-plus` → Zajímavosti a příběhy).

## Skryté vazby z přepisů
Hotové přepisy (`data/prepisy.json`) obsahují kmotry, svědky, porodní báby a sousedy. Porovnané s osobami v grafu
odhalí vazby, které rodina nezná: kmotr = strýc z matčiny strany, svědek = budoucí tchán, soused = příbuzný z jiné větve.
- Jde to **offline a souběžně** (žádný archiv) – vhodný úkol pro pomocníka.
- Postup: vytáhni z přepisů jména s rolí, rokem, obcí a čp. → porovnej s `OSOBY` (jméno, rodné příjmení, čp. z `bydliste`,
  věk v době události) → kandidáti na shodu. Prolog z `graf.py prolog` a `graf_pravidla.pl` (pravidlo `kmotr_z_rodiny`)
  ukáže, kteří kmotři už v rodině jsou.
- **Výstup jsou hypotézy** (`HYPOTEZY`), ne hrany. Hranu `kmotr`/`svedek` mezi existujícími osobami založ jen při jasném
  ztotožnění (jméno + bydliště nebo vztah uvedený v zápisu), jinak hypotéza s tím, co by ji ověřilo.
- `graf.py kontrola` hlídá, že kmotr či svědek v době události žil a byl dospělý – vyřadí hodně falešných shod.

## Po kole
- Shrň uživateli: kolik nových osob, domů a zápisů, co je doložené a co jen pravděpodobné, kolik snímků, co se vyvrátilo,
  2–4 další stopy. Aktualizuj `data/STAV.md` („Rozpracováno“) a frontu.
- Výstupy pomocníků v `pracovni/` nemaž, dokud nejsou vytěžené.
- Poznatky o nástrojích a portálech zapiš do `poznamky_pro_skill.md`.
