#!/usr/bin/env python3
"""Election district shapes for the Ballot Breakdown maps.
Writes ballotmeasures/cd/geo/<cd>-<year>.json: {AD(2)+ED(3): [ring, ...]} with [lon, lat] points,
for the election districts listed for that community district and year in ballotmeasures/cd/<cd>.json,
from the district lines in force at that election (data/edhistory/geo/ed<release>.topo.json)."""
import json, os, glob
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
CAT = {e['id']: e for e in json.load(open('data/edhistory/catalog.json'))['elections']}
def release(y):
    if y == 2026: return '26a1'
    return [v for k, v in CAT.items() if k.startswith(str(y) + '-11-') and k.endswith('general')][0]['release']
def shapes(rel):
    t = json.load(open('data/edhistory/geo/ed%s.topo.json' % rel))
    sx, sy = t['transform']['scale']; tx, ty = t['transform']['translate']
    arcs = []
    for a in t['arcs']:
        x = y = 0; pts = []
        for dx, dy in a:
            x += dx; y += dy; pts.append((round(x * sx + tx, 5), round(y * sy + ty, 5)))
        arcs.append(pts)
    def ring(r):
        out = []
        for i in r:
            p = arcs[i] if i >= 0 else arcs[~i][::-1]
            out += p[1:] if out else p
        d = [out[0]]
        for p in out[1:]:
            if p != d[-1]: d.append(p)
        return [list(p) for p in d]
    S = {}
    for g in list(t['objects'].values())[0]['geometries']:
        polys = [g['arcs']] if g['type'] == 'Polygon' else g['arcs'] if g['type'] == 'MultiPolygon' else []
        S.setdefault(g['properties']['e'], []).extend(ring(r) for p in polys for r in p)
    return S
os.makedirs('ballotmeasures/cd/geo', exist_ok=True)
cache = {}; n = miss = 0
for f in sorted(glob.glob('ballotmeasures/cd/[0-9]*.json')):
    D = json.load(open(f)); cd = D['cd'] if isinstance(D['cd'], str) else os.path.basename(f)[:3]
    for o in D['years']:
        rel = release(o['year'])
        if rel not in cache: cache[rel] = shapes(rel)
        S = cache[rel]; out = {}
        for r in o['eds']:
            if r[0] in S: out[r[0]] = S[r[0]]
            else: miss += 1; print('no shape', cd, o['year'], r[0])
        json.dump(out, open('ballotmeasures/cd/geo/%s-%d.json' % (cd, o['year']), 'w'), separators=(',', ':')); n += 1
print(n, 'files,', miss, 'election districts without a shape')
