#!/usr/bin/env python3
"""Box „Svět kolem“ v Knize předků: výběr událostí pro generaci (tools/udalosti.py → svet_kolem).

Spuštění: python3 -m unittest discover tests
"""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus", "tools"))
import udalosti  # noqa: E402
from test_export_udalosti import polozka, OSA, MISTA  # noqa: E402

A = {"y": "1860–1890", "f": ["* 1860 Holice", "† 1890 Holice"]}
B = {"y": "1880–1925", "f": ["* 1880 Holice", "† 1925 Holice"]}


class SvetKolem(unittest.TestCase):
    def test_sjednoceni_zivotu_a_3_az_5(self):
        ids = [e["id"] for e in udalosti.svet_kolem([A, B], OSA, MISTA)]
        self.assertTrue(3 <= len(ids) <= 5, ids)
        self.assertIn("1866-valka", ids)      # jen za života A
        self.assertIn("1918-chripka", ids)    # jen za života B
        self.assertNotIn("1866-cholera", ids)  # moravská, oba v Čechách
        self.assertEqual(ids, [e["id"] for e in sorted(udalosti.svet_kolem([A, B], OSA, MISTA), key=lambda e: (e["od"], e["id"]))])

    def test_nejvys_5(self):
        osa = [polozka(f"e{i}", str(1860 + i), str(1860 + i), k) for i, k in
               enumerate(["valka", "epidemie", "hlad", "rezim", "mena", "reforma", "migrace", "zivel"])]
        self.assertEqual(len(udalosti.svet_kolem([A, B], osa, MISTA)), 5)

    def test_doplni_do_3_pres_limit_kategorie(self):
        osa = [polozka(f"v{i}", str(1861 + 5 * i), str(1861 + 5 * i)) for i in range(4)]   # vše „valka“, limit 2
        self.assertEqual(len(udalosti.nejvyznamnejsi(osa, 5)), 2)
        self.assertEqual(len(udalosti.svet_kolem([A], osa, MISTA)), 3)

    def test_mene_kdyz_vic_neni(self):
        self.assertEqual([e["id"] for e in udalosti.svet_kolem([A], [polozka("x", "1870", "1870")], MISTA)], ["x"])

    def test_zadne_udalosti_prazdne(self):
        self.assertEqual(udalosti.svet_kolem([A], [polozka("po", "1990", "1990")], MISTA), [])
        self.assertEqual(udalosti.svet_kolem([{"y": ""}], OSA, MISTA), [])


if __name__ == "__main__":
    unittest.main()
