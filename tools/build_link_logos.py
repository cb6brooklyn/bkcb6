#!/usr/bin/env python3
"""The logo for every link: assets/link-logos/<first path part>.json maps each page a link can open to the logo of what
it opens (the Directory tile of that place, org, official or district), and assets/link-logos/_web.json maps outside
websites (each listing's own website) to the same logo. assets/site-bar.js reads them and puts the logo beside the link.
Run after the Directory rebuild (profiles/dir.json)."""
import json, os, re, glob
from urllib.parse import urlparse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
ICONS = 'app/data/civic/icons'
EXT = {f.rsplit('.', 1)[0]: f for f in os.listdir(ICONS)}
def norm(h):
    h = h.split('#')[0].split('?')[0]
    if h.endswith('/index.html'): h = h[:-10]
    if h.endswith('.html'): h = h[:-5]
    return h.rstrip('/') or '/'
def shard(h): p = h.strip('/').split('/'); return p[0] if len(p) > 1 else '_root'
def webkey(u):
    try: q = urlparse(u if re.match(r'https?://', u) else 'https://' + u)
    except Exception: return ''
    host = (q.hostname or '').lower()
    if host.startswith('www.'): host = host[4:]
    if not host: return ''
    seg = [s for s in q.path.lower().split('/') if s]
    # shared government hosts: the office is the first part (or two) of the path
    if host in ('nyc.gov', 'ny.gov', 'council.nyc.gov', 'nysenate.gov', 'assembly.state.ny.us', 'nyassembly.gov', 'house.gov', 'senate.gov', 'linktr.ee', 'facebook.com', 'instagram.com', 'sites.google.com'):
        return host + '/' + '/'.join(seg[:2 if seg[:1] == ['site'] else 1])
    return host
def main():
    D = json.load(open('profiles/dir.json'))
    out = {}; byname = {}
    for r in D['E']:
        name, href, cover = r[0], r[1], r[2]
        f = EXT.get(cover)
        if not f or not href.startswith('/'): continue
        k = norm(href); out.setdefault(shard(k), {}).setdefault(k, f)
        byname.setdefault(name.lower(), set()).add(f)
    # pages the site already shows a picture for (hub tiles and the like), where the Directory has none
    rx = re.compile(r'<a\b[^>]*href="([^"#:][^"]*)"[^>]*>\s*(?:<[^>]+>\s*){0,3}<img\b[^>]*src="([^"]+)"', re.I)
    pics = {}
    for fn in glob.glob('*.html') + glob.glob('*/index.html'):
        base = '/' + os.path.dirname(fn) + '/' if os.path.dirname(fn) else '/'
        for h, s in rx.findall(open(fn, encoding='utf-8', errors='ignore').read()):
            if re.match(r'(data:|https?:)', s) or re.search(r'app-?store|badge|google-?play|play-store|arrow|chevron|spinner|qr', s, re.I): continue
            h = h if h.startswith('/') else base + h; s = os.path.normpath(s if s.startswith('/') else base + s)
            if not os.path.isfile(s[1:]): continue
            pics.setdefault(norm(os.path.normpath(h) + ('/' if h.endswith('/') else '')), {}).setdefault(s, 0); pics[norm(os.path.normpath(h))][s] = pics[norm(os.path.normpath(h))].get(s, 0) + 1 if norm(os.path.normpath(h)) in pics else 1
    for k, c in pics.items():
        m = out.setdefault(shard(k), {})
        if k not in m and c: m[k] = max(c, key=c.get)
    for k, v in (('/', '/app/data/Logos/cb306.png'),):
        out.setdefault(shard(k), {})[k] = v
    web = {}
    P = json.load(open('app/data/civic/orgs/orgs-profiles.json', encoding='utf-8'))['profiles']
    for p in P:
        u = p.get('weburl') or p.get('web') or ''
        fs = byname.get((p.get('name') or '').lower())
        if not u or not fs or len(fs) != 1: continue
        k = webkey(u)
        if k: web.setdefault(k, set()).add(next(iter(fs)))
    web = {k: next(iter(v)) for k, v in web.items() if len(v) == 1}
    os.makedirs('assets/link-logos', exist_ok=True)
    for f in glob.glob('assets/link-logos/*.json'): os.remove(f)
    for s, m in out.items(): json.dump(m, open('assets/link-logos/%s.json' % s, 'w'), separators=(',', ':'))
    json.dump(web, open('assets/link-logos/_web.json', 'w'), separators=(',', ':'))
    print('pages with a logo:', sum(len(m) for m in out.values()), 'in', len(out), 'files | websites:', len(web))
if __name__ == '__main__': main()
