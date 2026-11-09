#!/usr/bin/env python3
"""„Kniha předků“ do PDF: vytiskne tiskovou route /kniha/<id>/ z hotového webu (web/dist) headless Chromem.

Použití: python3 -I tools/kniha_pdf.py <id osoby> [--web]      (např. jan-novak-1890)
         python3 -I tools/kniha_pdf.py --vse [--web]           (všechny osoby, které mají knihu)

Výstup vystupy/kniha-<id>.pdf; s --web navíc web/public/kniha/<id>.pdf (a do web/dist/kniha/, je-li),
odkaz „Kniha předků (PDF)“ na stránce osoby se objeví po dalším `npm run build`.
Když web/dist knihu neobsahuje, spustí `npm run data` (chybí-li data) a `npm run build`.

Jak: dist obslouží lokální HTTP server (file:// rozbije cesty /_astro/), výřezy z /img/ a /zdroje/ cestou
zmenší na tiskových ~165 dpi, JPEG kvalita 65 (ImageMagick, prostredi.zmensi_obrazek). Chrome se ovládá přes DevTools protokol
(vlastní minimální WebSocket klient, jen standardní knihovna): tiskne se až po window.knihaHotovo, tj. když
Paged.js dosází všechny stránky. Prostý `chrome --print-to-pdf` s časovým rozpočtem by dosázel jen první stranu.
"""
import base64, functools, http.server, json, os, shutil, socket, struct, subprocess, sys, tempfile, threading, time
import urllib.parse, urllib.request

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
from prostredi import najdi_chrome, zmensi_obrazek   # společné s fan_chart.py a export_web.py

ROOT = os.path.dirname(TOOLS)
WEB = os.path.join(ROOT, "web")
DIST = os.path.join(WEB, "dist")
TISK_PX = 1100            # delší strana výřezu v PDF: ~170 mm sazby × ~165 dpi (rukopis čitelný)
TISK_KVALITA = 65         # JPEG; s 1100 px drží knihu se zapisy "vse" kolem 10 MB
ZMENSIT = ("/img/", "/zdroje/")
LIMIT_S = int(os.environ.get("RODOKMEN_KNIHA_LIMIT_S", "180"))  # nejdéle na dosazení jedné knihy


# ---------- čistá logika (testy v tests/test_kniha_pdf.py) ----------

def osoby_s_knihou(dist):
    """Id osob, které mají v buildu knihu (dist/kniha/<id>/index.html) – rozhoduje hasBook() v lib/kniha.js."""
    d = os.path.join(dist, "kniha")
    if not os.path.isdir(d):
        return []
    return sorted(x for x in os.listdir(d) if os.path.isfile(os.path.join(d, x, "index.html")))


def vystupni_cesty(root, oid, web=False):
    """Kam se PDF uloží: vystupy/kniha-<id>.pdf, s --web navíc web/public/kniha/<id>.pdf (+ dist, existuje-li)."""
    out = [os.path.join(root, "vystupy", f"kniha-{oid}.pdf")]
    if web:
        out.append(os.path.join(root, "web", "public", "kniha", f"{oid}.pdf"))
        if os.path.isdir(os.path.join(root, "web", "dist")):
            out.append(os.path.join(root, "web", "dist", "kniha", f"{oid}.pdf"))
    return out


def zmensit(cesta):
    """Má se obrázek na této URL cestě před tiskem zmenšit?"""
    p = urllib.parse.unquote(cesta.split("?")[0]).lower()
    return p.startswith(ZMENSIT) and p.endswith((".jpg", ".jpeg", ".png", ".webp"))


def parsuj_argumenty(argv):
    """→ (id nebo None, vse, web); chybné použití → SystemExit s nápovědou."""
    web, vse = "--web" in argv, "--vse" in argv
    zbytek = [a for a in argv if a not in ("--web", "--vse")]
    if any(a.startswith("-") for a in zbytek) or len(zbytek) > 1 or vse == bool(zbytek):
        sys.exit(__doc__.split("\n\n")[1])
    return (zbytek[0] if zbytek else None), vse, web


# ---------- build ----------

def npm(*args):
    n = shutil.which("npm")
    if not n:
        sys.exit("Chybí npm (Node.js) – bez něj web nesestavím. Nainstalujte Node.js a ve web/ spusťte `npm install`.")
    print("web/: npm", *args)
    subprocess.run([n, *args], cwd=WEB, check=True)


def zajisti_build(oid):
    if oid and os.path.isfile(os.path.join(DIST, "kniha", oid, "index.html")):
        return
    if not oid and osoby_s_knihou(DIST):
        return
    if not os.path.isdir(os.path.join(WEB, "node_modules")):
        npm("install")
    if not os.path.isfile(os.path.join(WEB, "src", "data", "site.json")):
        npm("run", "data")
    npm("run", "build")


# ---------- HTTP server nad dist ----------

class Obsluha(http.server.SimpleHTTPRequestHandler):
    cache = None   # složka zmenšených obrázků (nastaví server)

    def translate_path(self, path):
        skutecna = super().translate_path(path)
        if not zmensit(path) or not os.path.isfile(skutecna):
            return skutecna
        cil = os.path.join(self.cache, os.path.relpath(skutecna, self.directory))
        if not os.path.exists(cil):
            try:
                if not zmensi_obrazek(skutecna, cil, TISK_PX, TISK_KVALITA):
                    return skutecna
            except subprocess.CalledProcessError:
                return skutecna
        return cil if os.path.getsize(cil) < os.path.getsize(skutecna) else skutecna   # malé obrázky nechat

    def log_message(self, *a):
        pass


def spust_server(dist, cache):
    Obsluha.cache = cache
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Obsluha, directory=dist))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


# ---------- Chrome přes DevTools protokol ----------

class WebSocket:
    """Minimální klient RFC 6455 (text, bez rozšíření) – stačí na lokální DevTools endpoint Chromu."""

    def __init__(self, url):
        u = urllib.parse.urlparse(url)
        self.s = socket.create_connection((u.hostname, u.port), timeout=max(LIMIT_S, 30))
        klic = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET {u.path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\nUpgrade: websocket\r\n"
                        f"Connection: Upgrade\r\nSec-WebSocket-Key: {klic}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        hlavicka = b""
        while b"\r\n\r\n" not in hlavicka:
            kus = self.s.recv(1)
            if not kus:
                raise ConnectionError("DevTools: spojení uzavřeno při handshake")
            hlavicka += kus
        if b" 101 " not in hlavicka.split(b"\r\n")[0]:
            raise ConnectionError("DevTools: handshake selhal: " + hlavicka.split(b"\r\n")[0].decode())

    def _cti(self, n):
        buf = bytearray()
        while len(buf) < n:
            kus = self.s.recv(min(n - len(buf), 1 << 20))
            if not kus:
                raise ConnectionError("DevTools: spojení uzavřeno")
            buf += kus
        return bytes(buf)

    def posli(self, text):
        data = text.encode()
        h = bytearray([0x81])
        n = len(data)
        if n < 126:
            h.append(0x80 | n)
        elif n < 1 << 16:
            h += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            h += bytes([0x80 | 127]) + struct.pack(">Q", n)
        maska = os.urandom(4)
        self.s.sendall(bytes(h) + maska + bytes(b ^ maska[i % 4] for i, b in enumerate(data)))

    def prijmi(self):
        zprava = bytearray()
        while True:
            b0, b1 = self._cti(2)
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._cti(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._cti(8))[0]
            data = self._cti(n)
            op = b0 & 0x0F
            if op == 8:
                raise ConnectionError("DevTools: Chrome spojení zavřel")
            if op in (0, 1, 2):
                zprava += data
                if b0 & 0x80:
                    return zprava.decode()
            # ping/pong ignorujeme (Chrome je lokálně neposílá)


class Chrome:
    def __init__(self, cesta):
        self.profil = tempfile.mkdtemp(prefix="kniha-pdf-chrome-")
        self.proc = subprocess.Popen([cesta, "--headless=new", "--disable-gpu", "--no-first-run",
                                      "--no-default-browser-check", "--remote-debugging-port=0",
                                      f"--user-data-dir={self.profil}", "about:blank"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        port_soubor = os.path.join(self.profil, "DevToolsActivePort")
        konec = time.time() + 30
        while not (os.path.exists(port_soubor) and open(port_soubor).read().strip()):
            if time.time() > konec or self.proc.poll() is not None:
                self.zavri()
                sys.exit("Chrome se nespustil v headless režimu (DevToolsActivePort chybí).")
            time.sleep(0.1)
        self.port = int(open(port_soubor).read().split()[0])
        self.n = 0

    def nova_karta(self):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/json/new?about:blank", method="PUT")
        info = json.load(urllib.request.urlopen(req, timeout=30))
        self.ws = WebSocket(info["webSocketDebuggerUrl"])

    def volej(self, metoda, **params):
        self.n += 1
        self.ws.posli(json.dumps({"id": self.n, "method": metoda, "params": params}))
        while True:
            z = json.loads(self.ws.prijmi())
            if z.get("id") == self.n:
                if "error" in z:
                    raise RuntimeError(f"{metoda}: {z['error'].get('message')}")
                return z.get("result", {})

    def vytiskni(self, url):
        """Otevře url, počká na window.knihaHotovo (Paged.js dosázel) a vrátí PDF (bytes)."""
        self.nova_karta()
        self.volej("Page.enable")
        self.volej("Page.navigate", url=url)
        konec = time.time() + LIMIT_S
        while True:
            r = self.volej("Runtime.evaluate", expression="window.knihaHotovo === true", returnByValue=True)
            if r.get("result", {}).get("value") is True:
                break
            if time.time() > konec:
                raise TimeoutError(f"{url}: kniha se do {LIMIT_S} s nedosázela (window.knihaHotovo)")
            time.sleep(0.25)
        pdf = self.volej("Page.printToPDF", preferCSSPageSize=True, printBackground=True,
                         displayHeaderFooter=False, generateTaggedPDF=True)
        self.volej("Page.close")
        return base64.b64decode(pdf["data"])

    def zavri(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        shutil.rmtree(self.profil, ignore_errors=True)


# ---------- hlavní běh ----------

def main(argv):
    oid, vse, web = parsuj_argumenty(argv)
    if not os.path.isdir(WEB):
        sys.exit(f"{ROOT} nemá složku web/ – spouštějte projektovou kopii z kořene projektu.")
    chrome = najdi_chrome()
    if not chrome:
        sys.exit("Chybí Google Chrome (nebo Chromium/Edge). Nainstalujte ho, případně nastavte RODOKMEN_CHROME=<cesta>.")
    zajisti_build(oid)
    osoby = osoby_s_knihou(DIST) if vse else [oid]
    if oid and oid not in osoby_s_knihou(DIST):
        sys.exit(f"{oid}: kniha neexistuje (neznámé id, nebo osoba nemá aspoň 2 generace předků).")
    cache = tempfile.mkdtemp(prefix="kniha-pdf-img-")
    srv = spust_server(DIST, cache)
    ch = Chrome(chrome)
    try:
        for o in osoby:
            try:
                pdf = ch.vytiskni(f"http://127.0.0.1:{srv.server_address[1]}/kniha/{o}/")
            except TimeoutError as e:
                sys.exit(f"{e}.\nZkontrolujte: chyby JS v konzoli stránky /kniha/{o}/ (`npm run dev` ve web/), "
                         "že Kniha.astro po dosazení Paged.js nastaví window.knihaHotovo, a u velké knihy "
                         "prodlužte limit: RODOKMEN_KNIHA_LIMIT_S=600.")
            for cil in vystupni_cesty(ROOT, o, web):
                os.makedirs(os.path.dirname(cil), exist_ok=True)
                with open(cil, "wb") as f:
                    f.write(pdf)
                print(os.path.relpath(cil, ROOT), f"{len(pdf) / 1e6:.1f} MB")
    finally:
        ch.zavri()
        srv.shutdown()
        shutil.rmtree(cache, ignore_errors=True)
    if web:
        print("Odkaz „Kniha předků (PDF)“ se na stránce osoby objeví po `npm run build` ve web/.")


if __name__ == "__main__":
    main(sys.argv[1:])
