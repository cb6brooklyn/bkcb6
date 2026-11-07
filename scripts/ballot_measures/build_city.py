"""Builds ballotmeasures/1894/build/units.json (the build-your-own-city data)
and adds map label points to ballotmeasures/1894.json.
Population 1900-2020: U.S. Census decennial counts.
2020 population, housing units and land area: U.S. Census Bureau TIGERweb (Census 2020 layers)."""
import json, os, warnings
warnings.filterwarnings('ignore')
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from shapely import make_valid

R = '/root/bkcb6'
H = os.path.dirname(os.path.abspath(__file__))
YEARS = [1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]

POP = {
 'manhattan': [1850093, 2331542, 2284103, 1867312, 1889924, 1960101, 1698281, 1539233, 1428285, 1487536, 1537195, 1585873, 1694251],
 'bronx':     [200507, 430980, 732016, 1265258, 1394711, 1451277, 1424815, 1471701, 1168972, 1203789, 1332650, 1385108, 1472654],
 'brooklyn':  [1166582, 1634351, 2018356, 2560401, 2698285, 2738175, 2627319, 2602012, 2230936, 2300664, 2465326, 2504700, 2736074],
 'queens':    [152999, 284041, 469042, 1079129, 1297634, 1550849, 1809578, 1986473, 1891325, 1951598, 2229379, 2230722, 2405464],
 'staten':    [67021, 85969, 116531, 158346, 174441, 191555, 221991, 295443, 352121, 378977, 443728, 468730, 495747],
 'nassau':    [55448, 83930, 126120, 303053, 406748, 672765, 1300171, 1428080, 1321582, 1287348, 1334544, 1339532, 1395774],
 'suffolk':   [77582, 96138, 110246, 161055, 197355, 276129, 666784, 1124950, 1284231, 1321864, 1419369, 1493350, 1525920],
 'yonkers':   [47931, 79803, 100176, 134646, 142598, 152798, 190634, 204297, 195351, 188082, 196086, 195976, 211569],
 'mtvernon':  [21228, 30919, 42726, 61499, 67362, 71899, 76010, 72778, 66713, 67153, 68381, 67292, 73893],
 'newrochelle': [14720, 28867, 36213, 54000, 58408, 59725, 76812, 75385, 70794, 67265, 72182, 77062, 79726],
}
WEST = [184257, 283055, 344436, 520947, 573558, 625816, 808891, 894404, 866599, 874866, 923459, 949113, 1004457]
POP['westrest'] = [w - a - b - c for w, a, b, c in zip(WEST, POP['yonkers'], POP['mtvernon'], POP['newrochelle'])]

# Colors: one per unit; every pair is at least 15 apart in OKLab (normal vision). Names on the map and the table carry identity too.
U = [
 dict(id='manhattan', name='Manhattan', sub='New York County', kind='Borough', inNow=True, color='#e6194b'),
 dict(id='bronx', name='The Bronx', sub='Bronx County', kind='Borough', inNow=True, color='#df9555'),
 dict(id='brooklyn', name='Brooklyn', sub='Kings County', kind='Borough', inNow=True, color='#4363d8'),
 dict(id='queens', name='Queens', sub='Queens County', kind='Borough', inNow=True, color='#57c43c'),
 dict(id='staten', name='Staten Island', sub='Richmond County', kind='Borough', inNow=True, color='#8c0888'),
 dict(id='nassau', name='Nassau County', sub='Hempstead, North Hempstead, Oyster Bay, Glen Cove, Long Beach', kind='County', inNow=False, color='#46b5e4'),
 dict(id='suffolk', name='Suffolk County', sub='Eastern Long Island', kind='County', inNow=False, color='#dd77f4'),
 dict(id='yonkers', name='Yonkers', sub='City in Westchester County', kind='City', inNow=False, color='#3e6102'),
 dict(id='mtvernon', name='Mount Vernon', sub='City in Westchester County', kind='City', inNow=False, color='#8c352a'),
 dict(id='newrochelle', name='New Rochelle', sub='City in Westchester County', kind='City', inNow=False, color='#a5619f'),
 dict(id='westrest', name='Rest of Westchester', sub='Westchester County outside Yonkers, Mount Vernon and New Rochelle', kind='County part', inNow=False, color='#269364'),
]

def rnd(g, n=4):
    def r(c):
        if isinstance(c[0], (int, float)): return [round(c[0], n), round(c[1], n)]
        return [r(x) for x in c]
    d = mapping(g); return {'type': d['type'], 'coordinates': r(d['coordinates'])}

boro = {f['properties']['boroname']: make_valid(shape(f['geometry'])) for f in json.load(open(R + '/data/boro-simple.geojson'))['features']}
cty = {f['properties']['COUNTY']: f for f in json.load(open(H + '/raw/counties2020.geojson'))['features']}
cs = {f['properties']['NAME']: make_valid(shape(f['geometry'])) for f in json.load(open(H + '/raw/cousub.geojson'))['features']}
CS = {'yonkers': 'Yonkers city', 'mtvernon': 'Mount Vernon city', 'newrochelle': 'New Rochelle city'}
# 2020 attributes from TIGERweb (Census 2020)
ATTR = {
 'manhattan': cty['061'], 'bronx': cty['005'], 'brooklyn': cty['047'], 'queens': cty['081'], 'staten': cty['085'],
 'nassau': cty['059'], 'suffolk': cty['103']}
CSA = {'yonkers': (211569, 85528, 46634435), 'mtvernon': (73893, 30350, 11375581), 'newrochelle': (79726, 30531, 26640876)}
geo = {
 'manhattan': boro['Manhattan'], 'bronx': boro['Bronx'], 'brooklyn': boro['Brooklyn'], 'queens': boro['Queens'], 'staten': boro['Staten Island'],
 'nassau': unary_union([g for n, g in cs.items() if n in [f['properties']['NAME'] for f in json.load(open(H + '/raw/cousub.geojson'))['features'] if f['properties']['COUNTY'] == '059']]),
 'suffolk': make_valid(shape(cty['103']['geometry'])),
}
for k, n in CS.items(): geo[k] = cs[n]
west = unary_union([g for n, g in cs.items() if n in [f['properties']['NAME'] for f in json.load(open(H + '/raw/cousub.geojson'))['features'] if f['properties']['COUNTY'] == '119']])
geo['westrest'] = west.difference(unary_union([cs[n] for n in CS.values()]))
SQM = 2589988.11
wa = cty['119']['properties']
for u in U:
    k = u['id']
    if k in ATTR:
        p = ATTR[k]['properties']; hu, land = p['HU100'], p['AREALAND']
        assert p['POP100'] == POP[k][-1], (k, p['POP100'])
    elif k in CSA:
        _, hu, land = CSA[k]
    else:
        hu = wa['HU100'] - sum(v[1] for v in CSA.values()); land = wa['AREALAND'] - sum(v[2] for v in CSA.values())
    u['pop'] = POP[k]; u['hu2020'] = hu; u['sqmi'] = round(land / SQM, 1)
    g = geo[k].simplify(0.0015 if k in ('suffolk', 'westrest', 'nassau') else 0.0006, preserve_topology=True)
    u['g'] = rnd(g)
    c = geo[k].representative_point() if k != 'suffolk' else geo[k].centroid
    u['lab'] = [round(c.y, 4), round(c.x, 4)]
LAB = {'manhattan': [40.7831, -73.9712], 'bronx': [40.8350, -73.8700], 'brooklyn': [40.6500, -73.9496], 'queens': [40.7282, -73.7949], 'staten': [40.5795, -74.1502],
       'nassau': [40.7400, -73.5900], 'suffolk': [40.8600, -72.8500], 'yonkers': [40.9480, -73.9350], 'mtvernon': [40.9000, -73.8120], 'newrochelle': [40.9300, -73.7300], 'westrest': [41.1500, -73.7700]}
for u in U: u['lab'] = LAB[u['id']]
os.makedirs(R + '/ballotmeasures/1894/build', exist_ok=True)
json.dump(dict(years=YEARS, units=U), open(R + '/ballotmeasures/1894/build/units.json', 'w'), separators=(',', ':'))
for u in U: print(u['id'], u['pop'][0], u['pop'][-1], u['hu2020'], u['sqmi'])
print(os.path.getsize(R + '/ballotmeasures/1894/build/units.json') // 1024, 'KB')

# label points for the 1894 map
D = json.load(open(R + '/ballotmeasures/1894.json'))
L1894 = {'ny': ('New York County', 'Manhattan and the West Bronx', [40.80, -73.955]), 'kings': ('Kings County', 'Brooklyn', [40.650, -73.950]),
 'queens': ('Queens County', 'western towns, now the Borough of Queens', [40.712, -73.835]), 'richmond': ('Richmond County', 'Staten Island', [40.580, -74.150]),
 'westchester': ('Town of Westchester', 'East Bronx', [40.840, -73.840]), 'eastchester': ('East Chester', 'town', [40.968, -73.825]),
 'pelham': ('Pelham', 'town', [40.898, -73.772]), 'mtvernon': ('Mount Vernon', 'city', [40.928, -73.892])}
for p in D['places']:
    t, s, c = L1894[p['id']]; p['lab'] = dict(t=t, s=s, c=c)
    if p['id'] == 'queens': p['lab2'] = dict(t='Queens County', s='eastern towns, now Nassau County', c=[40.80, -73.57])
json.dump(D, open(R + '/ballotmeasures/1894.json', 'w'), separators=(',', ':'))
