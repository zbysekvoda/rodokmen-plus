#!/usr/bin/env python3
"""Kramerius NKP full-text search (API v5). Usage: kramerius.py 'SOLR_QUERY' [rows] [--server https://<knihovna>]
e.g. kramerius.py 'text_ocr:"Jan Novák" AND datum_begin:[1860 TO 1920]'
--server: jiná knihovna s rozhraním Kramerius v5 (např. https://kramerius.army.cz); výchozí https://kramerius5.nkp.cz.
Parametr --server podle https://github.com/hnizdiljan/rodokmen-skill/blob/d172316bc190d0f44894fa67115505729d587c6a/skills/rodokmen/tools/kramerius.py (MIT).
Sloupec přístupu: public = volně; private+DNNT = čitelné po přihlášení na ndk.cz (reference/portaly.md → DNNT);
private = jen v knihovně. Filtr datum_begin vyřadí část čísel periodik – při malém počtu nálezů hledej i bez něj."""
import os,re,sys,json,urllib.request,urllib.parse
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # -I nepřidá složku skriptu sama
import slusne; slusne.instaluj()   # společný limit rychlosti k webům archivů (slusne.py)
a=sys.argv[1:]; server='https://kramerius5.nkp.cz'
if '--server' in a:
    i=a.index('--server')
    if i+1>=len(a): sys.exit('--server chce adresu knihovny (https://…).')
    server=a[i+1].rstrip('/'); del a[i:i+2]
s=urllib.parse.urlsplit(server)
if (s.scheme!='https' or s.username or s.password or s.port not in (None,443) or s.query or s.fragment or s.path
        or not re.fullmatch(r'[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+',s.hostname or '') or re.fullmatch(r'[0-9.]+',s.hostname or '')):
    sys.exit('--server musí být https:// a doménové jméno knihovny (např. https://kramerius.army.cz).')
if not a:
    sys.exit(__doc__)
q=a[0]; rows=a[1] if len(a)>1 else '30'
p={'q':q+' AND fedora.model:page','fl':'PID,root_title,root_pid,datum_str,details,dostupnost,dnnt,dnnt-labels','rows':rows,'wt':'json','hl':'true','hl.fl':'text_ocr','hl.fragsize':'250'}
u=server+'/search/api/v5.0/search?'+urllib.parse.urlencode(p)
d=json.load(urllib.request.urlopen(u,timeout=90))
print('found',d['response']['numFound'])
hl=d.get('highlighting',{})
for x in d['response']['docs']:
    h=' | '.join(hl.get(x['PID'],{}).get('text_ocr',[]))[:400].replace('\n',' ')
    pristup=x.get('dostupnost') or '?'
    if pristup=='private' and (x.get('dnnt') or 'dnnto' in (x.get('dnnt-labels') or [])): pristup='private+DNNT'
    det=str(x['details'][0]).split()[0] if x.get('details') else ''
    print('-',x.get('datum_str'),'|',str(x.get('root_title'))[:60],'| s.',det,'|',x['PID'],'|',pristup)
    if h: print('   ',h)
