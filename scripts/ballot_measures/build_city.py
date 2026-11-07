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
YEARS = [1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020, 2021, 2022, 2023, 2024, 2025]
EST_FROM = 2021  # July 1 estimates, Census Bureau Population Estimates Program, Vintage 2025 (sub-est2025.csv)

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
EST = {
 'manhattan': [1569781, 1593919, 1631534, 1665510, 1664862], 'bronx': [1420980, 1384053, 1380478, 1406052, 1406332],
 'brooklyn': [2634576, 2600751, 2611893, 2658657, 2653963], 'queens': [2328520, 2291363, 2314747, 2367034, 2358182],
 'staten': [494101, 492579, 495182, 499572, 501290], 'nassau': [1391787, 1388346, 1388940, 1397783, 1398939],
 'suffolk': [1533742, 1531736, 1533173, 1543330, 1546090], 'yonkers': [210137, 208926, 209192, 211546, 212603],
 'mtvernon': [72867, 71997, 71691, 72148, 72304], 'newrochelle': [81460, 82558, 84300, 85667, 85864]}
for k, v in EST.items(): POP[k] = POP[k] + v
WM = json.load(open(H + '/raw/westchester-municipalities.json'))
for k, n in (('eastchester', 'Eastchester town'), ('pelham', 'Pelham town')): POP[k] = [WM[n][str(y)] for y in YEARS]
WEST = [184257, 283055, 344436, 520947, 573558, 625816, 808891, 894404, 866599, 874866, 923459, 949113, 1004457, 1000252, 994313, 998335, 1009165, 1015743]
POP['westrest'] = [w - a - b - c for w, a, b, c in zip(WEST, POP['yonkers'], POP['mtvernon'], POP['newrochelle'])]

# Colors: one per unit; every pair is at least 15 apart in OKLab (normal vision). Names on the map and the table carry identity too.
U = [
 dict(id='manhattan', name='Manhattan', sub='New York County', kind='Borough', inNow=True, color='#e6194b'),
 dict(id='bronx', name='The Bronx', sub='West Bronx and Town of Westchester', kind='Borough', inNow=True, color='#df9555'),
 dict(id='brooklyn', name='Brooklyn', sub='Kings County', kind='Borough', inNow=True, color='#4363d8'),
 dict(id='queens', name='Queens', sub='Western towns of 1894 Queens', kind='Borough', inNow=True, color='#57c43c'),
 dict(id='staten', name='Staten Island', sub='Richmond County', kind='Borough', inNow=True, color='#8c0888'),
 dict(id='nassau', name='Nassau County', sub='Eastern towns of 1894 Queens', kind='County', inNow=False, color='#46b5e4'),
 dict(id='mtvernon', name='Mount Vernon', sub='Voted no; stayed out', kind='Westchester', inNow=False, color='#8c352a'),
 dict(id='eastchester', name='Eastchester', sub='Part that stayed in Westchester', kind='Westchester', inNow=False, color='#269364'),
 dict(id='pelham', name='Pelham', sub='Part that stayed in Westchester', kind='Westchester', inNow=False, color='#a5619f'),
]

def rnd(g, n=4):
    def r(c):
        if isinstance(c[0], (int, float)): return [round(c[0], n), round(c[1], n)]
        return [r(x) for x in c]
    d = mapping(g); return {'type': d['type'], 'coordinates': r(d['coordinates'])}

boro = {f['properties']['boroname']: make_valid(shape(f['geometry'])) for f in json.load(open(R + '/data/boro-simple.geojson'))['features']}
cty = {f['properties']['COUNTY']: f for f in json.load(open(H + '/raw/counties2020.geojson'))['features']}
cs = {f['properties']['NAME']: make_valid(shape(f['geometry'])) for f in json.load(open(H + '/raw/cousub.geojson'))['features']}
CS = {'mtvernon': 'Mount Vernon city', 'eastchester': 'Eastchester town', 'pelham': 'Pelham town'}
# 2020 attributes from TIGERweb (Census 2020)
ATTR = {
 'manhattan': cty['061'], 'bronx': cty['005'], 'brooklyn': cty['047'], 'queens': cty['081'], 'staten': cty['085'],
 'nassau': cty['059']}
WA = json.load(open(H + '/raw/westchester-cousub-2020.json'))
CSA = {k: (WA[n]['POP100'], WA[n]['HU100'], WA[n]['AREALAND']) for k, n in CS.items()}
geo = {
 'manhattan': boro['Manhattan'], 'bronx': boro['Bronx'], 'brooklyn': boro['Brooklyn'], 'queens': boro['Queens'], 'staten': boro['Staten Island'],
 'nassau': unary_union([g for n, g in cs.items() if n in [f['properties']['NAME'] for f in json.load(open(H + '/raw/cousub.geojson'))['features'] if f['properties']['COUNTY'] == '059']]),
}
for k, n in CS.items(): geo[k] = cs[n]
west = unary_union([g for n, g in cs.items() if n in [f['properties']['NAME'] for f in json.load(open(H + '/raw/cousub.geojson'))['features'] if f['properties']['COUNTY'] == '119']])
SQM = 2589988.11
wa = cty['119']['properties']
for u in U:
    k = u['id']
    if k in ATTR:
        p = ATTR[k]['properties']; hu, land = p['HU100'], p['AREALAND']
        assert p['POP100'] == POP[k][12], (k, p['POP100'])
    elif k in CSA:
        pp, hu, land = CSA[k]; assert pp == POP[k][12], (k, pp)
    else:
        hu = wa['HU100'] - sum(v[1] for v in CSA.values()); land = wa['AREALAND'] - sum(v[2] for v in CSA.values())
    u['pop'] = POP[k]; u['hu2020'] = hu; u['sqmi'] = round(land / SQM, 1)
    g = geo[k].simplify(0.0015 if k == 'nassau' else 0.0006, preserve_topology=True)
    u['g'] = rnd(g)
    c = geo[k].representative_point()
    u['lab'] = [round(c.y, 4), round(c.x, 4)]
LAB = {'manhattan': [40.7831, -73.9712], 'bronx': [40.8350, -73.8700], 'brooklyn': [40.6500, -73.9496], 'queens': [40.7282, -73.7949], 'staten': [40.5795, -74.1502],
       'nassau': [40.7400, -73.5900], 'mtvernon': [40.9150, -73.8850], 'eastchester': [40.9620, -73.8100], 'pelham': [40.9000, -73.7420]}
for u in U: u['lab'] = LAB[u['id']]
os.makedirs(R + '/ballotmeasures/1894/build', exist_ok=True)
json.dump(dict(years=YEARS, estFrom=EST_FROM, units=U), open(R + '/ballotmeasures/1894/build/units.json', 'w'), separators=(',', ':'))
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

# ---- Economy: GDP (BEA CAGDP1, 2001-2024) and unemployment (NYS DOL / BLS LAUS, 1990-2026) ----
GDP = json.load(open(H + '/raw/bea-cagdp1.json'))      # thousands of dollars; 'cur' current dollars, 'real' chained 2017 dollars
LA = json.load(open(H + '/raw/laus-annual.json'))      # annual average of monthly, not seasonally adjusted: lf, un, rate, m (months)
GY = list(range(2001, 2025)); UY = list(range(1976, 2027))
E = json.load(open(R + '/ballotmeasures/1894/build/units.json'))
for u in E['units']:
    k = u['id']
    if k in GDP: u['gdpCur'] = GDP[k]['cur']; u['gdpReal'] = GDP[k]['real']
    if k in LA: u['lf'] = [LA[k][str(y)]['lf'] if str(y) in LA[k] else None for y in UY]; u['un'] = [LA[k][str(y)]['un'] if str(y) in LA[k] else None for y in UY]
E['econ'] = dict(gdpYears=GY, ueYears=UY, ueLastMonths=LA['manhattan'][str(UY[-1])]['m'],
    westchester=dict(gdpCur=GDP['westchester']['cur'], gdpReal=GDP['westchester']['real'], lf=[LA['westchester'].get(str(y), {}).get('lf') for y in UY], un=[LA['westchester'].get(str(y), {}).get('un') for y in UY], pop=WEST),
    nyc=dict(lf=[LA['nyc'][str(y)]['lf'] for y in UY], un=[LA['nyc'][str(y)]['un'] for y in UY]))
json.dump(E, open(R + '/ballotmeasures/1894/build/units.json', 'w'), separators=(',', ':'))
print('econ added', os.path.getsize(R + '/ballotmeasures/1894/build/units.json') // 1024, 'KB')
