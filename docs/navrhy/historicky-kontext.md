# Historický kontext k životům předků

Stav: návrh schválen (2026-11-10), implementace v navazujících handoffech.

## Co už je
- `tools/napady.py` má natvrdo slovník `EPIDEMIE` (13 let: cholera 1831–1873, hladomor 1771–72, španělská chřipka…)
  a hledá podle něj úmrtí v letech epidemií. Je to zárodek osy, ale bez místa, bez zdroje a mimo data.
- Web má časovou osu `/osa/` (`template/web/src/lib/osa.js`, `Timeline.astro`), knihu předků (`/kniha/<id>/`)
  a příběhy (`reference/pribehy.md`, `data/zajimavosti.md`).
- `ztotozneni-mist` a `dnnt.py` už čtou Hosáka, Wolného a NDK, takže regionální prameny už máme po ruce.

## Varianty

### Zdroj
| varianta | + | − |
|---|---|---|
| **A. Kurátorovaná osa v pluginu** (`tools/udalosti.json`, ČR / Čechy / Morava / Slezsko, ~1620–1990) | spolehlivá, offline, plná kontrola nad formulací, žádné licence (vlastní text, fakta nejsou chráněná) | ruční práce (~150–250 položek), jen celostátní a zemská úroveň |
| **B. Wikidata (SPARQL: rok + místo / okres)** | pokryje bitvy, požáry a povodně i lokálně, CC0 | nevyrovnaná kvalita, u vesnic skoro nic, síť v headless běhu, šum |
| **C. Místní kroniky a monografie** (NDK, Wolny, Hosák, obecní kroniky) | nejcennější: „obcí táhla vojska, vyhořelo 12 stavení“ | dá se jen ručně / agentem, vlastní citace; patří do projektu, ne do pluginu |

**Doporučení:** A jako páteř, C jako projektová vrstva `data/udalosti.json` (stejný formát a povinný `zdroj`),
B jen jako volitelný nástroj pro agenta (`udalosti.py wikidata <obec>`), který navrhuje kandidáty do C a nic
nezapisuje sám.

### Rozsah
- Úrovně: `cr` (ČR / monarchie), `zeme` (cechy, morava, slezsko), `region` (panství / okres / farnost), `obec`.
- Do minulosti zhruba od roku 1620 (Bílá hora, třicetiletá válka). Matriky začínají kolem roku 1650, starší události
  slouží jen jako pozadí příběhu rodu.
- Kategorie: válka/bitva, epidemie, hlad/neúroda, živel (požár, povodeň), reforma/zákon (robota 1848, patent 1781,
  školství 1774/1869), správa (sčítání, katastr, číslování domů 1770), měna (1811, 1892, 1919, 1945, 1953), režim/okupace
  (1918, 1938/39, 1945, 1948), hospodářství (kolektivizace 1949–60), odsun a přesídlení.

### Formát položky (stejný v pluginu i v projektu)
```json
{"id": "1866-cholera", "od": "1866-07", "do": "1866-10", "uroven": "zeme", "kde": ["cechy", "morava"],
 "kategorie": "epidemie", "nazev": "Cholera", "text": "…1–2 věty…",
 "dopad": {"umrti": true, "vojaci": false}, "zdroj": "…", "jistota": "doc|lit|obecne"}
```
Projektové položky mají `kde` jako klíče z `mista.json`, takže se dají napárovat na bydliště osob a domy.

### Kde se kontext ukáže
1. **Nástroj pro agenta** (`tools/udalosti.py rok 1866 [--misto X]`, `udalosti.py osoba <id>`): vrátí události
   v životě osoby, každou s věkem osoby v tu chvíli. Je to nejlevnější a nejvíc pomůže u příběhů.
2. **Časová osa `/osa/` a karta osoby:** tenké svislé pásy událostí (přepínatelné), u osoby řádek „Doba“.
3. **Kniha předků:** u každé generace krátký box „Svět kolem“ (3–5 událostí za jejich život).
4. **Příběhy:** agent smí kontext použít, ale musí dodržet pravidlo z oddílu Doložené vs. kontext.

### Propojení s daty osob
- věk při události: bez nových dat, z `*` / `†`;
- odvod a válečná služba: muži ve věku 18–40 během války. Je to jen **otázka** pro badatele (vojenské matriky,
  kmenové listy), žádné tvrzení;
- shluky úmrtí: rozšířit `napady.py` o detekci roků / měsíců s nadprůměrem úmrtí v obci (z `zaznamy.json`).
  Shluk, který se kryje s událostí, je silný námět, shluk bez události zase námět na hledání v kronice.

### Doložené vs. kontext
- Vazbu osoby na událost tvrdíme jen tehdy, když ji nese zápis: příčina smrti „Cholera“, padl u…, odveden…
  Je to fakt osoby s citací (stávající mechanismus).
- Ostatní je **kontext** a vizuálně se odliší (šedý pás nebo box „Svět kolem“). V textu se formuluje
  „v roce jeho narození…“ / „v těch letech…“, nikdy „kvůli“ nebo „zúčastnil se“.
- Doplnit do `reference/pribehy.md` a do kontroly (`kontrola.py`): příběh nesmí spojit osobu s událostí kauzálně
  bez odkazu na zápis.

### Obecnost
Plugin nese jen `udalosti.json` s obecnou osou (ČR a země) a nástroje. Regionální a obecní vrstva leží v projektu
(`data/udalosti.json`) a šablona je prázdná. `EPIDEMIE` z `napady.py` se přesune do osy.

## Rozpad na úkoly
1. **Osa ČR / zemí**: `tools/udalosti.json` (~200 položek, 1620–1990) + schéma a test validity. Agent s rešerší,
   lidská revize.
2. **`tools/udalosti.py`**: dotazy `rok`, `rozsah`, `osoba` (s věkem), slučuje plugin a projekt; `napady.py` čte osu
   místo `EPIDEMIE`. Testy.
3. **Shluky úmrtí** v `napady.py` (podle obce a roku/měsíce, porovnání s osou).
4. **Pravidla v `reference/pribehy.md` + `playbook.md`**: kdy a jak kontext použít, doložené vs. kontext; kontrola
   kauzálních formulací.
5. **Web – osa a karta osoby**: export událostí do webu (`export_web.py`), pásy v `/osa/`, řádek „Doba“.
6. **Kniha předků**: box „Svět kolem“ u generací.
7. **Projektová vrstva**: návod, jak z NDK / Wolného / kronik zapsat `data/udalosti.json` (ve skillu
   `ztotozneni-mist` nebo v nové referenci), šablona prázdná.
8. *(volitelné)* **Wikidata kandidáti** pro obec / okres → návrhy do projektové vrstvy.

Pořadí: 1 → 2 → (3, 4 paralelně) → 5 → 6. Úkoly 7 a 8 kdykoli po kroku 2.

## Rozhodnutí (Zbyšek, 2026-11-10)
- Návrh schválen.
- Osa začíná rokem 1620.
- Hustota osy: ~200 položek (včetně zemských reforem a měn).
- Web: kontext za přepínačem, výchozí stav zapnuto.
