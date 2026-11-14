#!/usr/bin/env python3
"""Validace projektové vrstvy historických událostí data/udalosti.json v kontrola.py.

Spuštění: python3 -m unittest discover tests
"""
import importlib, json, os, shutil, sys, tempfile, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus", "tools")
kontrola = None


def setUpModule():
    """kontrola.py jde importovat jen z projektu (kontrola_domy chce data/STAV.md) – založ dočasný projekt."""
    global kontrola, _tmp
    _tmp = tempfile.mkdtemp()
    os.makedirs(os.path.join(_tmp, "tools")); os.makedirs(os.path.join(_tmp, "data"))
    open(os.path.join(_tmp, "data", "STAV.md"), "w").close()
    for f in ("kontrola.py", "kontrola_domy.py", "dolozeni.py", "udalosti.json"):
        shutil.copy(os.path.join(TOOLS, f), os.path.join(_tmp, "tools", f))
    sys.path.insert(0, os.path.join(_tmp, "tools"))
    for m in ("kontrola", "kontrola_domy"):
        sys.modules.pop(m, None)
    kontrola = importlib.import_module("kontrola")


def tearDownModule():
    sys.path.remove(os.path.join(_tmp, "tools"))
    for m in ("kontrola", "kontrola_domy"):
        sys.modules.pop(m, None)
    shutil.rmtree(_tmp)

VZOR = {"id": "1850-povoden-obec", "od": "1850-06", "do": "1850-06", "uroven": "zeme", "kde": ["morava"],
        "kategorie": "zivel", "nazev": "Povodeň", "text": "Obecní příklad.", "dopad": {"umrti": True, "vojaci": False},
        "zdroj": "Obecní kronika, s. 12", "jistota": "doc"}


class KontrolaUdalosti(unittest.TestCase):
    def chyby(self, obsah):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "udalosti.json")
            with open(p, "w", encoding="utf-8") as f:
                f.write(obsah if isinstance(obsah, str) else json.dumps(obsah))
            return kontrola.kontrola_udalosti(p)

    def test_chybejici_soubor(self):
        self.assertEqual(kontrola.kontrola_udalosti("/neexistuje/udalosti.json"), [])

    def test_validni(self):
        self.assertEqual(self.chyby([VZOR]), [])
        self.assertEqual(self.chyby([]), [])

    def test_template_je_prazdny_a_validni(self):
        p = os.path.join(os.path.dirname(TOOLS), "template", "data", "udalosti.json")
        self.assertEqual(json.load(open(p, encoding="utf-8")), [])
        self.assertEqual(kontrola.kontrola_udalosti(p), [])

    def test_neplatny_json(self):
        self.assertIn("platný JSON", self.chyby("[{")[0])

    def test_chybi_zdroj(self):
        e = dict(VZOR); del e["zdroj"]
        self.assertTrue(any("„zdroj“" in c for c in self.chyby([e])))
        self.assertTrue(any("„zdroj“" in c for c in self.chyby([dict(VZOR, zdroj="  ")])))

    def test_spatny_rozsah(self):
        self.assertTrue(any("je po do" in c for c in self.chyby([dict(VZOR, od="1851", do="1850")])))
        self.assertEqual(self.chyby([dict(VZOR, od="1850", do="1850-03-01")]), [])

    def test_duplicitni_id(self):
        self.assertTrue(any("duplicitní id" in c for c in self.chyby([VZOR, dict(VZOR)])))

    def test_kategorie_dle_osy(self):
        self.assertTrue(any("neznámá kategorie" in c for c in self.chyby([dict(VZOR, kategorie="mor")])))


if __name__ == "__main__":
    unittest.main()
