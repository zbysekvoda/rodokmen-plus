#!/usr/bin/env python3
"""Kurátorovaná osa historických událostí (tools/udalosti.json): schéma, rozsah a pokrytí EPIDEMIE z napady.py.

Spuštění: python3 -m unittest discover tests
"""
import json, os, re, sys, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus", "tools")
KATEGORIE = {"valka", "epidemie", "hlad", "zivel", "reforma", "sprava", "mena", "rezim", "povstani",
             "hospodarstvi", "migrace", "cirkev"}
UROVNE = {"cr": {"cechy", "morava", "slezsko"}, "zeme": {"cechy", "morava", "slezsko"}}
KLICE = {"id", "od", "do", "uroven", "kde", "kategorie", "nazev", "text", "dopad", "zdroj", "jistota"}
DATUM = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")


def nacti():
    with open(os.path.join(TOOLS, "udalosti.json"), encoding="utf-8") as f:
        return json.load(f)


def rok(d):
    return int(d[:4])


class Osa(unittest.TestCase):
    def setUp(self):
        self.osa = nacti()

    def test_schema(self):
        for e in self.osa:
            with self.subTest(id=e.get("id")):
                self.assertEqual(set(e), KLICE)
                self.assertRegex(e["od"], DATUM)
                self.assertRegex(e["do"], DATUM)
                self.assertIn(e["kategorie"], KATEGORIE)
                self.assertIn(e["uroven"], UROVNE)
                self.assertTrue(e["kde"] and set(e["kde"]) <= UROVNE[e["uroven"]])
                if e["uroven"] == "cr":
                    self.assertEqual(set(e["kde"]), UROVNE["cr"])
                self.assertTrue(e["nazev"].strip() and e["text"].strip())
                self.assertTrue(e["zdroj"].strip(), "chybí zdroj")
                self.assertIn(e["jistota"], {"doc", "lit", "obecne"})
                self.assertEqual(set(e["dopad"]), {"umrti", "vojaci"})
                self.assertTrue(all(isinstance(v, bool) for v in e["dopad"].values()))

    def test_od_do(self):
        for e in self.osa:
            self.assertLessEqual((e["od"] + "-00-00")[:10], (e["do"] + "-99-99")[:10], e["id"])

    def test_unikatni_id(self):
        ids = [e["id"] for e in self.osa]
        self.assertEqual(len(ids), len(set(ids)))
        for i in ids:
            self.assertRegex(i, r"^\d{4}-[a-z0-9-]+$")

    def test_pocet_a_rozsah(self):
        self.assertTrue(180 <= len(self.osa) <= 220, len(self.osa))
        self.assertEqual(min(rok(e["od"]) for e in self.osa), 1620)
        self.assertLessEqual(max(rok(e["do"]) for e in self.osa), 1995)

    def test_epidemie_z_napadu(self):
        sys.path.insert(0, TOOLS)
        from napady import EPIDEMIE
        epid = [e for e in self.osa if e["kategorie"] == "epidemie"]
        for r in EPIDEMIE:
            with self.subTest(rok=r):
                self.assertTrue(any(rok(e["od"]) <= r <= rok(e["do"]) for e in epid), f"{r} ({EPIDEMIE[r]}) chybí v ose")


if __name__ == "__main__":
    unittest.main()
