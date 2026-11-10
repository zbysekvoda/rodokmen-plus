#!/usr/bin/env python3
"""Testy sekce „Shluky úmrtí v obci“ v tools/napady.py na syntetickém projektu v tmp.

Spuštění: python3 -m unittest discover tests
"""
import hashlib, json, os, shutil, subprocess, sys, tempfile, unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus", "tools")
sys.path.insert(0, TOOLS)
import napady, udalosti  # noqa: E402

MISTA = {"Holice": {"re": "Holic", "osm": "Holice, okres Pardubice, Pardubický kraj, Česko"},
         "Luhačovice": {"re": "Luhačovic", "osm": "Luhačovice, okres Zlín, Zlínský kraj, Česko"},
         "Ostřetín": {"re": "Ostřetín", "osm": "Ostřetín, okres Pardubice, Pardubický kraj, Česko"}}
OSA = [{"id": "1866-test-cholera", "od": "1866-06", "do": "1866-10", "uroven": "zeme", "kde": ["cechy"],
        "kategorie": "epidemie", "nazev": "Testovací cholera", "text": "t", "dopad": {"umrti": True, "vojaci": False},
        "zdroj": "z", "jistota": "lit"},
       {"id": "1880-test-povoden", "od": "1880", "do": "1880", "uroven": "cr", "kde": ["cechy", "morava", "slezsko"],
        "kategorie": "zivel", "nazev": "Povodeň bez obětí", "text": "t", "dopad": {"umrti": False, "vojaci": False},
        "zdroj": "z", "jistota": "lit"}]


def osoby():
    out = {"koren": dict(n="Kořen", sex="M", y="1840–1866", st="doc", f=["* 1840 Holice", "† 1866 Holice"])}
    i = 0
    def zemrel(fakt):
        nonlocal i
        i += 1
        out[f"o{i}"] = dict(n=f"Osoba {i}", sex="M", y="", st="doc", f=[fakt])
    for d in ("3. 7. 1866", "9. 8. 1866", "12. 8. 1866"):   # Holice: shluk se shodou s cholerou (+ kořen † 1866)
        zemrel(f"† {d} Holice čp. 1")
    for r in (1850, 1855, 1860, 1870, 1875):
        zemrel(f"† {r} Holice")
    for r in ("1880", "1880", "1880", "2. 3. 1880"):                      # Luhačovice: shluk bez události (povodeň bez obětí)
        zemrel(f"† {r} Luhačovice")
    for r in (1851, 1852, 1853, 1854, 1856, 1857):
        zemrel(f"† {r} Luhačovice")
    for r in (1850, 1851, 1852, 1852):                                    # Ostřetín: bez shluku (max 2 < 3)
        zemrel(f"† {r} Ostřetín")
    return out


class Shluky(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="napady_shluky_")
        self.addCleanup(shutil.rmtree, self.dir)
        os.makedirs(os.path.join(self.dir, "data"))
        self.osa = os.path.join(self.dir, "osa.json")
        with open(self.osa, "w", encoding="utf-8") as f:
            json.dump(OSA, f)
        self.vysledek = {(o, r): (c, ev) for o, r, c, _, _, ev in
                         napady.shluky_umrti(osoby().values(), MISTA, udalosti.nacti_osu(self.dir, self.osa))}

    def test_shoda_s_udalosti(self):
        c, ev = self.vysledek[("Holice", 1866)]
        self.assertEqual(c, 4)
        self.assertEqual([e["id"] for e in ev], ["1866-test-cholera"])
        sh = next(s for s in napady.shluky_umrti(osoby().values(), MISTA, udalosti.nacti_osu(self.dir, self.osa)) if s[0] == "Holice")
        radek = napady.radek_shluku(*sh)
        self.assertIn("shoda s událostí Testovací cholera (1866)", radek)
        self.assertIn("srpna (2)", radek)

    def test_bez_udalosti(self):
        c, ev = self.vysledek[("Luhačovice", 1880)]
        self.assertEqual((c, ev), (4, []))   # událost bez dopadu na úmrtí se nepočítá
        sh = next(s for s in napady.shluky_umrti(osoby().values(), MISTA, udalosti.nacti_osu(self.dir, self.osa)) if s[0] == "Luhačovice")
        self.assertIn("bez známé události – hledat v obecní/farní kronice", napady.radek_shluku(*sh))

    def test_obec_bez_shluku(self):
        self.assertFalse([k for k in self.vysledek if k[0] == "Ostřetín"])
        self.assertEqual(set(self.vysledek), {("Holice", 1866), ("Luhačovice", 1880)})

    def test_zemska_udalost_jine_zeme_neplati(self):
        lid = [dict(n=str(i), f=["† 1866 Luhačovice"]) for i in range(3)]
        sh = napady.shluky_umrti(lid, MISTA, udalosti.nacti_osu(self.dir, self.osa))
        self.assertEqual([(s[0], s[1], s[5]) for s in sh], [("Luhačovice", 1866, [])])


class CelyNastroj(unittest.TestCase):
    """napady.py jako skript nad syntetickým projektem: sekce se vypíše a data/ se nezmění."""

    def test_vypis_a_nic_se_nezapisuje(self):
        d = tempfile.mkdtemp(prefix="napady_projekt_")
        self.addCleanup(shutil.rmtree, d)
        shutil.copytree(TOOLS, os.path.join(d, "tools"), ignore=shutil.ignore_patterns("__pycache__"))
        os.makedirs(os.path.join(d, "data"))
        with open(os.path.join(d, "data", "osoby.py"), "w", encoding="utf-8") as f:
            f.write(f"KORENY = {{'hlavni': 'koren'}}\nOSOBY = {osoby()!r}\n")
        for jmeno, obsah in (("mista.json", MISTA), ("udalosti.json", OSA)):
            with open(os.path.join(d, "data", jmeno), "w", encoding="utf-8") as f:
                json.dump(obsah, f, ensure_ascii=False)
        def otisk():
            out = {}
            for n in sorted(os.listdir(os.path.join(d, "data"))):
                with open(os.path.join(d, "data", n), "rb") as f:
                    out[n] = hashlib.sha256(f.read()).hexdigest()
            return out
        pred = otisk()
        r = subprocess.run([sys.executable, "-I", os.path.join(d, "tools", "napady.py"), d],
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("## Shluky úmrtí v obci", r.stdout)
        self.assertIn("Holice 1866: 4 úmrtí", r.stdout)
        self.assertIn("Testovací cholera", r.stdout)
        self.assertIn("Luhačovice 1880: 4 úmrtí", r.stdout)
        self.assertNotIn("Ostřetín 18", r.stdout)
        self.assertIn("## Úmrtí v roce epidemie / války", r.stdout)
        self.assertEqual(otisk(), pred)


if __name__ == "__main__":
    unittest.main()
