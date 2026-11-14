#!/usr/bin/env python3
"""Hloubka vějíře: fan_chart.py --generaci N (Kniha předků) vs. plná hloubka bez parametru.

Fixture = vymyšlená přímá linie Nováků přes 9 generací (kořen + 8 generací otců a jejich manželek),
tedy hlubší než výchozí kniha.generaci = 6. Nástroje se kopírují do dočasného projektu (fan_chart.py čte
data/osoby.py vedle složky tools/) a vějíř se kreslí v režimu --web (bez Chromu).

Spuštění: python3 -I tests/test_fan_chart_generaci.py
"""
import json, os, re, shutil, subprocess, sys, tempfile, unittest

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus")
TOOLS = os.path.join(SKILL, "tools")
GENERACI = 9   # kořen + 8 generací předků


def fixture():
    """data/osoby.py: Petr Novák (kořen), nad ním otcové Novákové G1–G8 a jejich manželky."""
    osoby = {"novak-g0": dict(n="Petr Novák G0", sex="M", y="* 1990", st="fam")}
    vztahy = []
    for g in range(1, GENERACI):
        dite = f"novak-g{g - 1}"
        rok = 1990 - 30 * g
        osoby[f"novak-g{g}"] = dict(n=f"Jan Novák G{g}", sex="M", y=f"{rok}–{rok + 60}", st="doc")
        osoby[f"novakova-g{g}"] = dict(n=f"Anna Nováková G{g}", sex="F", y=f"{rok + 2}–{rok + 65}", st="doc")
        vztahy += [dict(t="rodic", a=f"novak-g{g}", b=dite), dict(t="rodic", a=f"novakova-g{g}", b=dite),
                   dict(t="manzele", a=f"novak-g{g}", b=f"novakova-g{g}")]
    return f"KORENY = {{'hlavni': 'novak-g0'}}\nOSOBY = {osoby!r}\nVZTAHY = {vztahy!r}\n"


def hrefs():
    """Odkaz pro každé Kekulého číslo linie (1, 2^g otec, 2^g + 1 matka) → data-k ukáže nakreslené buňky."""
    out = {"1": "/osoba/novak-g0/"}
    for g in range(1, GENERACI):
        out[str(2 ** g)] = f"/osoba/novak-g{g}/"
        out[str(2 ** g + 1)] = f"/osoba/novakova-g{g}/"
    return out


class HloubkaVejire(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = os.path.realpath(tempfile.mkdtemp(prefix="fan_chart_test_"))
        shutil.copytree(TOOLS, os.path.join(cls.tmp, "tools"), ignore=shutil.ignore_patterns("__pycache__"))
        os.makedirs(os.path.join(cls.tmp, "data"))
        with open(os.path.join(cls.tmp, "data", "osoby.py"), "w", encoding="utf-8") as f:
            f.write(fixture())
        cls.hrefs = os.path.join(cls.tmp, "hrefs.json")
        with open(cls.hrefs, "w", encoding="utf-8") as f:
            json.dump(hrefs(), f)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, True)

    def vejir(self, *args):
        out = os.path.join(self.tmp, "fan-" + "-".join(args or ("plny",)) + ".svg")
        r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(self.tmp, "tools", "fan_chart.py"),
                            out, "--web", self.hrefs, *args], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, encoding="utf-8") as f:
            return f.read()

    def generace(self, svg):
        """Počet nakreslených generací včetně kořene = nejvyšší generace mezi buňkami s odkazem + 1."""
        return max(int(k).bit_length() for k in re.findall(r'<a href="[^"]*" data-k="(\d+)"', svg))

    def test_bez_parametru_plna_hloubka(self):
        svg = self.vejir()
        self.assertEqual(self.generace(svg), GENERACI)
        self.assertIn("Jan Novák G8", svg)

    def test_kniha_vychozi_6(self):
        svg = self.vejir("--generaci", "6")
        self.assertEqual(self.generace(svg), 6)
        self.assertIn("Jan Novák G5", svg)
        self.assertNotIn("Jan Novák G6", svg)
        self.assertNotIn("Anna Nováková G6", svg)

    def test_jina_hloubka(self):
        for n in (2, 4, 7):
            with self.subTest(n=n):
                self.assertEqual(self.generace(self.vejir("--generaci", str(n))), n)

    def test_hloubka_vetsi_nez_strom(self):
        self.assertEqual(self.vejir("--generaci", "20"), self.vejir())

    def test_omezeny_vejir_vyplni_cely_polomer(self):
        """Prstence se roztáhnou: vnější kruh omezeného vějíře má stejný poloměr jako plný (2240)."""
        svg = self.vejir("--generaci", "6")
        self.assertIn('viewBox="0 0 4520 4520"', svg)
        self.assertRegex(svg, r"A2240,2240 ")

    def test_neplatna_hodnota(self):
        for v in ("0", "x"):
            with self.subTest(v=v):
                r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(self.tmp, "tools", "fan_chart.py"),
                                    os.path.join(self.tmp, "x.svg"), "--web", self.hrefs, "--generaci", v],
                                   capture_output=True, text=True, encoding="utf-8")
                self.assertNotEqual(r.returncode, 0)

    def test_export_web_predava_generaci_knihy(self):
        zdroj = open(os.path.join(TOOLS, "export_web.py"), encoding="utf-8").read()
        self.assertIn('"--generaci", book_gens', zdroj)
        self.assertIn('.get("generaci", 6)', zdroj)


if __name__ == "__main__":
    unittest.main()
