#!/usr/bin/env python3
"""Test zapis.py dokumenty <klíč> --prejmenovat <nový> nad kopií ukázky v dočasné složce.

Funkce převzata z forku xkraust/rodokmen-skill, commit 79d3685.
Spuštění: python3 -I tests/test_zapis_prejmenovat.py
"""
import json, os, shutil, subprocess, sys, tempfile, unittest

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus")
STARY = "jan_novak_1890_portret"
NOVY = "jan_novak_1890_portret_1920"


def obsah(root):
    """{relativní cesta: bajty} všech souborů – pro porovnání „nic se nezměnilo“."""
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "__pycache__")]
        for f in files:
            p = os.path.join(base, f)
            with open(p, "rb") as fh:
                out[os.path.relpath(p, root)] = fh.read()
    return out


class Prejmenovat(unittest.TestCase):
    def setUp(self):
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="zapis_prejmenovat_test_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        r = subprocess.run([sys.executable, "-I", os.path.join(SKILL, "tools", "novy_projekt.py"), "projekt", "--ukazka"],
                           cwd=tmp, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.root = os.path.join(tmp, "projekt")
        data = os.path.join(self.root, "data")
        # odkazy na dokument, které ukázka sama nemá: výřez, originál, zvýraznění, foto na úvodu, obrázek v zajímavostech
        for sub in ("vyrezy", "zdroje"):
            os.makedirs(os.path.join(self.root, sub), exist_ok=True)
            with open(os.path.join(self.root, sub, STARY + ".jpg"), "wb") as f:
                f.write(b"\xff\xd8\xff\xd9")
        self.uprav_json("zvyrazneni.json", lambda d: d.update({STARY: {"boxes": [[0.1, 0.1, 0.9, 0.9]], "status": "ok"}}))
        self.uprav_json("web.json", lambda d: d["uvod"].update(foto=STARY, foto_popis="Jan Novák"))
        with open(os.path.join(data, "zajimavosti.md"), "a", encoding="utf-8") as f:
            f.write(f"\n![Jan Novák](img/{STARY}.jpg)\n")

    def uprav_json(self, name, fn):
        path = os.path.join(self.root, "data", name)
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        fn(d)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")

    def tool(self, name, *args):
        return subprocess.run([sys.executable, "-I", os.path.join("tools", name), *args], cwd=self.root,
                              capture_output=True, text=True, encoding="utf-8")

    def test_prejmenuje_klic_i_odkazy(self):
        r = self.tool("kontrola.py")
        self.assertEqual(r.returncode, 0, "kontrola před přejmenováním:\n" + r.stdout + r.stderr)

        r = self.tool("zapis.py", "dokumenty", STARY, "--prejmenovat", NOVY)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        for rel, b in obsah(self.root).items():
            if rel.split(os.sep)[0] in ("data", "vyrezy", "zdroje"):
                self.assertNotIn(STARY + '"', b.decode("utf-8", "replace"), rel)
                self.assertNotIn(STARY + ".jpg", b.decode("utf-8", "replace"), rel)
                self.assertNotIn(STARY + ".jpg", rel)
        for sub in ("vyrezy", "zdroje"):
            self.assertTrue(os.path.isfile(os.path.join(self.root, sub, NOVY + ".jpg")), sub)
        data = os.path.join(self.root, "data")
        with open(os.path.join(data, "dokumenty.json"), encoding="utf-8") as f:
            self.assertEqual([d["img"] for d in json.load(f)], [NOVY])
        with open(os.path.join(data, "zvyrazneni.json"), encoding="utf-8") as f:
            self.assertIn(NOVY, json.load(f))
        with open(os.path.join(data, "web.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["uvod"]["foto"], NOVY)
        with open(os.path.join(data, "zajimavosti.md"), encoding="utf-8") as f:
            self.assertIn(f"img/{NOVY}.jpg", f.read())

        r = self.tool("kontrola.py")
        self.assertEqual(r.returncode, 0, "kontrola po přejmenování:\n" + r.stdout + r.stderr)

    def test_kolize_a_nahled_nic_nezmeni(self):
        pred = obsah(self.root)
        for cil in ("ukazka_krest_jan_novak_1890",   # klíč matričního zápisu
                    STARY.upper(),                   # stejný klíč jen jinou velikostí písmen
                    "a/b"):                          # cesta místo klíče
            r = self.tool("zapis.py", "dokumenty", STARY, "--prejmenovat", cil)
            self.assertNotEqual(r.returncode, 0, cil)
            self.assertIn("Přejmenování se nezdařilo", r.stderr, cil)
        r = self.tool("zapis.py", "dokumenty", "neexistuje", "--prejmenovat", NOVY)
        self.assertNotEqual(r.returncode, 0)
        r = self.tool("zapis.py", "dokumenty", STARY, "--prejmenovat", NOVY, "--nahled")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Náhled: nic nezměněno.", r.stdout)
        self.assertEqual(obsah(self.root), pred)

    def test_kolize_s_existujicim_dokumentem(self):
        self.uprav_json("dokumenty.json", lambda d: d.append({"img": NOVY, "popis": "jiný", "osoby": []}))
        pred = obsah(self.root)
        r = self.tool("zapis.py", "dokumenty", STARY, "--prejmenovat", NOVY)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("už existuje", r.stderr)
        self.assertEqual(obsah(self.root), pred)


if __name__ == "__main__":
    unittest.main()
