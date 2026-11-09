#!/usr/bin/env python3
"""Test brzdy slusne.py bez sítě: lokální HTTP server vrací Retry-After / RateLimit-* a ověřuje se, že se čeká.

Spuštění: python3 -I tests/test_slusne_retry_after.py
"""
import atexit, email.utils, http.server, os, shutil, subprocess, sys, tempfile, threading, time, unittest, urllib.error, urllib.request
from unittest import mock

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills", "rodokmen-plus", "tools")
os.environ["SLUSNE_DIR"] = tempfile.mkdtemp(prefix="slusne_test_")
atexit.register(shutil.rmtree, os.environ["SLUSNE_DIR"], True)
sys.path.insert(0, TOOLS)
import slusne  # noqa: E402

ODPOVEDI = {}   # cesta → (kód, hlavičky)


class Server(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        kod, hlavicky = ODPOVEDI.get(self.path.split("?")[0], (200, {}))
        self.send_response(kod)
        for k, v in hlavicky.items():
            self.send_header(k, v)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


class RetryAfter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        slusne.instaluj()
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Server)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.srv.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        for f in os.listdir(os.environ["SLUSNE_DIR"]):   # každý test s čistým stavem brzdy
            os.remove(os.path.join(os.environ["SLUSNE_DIR"], f))

    def get(self, cesta):
        with urllib.request.urlopen(self.base + cesta, timeout=10) as r:
            return r.read()

    def cas_dalsiho(self, cesta):
        t = time.time()
        self.get(cesta)
        return time.time() - t

    # Cesty končí .png → rozestup obrázků 0,05 s, takže změřené čekání je jen to, které chtěl server.
    def test_retry_after_sekundy_u_200(self):
        ODPOVEDI["/a.png"] = (200, {"Retry-After": "2"})
        self.get("/a.png")
        ODPOVEDI["/a.png"] = (200, {})
        cekal = self.cas_dalsiho("/a.png")
        print(f"\n  Retry-After: 2 → další požadavek čekal {cekal:.2f} s", end="")
        self.assertGreaterEqual(cekal, 1.9)
        self.assertLess(cekal, 4)

    def test_retry_after_datum_http(self):
        ODPOVEDI["/b.png"] = (200, {"Retry-After": email.utils.formatdate(time.time() + 3, usegmt=True)})
        self.get("/b.png")
        ODPOVEDI["/b.png"] = (200, {})
        cekal = self.cas_dalsiho("/b.png")
        print(f"\n  Retry-After: <datum HTTP +3 s> → čekal {cekal:.2f} s", end="")
        self.assertGreaterEqual(cekal, 1.9)   # datum HTTP má rozlišení 1 s
        self.assertLess(cekal, 5)

    def test_ratelimit_remaining_0(self):
        ODPOVEDI["/c.png"] = (200, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "2"})
        self.get("/c.png")
        ODPOVEDI["/c.png"] = (200, {})
        cekal = self.cas_dalsiho("/c.png")
        print(f"\n  X-RateLimit-Remaining: 0, Reset: 2 → čekal {cekal:.2f} s", end="")
        self.assertGreaterEqual(cekal, 1.9)

    def test_ratelimit_ietf_tvar(self):
        ODPOVEDI["/d.png"] = (200, {"RateLimit": '"default";r=0;t=2'})
        self.get("/d.png")
        ODPOVEDI["/d.png"] = (200, {})
        self.assertGreaterEqual(self.cas_dalsiho("/d.png"), 1.9)

    def test_429_s_dlouhym_retry_after_blokuje_web(self):
        datum = email.utils.formatdate(time.time() + 3 * 3600, usegmt=True)
        ODPOVEDI["/e.png"] = (429, {"Retry-After": datum})
        with self.assertRaises(slusne.Zablokovano):
            self.get("/e.png")
        do, proc = slusne.blokace("127.0.0.1")
        print(f"\n  429 + Retry-After +3 h → blokace na {(do - time.time()) / 3600:.2f} h ({proc})", end="")
        self.assertGreater(do - time.time(), 3 * 3600 - 60)
        with self.assertRaises(slusne.Zablokovano):   # další požadavek už na server nejde
            self.get("/a.png")

    def test_429_s_kratkym_retry_after_blokuje_aspon_30_min(self):
        ODPOVEDI["/f.png"] = (429, {"Retry-After": "5"})
        with self.assertRaises(slusne.Zablokovano):
            self.get("/f.png")
        do, _ = slusne.blokace("127.0.0.1")
        self.assertGreater(do - time.time(), slusne.BLOKACE - 60)

    def test_sekundy(self):
        ted = 1_800_000_000
        self.assertEqual(slusne.sekundy("120", ted), 120)
        self.assertEqual(slusne.sekundy(str(ted + 30), ted), 30)
        self.assertEqual(slusne.sekundy(email.utils.formatdate(ted + 90, usegmt=True), ted), 90)
        self.assertEqual(slusne.sekundy("nesmysl", ted), 0)
        self.assertEqual(slusne.sekundy(None, ted), 0)


class CurlHlavicky(unittest.TestCase):
    """curl větev bez sítě a bez spaní: subprocess.run je podvržený (zapíše hlavičky do souboru -D a vrátí kód),
    time.sleep jen zaznamená, kolik se mělo čekat."""
    URL = "https://archiv.example.invalid/snimek.png"   # .png → rozestup obrázků 0,05 s, měří se jen pauza od serveru

    def setUp(self):
        for f in os.listdir(os.environ["SLUSNE_DIR"]):
            os.remove(os.path.join(os.environ["SLUSNE_DIR"], f))
        self.spani, self.volani, self.odpovedi = [], [], []
        p1 = mock.patch.object(slusne.subprocess, "run", side_effect=self._curl)
        p2 = mock.patch.object(slusne.time, "sleep", side_effect=self.spani.append)
        p1.start(), p2.start()
        self.addCleanup(mock.patch.stopall)

    def _curl(self, cmd, **kw):
        """Odpověď z fronty self.odpovedi: (kód, hlavičky) nebo seznam takových dvojic (přesměrování s -L)."""
        self.volani.append(cmd)
        odpoved = self.odpovedi.pop(0)
        bloky = odpoved if isinstance(odpoved, list) else [odpoved]
        soubor = cmd[len(cmd) - 1 - cmd[::-1].index("-D") + 1]   # poslední -D, jako curl
        if soubor != "-":
            with open(soubor, "w", encoding="latin-1") as f:
                for kod, hl in bloky:
                    f.write(f"HTTP/2 {kod}\r\n" + "".join(f"{k}: {v}\r\n" for k, v in hl.items()) + "\r\n")
        return subprocess.CompletedProcess(cmd, 0, None, f"\nSLUSNE {bloky[-1][0]}\n")

    def test_200_s_retry_after_dalsi_curl_ceka(self):
        self.odpovedi += [(200, {"Retry-After": "2"}), (200, {})]
        slusne.curl(["-s", self.URL])
        self.assertEqual(self.spani, [])
        slusne.curl(["-s", self.URL])
        self.assertEqual(len(self.spani), 1)
        self.assertAlmostEqual(self.spani[0], 2, delta=0.5)

    def test_200_s_ratelimit_remaining_0(self):
        self.odpovedi += [(200, {"RateLimit-Remaining": "0", "RateLimit-Reset": "7"}), (200, {})]
        slusne.curl([self.URL])
        slusne.curl([self.URL])
        self.assertAlmostEqual(self.spani[0], 7, delta=0.5)

    def test_429_retry_after_sekundy(self):
        self.odpovedi.append((429, {"Retry-After": "7200"}))
        with self.assertRaises(slusne.Zablokovano):
            slusne.curl([self.URL])
        do, proc = slusne.blokace("archiv.example.invalid")
        self.assertAlmostEqual(do - time.time(), 7200, delta=60)
        self.assertIn("Retry-After 7200", proc)
        with self.assertRaises(slusne.Zablokovano):   # další curl už se nespustí
            slusne.curl([self.URL])
        self.assertEqual(len(self.volani), 1)

    def test_429_retry_after_datum_http(self):
        self.odpovedi.append((429, {"Retry-After": email.utils.formatdate(time.time() + 3 * 3600, usegmt=True)}))
        with self.assertRaises(slusne.Zablokovano):
            slusne.curl([self.URL])
        do, _ = slusne.blokace("archiv.example.invalid")
        self.assertAlmostEqual(do - time.time(), 3 * 3600, delta=60)

    def test_429_kratky_retry_after_blokuje_aspon_30_min(self):
        self.odpovedi.append((429, {"Retry-After": "5"}))
        with self.assertRaises(slusne.Zablokovano):
            slusne.curl([self.URL])
        do, _ = slusne.blokace("archiv.example.invalid")
        self.assertGreater(do - time.time(), slusne.BLOKACE - 60)

    def test_presmerovani_plati_posledni_odpoved(self):
        self.odpovedi.append([(301, {"Retry-After": "9999", "Location": "/jinam"}), (429, {"Retry-After": "7200"})])
        with self.assertRaises(slusne.Zablokovano):
            slusne.curl(["-L", self.URL])
        do, _ = slusne.blokace("archiv.example.invalid")
        self.assertAlmostEqual(do - time.time(), 7200, delta=60)

    def test_vlastni_dump_header_se_precte_a_nesmaze(self):
        fd, vlastni = tempfile.mkstemp(dir=os.environ["SLUSNE_DIR"])
        os.close(fd)
        self.odpovedi += [(200, {"Retry-After": "3"}), (200, {})]
        slusne.curl(["-D", vlastni, self.URL])
        self.assertEqual(self.volani[0].count("-D"), 1)   # žádné druhé -D
        self.assertTrue(os.path.exists(vlastni))
        slusne.curl([self.URL])
        self.assertAlmostEqual(self.spani[0], 3, delta=0.5)

    def test_docasny_soubor_hlavicek_se_smaze(self):
        self.odpovedi.append((200, {}))
        slusne.curl([self.URL])
        soubor = self.volani[0][self.volani[0].index("-D") + 1]
        self.assertFalse(os.path.exists(soubor))


if __name__ == "__main__":
    unittest.main(verbosity=2)
