#!/usr/bin/env python3
"""data/park-signs/<park id>.json: every sign NYC Parks has posted in each park (Parks Signs, NYC Open Data hv9n-xgy4,
all 11,942), for the park profile maps, which show a park's signs once the map is zoomed in.
Each file: {"park": name, "src", "signs": [[lat, lon, cat, what, where, type], ...]}; a sign filed under a zone of a park
(B126-ZN03) goes with the park (B126). Categories follow parks-policy/ (dogs, play, fields, restrooms, gardens, pools,
skate, name, other). Usage: python3 scripts/park_signs.py"""
import json, os, re, urllib.request, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
U = 'https://data.cityofnewyork.us/resource/hv9n-xgy4.json?$limit=50000&$order=system'
req = urllib.request.Request(U, headers={'X-App-Token': 'HvFoIfzodzpRML7a1104Ca2tM', 'User-Agent': 'bkcb6.app'})
rows = json.load(urllib.request.urlopen(req, timeout=300))
def cat(w, t):
    w = w.lower()
    if 'dog' in w: return 'dogs'
    if 'playground' in w: return 'play'
    if 'comfort station' in w: return 'restrooms'
    if w.startswith('gt garden'): return 'gardens'
    if 'pool' in w: return 'pools'
    if 'skate' in w: return 'skate'
    if re.search(r'athletic|tennis|track|field|court', w): return 'fields'
    if 'routed' in w or t == 'Routed Sign': return 'name'
    return 'other'
out = {}
n = 0
for r in rows:
    pt = (r.get('point') or {}).get('coordinates')
    pid = (r.get('gispropnum') or '').strip()
    if not pt or not pid: continue
    base = pid.split('-')[0]
    w = re.sub(r'\s*\(\d+\)$', '', r.get('amenitytype') or '').strip() or (r.get('signtype') or 'Sign')
    o = out.setdefault(base, {'park': r.get('propertyname') or '', 'signs': []})
    o['signs'].append([round(pt[1], 6), round(pt[0], 6), cat(w, r.get('signtype') or ''), w, r.get('propertylocation') or '', r.get('signtype') or ''])
    n += 1
src = 'NYC Parks, Parks Signs (NYC Open Data hv9n-xgy4), downloaded %s' % datetime.date.today().isoformat()
for k, o in out.items():
    o['src'] = src
    json.dump(o, open('data/park-signs/%s.json' % k, 'w'), separators=(',', ':'), ensure_ascii=False)
print(len(rows), 'rows;', n, 'signs in', len(out), 'parks;', len(out.get('B073', {}).get('signs', [])), 'in Prospect Park;', len(out.get('B431', {}).get('signs', [])), 'in Brooklyn Bridge Park')
