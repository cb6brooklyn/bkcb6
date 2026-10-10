"""The apps' Business improvement districts screen (civic/bids.geojson): the three BIDs, plus the proposed Gowanus BID
(the Gowanus rezoning area) and the Red Hook Business Alliance (Red Hook, which has no BID), each with its own color."""
import json
from shapely.geometry import shape, Polygon, mapping
C = 'app/data/civic'
P = f'{C}/bids.geojson'
d = json.load(open(P))
d['features'] = [f for f in d['features'] if f['properties'].get('slug') not in ('gowanus-bid-proposed', 'red-hook-business-alliance')]
def feature(geom, **props):
    g = Polygon([(x, y) for x, y, *_ in geom.exterior.coords], [[(x, y) for x, y, *_ in r.coords] for r in geom.interiors])
    c = g.centroid
    props.update(lat=round(c.y, 6), lon=round(c.x, 6))
    return {'type': 'Feature', 'properties': props, 'geometry': mapping(g)}
gow = shape(json.load(open('data/gowanus_rezoning_boundary.geojson'))['features'][0]['geometry'])
if gow.geom_type == 'MultiPolygon': gow = max(gow.geoms, key=lambda g: g.area)
cb6 = shape(json.load(open('data/cb6_boundary.geojson'))['features'][0]['geometry'])
rh = Polygon(json.load(open(f'{C}/hoods-cb6.json'))['Red Hook'][0]).intersection(cb6)
if rh.geom_type == 'MultiPolygon': rh = max(rh.geoms, key=lambda g: g.area)
d['features'].append(feature(gow, name='Gowanus BID, proposed', borough='Brooklyn', year=None, url='https://gowanusimprovementdistrict.org/',
                             slug='gowanus-bid-proposed', cds=['306'], councils=[39], status='Being formed: the proposed district is the Gowanus rezoning area'))
d['features'].append(feature(rh, name='Red Hook Business Alliance', borough='Brooklyn', year=2019, url='https://redhookbiz.org/',
                             slug='red-hook-business-alliance', cds=['306'], councils=[38], status='A business alliance; Red Hook has no BID'))
json.dump(d, open(P, 'w'), separators=(',', ':'))
print([ (f['properties']['name'], f['properties'].get('year')) for f in d['features']])
# a color for each, in lists.json (every app's copy)
for L in [f'{C}/lists.json', 'app/data/variants/cb6/civic/lists.json', 'app/data/variants/bk/civic/lists.json', 'app/data/variants/beyond/civic/lists.json']:
    try: j = json.load(open(L))
    except FileNotFoundError: continue
    j['lists']['BidsOrgsView.colors'] = ['#f47920', '#1d4ed8', '#2d6a4f', '#7c3aed', '#be123c']
    json.dump(j, open(L, 'w'), ensure_ascii=False, indent=1)
print('colors set')
