#!/usr/bin/env python3
"""Přihlašovací brána (nginx šablona, Netlify Edge Function) chrání i Knihu předků: /kniha/<id>.pdf a /kniha/<id>/.

Spuštění: python3 -m unittest discover tests
"""
import os, re, unittest

WEB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus", "template", "web")
CHRANENE = ("/kniha/jan-novak-1890.pdf", "/kniha/jan-novak-1890/", "/osoba/jan-novak-1890/", "/img/x.jpg")


def nginx_location(conf, path):
    """Blok location, který nginx pro cestu vybere: přesná shoda, pak regex (v pořadí), jinak nejdelší prefix."""
    bloky = re.findall(r"location\s+(=|~\*|~)?\s*(\S+)\s*\{(.*?)\n  \}", conf, re.S)
    for mod, vzor, telo in bloky:
        if mod == "=" and vzor == path:
            return telo
    for mod, vzor, telo in bloky:
        if mod in ("~*", "~") and re.search(vzor, path, re.I if mod == "~*" else 0):
            return telo
    prefixy = [(vzor, telo) for mod, vzor, telo in bloky if not mod and path.startswith(vzor)]
    return max(prefixy, key=lambda x: len(x[0]))[1]


class Nginx(unittest.TestCase):
    conf = open(os.path.join(WEB, "nginx.sablona.conf"), encoding="utf-8").read()

    def test_kniha_vyzaduje_prihlaseni(self):
        for path in CHRANENE:
            with self.subTest(path=path):
                self.assertIn("if ($rodokmen_ok = 0)", nginx_location(self.conf, path))
                self.assertIn("return 401", nginx_location(self.conf, path))

    def test_prihlaseni_je_volne(self):
        self.assertNotIn("return 401", nginx_location(self.conf, "/prihlaseni.html"))


class Netlify(unittest.TestCase):
    js = open(os.path.join(WEB, "netlify", "brana.sablona.js"), encoding="utf-8").read()

    def test_brana_bezi_na_vsech_cestach(self):
        self.assertRegex(self.js, r"export const config = \{ path: '/\*' \}")

    def test_jedina_vyjimka_je_prihlaseni(self):
        vyjimky = re.findall(r"if \(url\.pathname === '([^']+)'\) return context\.next\(\)", self.js)
        self.assertEqual(vyjimky, ["/prihlaseni.html"])
        self.assertNotRegex(self.js, r"pathname\.(startsWith|endsWith|includes)")


if __name__ == "__main__":
    unittest.main()
