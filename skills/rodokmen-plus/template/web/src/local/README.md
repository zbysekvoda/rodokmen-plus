# web/src/local – vlastní doplňky projektu

Co je v této složce, aktualizace šablony (`novy_projekt.py` na stejnou složku) **nepřepíše ani nesmaže**.
Patří sem úpravy webu jen pro tento projekt; soubory šablony mimo `local/` neupravujte.
Postup převzat z [xsigik/rodokmen-skill](https://github.com/xsigik/rodokmen-skill) (commit 318a965, MIT).

- `osoba/*.astro` – vloží se na stránku každé osoby (pod fakta, abecedně podle názvu) a dostanou prop `p`
  (osoba z `site.json`, vlastní pole v `p.extra`).
- `stranky/**/*.astro` – samostatné stránky: `stranky/kronika.astro` → `/kronika/`. Používejte layout
  `../../layouts/Base.astro` (cesty relativně k souboru).
- `presmerovani.json` – přesměrování starých adres, např. `{"/stara-adresa/": "/osoba/jan-novak-1850/"}`.

Prázdná složka nevadí, web se sestaví i bez ní.
