#!/usr/bin/env python3
"""Test cteni_ai.py bez sítě: chybějící klíč, lhůty, klíč v projektu, zpracování (mock) odpovědi OpenRouteru.

Spuštění: python3 -I tests/test_cteni_ai.py
"""
import io, json, os, shutil, sys, tempfile, unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus", "tools")


def projekt():
    """Dočasný projekt s kopií nástroje (ROOT = složka projektu)."""
    d = tempfile.mkdtemp(prefix="cteni_ai_")
    for sub in ("tools", "data", "zdroje"):
        os.makedirs(os.path.join(d, sub))
    shutil.copy(os.path.join(TOOLS, "cteni_ai.py"), os.path.join(d, "tools"))
    open(os.path.join(d, "data", "STAV.md"), "w").close()
    with open(os.path.join(d, "data", "zaznamy.json"), "w") as f:
        json.dump([{"klic": "n-stary-1820", "druh": "N", "datum": "1820-03-05"},
                   {"klic": "n-mlady-1990", "druh": "N", "datum": "1990"}], f)
    for k in ("n-stary-1820", "n-mlady-1990"):
        with open(os.path.join(d, "zdroje", k + ".jpg"), "wb") as f:
            f.write(b"\xff\xd8jpeg")
    sys.path.insert(0, os.path.join(d, "tools"))
    sys.modules.pop("cteni_ai", None)
    import cteni_ai
    sys.path.pop(0)
    return d, cteni_ai


class Odpoved(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Test(unittest.TestCase):
    def setUp(self):
        self.d, self.m = projekt()
        self.env = mock.patch.dict(os.environ, {"HOME": self.d}, clear=False)
        self.env.start()
        os.environ.pop("OPENROUTER_API_KEY", None)
        self.m.SOUBOR_KLICE = os.path.join(self.d, "neexistuje.key")

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.d, True)

    def spust(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            kod = self.m.main(list(args))
        return kod, out.getvalue(), err.getvalue()

    def test_bez_klice_jen_oznami(self):
        with mock.patch("urllib.request.urlopen") as u:
            kod, out, err = self.spust("n-stary-1820")
        self.assertEqual(kod, 3)
        self.assertIn("chybí klíč", err)
        self.assertEqual(out, "")
        u.assert_not_called()
        self.assertFalse(os.path.exists(os.path.join(self.d, "pracovni")))

    def test_mladsi_nez_lhuta_neposle(self):
        os.environ["OPENROUTER_API_KEY"] = "test"
        with mock.patch("urllib.request.urlopen") as u:
            kod, _, err = self.spust("n-mlady-1990")
        self.assertEqual(kod, 2)
        self.assertIn("mladší než 100 let", err)
        u.assert_not_called()

    def test_klic_v_projektu_odmitne(self):
        os.environ["OPENROUTER_API_KEY"] = "test"
        with open(os.path.join(self.d, "data", "poznamky.md"), "w") as f:
            f.write("klic sk-or-v1-abcdef0123456789\n")
        with mock.patch("urllib.request.urlopen") as u:
            kod, _, err = self.spust("n-stary-1820")
        self.assertEqual(kod, 2)
        self.assertIn("poznamky.md", err)
        u.assert_not_called()

    def test_mock_odpoved_zapise_do_pracovni(self):
        os.environ["OPENROUTER_API_KEY"] = "test"
        obsah = {"prepis": "Joannes [...] filius", "preklad": "Jan […] syn", "nejista_mista": ["příjmení"]}
        odp = {"choices": [{"message": {"content": "```json\n" + json.dumps(obsah) + "\n```"}}], "usage": {"cost": 0.002}}
        with mock.patch("urllib.request.urlopen", return_value=Odpoved(json.dumps(odp).encode())) as u:
            kod, out, _ = self.spust("n-stary-1820", "--model", "fable", "--zapsat")
        self.assertEqual(kod, 0)
        telo = json.loads(u.call_args[0][0].data)
        self.assertEqual(telo["model"], self.m.MODELY["fable"])
        self.assertEqual(telo["provider"], {"data_collection": "deny"})
        v = json.loads(out)
        self.assertEqual(v["prepis"], "Joannes [...] filius")
        self.assertEqual(v["cena_usd"], 0.002)
        self.assertIn("ověřit", v["stav"])
        soubory = os.listdir(os.path.join(self.d, "pracovni", "cteni_ai"))
        self.assertEqual(len(soubory), 1)
        self.assertFalse(os.path.exists(os.path.join(self.d, "data", "prepisy.json")))


if __name__ == "__main__":
    unittest.main()
