#!/usr/bin/env python3
"""Krátké příběhy: každá zajímavost (## v data/zajimavosti*.md) má na webu vlastní stránku /pribeh/<slug>/.

Spuštění: python3 -m unittest discover tests
"""
import json, os, shutil, subprocess, sys, tempfile, unittest

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus")
TOOLS = os.path.join(SKILL, "tools")


class KratkePribehy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = os.path.realpath(tempfile.mkdtemp(prefix="export_kratke_test_"))
        cls.dir = os.path.join(cls.tmp, "uk")
        r = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "novy_projekt.py"), "uk", "--ukazka"], cwd=cls.tmp,
                           capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, r.stderr
        # skupina (##) s položkami (###), kolize slugu s příběhem z web.json a odkaz [[pribeh:…]] na krátký příběh
        with open(os.path.join(cls.dir, "data", "zajimavosti.md"), "a", encoding="utf-8") as f:
            f.write("\n## Kovárna\nÚvod skupiny.\n\n### Výheň z roku 1786\nPrvní věta o výhni. Druhá věta.\n\n"
                    "### Kovadlina\nViz [[pribeh:vyhen-z-roku-1786]] a [[osoba:jan-novak-1890]].\n\n"
                    "## Kovárna!\nSlug by byl stejný jako u příběhu z web.json, dostane příponu.\n")
        r = subprocess.run([sys.executable, "-I", os.path.join(cls.dir, "tools", "export_web.py")], cwd=cls.dir,
                           capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, r.stdout + r.stderr
        cls.gen = os.path.join(cls.dir, "web", "src", "generated")
        with open(os.path.join(cls.dir, "web", "src", "data", "site.json"), encoding="utf-8") as f:
            cls.site = json.load(f)
        cls.kratke = {x["slug"]: x for x in cls.site["config"]["kratkePribehy"]}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, True)

    def cti(self, slug):
        with open(os.path.join(self.gen, "pribehy", slug + ".md"), encoding="utf-8") as f:
            return f.read()

    def test_kazda_zajimavost_ma_soubor(self):
        for slug in ("158-let-v-jedne-kovarne", "cholera-v-roce-1855", "vyhen-z-roku-1786", "kovadlina", "kovarna-2"):
            self.assertIn(slug, self.kratke)
            self.assertTrue(os.path.exists(os.path.join(self.gen, "pribehy", slug + ".md")), slug)

    def test_frontmatter_a_telo(self):
        t = self.cti("cholera-v-roce-1855")
        self.assertTrue(t.startswith("---\n"))
        self.assertIn("title: 'Cholera v roce 1855'", t)
        self.assertIn("kratky: true", t)
        self.assertNotIn("## Cholera", t)          # nadpis je v titulku, ne v těle
        self.assertNotIn("Mlynáři ze Slatiňan", t)  # jen vlastní text

    def test_lead_je_prvni_veta_bez_odkazu(self):
        self.assertEqual(self.kratke["vyhen-z-roku-1786"]["lead"], "První věta o výhni.")
        self.assertNotIn("](", self.kratke["cholera-v-roce-1855"]["lead"])

    def test_skupina(self):
        self.assertEqual(self.kratke["kovadlina"]["skupina"], "Kovárna")
        self.assertEqual(self.kratke["cholera-v-roce-1855"]["skupina"], "")

    def test_kolize_s_velkym_pribehem(self):
        self.assertNotIn("kovarna", self.kratke)
        self.assertEqual([x["slug"] for x in self.site["config"]["pribehy"]], ["kovarna"])
        self.assertNotIn("kratky: true", self.cti("kovarna"))

    def test_wiki_odkaz_na_kratky_pribeh(self):
        self.assertIn("(/pribeh/vyhen-z-roku-1786/)", self.cti("kovadlina"))

    def test_zminky_vedou_na_stranku_pribehu(self):
        m = self.site["people"]["jan-novak-1890"]["mentions"]
        self.assertTrue(any(x["href"].startswith("/pribeh/kovadlina/") and x["page"] == "Kovadlina" for x in m), m)
        self.assertFalse(any(x["href"].startswith("/zajimavosti/") for p in self.site["people"].values() for x in p["mentions"]))

    def test_karty_na_uvodu(self):
        c = self.site["config"]["zajimavosti_na_uvodu"][0]
        self.assertEqual(c["href"], "/pribeh/158-let-v-jedne-kovarne/")

    def test_stare_kotvy(self):
        # /zajimavosti/#<kotva nadpisu> → nová adresa (stránka /zajimavosti/ přesměrovává)
        self.assertEqual(self.site["config"]["zajimavostiKotvy"]["cholera-v-roce-1855"], "cholera-v-roce-1855")
        self.assertEqual(self.site["config"]["zajimavostiKotvy"]["158-let-v-jedné-kovárně"], "158-let-v-jedne-kovarne")

    def test_rody_z_osob(self):
        self.assertTrue(self.kratke["cholera-v-roce-1855"]["rody"])


if __name__ == "__main__":
    unittest.main()
