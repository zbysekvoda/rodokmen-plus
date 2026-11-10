#!/usr/bin/env python3
"""Testy tools/udalosti.py: rok, rozsah, osoba (věk), filtr podle místa a sloučení projektové vrstvy.

Spuštění: python3 -m unittest discover tests
"""
import contextlib, io, json, os, shutil, sys, tempfile, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus", "tools")
UKAZKA = os.path.join(os.path.dirname(TOOLS), "template", "ukazka")
sys.path.insert(0, TOOLS)
import udalosti  # noqa: E402


def polozka(id, od, do, uroven="zeme", kde=("morava",), kategorie="zivel", nazev="Test"):
    return {"id": id, "od": od, "do": do, "uroven": uroven, "kde": list(kde), "kategorie": kategorie, "nazev": nazev,
            "text": "t", "dopad": {"umrti": False, "vojaci": False}, "zdroj": "z", "jistota": "lit"}


class Projekt(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="udalosti_test_")
        self.addCleanup(shutil.rmtree, self.dir)
        os.makedirs(os.path.join(self.dir, "data"))
        self.osa = os.path.join(self.dir, "osa.json")
        self.zapis("osa.json", [polozka("1850-cr", "1850", "1852", "cr", ("cechy", "morava", "slezsko")),
                                polozka("1851-morava", "1851-05", "1851-06", kde=("morava",)),
                                polozka("1851-cechy", "1851", "1851", kde=("cechy",), nazev="Puvodni"),
                                polozka("1900-cr", "1900", "1900", "cr", ("cechy", "morava", "slezsko"))])
        self.zapis("data/mista.json", {"Holice": {"osm": "Holice, okres Pardubice, Pardubický kraj, Česko"},
                                       "Luhačovice": {"osm": "Luhačovice, okres Zlín, Zlínský kraj, Česko"},
                                       "Jihlava": {"osm": "Jihlava, Kraj Vysočina, Česko"},
                                       "Ves": {"zeme": "slezsko"}})

    def zapis(self, rel, data):
        with open(os.path.join(self.dir, rel), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def ids(self, od, do, misto=None):
        osa = udalosti.nacti_osu(self.dir, self.osa)
        return [e["id"] for e in udalosti.v_rozsahu(osa, od, do, misto, udalosti.nacti_mista(self.dir))]

    def test_rok(self):
        self.assertEqual(self.ids(1851, 1851), ["1850-cr", "1851-cechy", "1851-morava"])
        self.assertEqual(self.ids(1853, 1853), [])

    def test_rozsah_prekryv(self):
        self.assertEqual(self.ids(1852, 1900), ["1850-cr", "1900-cr"])

    def test_filtr_mista(self):
        self.assertEqual(self.ids(1851, 1851, "Holice"), ["1850-cr", "1851-cechy"])
        self.assertEqual(self.ids(1851, 1851, "Luhačovice"), ["1850-cr", "1851-morava"])
        self.assertEqual(self.ids(1851, 1851, "Ves"), ["1850-cr"])
        self.assertEqual(self.ids(1851, 1851, "Jihlava"), ["1850-cr", "1851-cechy", "1851-morava"])   # země nejasná

    def test_bez_projektove_vrstvy(self):
        self.assertEqual(len(udalosti.nacti_osu(self.dir, self.osa)), 4)

    def test_slouceni_projektove_vrstvy(self):
        self.zapis("data/udalosti.json", [polozka("1851-cechy", "1851", "1851", kde=("cechy",), nazev="Projektova"),
                                          polozka("1851-pozar-holic", "1851-04", "1851-04", "obec", ("Holice",))])
        osa = udalosti.nacti_osu(self.dir, self.osa)
        self.assertEqual(len(osa), 5)
        self.assertEqual(next(e for e in osa if e["id"] == "1851-cechy")["nazev"], "Projektova")
        self.assertIn("1851-pozar-holic", self.ids(1851, 1851, "Holice"))
        self.assertNotIn("1851-pozar-holic", self.ids(1851, 1851, "Luhačovice"))

    def test_zivot_fallback(self):
        self.assertEqual(udalosti.zivot({"f": ["* 1. 1. 1850 Holice", "† 1900"]}), (1850, 1900, False))
        self.assertEqual(udalosti.zivot({"y": "* 1931"}, dnes=2026), (1931, 2011, True))
        self.assertEqual(udalosti.zivot({"y": "* 1980"}, dnes=2026), (1980, 2026, True))
        self.assertEqual(udalosti.zivot({"f": ["† 1800"]}), (1720, 1800, True))
        self.assertIsNone(udalosti.zivot({"f": ["kovář"]}))


class Ukazka(unittest.TestCase):
    """CLI nad vymyšleným ukázkovým projektem (template/ukazka jako data/)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="udalosti_ukazka_")
        self.addCleanup(shutil.rmtree, self.dir)
        shutil.copytree(UKAZKA, os.path.join(self.dir, "data"))

    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            kod = udalosti.main(["--projekt", self.dir, *args])
        return kod, out.getvalue()

    def test_rok(self):
        kod, out = self.run_cli("rok", "1866", "--misto", "Holice")
        self.assertEqual(kod, 0)
        self.assertIn("Cholera 1866", out)

    def test_rozsah(self):
        kod, out = self.run_cli("rozsah", "1914", "1918")
        self.assertEqual(kod, 0)
        self.assertIn("Španělská chřipka", out)

    def test_osoba_s_vekem(self):
        kod, out = self.run_cli("osoba", "jan-novak-1890")
        self.assertEqual(kod, 0)
        self.assertIn("1890–1944", out)
        self.assertIn("místo Holice", out)
        self.assertRegex(out, r"1918–1919 \(věk 28\)\s+Španělská chřipka")

    def test_nezname(self):
        self.assertEqual(self.run_cli("osoba", "nikdo-1900")[0], 1)
        self.assertEqual(self.run_cli("rok", "1900", "--misto", "Atlantida")[0], 1)


if __name__ == "__main__":
    unittest.main()
