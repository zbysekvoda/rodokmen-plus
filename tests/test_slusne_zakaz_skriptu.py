#!/usr/bin/env python3
"""Test bez sítě: SOA Třeboň a eBadatelna zakázaly skripty – slusne.py požadavek neodešle a 403 nikdy neopakuje.

Spuštění: python3 -I tests/test_slusne_zakaz_skriptu.py
"""
import atexit, http.client, os, shutil, sys, tempfile, unittest, urllib.request
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus", "tools")
os.environ["SLUSNE_DIR"] = tempfile.mkdtemp(prefix="slusne_test_")
atexit.register(shutil.rmtree, os.environ["SLUSNE_DIR"], True)
sys.path.insert(0, TOOLS)
import slusne  # noqa: E402

HOSTY = ("digi.ceskearchivy.cz", "ebadatelna.soapraha.cz")


class ZakazSkriptu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        slusne.instaluj()

    def test_curl_neodesle_request(self):
        for host in HOSTY:
            with self.subTest(host=host), mock.patch("subprocess.run") as run:
                with self.assertRaises(slusne.ZakazSkriptu) as e:
                    slusne.curl(["-s", f"https://{host}/4250/5"])
                run.assert_not_called()
                zprava = str(e.exception)
                self.assertIn("od 2. 11. 2026", zprava)
                self.assertIn("prohlížeč", zprava)
                self.assertIn("NEOBCHÁZEJ", zprava)

    def test_urllib_neotevre_spojeni(self):
        for host in HOSTY:
            with self.subTest(host=host), mock.patch.object(http.client.HTTPConnection, "connect") as c1, \
                    mock.patch.object(http.client.HTTPSConnection, "connect") as c2:
                with self.assertRaises(slusne.ZakazSkriptu):
                    urllib.request.urlopen(f"https://{host}/")
                c1.assert_not_called()
                c2.assert_not_called()

    def test_403_se_neopakuje(self):
        # I kdyby 403 přišla (jiná cesta než pockej), skončí hláškou a nezablokuje se do opakování po 30 min.
        for host in HOSTY:
            with self.subTest(host=host):
                with self.assertRaises(slusne.ZakazSkriptu):
                    slusne.posoudit(host, "dotaz", 403)
                with self.assertRaises(slusne.ZakazSkriptu):
                    slusne.po_odpovedi(host, "obr", 403, lambda jmeno: None)

    def test_ostatni_weby_beze_zmeny(self):
        self.assertIsNone(slusne.zakaz_skriptu("aron.vychodoceskearchivy.cz"))
        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(stderr="\nSLUSNE 200\n", returncode=0)
            slusne.curl(["-s", "https://aron.vychodoceskearchivy.cz/x"])
            run.assert_called_once()

    def test_zakaz_je_systemexit(self):
        # nástroje chytají Exception/OSError – zákaz jim nesmí proklouznout do opakování
        self.assertTrue(issubclass(slusne.ZakazSkriptu, SystemExit))


if __name__ == "__main__":
    unittest.main()
