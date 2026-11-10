#!/usr/bin/env python3
"""Testy `udalosti.py wikidata`: převod odpovědi SPARQL (fixture) na formát data/udalosti.json, bez sítě.

Spuštění: python3 -m unittest discover tests
"""
import contextlib, io, json, os, shutil, sys, tempfile, unittest, urllib.error
from unittest import mock

TESTS = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(TESTS), "skills", "rodokmen-plus", "tools")
sys.path.insert(0, TOOLS)
import udalosti  # noqa: E402

with open(os.path.join(TESTS, "fixtures", "wikidata_sparql.json"), encoding="utf-8") as f:
    ODPOVED = json.load(f)
POLE = {"id", "od", "do", "uroven", "kde", "kategorie", "nazev", "text", "dopad", "zdroj", "jistota"}


class Wikidata(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "data"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_cli(self, *args, stahni=None):
        out, err = io.StringIO(), io.StringIO()
        stahni = stahni or mock.Mock(return_value=ODPOVED)
        with mock.patch.object(udalosti, "wd_stahni", stahni), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            kod = udalosti.main(["--projekt", self.tmp, "wikidata", *args])
        return kod, out.getvalue(), err.getvalue(), stahni

    def test_format_a_qid(self):
        kod, out, _, _ = self.run_cli("Hradec Králové", "--klic", "hradec")
        self.assertEqual(kod, 0)
        kand = json.loads(out)
        self.assertEqual(len(kand), 2)  # duplicitní QID sloučen
        bitva, pozar = kand
        self.assertEqual(set(bitva), POLE)
        self.assertEqual(bitva["zdroj"], "Wikidata Q152497")
        self.assertEqual((bitva["id"], bitva["od"], bitva["do"]), ("1866-bitva-u-hradce-kralove", "1866-07-03", "1866-07-03"))
        self.assertEqual((bitva["uroven"], bitva["kde"], bitva["kategorie"]), ("obec", ["hradec"], "valka"))
        self.assertEqual((pozar["od"], pozar["do"], pozar["kategorie"]), ("1890", "1891", "zivel"))
        self.assertEqual(pozar["zdroj"], "Wikidata Q99999")

    def test_okres(self):
        _, out, _, stahni = self.run_cli("Pardubice", "--okres")
        self.assertEqual(json.loads(out)[0]["uroven"], "region")
        self.assertIn("wd:Q548611", stahni.call_args[0][0])
        self.assertIn('"Pardubice"@cs', stahni.call_args[0][0])

    def test_nic_nezapisuje(self):
        pred = sorted(os.walk(self.tmp))
        self.run_cli("Holice")
        self.assertEqual(sorted(os.walk(self.tmp)), pred)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "data", "udalosti.json")))

    def test_sitova_chyba(self):
        kod, out, err, _ = self.run_cli("Holice", stahni=mock.Mock(side_effect=urllib.error.URLError("timeout")))
        self.assertEqual(kod, 2)
        self.assertEqual(out, "")
        self.assertIn("Wikidata nejsou dostupná", err)
        self.assertNotIn("Traceback", err)

    def test_user_agent_bez_emailu(self):
        req = {}

        class Odp(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def urlopen(r, timeout):
            req["r"], req["t"] = r, timeout
            return Odp(json.dumps(ODPOVED).encode())
        with mock.patch("urllib.request.urlopen", urlopen):
            udalosti.wd_stahni("SELECT 1")
        ua = req["r"].get_header("User-agent")
        self.assertRegex(ua, r"^rodokmen-plus/\S+ \(genealogy tool\)$")
        self.assertNotIn("@", ua)
        self.assertTrue(0 < req["t"] <= 60)
        self.assertTrue(req["r"].full_url.startswith("https://query.wikidata.org/sparql?"))


if __name__ == "__main__":
    unittest.main()
