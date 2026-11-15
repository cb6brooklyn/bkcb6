#!/usr/bin/env python3
"""bkcb6.app/profiles/: the Directory on the site, fully interactive. The same entries, categories and square logo
tiles as the apps' Directory (read from the apps' tools.json dir-* lists), with a search that works inside whatever is
picked, dropdowns for section, category, borough, neighborhood and district (community board, Council, Assembly, State
Senate, Congress), Near me, and a map of the results with each entry's logo.

Writes profiles/index.html (from scripts/directory_web.html), profiles/dir.json, and /directory-in/<key>/ pages that
open the Directory on that district. Rerunnable; runs at the end of app_directory_tiles.py."""
import json, os, re, collections, sys
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
sys.path.insert(0, P('scripts'))
import directory_grid as G
D = json.load(open(P('app/data/civic/orgs/orgs-profiles.json'), encoding='utf-8'))['profiles']
BY = {p['slug']: p for p in D}
OFF = {o['slug']: o for o in json.load(open(P('app/data/civic/officials.json'), encoding='utf-8'))}
BOARDS = {b['borocd']: b for b in json.load(open(P('app/data/civic/boards.json'), encoding='utf-8'))}
BOROS = ['Brooklyn', 'Manhattan', 'Bronx', 'Queens', 'Staten Island']
MERGE = [('Schools by borough, ', 'Schools'), ('Community-based organizations, ', 'Community-based organizations')]

def lists(app):
    T = json.load(open(P('app/data/civic/ui', app, 'tools.json'), encoding='utf-8'))['lists']
    S = json.load(open(P('app/data/civic/ui', app, 'screens.json'), encoding='utf-8'))
    out = []
    for sec in S.get('dirSections', []):
        for it in T.get(sec['list'], []):
            d = it.get('dest', '')
            if d.startswith('screen:tools:'):
                lid = d[len('screen:tools:'):]
                out.append((sec['title'], S.get('titles', {}).get(lid, {}).get('title') or lid, lid, T.get(lid, [])))
            else:
                out.append((sec['title'], sec['title'], sec['list'], [it]))
    return out
def seccat(head, title, lid):
    for pre, name in MERGE:
        if head.startswith(pre): return name, title
    if lid.startswith('dir-cul-'): return head, title.split(', ')[0]
    return head, title
pairs = collections.OrderedDict()   # (section, category) in order
E = collections.OrderedDict()       # dest -> entry
def add(head, title, lid, items):
    s, c = seccat(head, title, lid)
    pairs.setdefault(s, collections.OrderedDict()).setdefault(c, 0)
    for it in items:
        d = it['dest']
        if d.startswith('screen:board:'): d = 'board:' + d.rsplit(':', 1)[1]
        elif d.startswith('org:') and BY.get(d[4:], {}).get('group') == 'Community boards': d = 'board:' + str(BY[d[4:]].get('cd'))
        e = E.setdefault(d, {'name': it['title'], 'cover': it['cover'], 'b': it.get('b', ''), 'h': it.get('h', ''), 'cats': []})
        if (s, c) not in e['cats']: e['cats'].append((s, c))
for head, title, lid, items in lists('cb6'):
    if lid.startswith('dir-cb6-'): add(head, title, lid, items)
for head, title, lid, items in lists('beyond'): add(head, title, lid, items)
# ---- where each one is, its page, and the words it answers to ----
LAYERS = [('cd', 'data/community-districts.geojson', 'boro_cd'), ('cc', 'data/council-districts.geojson', 'cc'), ('ad', 'data/assembly-districts.geojson', 'ad'),
          ('sd', 'data/senate-districts.geojson', 'sd'), ('cg', 'data/congressional-districts.geojson', 'cong_dist')]
geo = {}
for t, f, prop in LAYERS:
    feats = json.load(open(P(f)))['features']; gs = [shape(x['geometry']) for x in feats]
    geo[t] = (feats, gs, STRtree(gs), prop)
def districts(lat, lng):
    out = {}
    pt = Point(lng, lat)
    for t, (feats, gs, tree, prop) in geo.items():
        for i in tree.query(pt):
            if gs[i].contains(pt):
                n = str(feats[i]['properties'][prop]).strip()
                if t == 'cd' and not (n.isdigit() and len(n) == 3 and 1 <= int(n[1:]) <= 18): break
                out[t] = int(n); break
    return out
nolink = 0
for d, e in E.items():
    kind, key = d.split(':', 1)
    p = None; href = ''; ext = 0; keys = ''
    if kind == 'official':
        o = OFF.get(key, {}); href = '/%s/' % key
        keys = (o.get('seat', '') + ' ' + G.KEYS.get(o.get('type'), '').format(n=o.get('district') or '')).strip()
        p = next((x for x in D if x.get('official') == key), None)
    elif kind == 'board':
        b = BOARDS.get(key, {}); href = '/%s.html' % b['slug'] if b else ''
        nn = int(key[1:]) if key.isdigit() else 0
        keys = 'cb%d cb %d community district %d %s%d %s' % (nn, nn, nn, G.BABBR.get(b.get('borough'), ''), nn, key)
        p = next((x for x in D if x.get('group') == 'Community boards' and str(x.get('cd')) == key), None)
    else:
        p = BY.get(key)
        if p:
            href = G.site_page(p) or ''
            if not href and p.get('weburl'): href, ext = p['weburl'], 1
            keys = ' '.join(x for x in (p.get('seat') or '', p.get('addr') or '') if x)
    if not href: nolink += 1
    lat = lng = 0
    if p:
        try: lat, lng = float(p.get('lat') or 0), float(p.get('lng') or 0)
        except Exception: lat = lng = 0
    e.update(href=href, ext=ext, keys=keys.lower(), lat=round(lat, 5), lng=round(lng, 5), dist=districts(lat, lng) if lat and lng else {})
    if kind == 'board' and key.isdigit(): e['dist']['cd'] = int(key)
sections = [{'n': s, 'cats': list(cs)} for s, cs in pairs.items()]
sidx = {s['n']: i for i, s in enumerate(sections)}
hoods = sorted({e['h'] for e in E.values() if e['h']})
hidx = {h: i for i, h in enumerate(hoods)}
rows = []
for e in E.values():
    cats = [sidx[s] * 1000 + sections[sidx[s]]['cats'].index(c) for s, c in e['cats']]
    dd = e['dist']
    rows.append([e['name'], e['href'], e['cover'], cats, BOROS.index(e['b']) if e['b'] in BOROS else -1, hidx.get(e['h'], -1),
                 dd.get('cd', 0), dd.get('cc', 0), dd.get('ad', 0), dd.get('sd', 0), dd.get('cg', 0), e['lat'], e['lng'], e['ext'], e['keys']])
for i, s in enumerate(sections): s['count'] = sum(1 for r in rows if any(x // 1000 == i for x in r[3]))
dk = {t: sorted({r[6 + j] for r in rows if r[6 + j]}) for j, t in enumerate(('cd', 'cc', 'ad', 'sd', 'cg'))}
data = {'sections': sections, 'boros': BOROS, 'hoods': hoods, 'districts': dk, 'E': rows}
os.makedirs(P('profiles'), exist_ok=True)
body = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
open(P('profiles/dir.json'), 'w', encoding='utf-8').write(body)
import hashlib
page = open(P('scripts/directory_web.html'), encoding='utf-8').read().replace('__N__', '{:,}'.format(len(rows))).replace('__V__', hashlib.sha1(body.encode()).hexdigest()[:10])
open(P('profiles/index.html'), 'w', encoding='utf-8').write(page)
# the Directory inside one district: its own address, which opens the Directory on it
import shutil
if os.path.isdir(P('directory-in')): shutil.rmtree(P('directory-in'))
BN = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
def dname(t, n): return '%s Community Board %d' % (BN[str(n)[0]], int(str(n)[1:])) if t == 'cd' else {'cc': 'Council District %s', 'ad': 'Assembly District %s', 'sd': 'State Senate District %s', 'cg': 'Congressional District %s'}[t] % n
for t, ks in dk.items():
    for k in ks:
        os.makedirs(P('directory-in', '%s-%s' % (t, k)), exist_ok=True)
        nm = dname(t, k)
        open(P('directory-in', '%s-%s' % (t, k), 'index.html'), 'w').write(
            '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="apple-itunes-app" content="app-id=6813967208"><title>The Directory in %s &mdash; bkcb6.app</title>'
            '<link rel="canonical" href="https://bkcb6.app/profiles/#d=%s-%s"><meta http-equiv="refresh" content="0;url=/profiles/#d=%s-%s"></head>'
            '<body><p><a href="/profiles/#d=%s-%s">The Directory in %s</a></p></body></html>\n' % (nm, t, k, t, k, t, k, nm))
print('web directory:', len(rows), 'profiles |', len(sections), 'sections |', sum(len(s['cats']) for s in sections), 'categories |', len(hoods), 'neighborhoods |',
      'no page to open:', nolink, '| dir.json %.1f MB' % (len(body) / 1e6), '| district pages:', sum(len(v) for v in dk.values()))
