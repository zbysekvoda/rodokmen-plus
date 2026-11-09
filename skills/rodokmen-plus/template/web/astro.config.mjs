import { defineConfig } from 'astro/config';
import { existsSync, readFileSync } from 'node:fs';

// přesměrování projektu z src/local/presmerovani.json ({"/stara/": "/nova/"}) – aktualizace šablony ho nepřepíše
const r = new URL('./src/local/presmerovani.json', import.meta.url);
const redirects = existsSync(r) ? JSON.parse(readFileSync(r, 'utf8')) : {};

export default defineConfig({
  trailingSlash: 'always',
  build: { format: 'directory' },
  redirects,
});
