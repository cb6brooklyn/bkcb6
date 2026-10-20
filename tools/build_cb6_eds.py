"""BKCB6's election districts on every BOE election district map since 2012: data/cbhistory/ed306/<release>.json
(GeoJSON, property e = AD and ED, e.g. 52061) from data/edhistory/geo/ed<release>.topo.json, keeping the EDs that
data/edhistory/geo/ed2cd<release>.json puts in BKCB6. index.json lists the releases with their dates."""
import json, os
CB = '306'
cat = json.load(open('data/edhistory/catalog.json'))['releases']
os.makedirs('data/cbhistory/ed306', exist_ok=True)
def decode(t):
    tr = t.get('transform'); arcs = []
    for a in t['arcs']:
        x = y = 0; pts = []
        for p in a:
            if tr:
                x += p[0]; y += p[1]
                pts.append([round(x * tr['scale'][0] + tr['translate'][0], 6), round(y * tr['scale'][1] + tr['translate'][1], 6)])
            else:
                pts.append(p)
        arcs.append(pts)
    def ring(ix):
        out = []
        for i in ix:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            out.extend(a if not out else a[1:])
        return out
    return ring
idx = []
for rel in sorted(cat, key=lambda r: cat[r]['date']):
    m = json.load(open('data/edhistory/geo/ed2cd%s.json' % rel))
    t = json.load(open('data/edhistory/' + cat[rel]['file']))
    ring = decode(t); o = t['objects'][list(t['objects'])[0]]; feats = []
    for g in o['geometries']:
        e = str(g['properties']['e'])
        if m.get(e) != CB:
            continue
        if g['type'] == 'Polygon':
            geom = {'type': 'Polygon', 'coordinates': [ring(r) for r in g['arcs']]}
        elif g['type'] == 'MultiPolygon':
            geom = {'type': 'MultiPolygon', 'coordinates': [[ring(r) for r in p] for p in g['arcs']]}
        else:
            continue
        feats.append({'type': 'Feature', 'properties': {'e': e}, 'geometry': geom})
    json.dump({'type': 'FeatureCollection', 'release': rel, 'date': cat[rel]['date'], 'features': feats}, open('data/cbhistory/ed306/%s.json' % rel, 'w'), separators=(',', ':'))
    idx.append({'r': rel, 'date': cat[rel]['date'], 'n': len(feats)})
json.dump(idx, open('data/cbhistory/ed306/index.json', 'w'), separators=(',', ':'))
print(len(idx), 'releases', [(i['r'], i['n']) for i in idx][:6], '...')
