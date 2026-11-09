#!/usr/bin/env python3
"""Test argumentů a založení projektu v novy_projekt.py (vše v dočasné složce).

Spuštění: python3 -I tests/test_novy_projekt.py
"""
import os, shutil, subprocess, sys, tempfile, unittest

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus")
SCRIPT = os.path.join(SKILL, "tools", "novy_projekt.py")
IGNOR = ("node_modules", "dist", ".astro", "__pycache__")


def soubory(root):
    out = set()
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNOR]
        for f in files:
            out.add(os.path.normpath(os.path.relpath(os.path.join(base, f), root)))
    return out


def vse(root):
    out = set()
    for base, dirs, files in os.walk(root):
        for x in dirs + files:
            out.add(os.path.relpath(os.path.join(base, x), root))
    return out


class NovyProjekt(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="novy_projekt_test_"))   # macOS: /var → /private/var
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def run_script(self, *args):
        return subprocess.run([sys.executable, "-I", SCRIPT, *args], cwd=self.tmp,
                              capture_output=True, text=True, encoding="utf-8")

    def test_help(self):
        r = self.run_script("--help")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--ukazka", r.stdout)
        self.assertIn("Založí nový projekt", r.stdout)
        self.assertEqual(os.listdir(self.tmp), [])

    def test_neznama_volba(self):
        r = self.run_script("projekt", "--neznama")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--neznama", r.stderr)
        self.assertEqual(os.listdir(self.tmp), [])

    def test_bez_argumentu(self):
        r = self.run_script()
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(os.listdir(self.tmp), [])

    def over_strukturu(self, dst, data_src):
        for d in ("data", "web", "tools", "vyrezy", "zdroje", "dokumenty", "pracovni", ".claude"):
            self.assertTrue(os.path.isdir(os.path.join(dst, d)), d)
        self.assertLessEqual(soubory(os.path.join(SKILL, "template", data_src)), soubory(os.path.join(dst, "data")))
        self.assertEqual(soubory(os.path.join(SKILL, "template", "web")), soubory(os.path.join(dst, "web")))
        nastroje = {f for f in os.listdir(os.path.join(SKILL, "tools"))
                    if f.endswith((".py", ".sh", ".pl")) and f != "novy_projekt.py"}
        self.assertEqual(nastroje, set(os.listdir(os.path.join(dst, "tools"))))
        for name in ("CLAUDE.md", ".gitignore", ".gitattributes", "poznamky_pro_skill.md",
                     os.path.join(".claude", "launch.json"), os.path.join(".claude", "settings.json")):
            with open(os.path.join(SKILL, "template", name), "rb") as a, open(os.path.join(dst, name), "rb") as b:
                self.assertEqual(a.read(), b.read(), name)
        with open(os.path.join(SKILL, "VERZE"), encoding="utf-8") as a, \
                open(os.path.join(dst, ".skill_verze"), encoding="utf-8") as b:
            self.assertEqual(a.read(), b.read())

    def test_bezne_zalozeni(self):
        r = self.run_script("projekt")
        self.assertEqual(r.returncode, 0, r.stderr)
        dst = os.path.join(self.tmp, "projekt")
        self.assertIn("Projekt připraven: " + dst, r.stdout)
        self.assertEqual(os.listdir(self.tmp), ["projekt"])
        self.over_strukturu(dst, "data")
        # druhé spuštění (aktualizace) nic nemění a nezakládá zálohu webu
        pred = vse(dst)
        r = self.run_script("projekt")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(vse(dst), pred)

    def test_ukazka_v_libovolnem_poradi(self):
        for args, name in ((("a", "--ukazka"), "a"), (("--ukazka", "b"), "b")):
            r = self.run_script(*args)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.over_strukturu(os.path.join(self.tmp, name), "ukazka")
        self.assertEqual(sorted(os.listdir(self.tmp)), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
