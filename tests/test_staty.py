#!/usr/bin/env python3
"""Testy státních útvarů (tools/staty.json + udalosti.staty_v_rozsahu): hlavní linie, výjimky oblastí, projekt.

Spuštění: python3 -m unittest discover tests
"""
import datetime, json, os, shutil, sys, tempfile, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus", "tools")
sys.path.insert(0, TOOLS)
import udalosti  # noqa: E402

MISTA = {"Holice": {"zeme": "cechy"}, "Hlučín": {"zeme": "slezsko", "oblast": "hlucinsko"},
         "Liberec": {"zeme": "cechy", "oblast": "sudety"}, "Brno": {"zeme": "morava"}}


class Staty(unittest.TestCase):
    def setUp(self):
        self.staty = udalosti.nacti_staty()

    def nazvy(self, od, do, misto=None):
        return [u["stat"]["id"] for u in udalosti.staty_v_rozsahu(self.staty, od, do, misto, MISTA)]

    def test_osa_validni_a_navazuje(self):
        hlavni = sorted((s for s in self.staty if s["kde"] == ["cechy", "morava", "slezsko"]), key=lambda s: s["od"])
        for a, b in zip(hlavni, hlavni[1:]):
            self.assertEqual(udalosti._datum(a["do"], True) + datetime.timedelta(days=1), udalosti._datum(b["od"]), b["id"])
        for s in self.staty:
            self.assertTrue({"id", "od", "do", "kde", "nazev", "zrizeni", "text", "zdroj"} <= s.keys(), s["id"])
            self.assertIn(s["zrizeni"], ("monarchie", "republika", "okupace"))

    def test_hlavni_linie(self):
        self.assertEqual(self.nazvy(1850, 1850, "Holice"), ["rakouske-cisarstvi"])
        self.assertEqual(self.nazvy(1940, 1940, "Brno"), ["protektorat"])
        self.assertEqual(self.nazvy(1918, 1918), ["rakousko-uhersko", "csr-prvni"])

    def test_zeme(self):
        u = udalosti.staty_v_rozsahu(self.staty, 1850, 1850, "Brno", MISTA)[0]
        self.assertEqual(u["zeme"], "Markrabství moravské")

    def test_sudety(self):
        self.assertEqual(self.nazvy(1938, 1946, "Liberec"), ["csr-prvni", "sudety-nemecka-rise", "csr-treti"])

    def test_hlucinsko(self):
        self.assertEqual(self.nazvy(1740, 1760, "Hlučín"), ["habsburska-monarchie", "hlucinsko-prusko"])
        self.assertEqual(self.nazvy(1919, 1921, "Hlučín"), ["hlucinsko-nemecka-republika", "hlucinsko-csr"])
        u = udalosti.staty_v_rozsahu(self.staty, 1938, 1938, "Hlučín", MISTA)
        self.assertEqual([x["stat"]["id"] for x in u], ["hlucinsko-csr", "hlucinsko-nemecka-rise"])

    def test_projekt_prebiji(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d)
        os.makedirs(os.path.join(d, "data"))
        with open(os.path.join(d, "data", "staty.json"), "w", encoding="utf-8") as f:
            json.dump([{"id": "protektorat", "od": "1939-03-15", "do": "1945-05-08", "kde": ["cechy", "morava", "slezsko"],
                        "nazev": "Jinak", "zrizeni": "okupace", "text": "t", "zdroj": "z"}], f)
        u = udalosti.staty_v_rozsahu(udalosti.nacti_staty(d), 1940, 1940)
        self.assertEqual(u[0]["stat"]["nazev"], "Jinak")


if __name__ == "__main__":
    unittest.main()
