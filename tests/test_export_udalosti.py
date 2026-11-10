#!/usr/bin/env python3
"""Historický kontext ve webu: výběr „Doba“ (tools/udalosti.py) a export událostí v export_web.py / export_web_domy.py.

Spuštění: python3 -m unittest discover tests
"""
import json, os, shutil, subprocess, sys, tempfile, unittest

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus")
TOOLS = os.path.join(SKILL, "tools")
sys.path.insert(0, TOOLS)
import udalosti  # noqa: E402


def polozka(id, od, do, kategorie="valka", uroven="cr", kde=("cechy", "morava", "slezsko"), umrti=False):
    return {"id": id, "od": od, "do": do, "uroven": uroven, "kde": list(kde), "kategorie": kategorie, "nazev": id,
            "text": "t", "dopad": {"umrti": umrti, "vojaci": False}, "zdroj": "z", "jistota": "lit"}


OSA = [polozka("1800-pred", "1800", "1801"),
       polozka("1866-valka", "1866", "1866", umrti=True),
       polozka("1866-cholera", "1866", "1867", "epidemie", "zeme", ("morava",), umrti=True),
       polozka("1880-sprava", "1880", "1880", "sprava"),
       polozka("1914-valka", "1914", "1918", umrti=True),
       polozka("1915-uvnitr", "1915", "1916", umrti=True),
       polozka("1916-dalsi-valka", "1916", "1916"),
       polozka("1918-chripka", "1918", "1919", "epidemie", umrti=True),
       polozka("1990-po", "1990", "1990")]
MISTA = {"Holice": {"osm": "Holice, okres Pardubice, Pardubický kraj, Česko"}}
OSOBA = {"y": "1860–1920", "f": ["* 1860 Holice", "† 1920 Holice"]}


class Doba(unittest.TestCase):
    def test_jen_za_zivota_a_misto(self):
        ids = [e["id"] for e, _ in udalosti.doba(OSOBA, OSA, MISTA, n=10)]
        self.assertNotIn("1800-pred", ids)
        self.assertNotIn("1990-po", ids)
        self.assertNotIn("1866-cholera", ids)   # moravská, osoba žije v Čechách
        self.assertIn("1918-chripka", ids)

    def test_vek_a_poradi(self):
        d = udalosti.doba(OSOBA, OSA, MISTA)
        self.assertEqual([e["od"] for e, _ in d], sorted(e["od"] for e, _ in d))
        self.assertIn(("1918-chripka", 58), [(e["id"], v) for e, v in d])

    def test_pestrost(self):
        ids = [e["id"] for e, _ in udalosti.doba(OSOBA, OSA, MISTA, n=5)]
        self.assertNotIn("1915-uvnitr", ids)        # leží celá uvnitř vybrané války stejné kategorie
        self.assertLessEqual(sum(i.endswith("valka") for i in ids), 2)
        self.assertLessEqual(len(ids), 5)

    def test_bez_let(self):
        self.assertEqual(udalosti.doba({"y": "", "f": []}, OSA, MISTA), [])

    def test_kontext_osob_filtruje_na_zivoty(self):
        ids = {e["id"] for e in udalosti.kontext_osob([OSOBA], OSA, MISTA)}
        self.assertNotIn("1800-pred", ids)
        self.assertNotIn("1990-po", ids)
        self.assertNotIn("1866-cholera", ids)
        self.assertIn("1880-sprava", ids)
        mor = {"y": "1850–1870", "f": ["* 1850 Brno"], "bydliste": [{"obec": "Brno"}]}
        ids = {e["id"] for e in udalosti.kontext_osob([mor], OSA, {"Brno": {"zeme": "morava"}})}
        self.assertIn("1866-cholera", ids)

    def test_pro_web(self):
        e = udalosti.pro_web(dict(OSA[1], od="1866-06-14"))
        self.assertEqual((e["od"], e["do"], e["datum"][0]), (1866, 1866, "1866-06-14"))
        self.assertGreater(e["vaha"], 0)


class ExportUkazky(unittest.TestCase):
    """Ukázkový projekt (novy_projekt.py --ukazka) → export_web.py → web/src/data/site.json."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = os.path.realpath(tempfile.mkdtemp(prefix="export_udalosti_test_"))
        cls.dir = os.path.join(cls.tmp, "uk")
        r = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "novy_projekt.py"), "uk", "--ukazka"], cwd=cls.tmp,
                           capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, r.stderr
        # projektová vrstva: místní událost Holic (klíč z mista.json) a jedna mimo životy osob
        with open(os.path.join(cls.dir, "data", "udalosti.json"), "w", encoding="utf-8") as f:
            json.dump([polozka("1905-pozar-holic", "1905", "1905", "zivel", "obec", ("Holice",), umrti=True),
                       polozka("1500-mimo", "1500", "1500", "zivel", "obec", ("Holice",))], f, ensure_ascii=False)
        r = subprocess.run([sys.executable, "-I", os.path.join(cls.dir, "tools", "export_web.py")], cwd=cls.dir,
                           capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, r.stdout + r.stderr
        with open(os.path.join(cls.dir, "web", "src", "data", "site.json"), encoding="utf-8") as f:
            cls.site = json.load(f)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, True)

    def test_udalosti_v_datech(self):
        ids = {e["id"] for e in self.site["events"]}
        self.assertIn("1918-spanelska-chripka", ids)
        self.assertIn("1905-pozar-holic", ids)
        e = next(e for e in self.site["events"] if e["id"] == "1905-pozar-holic")
        self.assertTrue(e["projekt"])
        for k in ("od", "do", "nazev", "text", "kategorie", "vaha"):
            self.assertIn(k, e)

    def test_filtr_na_zivoty(self):
        ids = {e["id"] for e in self.site["events"]}
        self.assertNotIn("1500-mimo", ids)
        osa = udalosti.nacti_osu(self.dir)
        self.assertLess(len(ids), len(osa))
        prvni = min(int(y) for p in self.site["people"].values() for y in __import__("re").findall(r"\b1[5-9]\d\d\b", p["y"]))
        self.assertTrue(all(e["do"] >= prvni - 1 for e in self.site["events"]), "událost dávno před první osobou")

    def test_doba_osoby(self):
        jan = self.site["people"]["jan-novak-1890"]
        self.assertTrue(3 <= len(jan["doba"]) <= 5, jan["doba"])
        ids = {e["id"] for e in self.site["events"]}
        self.assertTrue(all(x["id"] in ids for x in jan["doba"]))
        self.assertIn({"id": "1918-spanelska-chripka", "vek": 28}, jan["doba"])

    def test_doba_domu(self):
        domy = [h for h in self.site["houses"].values() if h.get("processed")]
        self.assertTrue(domy)
        ids = {e["id"] for e in self.site["events"]}
        self.assertTrue(any(h["doba"] for h in domy))
        for h in domy:
            self.assertLessEqual(len(h["doba"]), 5)
            self.assertTrue(all(x["id"] in ids for x in h["doba"]))

    def test_svet_kolem_generace_knihy(self):
        """p.svet[g-1] = události pro generaci g od osoby (box „Svět kolem“ v Knize předků), id ze site.events."""
        ids = {e["id"] for e in self.site["events"]}
        lide = self.site["people"]
        s_knihou = [p for p in lide.values() if p.get("svet")]
        self.assertTrue(s_knihou)
        for p in s_knihou:
            rodice = [x for x in (p.get("father"), p.get("mother")) if x in lide]
            self.assertTrue(rodice)
            for g in p["svet"]:
                self.assertLessEqual(len(g), 5)
                self.assertTrue(set(g) <= ids)
        self.assertTrue(any(3 <= len(g) <= 5 for p in s_knihou for g in p["svet"]))
        self.assertNotIn("svet", next(p for p in lide.values() if not (p.get("father") or p.get("mother"))))


if __name__ == "__main__":
    unittest.main()
