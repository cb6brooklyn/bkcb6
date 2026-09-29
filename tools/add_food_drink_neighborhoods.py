"""Stamp every place in data/food-drink/cb6.json with its neighborhood (nb),
from data/city-neighborhoods.geojson; a point that falls in a gap between
neighborhood shapes (a street bed, the canal) gets the nearest one."""
import json
from shapely.geometry import shape, Point
NB = [(f['properties']['nb'], shape(f['geometry']).buffer(0))
      for f in json.load(open('data/city-neighborhoods.geojson'))['features']
      if f['properties'].get('boro') == 'Brooklyn']
for fn in ['data/food-drink/cb6.json']:
    d = json.load(open(fn)); n = 0
    for p in d['items']:
        if not (p.get('lat') and p.get('lng')): continue
        pt = Point(p['lng'], p['lat'])
        hit = next((k for k, g in NB if g.contains(pt)), None)
        p['nb'] = hit or min(NB, key=lambda x: x[1].distance(pt))[0]; n += 1
    json.dump(d, open(fn, 'w'), separators=(',', ':'))
    print(fn, n, 'stamped')
