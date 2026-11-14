# Inspirace: Kinfolk Observatory (Vibe Genealogy)

Zdroj: <https://vibegenealogy.ai/p/fun-prompt-friday-fable-make-something-incredible-kinfolk-observatory>
(nástroj: observatory.vibegenealogy.ai). Prohlížeč GEDCOM souboru se 13 pohledy, vše běží v prohlížeči
(nic se nenahrává, bez AI za běhu), vzorový strom s 3 214 lidmi a skrytými žijícími. Vznikl z jednoho
promptu („udělej co nejúžasnější vizuální průzkum mých rodinných dat“), agent si práci rozdělil na 10 subagentů.

Prozkoumáno 14. 11. 2026, srovnáno s webem v `skills/rodokmen-plus/template/web`.

## Srovnání pohledů

| Observatory | U nás | Stav |
|---|---|---|
| Night Sky (hvězda = osoba, střed = nejstarší) | – | chybí, spíš efekt než užitek |
| Ancestor Fan, zlaté okraje u implexu | `/vejir/` (fan_chart.py), implex v `lib/predci.js` | máme; zvýraznění implexu ve vějíři ověřit |
| Hourglass (předci + potomci, volitelné generace) | `/strom-cely/` | máme (předci nahoru, potomci dolů) |
| Ancestors Through Time: tree / untangled / by birth year + Y-DNA, mtDNA, X-DNA linie | `/vejir-cas/`, `/predci/` | **chybí DNA linie** |
| River of Lifetimes + křivka „současně žijících“ | `/reka/`, `/pasy/` | máme; chybí křivka počtu žijících a barvení podle místa |
| The Tangle (síť příjmení, tloušťka = opakované sňatky rodů) | `/rody/` (seznam) | **chybí síť příjmení** |
| How Are We Related? + „Surprise me“ | graf + Prolog v nástrojích, `/osa-vazby/` | **chybí na webu** |
| Life Story (opatrný narativ „je zapsán jako…“) | `/osoba/`, `/pribeh/` | máme (ruční příběhy); auto-narativ ze faktů chybí |
| By the Numbers | `/statistiky/` | máme |
| Descendants (radiální, barva podle dítěte) | – | **chybí vějíř potomků** |
| Where They Lived (mřížka místo × desetiletí, stuhy rodič→dítě) | `/mapa/`, `/domy/` | mřížka i stuhy chybí |
| Things Worth Checking | `tools/kontrola.py` (věk rodičů, dítě po smrti) | máme jen v CLI, ne na webu |
| What's Missing (zaplnění po generacích, chybějící data) | `/statistiky/` (pruhy po generacích), `/predci/`, `/hledame/`, `tools/fronta.py` | máme |

## Doporučené náměty (podle poměru užitek / práce)

1. **„Jak jsme příbuzní?“ na webu** – výběr dvou osob, věta v češtině („pra­prateta“…) a nejbližší společní
   předci. Data i logika už jsou v grafu (`graf.py`, `graf_pravidla.pl`); stačí předpočítat
   v `export_web.py` nebo spočítat v JS nad `people`. Nejvyšší hodnota pro rodinu.
2. **DNA linie** (Y po otcích, mtDNA po matkách, X-DNA vzor) jako přepínač ve vějíři – zvýraznění větví.
   Levné (jen filtr Kekulého čísel), užitečné pro lidi s DNA testem.
3. **Vějíř potomků** od zvolené osoby – obrácený `fan_chart.py`, barva podle dítěte.
4. **„Stojí za ověření“ na webu** – výstup věcných kontrol z `kontrola.py` jako stránka (jen pro rodinu,
   formulace „ověřte v pramenu“, ne verdikt).
5. **Síť příjmení** (rody jako uzly, sňatky jako hrany) na `/rody/`.
6. Křivka současně žijících na `/reka/`, mřížka místo × desetiletí na `/mapa/` – až nakonec.

Night Sky a auto-generovaný narativ nedoporučuji: první je efekt bez nové informace, druhé u nás nahrazují
ruční příběhy z pramenů, které jsou silnější.

## Co převzít z přístupu
- Opatrný jazyk („je zapsán jako“) u všeho, co je odvozené z dat – sedí k naší metodice.
- Tlačítko „Překvap mě“ (náhodná dvojice / osoba) jako vstupní bod pro rodinu.
