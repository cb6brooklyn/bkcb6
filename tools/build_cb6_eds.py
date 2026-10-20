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

# Before the 2012 BOE map: the 2010 Census voting districts (the EDs of about 2010), given the Kings County
# TIGER file tl_2010_36047_vtd10.shp as argv[1] and its ED-to-community-district file as argv[2]
# (built by area of overlap with data/cd-boundaries-lite.geojson; a VTD named "4000073 4000075" or with a range
# stands for several EDs: property e is the first, all lists them).
import sys
if len(sys.argv) > 2:
    import shapefile, re
    from shapely.geometry import shape, mapping
    m = json.load(open(sys.argv[2]))
    def vkeys(n):
        o = []
        for a, b in re.findall(r'(\d{7})(?:-(\d{7}))?', n):
            lo = int(a[2:]); hi = int(b[2:]) if b else lo
            o += ['%d%03d' % (int(a[:2]), e) for e in range(lo, hi + 1)]
        return o
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 6), round(c[1], 6)]
    feats = []
    for sr in shapefile.Reader(sys.argv[1]).shapeRecords():
        ks = vkeys(sr.record['NAME10'])
        if not ks or m.get(ks[0]) != CB:
            continue
        g = json.loads(json.dumps(mapping(shape(sr.shape.__geo_interface__).buffer(0).simplify(0.00002))))
        g['coordinates'] = rnd(g['coordinates'])
        p = {'e': ks[0]}
        if len(ks) > 1:
            p['all'] = ks
        feats.append({'type': 'Feature', 'properties': p, 'geometry': g})
    json.dump({'type': 'FeatureCollection', 'release': 'vtd2010', 'date': '2008-01-01', 'features': feats}, open('data/cbhistory/ed306/vtd2010.json', 'w'), separators=(',', ':'))
    idx.insert(0, {'r': 'vtd2010', 'date': '2008-01-01', 'n': len(feats), 'label': '2010 Census voting districts'})
    json.dump(idx, open('data/cbhistory/ed306/index.json', 'w'), separators=(',', ':'))
    print('vtd2010', len(feats))

# Elections with election-district results in BKCB6 (data/edhistory), for elections.html: id, date, label, ED map
# and the contests on any BKCB6 ballot.
cat_e = json.load(open('data/edhistory/catalog.json'))['elections']
have = {x['r'] for x in json.load(open('data/cbhistory/ed306/index.json'))}
els = []
for e in cat_e:
    if e.get('release') not in have:
        continue
    ix = json.load(open('data/edhistory/e/%s/index.json' % e['id']))
    cs = [{'id': c['id'], 't': c['title'], 'p': c.get('party') or '', 'rcv': bool(c.get('rcv'))} for c in ix['contests'] if CB in (c.get('cds') or [])]
    if cs:
        els.append({'id': e['id'], 'date': e['date'], 'label': e['label'], 'r': e['release'], 'contests': cs})
json.dump(els, open('data/cbhistory/ed306/elections.json', 'w'), separators=(',', ':'))
print(len(els), 'elections with BKCB6 contests')
