#!/usr/bin/env python3
"""The Directory inside every district: what is in each community board and each Council, Assembly, State Senate and
Congressional district, by category, opened from that board's or that official's profile. No build.

Reads the Directory's tiles (tools.json dir-* lists) and the profiles' spots, and writes
  app/data/civic/directory-in/<cd|cc|ad|sd|cg>-<n>.json   {"cats": [{"k", "n"}], "items": [{title, cover, dest, k, h}]}
  screens.json "nodes" dird-<key>   one small screen per district: each category's name and its logo grid
  profile-index.json pages "/directory-in/<key>/" -> "node:dird-<key>", so the card's button opens the screen in the app
  a "Directory" card (going, id "dirin") on each board's and each official's Directory profile.
Rerunnable. Runs at the end of app_directory_tiles.py."""
import json, os, re, collections
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
pf = P('app/data/civic/orgs/orgs-profiles.json'); DD = json.load(open(pf, encoding='utf-8')); D = DD['profiles']
OFF = {o['slug']: o for o in json.load(open(P('app/data/civic/officials.json'), encoding='utf-8'))}
LAYERS = [('cd', 'data/community-districts.geojson', 'boro_cd'), ('cc', 'data/council-districts.geojson', 'cc'), ('ad', 'data/assembly-districts.geojson', 'ad'),
          ('sd', 'data/senate-districts.geojson', 'sd'), ('cg', 'data/congressional-districts.geojson', 'cong_dist')]
BN = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
def dname(t, n):
    if t == 'cd': return '%s Community Board %d' % (BN[n[0]], int(n[1:]))
    return {'cc': 'Council District %s', 'ad': 'Assembly District %s', 'sd': 'State Senate District %s', 'cg': 'Congressional District %s'}[t] % n
# ---- a category for every tile, from the list it sits in ----
def category(lid, title):
    if lid.startswith('dir-act-'): return (5, 'Parks: ' + title)
    if lid.startswith('dir-cul-'): return (4, title.split(', ')[0])
    if lid.startswith('dir-sch-'): return (3, title)
    if lid.startswith('dir-cbo-'): return (7, 'Community organizations: ' + title)
    if lid.startswith('dir-hosp-'): return (4, 'Hospitals')
    if lid.startswith('dir-rx-'): return (4, 'Pharmacies')
    if lid.startswith('dir-mkt-'): return (4, 'Supermarkets')
    if lid.startswith('dir-agencies-'): return (2, 'Government offices')
    if lid.startswith('dir-officials-'): return (1, "Elected officials' offices")
    if lid.startswith('dir-cb6-groups-'): return (6, 'Community groups: ' + title)
    if lid.startswith('dir-cb6-business-improvement-districts'): return (6, 'Business improvement districts')
    if lid.startswith('dir-cb6-schools-parks-and-facilities-'): return (4, title)
    if lid.startswith('dir-cb6-local-businesses-'): return (8, title)
    return None
tiles = collections.OrderedDict()   # (dest, category) -> tile
order = {}
for app in ('beyond', 'cb6'):
    T = json.load(open(P('app/data/civic/ui', app, 'tools.json'), encoding='utf-8'))['lists']
    S = json.load(open(P('app/data/civic/ui', app, 'screens.json'), encoding='utf-8'))
    for lid, items in T.items():
        if not lid.startswith('dir-') or lid.startswith('dir-sections-'): continue
        c = category(lid, S.get('titles', {}).get(lid, {}).get('title') or lid)
        if not c: continue
        order[c[1]] = c[0]
        for it in items:
            d = it['dest'] if not it['dest'].startswith('screen:board:') else it['dest']
            tiles.setdefault((d, c[1]), {'title': it['title'], 'cover': it.get('cover') or it.get('tile'), 'dest': d, 'k': c[1], 'h': it.get('h', '')})
spot = {}
for p in D:
    try: lat, lng = float(p.get('lat') or 0), float(p.get('lng') or 0)
    except Exception: continue
    if not lat or not lng: continue
    spot['org:' + p['slug']] = (lat, lng)
    if p.get('official'): spot['official:' + p['official']] = (lat, lng)
# ---- which district each spot is in ----
inside = {}   # dest -> {type: n}
for t, f, prop in LAYERS:
    feats = json.load(open(P(f)))['features']
    geoms = [shape(x['geometry']) for x in feats]; tree = STRtree(geoms)
    for d, (lat, lng) in spot.items():
        pt = Point(lng, lat)
        for i in tree.query(pt):
            if geoms[i].contains(pt):
                n = str(feats[i]['properties'][prop]).strip()
                if t == 'cd' and not (n.isdigit() and len(n) == 3 and 1 <= int(n[1:]) <= 18): break   # parks and airports are not boards
                inside.setdefault(d, {})[t] = str(int(n)) if t != 'cd' else n
                break
by = collections.defaultdict(list)
for (d, k), tile in tiles.items():
    for t, n in (inside.get(d) or {}).items(): by[t + '-' + n].append(tile)
out = P('app/data/civic/directory-in'); os.makedirs(out, exist_ok=True)
for f in os.listdir(out): os.remove(os.path.join(out, f))
count = {}
for key, items in by.items():
    cats = collections.Counter(x['k'] for x in items)
    cl = [{'k': k, 'n': cats[k]} for k in sorted(cats, key=lambda k: (order[k], k))]
    items.sort(key=lambda x: (order[x['k']], x['k'], x['h'], x['title'].lower()))
    json.dump({'cats': cl, 'items': items}, open(os.path.join(out, key + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    count[key] = len({x['dest'] for x in items})
# ---- one screen per district ----
def node(key):
    t, n = key.split('-', 1); F = 'civic/directory-in/%s.json' % key
    item = {'type': 'v', 'spacing': 4, 'dest': '{dest}', 'maxWidth': 'full', 'align': 'top', 'children': [
        {'type': 'image', 'tile': '{cover}', 'height': 96, 'maxWidth': 'full', 'align': 'center', 'bg': 'white', 'corner': 12, 'border': 'rule', 'borderWidth': 1, 'pad': 4},
        {'type': 'text', 'text': '{title}', 'size': 10, 'weight': 'medium', 'lines': 2, 'textAlign': 'center', 'maxWidth': 'full', 'align': 'center'},
        {'type': 'text', 'text': '{h}', 'size': 9, 'color': 'muted', 'lines': 1, 'when': {'has': 'h'}, 'textAlign': 'center', 'maxWidth': 'full', 'align': 'center'}]}
    return {'type': 'v', 'spacing': 12, 'title': dname(t, n), 'children': [
        {'type': 'text', 'text': 'In %s: %s places in the Directory, by category.' % (dname(t, n), '{:,}'.format(count[key])), 'size': 14, 'color': 'ink'},
        {'type': 'each', 'spacing': 14, 'data': {'file': F, 'at': 'cats'}, 'item': {'type': 'v', 'spacing': 8, 'children': [
            {'type': 'text', 'text': '{k} · {n}', 'size': 12, 'mono': True, 'upper': True, 'tracking': 0.8, 'color': 'orange'},
            {'type': 'each', 'columns': 3, 'spacing': 8, 'data': {'file': F, 'at': 'items', 'where': {'k': '{k}'}}, 'item': item}]}}]}
for app in ('cb6', 'bk', 'beyond'):
    sf = P('app/data/civic/ui', app, 'screens.json'); S = json.load(open(sf, encoding='utf-8'))
    nodes = S.setdefault('nodes', {})
    for k in [k for k in nodes if k.startswith('dird-')]: del nodes[k]
    for key in by: nodes['dird-' + key] = node(key)
    open(sf, 'w', encoding='utf-8').write(json.dumps(S, ensure_ascii=False, separators=(',', ':')) + '\n')
# ---- the links open the screens ----
xf = P('app/data/civic/profile-index.json'); X = json.load(open(xf, encoding='utf-8'))
X['pages'] = {k: v for k, v in X['pages'].items() if not k.startswith('/directory-in/')}
for key in by: X['pages']['/directory-in/%s/' % key] = 'node:dird-' + key
json.dump(X, open(xf, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
# ---- a card on each board's and each official's profile ----
CH = {'council': 'cc', 'assembly': 'ad', 'senate': 'sd', 'congress': 'cg'}
cards = 0
for p in D:
    p['going'] = [g for g in (p.get('going') or []) if g.get('id') != 'dirin']
    key = None
    if p.get('group') == 'Community boards' and p.get('cd'): key = 'cd-' + str(p['cd'])
    elif p.get('official') in OFF and OFF[p['official']].get('chamber') in CH and OFF[p['official']].get('district'):
        key = '%s-%s' % (CH[OFF[p['official']]['chamber']], int(OFF[p['official']]['district']))
    if not key or key not in by: continue
    t, n = key.split('-', 1)
    p['going'].append({'id': 'dirin', 'img': '', 'kicker': 'Directory', 'title': 'What is in %s' % dname(t, n),
                       'text': 'Schools, parks and what you can play in them, community groups, museums, theatres and government offices inside the district: %s places, by category.' % '{:,}'.format(count[key]),
                       'btns': [['Open the Directory here', 'https://bkcb6.app/directory-in/%s/' % key, 'hot']]})
    cards += 1
open(pf, 'w', encoding='utf-8').write(json.dumps(DD, ensure_ascii=False, indent=1) + '\n')
sz = sum(os.path.getsize(os.path.join(out, f)) for f in os.listdir(out))
print('districts:', len(by), collections.Counter(k.split('-')[0] for k in by), '| cards on profiles:', cards, '| files: %.1f MB' % (sz / 1e6))
