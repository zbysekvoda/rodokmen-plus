# Návrh: volitelné strojové čtení výřezů přes OpenRouter

Stav: **schváleno, implementováno** (fáze 2).

## Proč
Dnes čte matriky výhradně agent sám (`SKILL.md`, Režim předci, krok 5–6): stáhne snímek, čte v plném rozlišení,
u vybledlých míst `vylepsi_snimek.py` (varianty kontrastu), ověření čtení `overit.py` (dvě poloviny výřezu)
a nezávislý audit `audit.py` (subagent, týž model). Slabina: všechna čtení dělá **jedna rodina modelů**, takže
se chyby (záměna kurentních písmen, latinské zkratky, jména obcí) navzájem nepotvrdí, ale ani neodhalí.

Nedávný pokus ukázal, že druhé čtení výřezu jiným multimodálním modelem (Gemini, Fable) zlepšilo přepis
sporných míst. Návrh to dělá volitelnou součástí skillu: **druhý názor**, ne náhrada čtení agentem.

## Co se nemění bez klíče
- Bez klíče skill funguje přesně jako dnes; žádný krok workflow na nástroji nezávisí.
- Nástroj při chybějícím klíči jen vypíše jednu srozumitelnou větu (jak klíč zadat) a skončí kódem 3, nic nezapíše.
- `kontrola.py`, export webu, kniha PDF ani data se nemění.

## Rozhraní nástroje `tools/cteni_ai.py`
```
python3 -I tools/cteni_ai.py <klíč zápisu | cesta k výřezu> [--model gemini|fable|<openrouter-id>]
        [--jazyk la|de|cs] [--kontext "křest, Horní Lhota 1820, hledám Jana Nováka"] [--zapsat]
```
- Vstup: výřez `zdroje/<klíč>.jpg` (plné rozlišení; nad ~2000 px po delší straně se zmenší), volitelně kontext
  ze `zaznamy.json` (typ, rok, farnost) – **bez dalších osobních údajů z grafu**.
- Výstup na stdout: JSON `{model, prepis, preklad, nejista_mista[], cena_usd, cas}`; nejistá místa model značí
  „(?)“ a „[…]“ stejně jako skill.
- `--zapsat` uloží do `pracovni/cteni_ai/<klíč>_<model>.json` – **nikdy přímo do `data/prepisy.json`**.
- Návrat do workflow: agent porovná strojové čtení se svým, rozdíly ověří na výřezu (`overit.py`)
  a do `prepisy.json` zapíše své rozhodnutí. Pokud čtení převzal, přidá k přepisu pole
  `"stroj": "<model>, nepotvrzeno"` → `kontrola.py` ho bude hlásit jako *strojové čtení k ověření*, dokud
  uživatel/agent pole neodstraní (= ověřeno na výřezu).
- `audit.py` může strojové čtení přiložit jako jiný výklad (žádná nová povinnost).

## Klíč
- Env proměnná `OPENROUTER_API_KEY`, jinak soubor `~/.config/rodokmen/openrouter.key` (práva 600).
- **Nikdy** v projektu, v `data/`, ve `web.json`, v exportu ani v gitu. Nástroj odmítne běžet, najde-li klíč
  uvnitř složky projektu, a `kontrola.py` přidá test, že se řetězec `sk-or-` v projektu nevyskytuje.
- Skill klíč nikdy nečte do konverzace; uživatel ho zadá sám v terminálu (postup v `reference/matriky.md`).

## Odhad nákladů (výřez ~1800×1200 px, výstup ~600 tokenů přepis + překlad)
Ceny jsou orientační k 11/2026 – před zavedením ověřit na openrouter.ai/models; nástroj vrací skutečnou cenu
z odpovědi OpenRouteru.

| model | vstup obrázek+prompt | výstup | cena / výřez | 100 výřezů |
|---|---|---|---|---|
| Gemini Flash (třída 2.5) | ~1,5k tok. | ~0,6k | ≈ 0,002 USD | ≈ 0,2 USD |
| Gemini Pro (třída 2.5, s uvažováním) | ~1,5k | ~0,6k + uvažování ~2k | ≈ 0,03 USD | ≈ 3 USD |
| Fable 5.1 | ~1,6k | ~0,6k | ≈ 0,02–0,05 USD | ≈ 2–5 USD |

Celá stránka matriky (dvoustrana, 4000+ px) stojí ~3–4× víc a čte se hůř; doporučení je posílat jen výřezy.

## Rizika
- **Soukromí:** snímek odchází třetí straně (OpenRouter + poskytovatel modelu). Matriky starší lhůt jsou veřejné,
  ale nástroj odmítne zápisy mladší 100 let (narození), resp. 75 let (sňatek, úmrtí) bez `--souhlas`, a nikdy
  neposílá rodinné dokumenty z `dokumenty/` ani údaje od rodiny. Uživatel souhlasí jednou při nastavení
  (`reference/soukromi.md` → Cizí služby). OpenRouter umožňuje zakázat poskytovatele, kteří trénují na datech
  – nástroj posílá `provider: {data_collection: "deny"}`.
- **Halucinace:** model doplní pravděpodobné jméno místo nečitelného. Proto: strojové čtení je jen kandidát,
  nikdy se nezapíše samo, kontrola ho hlásí do ověření a prompt vyžaduje „[…]“ místo hádání.
- **Náklady / limity:** strop `--max-usd` (výchozí 1 USD na běh), nástroj neprochází dávky sám.
- **Závislost na službě:** výpadek = nástroj skončí chybou, workflow pokračuje bez něj.

## Fáze 2 (při souhlasu)
1. `tools/cteni_ai.py` (stdlib `urllib`, bez nových závislostí), chybějící klíč → kód 3 + návod.
2. Test bez sítě: mock HTTP vrstvy, chybějící klíč, klíč v projektu, lhůty.
3. `kontrola.py`: hlášení `"stroj"` u přepisů a hledání `sk-or-` v projektu.
4. Zmínka ve `SKILL.md` (krok 5, volitelné) a `reference/matriky.md`, `reference/soukromi.md`.
5. `kontrola_soukromi.py` projde.

## Rozhodnutí
2026-11-14 uživatel zvolil **implementovat podle návrhu** (Desk). Implementace: `tools/cteni_ai.py`,
`tests/test_cteni_ai.py` (bez sítě), hlášení `"stroj"` v `kontrola.py`, zmínky ve `SKILL.md`, `reference/matriky.md`,
`reference/soukromi.md`. ID modelů v `MODELY` ověřit na openrouter.ai/models při prvním ostrém běhu.
Test `sk-or-` v `kontrola.py` nebyl zaveden: odmítnutí klíče v projektu dělá přímo nástroj.
