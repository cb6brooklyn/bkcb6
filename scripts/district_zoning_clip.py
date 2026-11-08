#!/usr/bin/env python3
"""data/districts/zoning/<district>.geojson: City Planning's zoning districts (nyzd, all 5,440 features) cut to each
district's own boundary (and data/districts/parks/<district>.geojson, the same for parks), so a profile map shows zoning only inside the district it is about (as the CB6 home map does).
Every district file in data/districts/ except the whole city and the state (which need no cut).
Usage: python3 scripts/district_zoning_clip.py <folder holding z0.json z2000.json z4000.json from the nyzd query>"""
import glob, json, os, sys, warnings
warnings.filterwarnings('ignore')
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from district_overlaps import clean
SRC = sys.argv[1]
feats = [f for p in sorted(glob.glob(os.path.join(SRC, 'z*.json'))) for f in json.load(open(p))['features']]
zs = []
for f in feats:
    g = shape(f['geometry']); g = g if g.is_valid else g.buffer(0)
    zs.append((f['properties'].get('ZONEDIST') or '', g))
print(len(zs), 'zoning districts')
tree = STRtree([g for _, g in zs])
def rnd(c):
    if isinstance(c[0], (int, float)): return [round(c[0], 6), round(c[1], 6)]
    return [rnd(x) for x in c]
os.makedirs('data/districts/zoning', exist_ok=True)
os.makedirs('data/districts/parks', exist_ok=True)
# parks (data/parks-citywide.geojson) cut the same way
parks = []
for f in json.load(open('data/parks-citywide.geojson'))['features']:
    if not f.get('geometry'): continue
    c = clean(f['geometry'])
    if not c: continue
    g = shape(c); g = g if g.is_valid else g.buffer(0)
    parks.append((f['properties'], g))
ptree = STRtree([g for _, g in parks])
n = 0
for p in sorted(glob.glob('data/districts/*.geojson')):
    stem = os.path.basename(p)[:-8]
    if stem in ('city-nyc', 'state-ny', 'landuse-nyc') or stem.startswith('state-') or stem.startswith('city-'): continue
    try: gj = json.load(open(p))
    except Exception: continue
    fs = gj.get('features') or []
    if not fs: continue
    d = shape(clean({'type': 'GeometryCollection', 'geometries': [f['geometry'] for f in fs if f.get('geometry')]}))
    d = (d if d.is_valid else d.buffer(0)).buffer(0)
    out = []
    for i in tree.query(d):
        z, g = zs[i]
        x = g.intersection(d)
        if x.is_empty: continue
        x = x if x.geom_type in ('Polygon', 'MultiPolygon') else unary_union([y for y in getattr(x, 'geoms', []) if y.geom_type in ('Polygon', 'MultiPolygon')])
        if x.is_empty or x.area <= 0: continue
        m = mapping(x); m['coordinates'] = rnd(m['coordinates'])
        out.append({'type': 'Feature', 'properties': {'ZONEDIST': z}, 'geometry': m})
    json.dump({'type': 'FeatureCollection', 'features': out}, open('data/districts/zoning/%s.geojson' % stem, 'w'), separators=(',', ':'))
    pk = []
    for i in ptree.query(d):
        props, g = parks[i]
        x = g.intersection(d)
        if x.is_empty: continue
        x = x if x.geom_type in ('Polygon', 'MultiPolygon') else unary_union([y for y in getattr(x, 'geoms', []) if y.geom_type in ('Polygon', 'MultiPolygon')])
        if x.is_empty or x.area <= 0: continue
        m = mapping(x); m['coordinates'] = rnd(m['coordinates'])
        pk.append({'type': 'Feature', 'properties': props, 'geometry': m})
    json.dump({'type': 'FeatureCollection', 'features': pk}, open('data/districts/parks/%s.geojson' % stem, 'w'), separators=(',', ':'))
    n += 1
print(n, 'files')
