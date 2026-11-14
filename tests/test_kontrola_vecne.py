#!/usr/bin/env python3
"""Strukturovaný výstup věcných kontrol kontrola.py (vecne_polozky) a z něj odvozený text.

Spuštění: python3 -m unittest discover tests
"""
import importlib, os, shutil, sys, tempfile, unittest

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
    for m in ("kontrola", "kontrola_domy", "dolozeni"):
        sys.modules.pop(m, None)
    kontrola = importlib.import_module("kontrola")


def tearDownModule():
    sys.path.remove(os.path.join(_tmp, "tools"))
    for m in ("kontrola", "kontrola_domy", "dolozeni"):
        sys.modules.pop(m, None)
    shutil.rmtree(_tmp)


class Graf:
    def __init__(self, rodice):
        self._r = rodice

    def rodice(self, i):
        return self._r.get(i, (None, None))


O = {
    "otec": {"n": "Jan Novák", "f": ["* 1. 1. 1800", "† 1. 1. 1840"], "r": ["mat_1"]},
    "matka": {"n": "Anna Nováková", "f": ["* 1. 1. 1832"]},
    "dite": {"n": "Josef Novák", "f": ["* 1. 6. 1842"], "r": ["mat_2"]},
}


class VecnePolozky(unittest.TestCase):
    def setUp(self):
        self.p = kontrola.vecne_polozky(Graf({"dite": ("otec", "matka")}), O, [], {})

    def test_dite_po_smrti_otce(self):
        x = [p for p in self.p if p["typ"] == "narozeni_po_smrti"]
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0]["zavaznost"], "chyba")
        self.assertEqual(x[0]["osoby"], ["dite", "otec"])
        self.assertEqual(x[0]["zapisy"], ["mat_2", "mat_1"])
        self.assertIn("Ověřte", x[0]["vyzva"])

    def test_vek_matky(self):
        x = [p for p in self.p if p["typ"] == "vek_porod_matka"]
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0]["osoby"], ["matka", "dite"])
        self.assertIn("10 let", x[0]["vyzva"])

    def test_text_odvozeny(self):
        err, warn = [], []
        p = kontrola.vecne_kontroly(err, warn, Graf({"dite": ("otec", "matka")}), O, [], {})
        self.assertEqual(err, [x["text"] for x in p if x["zavaznost"] == "chyba"])
        self.assertEqual(warn, [x["text"] for x in p if x["zavaznost"] == "upozorneni"])
        self.assertTrue(any("dní po smrti otce" in e for e in err))

    def test_bez_problemu(self):
        ok = {"a": {"n": "A", "f": ["* 1. 1. 1800"]}, "b": {"n": "B", "f": ["* 1. 1. 1830"]}}
        self.assertEqual(kontrola.vecne_polozky(Graf({"b": ("a", None)}), ok, [], {}), [])


if __name__ == "__main__":
    unittest.main()
