#!/usr/bin/env python3
"""Testy čisté logiky tools/kniha_pdf.py a tools/prostredi.py (bez Chromu a bez buildu webu).

Spuštění: python3 -m unittest discover tests
"""
import os, shutil, sys, tempfile, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus", "tools")
sys.path.insert(0, TOOLS)
import kniha_pdf  # noqa: E402
import prostredi  # noqa: E402


class HledaniChromu(unittest.TestCase):
    def test_prvni_existujici_cesta(self):
        ex = {"/b/chrome"}
        self.assertEqual(prostredi.najdi_chrome(("/a/chrome", "/b/chrome"), env={}, exists=ex.__contains__,
                                                which=lambda c: None), "/b/chrome")

    def test_z_path(self):
        self.assertEqual(prostredi.najdi_chrome(("/a/chrome", "chromium"), env={}, exists=lambda c: False,
                                                which=lambda c: "/usr/bin/chromium" if c == "chromium" else None),
                         "/usr/bin/chromium")

    def test_promenna_prostredi_ma_prednost(self):
        ex = {"/a/chrome", "/vlastni/chrome"}
        self.assertEqual(prostredi.najdi_chrome(("/a/chrome",), env={"RODOKMEN_CHROME": "/vlastni/chrome"},
                                                exists=ex.__contains__, which=lambda c: None), "/vlastni/chrome")

    def test_neexistujici_promenna_se_ignoruje(self):
        ex = {"/a/chrome"}
        self.assertEqual(prostredi.najdi_chrome(("/a/chrome",), env={"RODOKMEN_CHROME": "/neni"},
                                                exists=ex.__contains__, which=lambda c: None), "/a/chrome")

    def test_nic(self):
        self.assertIsNone(prostredi.najdi_chrome(("/a",), env={}, exists=lambda c: False, which=lambda c: None))

    def test_fan_chart_pouziva_spolecny_modul(self):
        zdroj = open(os.path.join(TOOLS, "fan_chart.py"), encoding="utf-8").read()
        self.assertIn("from prostredi import najdi_chrome", zdroj)
        self.assertNotIn("/Applications/Google Chrome.app", zdroj)


class VyberOsob(unittest.TestCase):
    def setUp(self):
        self.dist = tempfile.mkdtemp(prefix="kniha_test_")
        self.addCleanup(shutil.rmtree, self.dist)

    def stranka(self, rel):
        p = os.path.join(self.dist, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").close()

    def test_jen_slozky_s_index_html(self):
        self.stranka("kniha/jan-novak-1890/index.html")
        self.stranka("kniha/anna-krizova-1856/index.html")
        self.stranka("kniha/jan-novak-1890.pdf")             # PDF z --web, ne kniha
        os.makedirs(os.path.join(self.dist, "kniha", "prazdna"))
        self.assertEqual(kniha_pdf.osoby_s_knihou(self.dist), ["anna-krizova-1856", "jan-novak-1890"])

    def test_bez_knih(self):
        self.assertEqual(kniha_pdf.osoby_s_knihou(self.dist), [])


class Cesty(unittest.TestCase):
    def test_bez_web(self):
        self.assertEqual(kniha_pdf.vystupni_cesty("/p", "jan-novak-1890"),
                         [os.path.join("/p", "vystupy", "kniha-jan-novak-1890.pdf")])

    def test_web_bez_dist(self):
        self.assertEqual(kniha_pdf.vystupni_cesty("/neexistuje", "x", web=True),
                         [os.path.join("/neexistuje", "vystupy", "kniha-x.pdf"),
                          os.path.join("/neexistuje", "web", "public", "kniha", "x.pdf")])

    def test_web_s_dist(self):
        root = tempfile.mkdtemp(prefix="kniha_test_")
        self.addCleanup(shutil.rmtree, root)
        os.makedirs(os.path.join(root, "web", "dist"))
        self.assertEqual(kniha_pdf.vystupni_cesty(root, "x", web=True)[-1],
                         os.path.join(root, "web", "dist", "kniha", "x.pdf"))

    def test_zmensovane_obrazky(self):
        self.assertTrue(kniha_pdf.zmensit("/img/krest%20jan.JPG"))
        self.assertTrue(kniha_pdf.zmensit("/zdroje/a.png?v=1"))
        self.assertFalse(kniha_pdf.zmensit("/_astro/font.woff2"))
        self.assertFalse(kniha_pdf.zmensit("/kniha/jan/"))


class Argumenty(unittest.TestCase):
    def test_platne(self):
        self.assertEqual(kniha_pdf.parsuj_argumenty(["jan-novak-1890"]), ("jan-novak-1890", False, False))
        self.assertEqual(kniha_pdf.parsuj_argumenty(["--vse", "--web"]), (None, True, True))
        self.assertEqual(kniha_pdf.parsuj_argumenty(["--web", "x"]), ("x", False, True))

    def test_neplatne(self):
        for a in ([], ["--vse", "x"], ["a", "b"], ["--neznamy"]):
            with self.subTest(a=a), self.assertRaises(SystemExit):
                kniha_pdf.parsuj_argumenty(a)


if __name__ == "__main__":
    unittest.main()
