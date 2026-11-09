#!/usr/bin/env python3
"""Test parseru mza.py bez sítě nad uloženými ukázkami stránky knihy (tests/fixtures/mza_detail_*.html).

Spuštění: python3 -I tests/test_mza_parser.py
"""
import contextlib, io, os, shutil, sys, tempfile, unittest
from unittest import mock

TESTS = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(TESTS), "skills", "rodokmen-plus", "tools")
PROJ = tempfile.mkdtemp(prefix="mza_test_")   # mza.py běží jen ze složky projektu (data/STAV.md)
os.makedirs(os.path.join(PROJ, "data"))
open(os.path.join(PROJ, "data", "STAV.md"), "w").close()
shutil.copytree(TOOLS, os.path.join(PROJ, "tools"))
os.environ.setdefault("SLUSNE_DIR", os.path.join(PROJ, "slusne"))
sys.path.insert(0, os.path.join(PROJ, "tools"))
import mza  # noqa: E402


def ukazka(jmeno):
    with open(os.path.join(TESTS, "fixtures", jmeno), encoding="utf-8") as f:
        return f.read()


class Detail(unittest.TestCase):
    def setUp(self):
        mza._DETAIL.clear()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(PROJ, True)

    def test_seznam_snimku(self):
        with mock.patch.object(mza, "get", return_value=ukazka("mza_detail_snimky.html")):
            d = mza.detail("1")
        self.assertEqual(len(d["dzi"]), 3)
        self.assertEqual(d["jmena"], ["0001", "0002", "0003"])
        self.assertEqual(d["pole"]["Jazyk"], "latina")
        self.assertEqual(d["obce"], ["Ukázkov"])
        self.assertEqual(d["casti"], ["narození (1700–1710)"])

    def test_brana_altcha_konci_kodem_5(self):
        err = io.StringIO()
        with mock.patch.object(mza, "get", return_value=ukazka("mza_detail_altcha.html")), \
                contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as e:
            mza.detail("3090")
        self.assertEqual(e.exception.code, mza.OVERENI_KOD)
        self.assertIn("prohlížeči", err.getvalue())

    def test_jina_zmena_stranky_neni_brana(self):
        with mock.patch.object(mza, "get", return_value="<html>nic</html>"), self.assertRaises(SystemExit) as e:
            mza.detail("1")
        self.assertIn("chybí seznam snímků", str(e.exception.code))


if __name__ == "__main__":
    unittest.main()
