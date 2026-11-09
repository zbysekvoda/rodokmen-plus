# Export do PDF – „Kniha předků“ pro jednoho člověka

Stav: analýza a návrh (2026-11-09). Vizuální návrh: [`export-pdf-navrh.html`](export-pdf-navrh.html), otevřete v prohlížeči.

## Stav (2026-11-09)
**Hotovo (MVP, flow „Kniha předků – export do PDF“):** tisková route `/kniha/<id>/` s Paged.js a `@page` CSS;
obsah – obálka, statistiky, vějíř přes dvoustranu, karty po generacích, domy, příběhy, prameny s výřezy, tiráž;
`web.json` → `kniha`; `tools/kniha_pdf.py` (Chrome přes CDP, zmenšení výřezů) a odkaz na stránce osoby;
soukromí – žijící jako na webu, `kontrola.py` hlásí `CITLIVÉ` i u zápisů a bydlišť, brána nginx i Netlify chrání
`/kniha/*.pdf` a `/kniha/*/`; dokumentace v `reference/web.md` a `reference/soukromi.md`.
Ukázka `jan-novak-1890`: 15 stran, 0,47 MB.

**Odloženo:** statická mapa míst (dlaždice nejdou volně do tisku, viz Rizika – Mapy) a rodové pásy.

## Co chceme
Na stránce osoby (`/osoba/<id>/`) jde vytvořit PDF pro tuto osobu jako kořen: její předky, příběhy, domy,
ve kterých předci žili, a ukázky zápisů z matrik. Výstup má být vizuálně pěkný, na tisk (A4) i na čtení na obrazovce.

## Z čeho se dá stavět (co už v repu je)
| Potřeba | Zdroj |
|---|---|
| Graf osob, Kekulé od libovolného kořene | `data/osoby.py`, `tools/graf.py` (`cisla <koren>`) |
| Data webu (osoby, rody, zápisy, výřezy) | `tools/export_web.py` → `web/src/data/site.json`, `web/public/img` |
| Domy a vazba osoba ↔ dům | `data/domy.py`, `bydliste`, `tools/domy_rodiny.py`, `export_web_domy.py` |
| Příběhy, zajímavosti | `data/pribeh*.md`, `zajimavosti.md` (wiki odkazy `[[typ:cíl]]` už validuje kontrola) |
| Vějíř předků jako SVG + Chrome headless → PNG | `tools/fan_chart.py` (hledání Chromu na macOS/Win/Linux už je vyřešené) |
| Statistiky, časová osa | `web/src/lib/statistiky.js`, `osa.js` |
| Tiskové styly | `global.css` má jen základní `@media print` |
| Soukromí žijících, `CITLIVÉ` | `reference/soukromi.md`, `tools/kontrola.py`, `web.json → citlive_schvaleno` |

Podstatné omezení: **web je statický** (Astro → Netlify / nginx / CapRover). Na serveru nic neběží, takže
„tlačítko, které na serveru vyrobí PDF“ bez nové infrastruktury nejde.

## Varianty technického řešení

### A) Tisková stránka v Astru + Chrome `--print-to-pdf` (doporučeno)
- Nová route `web/src/pages/kniha/[slug].astro` (pro každou osobu, nebo jen pro `web.json → kniha.osoby`),
  layout bez navigace, `@page` pravidla (A4, okraje, zrcadlené okraje, číslo strany, živá záhlaví).
- Data bere z téhož `site.json` jako web → žádná druhá pravda, stejná filtrace soukromí.
- PDF vyrobí nástroj `tools/kniha_pdf.py <id>`: spustí `astro build` (nebo použije `dist/`), pak Chrome headless
  `--print-to-pdf` nad `dist/kniha/<id>/index.html` (stejný vzor jako `fan_chart.py`). Výsledek do `vystupy/`
  a volitelně do `web/public/kniha/<id>.pdf` → na stránce osoby se objeví odkaz „Stáhnout knihu (PDF)“.
- Pro čísla stran v obsahu, živá záhlaví (`string-set`) a `target-counter` přidat **Paged.js** (polyfill CSS
  Paged Media, MIT) – Chrome sám neumí obsah s čísly stran ani margin boxy spolehlivě.
- Na webu navíc tlačítko „Tisk“ → otevře `/kniha/<id>/` a `window.print()`; funguje i bez předgenerovaného PDF.

Plusy: jeden stack (HTML/CSS jako web), sdílené komponenty (vějíř, výřezy, rodový pás), nulová nová závislost na
serveru, Chrome už skill vyžaduje. Minusy: Paged.js je pomalejší u stovek stran; tisk z prohlížeče se liší podle
prohlížeče (proto je kanonický výstup ten z `kniha_pdf.py`).

### B) Typst / LaTeX z Pythonu
Krásná typografie, deterministický výstup, ale druhá šablona vedle webu (duplicitní logika výběru dat a soukromí),
nová závislost pro uživatele bez programátorského zázemí (instalace Typstu), obrázky a SVG vějíře se musí řešit zvlášť.
Dává smysl až kdyby šlo o tištěnou knihu ve stovkách výtisků.

### C) WeasyPrint / ReportLab
WeasyPrint umí CSS Paged Media nativně, ale potřebuje Pango/cairo (na Windows a macOS bolest) a nepodporuje
část CSS, kterou web používá (grid je omezený, `:has`). ReportLab = ruční sazba, nepoužitelné pro bohatý layout.

### D) Generování v prohlížeči (jsPDF / pdfmake)
Bez buildu, ale výsledek je výrazně horší (text jako vektorové kusy, špatné české dělení slov, fonty se musí
embedovat ručně). Nedoporučuji.

**Doporučení: A.** Tisk = další „pohled“ na stejná data jako web; PDF je build artefakt.

## Obsah knihy (pro kořen K)
1. **Obálka** – jméno K, „Kniha předků“, rozsah let (nejstarší doložený předek – dnes), motiv vějíře nebo
   výřez nejstaršího zápisu, rodová jména.
2. **Obsah** s čísly stran.
3. **Úvod** – kolik předků, kolik generací, kolik doloženo matrikou (`st=doc`) vs. od rodiny, odkud rod pochází
   (statistiky z `statistiky.js`).
4. **Vějíř předků** přes celou dvoustranu (z `fan_chart.py`, barvy podle rodů / stavu doložení).
5. **Generace** – kapitola na generaci (rodiče, prarodiče, …); každá osoba jako karta: jméno, roky, fakta
   (* × †), povolání, bydliště, poznámka, malý výřez zápisu. Kekulé číslo jako tichá marginálie.
6. **Rody** – pro každé příjmení v linii rodový pás (kde žili, kdy) a krátký text.
7. **Domy předků** – dvoustrana na dům: název / čp., obec, mapka nebo indikační skica, seznam držitelů,
   kteří z nich jsou předci K, příběh domu.
8. **Příběhy** – vybrané `pribeh*.md`, které zmiňují předky K (zpětný index už web má: „Zmíněno v příběhu“).
9. **Prameny** – ukázky výřezů zápisů (s přepisem), seznam použitých knih (`prosle_knihy.py`), archivní signatury.
10. **Mapa** míst předků (statický snímek – Leaflet v PDF nefunguje, nutné předrenderovat dlaždice nebo SVG
    obrys ČR + body z `mista.json`).
11. **Tiráž** – datum vygenerování, verze dat (git commit), stav doložení – legenda.

Rozsah se reguluje přepínači v `web.json → kniha` (`generaci: 6`, `domy: true`, `pribehy: true`,
`zapisy: "vybrane" | "vse" | false`). Typicky 30–80 stran.

## Rizika a otevřené body
- **Soukromí.** PDF se šíří mimo přihlášení webu. Výchozí pravidla jako web (žijící jen jméno a rok),
  `kontrola.py` musí běžet i nad knihou; PDF nesmí do gitu ani do veřejného `dist/` bez přihlášení
  (nginx/Netlify brána chrání i `/kniha/*.pdf` – ověřit, že brána pokrývá i binárky).
- **Kořen je dítě / boční příbuzný.** Kekulé od libovolného kořene už funguje (0.7.0), ale kořen bez
  doložených předků dá prázdnou knihu → v UI tlačítko jen když má osoba ≥ 2 generace předků.
- **Velikost.** Výřezy jsou JPG v plném rozlišení; pro PDF zmenšit na ~200 dpi při tiskové šířce (ImageMagick už
  `export_web.py` používá).
- **Fonty.** Newsreader / Source Serif / Source Sans jsou v `@fontsource` (OFL) → embedují se do PDF bez potíží,
  čeština OK. Dělení slov: `hyphens: auto` + `lang="cs"` funguje v Chromu.
- **Mapy.** Dlaždice OSM/Mapy.com nejde volně vkládat do tisku ve velkém – preferovat vlastní SVG nebo staré
  mapy z `mapy.json` s licencí, která to dovoluje.
- **Velké rody.** 10+ generací = stovky osob; Paged.js pak běží desítky sekund. Limit generací + vedlejší linie
  jen jako tabulka.

## Odhad práce (pro agenty)
| Krok | Velikost |
|---|---|
| `kniha/[slug].astro` + tiskový layout + `@page` CSS + Paged.js | M |
| Komponenty: obálka, karta osoby, generace, dům, příběh, prameny | M–L |
| `tools/kniha_pdf.py` (build + Chrome headless, zmenšení obrázků) | S |
| `web.json → kniha` konfigurace, tlačítko na stránce osoby | S |
| Soukromí: kontrola nad knihou, brána pro PDF | S |
| Statická mapa míst | M (lze odložit) |
| Dokumentace v `reference/web.md`, krok v playbooku | S |

MVP (bez mapy a rodových pásů) zhruba 2–3 handoffy; dá se rozdělit na flow: layout+data → komponenty → nástroj
a tlačítko → soukromí a dokumentace.
