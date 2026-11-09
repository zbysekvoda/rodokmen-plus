#!/usr/bin/env python3
"""Test litomerice.py bez sítě: portál vrátí stránku ověření člověka → srozumitelná hláška, kód 5, jediný request.

Spuštění: python3 -I tests/test_litomerice_overeni.py
"""
import atexit, contextlib, io, os, shutil, sys, tempfile, unittest
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus", "tools")
PROJ = tempfile.mkdtemp(prefix="litomerice_test_")
atexit.register(shutil.rmtree, PROJ, True)
os.environ["SLUSNE_DIR"] = os.path.join(PROJ, "slusne")
shutil.copytree(TOOLS, os.path.join(PROJ, "tools"))
os.makedirs(os.path.join(PROJ, "data"))
open(os.path.join(PROJ, "data", "STAV.md"), "w").close()   # litomerice.py běží jen v projektu
sys.path.insert(0, os.path.join(PROJ, "tools"))
import litomerice  # noqa: E402

STRANKY = {
    "challenge": '<html><script>location="/human/challenge?next=/digitalnibadatelna/"</script></html>',
    "verify": '<html><form action="/human/verify"></form></html>',
    "text": "<html><h1>Ověřujeme, že jste člověk</h1></html>",
}


class Odpoved(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


class Overeni(unittest.TestCase):
    def spust(self, stranka, fce, *args):
        volani = []

        def open_(req, timeout=None):
            volani.append(req.full_url)
            return Odpoved(stranka.encode())
        err = io.StringIO()
        with mock.patch.object(litomerice._op, "open", side_effect=open_), contextlib.redirect_stderr(err), \
                self.assertRaises(SystemExit) as cm:
            fce(*args)
        return cm.exception.code, err.getvalue(), volani

    def test_challenge_pri_hledani(self):
        for druh, stranka in STRANKY.items():
            with self.subTest(druh):
                kod, hlaska, volani = self.spust(stranka, litomerice.hledej, "Mělník")
                self.assertEqual(kod, litomerice.OVERENI_KOD)
                self.assertIn("ověřuje, že jde o člověka", hlaska)
                self.assertIn("prohlížeč", hlaska)
                self.assertIn("soal_zoomify.py", hlaska)
                self.assertEqual(len(volani), 1, "po ověření už žádný další request")

    def test_challenge_pri_dalsi_strane(self):
        kod, _, volani = self.spust(STRANKY["challenge"], litomerice.dalsi_strana, 2)
        self.assertEqual((kod, len(volani)), (litomerice.OVERENI_KOD, 1))

    def test_bezna_stranka_projde(self):
        self.assertEqual(litomerice.kontrola("<html>matriky</html>"), "<html>matriky</html>")


if __name__ == "__main__":
    unittest.main()
