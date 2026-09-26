#!/usr/bin/env python3
"""Build data/bqe/nb-<slug>.json for bkcb6.app/BQE/carrollgardens and /BQE/gowanus: the neighborhood
outline used on bkcb6.app maps (clipped to CB6), BQE and Gowanus Expressway mainline and ramps near it,
DOT truck routes inside it, DOT classification counts inside it, and every CB6 311 Truck Route
Violation complaint inside it."""
import json, os
from shapely.geometry import shape, mapping, Point, box
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CB6 = shape([f for f in json.load(open(os.path.join(ROOT, 'cd-boundaries-simple.geojson')))['features'] if str(f['properties']['cd']) == '306'][0]['geometry']).buffer(0)
NBS = {'carrollgardens': 'Carroll Gardens', 'gowanus': 'Gowanus'}
lines = json.load(open(os.path.join(ROOT, 'data', 'bqe', 'bqe-lines.geojson')))['features']
cm = json.load(open(os.path.join(ROOT, 'data', 'bqe', 'truck-complaints.json')))
cc = json.load(open(os.path.join(ROOT, 'data', 'bqe', 'cb6-counts.json')))
tr = []
for cd in ('306', '307', '302'):
    tr += json.load(open(os.path.join(ROOT, 'data', 'truck-routes', cd + '.json')))['features']
for slug, name in NBS.items():
    g = [shape(f['geometry']).buffer(0) for f in json.load(open(os.path.join(ROOT, 'data', 'city-neighborhoods.geojson')))['features'] if f['properties']['nb'] == name][0].intersection(CB6)
    view = box(*g.buffer(0.012).bounds)
    near = g.buffer(0.0015)   # about 150 m
    bqe = []
    for f in lines:
        s = shape(f['geometry'])
        if not s.intersects(view): continue
        p = dict(f['properties']); p['near'] = bool(s.intersects(near))
        bqe.append({'type': 'Feature', 'geometry': f['geometry'], 'properties': p})
    ramps_near = sorted(set(f['properties']['st'] for f in bqe if f['properties']['k'] == 'ramp' and f['properties']['near']))
    routes = []; seen = set()
    for f in tr:
        s = shape(f['geometry'])
        if not s.intersects(view): continue
        key = (f['properties'].get('segmentid'), round(s.length, 9))
        if key in seen: continue
        seen.add(key)
        gb = g.buffer(0.0003)   # inside the outline or along its edge streets (about 30 m)
        inside = s.intersects(gb) and s.intersection(gb).length > 0.0002
        routes.append({'type': 'Feature', 'geometry': f['geometry'], 'properties': {'st': f['properties']['street'], 't': f['properties']['routetype'], 'in': inside}})
    in_routes = {}
    for f in routes:
        if f['properties']['in']: in_routes.setdefault(f['properties']['st'], set()).add(f['properties']['t'])
    comps = [p for p in cm['p'] if p[4] == '06 BROOKLYN' and g.contains(Point(p[1], p[0]))]
    counts = [p for p in cc['places'] if p['nb'] == name and p['src'] == 'class']
    out = {'name': name, 'outline': mapping(g), 'bqe': bqe, 'ramps_near': ramps_near, 'routes': routes,
           'in_routes': {k: sorted(v) for k, v in sorted(in_routes.items())}, 'complaints': sorted(comps, key=lambda p: p[2]), 'counts': counts}
    json.dump(out, open(os.path.join(ROOT, 'data', 'bqe', 'nb-%s.json' % slug), 'w'), separators=(',', ':'))
    print(name, 'bqe feats', len(bqe), 'ramps near', ramps_near, 'routes', len(routes), 'in routes', out['in_routes'], 'complaints', len(comps), 'counts', len(counts))
