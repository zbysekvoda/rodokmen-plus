"""Společné hledání externích programů pro nástroje: Chrome (fan_chart.py, kniha_pdf.py) a ImageMagick
(export_web.py, export_web_domy.py, kniha_pdf.py). Jen standardní knihovna."""
import os, shutil, subprocess

# Pořadí: macOS, Windows (Chrome, pak Edge – oba umí headless tisk i CDP), Linux z PATH
CHROME_KANDIDATI = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    "/Applications/Chromium.app/Contents/MacOS/Chromium",
                    "C:/Program Files/Google/Chrome/Application/chrome.exe",
                    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
                    "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
                    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser")


def najdi_chrome(kandidati=CHROME_KANDIDATI, env=None, exists=os.path.exists, which=shutil.which):
    """Cesta ke Chromu (nebo Edge/Chromiu), jinak None. Proměnná RODOKMEN_CHROME má přednost."""
    env = os.environ if env is None else env
    vlastni = env.get("RODOKMEN_CHROME")
    if vlastni and (exists(vlastni) or which(vlastni)):
        return which(vlastni) or vlastni
    for c in kandidati:
        if exists(c):
            return c
        if which(c):
            return which(c)
    return None


def magick_bin():   # ImageMagick 7 (magick), jinak 6 (convert) – ten ale ne na Windows, tam je convert.exe jiný program
    return shutil.which("magick") or (os.name != "nt" and shutil.which("convert")) or None


def zmensi_obrazek(src, dst, max_px, kvalita=82):
    """Zmenšená kopie obrázku (delší strana nejvýš max_px, menší se nezvětšuje). Bez ImageMagicku vrací False."""
    m = magick_bin()
    if not m:
        return False
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    subprocess.run([m, src + "[0]", "-auto-orient", "-resize", f"{max_px}x{max_px}>", "-strip",
                    "-quality", str(kvalita), dst], check=True, capture_output=True)
    return True
