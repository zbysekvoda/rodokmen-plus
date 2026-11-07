# scitani_mza.py <rok> <snimek> <out.jpg> [x0,y0,x1,y1] [sirka] [--obec <obec>] – snímek ze sčítacích operátů MZA
# (mza.cz/scitacioperaty). Signatury operátů jsou v data/scitani_mza.json (viz template/data/scitani_mza.json):
#   {"<obec>": {"cesta": "LUN101/LUN101/<fond>", "prefix": "<fond>-<obec>", "operaty": {"1869": "<signatura>", …}}}
# Cesta po rocích: MZA má operáty jedné obce i na různých discích (1880 LUN101, 1890 LUN105) a 1857 je vedeno pod
# mateřskou obcí (jiný prefix). Proto může být operát i objekt {"sig": …, "cesta": …, "prefix": …} (chybějící pole
# se vezmou z obce) a "cesta"/"prefix" obce i slovník po rocích {"1857": …, "1880": …}.
# --url jen vypíše adresu snímku (Deepzoom .dzi) a nic nestahuje.
# Signaturu operátu přečtěte z adresy snímku v prohlížeči MZA (…/<cesta>/<prefix>-<signatura>/<…>-00010.jp2).
# --obec je povinné, jen když je v souboru víc obcí. Soubor jde zadat i přes --operaty <cesta.json>.
# Spouštět: python3 -I tools/slusne.py tools/scitani_mza.py …
# Od 2. 11. 2026 MZA na iipsrv vypnul protokol IIIF (403 i v prohlížeči); prohlížeč webu používá Deepzoom,
# takže skript stahuje dlaždice Deepzoom (256 px) jen pro požadovaný výřez a skládá je přes ImageMagick (magick).
import sys, os, math, re, subprocess, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import slusne
def _opt(name):
    if name in sys.argv:
        i=sys.argv.index(name); v=sys.argv[i+1]; del sys.argv[i:i+2]; return v
cfg_path=_opt("--operaty") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"data","scitani_mza.json")
obec=_opt("--obec")
jen_url="--url" in sys.argv
if jen_url: sys.argv.remove("--url")
if not os.path.exists(cfg_path): sys.exit(f"chybí {cfg_path} se signaturami operátů (vzor: template/data/scitani_mza.json)")
OBCE={k:v for k,v in json.load(open(cfg_path,encoding="utf-8")).items() if not k.startswith("_")}
if obec is None:
    if len(OBCE)!=1: sys.exit(f"zadejte --obec ({', '.join(OBCE)})")
    obec=next(iter(OBCE))
if obec not in OBCE: sys.exit(f"obec {obec} není v {cfg_path}")
C=OBCE[obec]; S=C["operaty"]
y,n,out=sys.argv[1],int(sys.argv[2]),sys.argv[3]
reg=sys.argv[4] if len(sys.argv)>4 else "0,0,1,1"; w=int(sys.argv[5]) if len(sys.argv)>5 else 1000
x0,y0,x1,y1=(float(v) for v in reg.split(","))
if y not in S: sys.exit(f"pro rok {y} není v {cfg_path} signatura operátu ({obec}: {', '.join(S)})")
def po_roce(v, pole):
    if isinstance(v, dict):
        if y not in v: sys.exit(f"{obec}: „{pole}“ nemá rok {y} ({', '.join(v)})")
        return v[y]
    return v
op=S[y] if isinstance(S[y],dict) else {"sig":S[y]}
try: s,cesta,prefix=op["sig"],po_roce(op.get("cesta",C.get("cesta")),"cesta"),po_roce(op.get("prefix",C.get("prefix")),"prefix")
except KeyError: sys.exit(f"{obec} {y}: operát jako objekt potřebuje „sig“")
if not cesta or not prefix: sys.exit(f"{obec} {y}: chybí „cesta“ nebo „prefix“ (u obce ani u operátu)")
base=f"{prefix}-{s}"
dz=f"https://www.mza.cz/iipsrv/iipsrv.fcgi?Deepzoom=/srv/{cesta}/{base}/{base}-{n*10:05d}.jp2"
if jen_url: print(f"{dz}.dzi"); sys.exit(0)
CURL=["-s","-f","--http2","-m","180","-A","Mozilla/5.0 (rodokmen-plus)"]
tmp=tempfile.mkdtemp(prefix="scitani_mza_")
p=slusne.curl(CURL+["-o",f"{tmp}/i.dzi",f"{dz}.dzi"])
if p.returncode: print(out,"dzi curl",p.returncode); sys.exit(1)
x=open(f"{tmp}/i.dzi").read()
W,H=(int(v) for v in re.search(r'Width="(\d+)" Height="(\d+)"',x).groups()); T=int(re.search(r'TileSize="(\d+)"',x).group(1))
top=math.ceil(math.log2(max(W,H)))
# nejmenší úroveň, kde má výřez aspoň požadovanou šířku
L=top
while L>0 and (W/2**(top-L+1))*(x1-x0)>=w: L-=1
lw,lh=math.ceil(W/2**(top-L)),math.ceil(H/2**(top-L))
px0,py0,px1,py1=int(x0*lw),int(y0*lh),min(lw,math.ceil(x1*lw)),min(lh,math.ceil(y1*lh))
cols=range(px0//T,(px1-1)//T+1); rows=range(py0//T,(py1-1)//T+1)
for r in rows:
    for c in cols:
        p=slusne.curl(CURL+["-o",f"{tmp}/{r:03d}_{c:03d}.jpg",f"{dz}_files/{L}/{c}_{r}.jpg"])
        if p.returncode: print(out,"tile",L,c,r,"curl",p.returncode); sys.exit(1)
rad=[]
for r in rows:
    f=f"{tmp}/row{r:03d}.jpg"; subprocess.run(["magick",*[f"{tmp}/{r:03d}_{c:03d}.jpg" for c in cols],"+append",f],check=True); rad.append(f)
ox,oy=px0-cols[0]*T,py0-rows[0]*T
subprocess.run(["magick",*rad,"-append","-crop",f"{px1-px0}x{py1-py0}+{ox}+{oy}","+repage","-resize",f"{w}x>",out],check=True)
for f in os.listdir(tmp): os.remove(f"{tmp}/{f}")
os.rmdir(tmp)
print(out,"ok",f"level {L}",f"{len(rows)*len(cols)} dlaždic")
