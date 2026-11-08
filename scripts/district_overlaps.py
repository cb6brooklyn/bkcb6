#!/usr/bin/env python3
"""Which districts, boards, precincts, school districts, fire battalions, BIDs and historic districts actually overlap
each district a profile map is drawn for (data/districts/<folder>-<id>.geojson), so a profile map offers and draws
only those (assets/profile-map.js reads data/districts/overlaps.json).

Overlap means the shapes share real land (the rivers and harbor are left out): at least 5% of the smaller shape's
land area, or at least a square kilometer (about 250 acres). Slivers where two maps drew the same line a little
differently, such as a Manhattan district's line running along the Brooklyn shore, do not count. Shapes that only share a boundary line, or overlap by a sliver from how the
lines were drawn, do not count. Rerun when any district file changes."""
import glob, json, os, re
from shapely.geometry import shape
from shapely.ops import transform
import warnings; warnings.filterwarnings('ignore')
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
M = lambda x, y, z=None: (x * 84300.0, y * 111000.0)   # degrees to meters at New York's latitude, for areas
MIN_FRAC, MIN_AREA = 0.05, 1000000.0

def clean(gj):
    t = gj['type']
    if t == 'Polygon':
        rings = [r for r in gj['coordinates'] if len(r) >= 4]
        return {'type': 'Polygon', 'coordinates': rings} if rings else None
    if t == 'MultiPolygon':
        ps = [c for c in (clean({'type': 'Polygon', 'coordinates': q}) for q in gj['coordinates']) if c]
        return {'type': 'MultiPolygon', 'coordinates': [c['coordinates'] for c in ps]} if ps else None
    if t == 'GeometryCollection':
        return {'type': 'GeometryCollection', 'geometries': [c for c in (clean(x) for x in gj['geometries']) if c]}
    return gj

def geom(f):
    g = shape(clean(f['geometry']))
    if not g.is_valid: g = g.buffer(0)
    return transform(M, g)

def load_sets():
    S = {}
    for kind in ('council', 'assembly', 'senate', 'congress', 'cb'):
        items = []
        for p in sorted(glob.glob(f'data/districts/{kind}-*.geojson')):
            ident = p.rsplit('-', 1)[1][:-8]
            if kind == 'cb' and not re.fullmatch(r'\d{3}', ident): continue
            g = json.load(open(p))
            items.append((ident, geom(g['features'][0]) if len(g['features']) == 1 else
                          geom({'geometry': {'type': 'GeometryCollection', 'geometries': [f['geometry'] for f in g['features']]}})))
        S[kind] = items
    S['school'] = [(str(int(f['properties']['schooldist'])), geom(f)) for b in ('manhattan', 'bronx', 'brooklyn', 'queens', 'statenisland')
                   for f in json.load(open(f'data/school-districts-{b}.geojson'))['features'] if f.get('geometry')]
    S['precinct'] = [(str(f['properties']['precinct']), geom(f)) for f in json.load(open('data/police-precincts-lite.geojson'))['features'] if f.get('geometry')]
    S['fire'] = [(str(f['properties']['fire_bn']), geom(f)) for f in json.load(open('data/fire_battalions.geojson'))['features']]
    S['bid'] = [(f['properties']['slug'], geom(f)) for f in json.load(open('data/bids.geojson'))['features'] if f.get('geometry')]
    S['historic'] = []
    for i, f in enumerate(json.load(open('data/historic-districts.geojson'))['features']):
        if f.get('geometry'): S['historic'].append((str(i), geom(f)))
    return S

def main():
    S = load_sets()
    # compare land only: district files run out into the rivers and the harbor, and water is not shared ground
    land = geom({'geometry': {'type': 'GeometryCollection', 'geometries': [f['geometry'] for f in json.load(open('data/districts/city-nyc.geojson'))['features']]}})
    trees = {k: (STRtree([g for _, g in v]), v) for k, v in S.items()}
    out = {}
    for p in sorted(glob.glob('data/districts/*.geojson')):
        name = os.path.basename(p)[:-8]
        if name == 'overlaps' or name.startswith(('state-', 'city-', 'landuse', 'counties')): continue
        try:
            g = json.load(open(p)); fs = [f for f in g['features'] if f.get('geometry')]
            own = geom(fs[0]) if len(fs) == 1 else geom({'geometry': {'type': 'GeometryCollection', 'geometries': [f['geometry'] for f in fs]}})
        except Exception as e:
            print('skip', name, e); continue
        own = own.intersection(land)
        if own.is_empty: continue
        row = {}
        for k, (tree, items) in trees.items():
            hits = []
            for i in tree.query(own):
                ident, other = items[i]
                if f'{k}-{ident}' == name: continue
                a = own.intersection(other).area
                if a > 0 and (a >= MIN_AREA or a >= MIN_FRAC * min(own.area, other.intersection(land).area or other.area)):
                    hits.append(ident)
            row[k] = sorted(hits, key=lambda x: (len(x), x))
        out[name] = row
    json.dump(out, open('data/districts/overlaps.json', 'w'), separators=(',', ':'))
    print(len(out), 'districts;', json.dumps(out.get('council-1')))

if __name__ == '__main__':
    main()
