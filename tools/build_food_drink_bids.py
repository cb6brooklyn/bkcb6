"""Cut the Brooklyn food-drink district files down to each CB6 BID boundary.
Writes data/food-drink/bid-<slug>.json with the boundary and every place inside it,
across every community district the BID touches."""
import json, glob
from shapely.geometry import shape, Point, mapping
SLUGS = ['park-slope-5th-avenue', 'north-flatbush', 'atlantic-avenue']
bids = {f['properties']['slug']: f for f in json.load(open('data/bids.geojson'))['features']}
files = sorted(glob.glob('data/food-drink/cb*.json')) + ['data/food-drink/navyyard.json']
src = {fn: json.load(open(fn))['items'] for fn in files}
for s in SLUGS:
    f = bids[s]; g = shape(f['geometry']).buffer(0)
    out, seen = [], set()
    for fn, items in src.items():
        for p in items:
            if p.get('lat') and p.get('lng') and g.contains(Point(p['lng'], p['lat'])):
                k = (p.get('name'), p.get('address'), p.get('t'))
                if k in seen: continue
                seen.add(k); out.append(p)
    doc = {'slug': s, 'name': f['properties']['name'], 'cds': f['properties']['cds'],
           'geometry': mapping(shape(f['geometry'])), 'items': out}
    json.dump(doc, open(f'data/food-drink/bid-{s}.json', 'w'), separators=(',', ':'))
    print(s, len(out))
