#!/usr/bin/env python3
"""The business improvement districts that reach into CB6 (Park Slope 5th Avenue, North Flatbush, Atlantic Avenue) also
run outside it, into Community Districts 2, 7 and 8. The BKCB6 audit (cb6_audit.py) covers District 6 only; this pulls the
same official registers for the parts of the three BIDs outside District 6, so every business in each BID is in the Directory.

Writes data/bid-audit/registers.json: one row per register record inside a BID and outside District 6, in cb6_audit's row
shape, with 'bid' (the BID's slug) and 'cd' (its community district).
Registers (pulled fresh): DOHMH restaurant inspections (43nn-pn8j), DCWP licenses (w7w3-xahh), NYS Ag & Markets food stores
(9a8c-vfzj), NYS Liquor Authority (9s3h-dpkz), NYS DOS salons and barber shops (y3u4-jbgh), NPI registry organizations,
FDIC branches, by the BIDs' ZIP codes. State, NPI and FDIC records are placed by the city's address points (GeoSearch).
Run: python3 scripts/bid_audit.py   (--cached: reuse the last pull in data/bid-audit/raw.json)"""
import json, os, re, sys, urllib.request, urllib.parse, time
from shapely.geometry import shape, Point
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
sys.path.insert(0, P('scripts'))
OUT = P('data/bid-audit'); os.makedirs(OUT, exist_ok=True)
SLUGS = ['park-slope-5th-avenue', 'north-flatbush', 'atlantic-avenue']
BIDS = {s: shape(json.load(open(P('data/bids/%s-boundary.geojson' % s)))['features'][0]['geometry']) for s in SLUGS}   # the city's BID file, Nov 16, 2026
EDGE = 0.00012   # about 12 meters: a storefront's address point can sit just off the BID's lot lines
CD6 = shape(json.load(open(P('data/cb6-audit/cd306.geojson'))))
CDS = [(f['properties']['boro_cd'], shape(f['geometry'])) for f in json.load(open(P('data/community-districts.geojson')))['features'] if f['properties']['boro_cd'].startswith('3')]
ZIPS = ['11201', '11215', '11217', '11238']
TOKEN = 'HvFoIfzodzpRML7a1104Ca2tM'
def get(u, data=None, tries=3):
    for i in range(tries):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, data=data, headers={'X-App-Token': TOKEN, 'User-Agent': 'bkcb6.app directory'}), timeout=180).read())
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(3)
def soda(host, ds, where, select=None, group=None, limit=50000):
    q = {'$where': where, '$limit': limit}
    if select: q['$select'] = select
    if group: q['$group'] = group
    return get('https://%s/resource/%s.json?' % (host, ds) + urllib.parse.urlencode(q))
GEO_F = P('data/cb6-audit/geosearch.json'); GEO = json.load(open(GEO_F)) if os.path.exists(GEO_F) else {}
def geo(addr, zip_):
    k = '%s|%s' % (addr, zip_)
    if k not in GEO:
        try:
            u = 'https://geosearch.planninglabs.nyc/v2/search?' + urllib.parse.urlencode({'text': '%s, Brooklyn, NY %s' % (re.sub(r'\s*#+\s*', ' ', addr), zip_), 'size': 1})
            ft = get(u)['features']; GEO[k] = ft[0]['geometry']['coordinates'][::-1] if ft else None
        except Exception: GEO[k] = None
    return GEO[k]
def where(lat, lng):
    if not lat or not lng: return None
    pt = Point(lng, lat)
    if CD6.contains(pt): return None
    for s, g in BIDS.items():
        if g.distance(pt) <= EDGE: return s
    return None
def cd_of(lat, lng):
    pt = Point(lng, lat)
    return next((c for c, g in CDS if g.contains(pt)), min(CDS, key=lambda c: c[1].distance(pt))[0])
zl = ','.join("'%s'" % z for z in ZIPS)
if '--cached' in sys.argv: raw = json.load(open(P(OUT, 'raw.json')))   # re-place the last pull
else:
    raw = {}
    # DOHMH: one row per restaurant, with its latest inspection date
    raw['restaurants'] = soda('data.cityofnewyork.us', '43nn-pn8j', "boro='Brooklyn' AND zipcode in(%s)" % zl,
                              select='camis,dba,building,street,zipcode,phone,cuisine_description,latitude,longitude,max(inspection_date) as last',
                              group='camis,dba,building,street,zipcode,phone,cuisine_description,latitude,longitude')
    raw['dcwp'] = soda('data.cityofnewyork.us', 'w7w3-xahh', "license_status='Active' AND address_zip in(%s)" % zl)
    raw['agmarkets'] = soda('data.ny.gov', '9a8c-vfzj', "zip_code in(%s)" % zl)
    raw['sla'] = soda('data.ny.gov', '9s3h-dpkz', "zipcode in(%s)" % zl)
    raw['appearance'] = soda('data.ny.gov', 'y3u4-jbgh', "business_zip in(%s)" % ','.join("'%s'" % z for z in ZIPS))
    npi = []
    for z in ZIPS:
        skip = 0
        while True:
            r = get('https://npiregistry.cms.hhs.gov/api/?' + urllib.parse.urlencode({'version': '2.1', 'postal_code': z, 'enumeration_type': 'NPI-2', 'limit': 200, 'skip': skip}))
            npi += r.get('results', []) or []
            if len(r.get('results') or []) < 200 or skip >= 1000: break
            skip += 200
    raw['npi'] = npi
    raw['fdic'] = []
    for z in ZIPS:
        raw['fdic'] += [x['data'] for x in get('https://api.fdic.gov/banks/locations?' + urllib.parse.urlencode({'filters': 'ZIP:%s' % z, 'limit': 500}))['data']]
    json.dump(raw, open(P(OUT, 'raw.json'), 'w'))
print({k: len(v) for k, v in raw.items()})
# into cb6_audit's row shape, placed, kept when inside a BID and outside District 6
rows = []
f = lambda v: float(v) if v not in (None, '', '0') and float(v) else None
for r in raw['restaurants']:
    rows.append({'src': 'restaurants', 'id': 'camis-' + r['camis'], 'name': r.get('dba', ''), 'alt': '', 'addr': '%s %s' % (r.get('building', ''), r.get('street', '')),
                 'zip': r.get('zipcode', ''), 'lat': f(r.get('latitude')), 'lng': f(r.get('longitude')), 'phone': r.get('phone', ''), 'cuisine': r.get('cuisine_description', ''), 'last': r.get('last', '')})
for r in raw['dcwp']:
    rows.append({'src': 'dcwp', 'id': 'dcwp-' + r['license_nbr'], 'name': r.get('dba_trade_name') or r.get('business_name', ''), 'alt': r.get('business_name', ''),
                 'addr': '%s %s' % (r.get('address_building', ''), r.get('address_street_name', '')), 'zip': r.get('address_zip', ''),
                 'lat': f(r.get('latitude')), 'lng': f(r.get('longitude')), 'phone': r.get('contact_phone', ''), 'cat': r.get('business_category', ''), 'premises': r.get('license_type') == 'Premises'})
for r in raw['agmarkets']:
    rows.append({'src': 'agmarkets', 'id': 'ag-' + r['license_number'], 'name': r.get('dba_name') or r.get('entity_name', ''), 'alt': r.get('entity_name', ''),
                 'addr': '%s %s' % (r.get('street_number', ''), r.get('street_name', '')), 'zip': r.get('zip_code', ''), 'lat': None, 'lng': None, 'estab': r.get('estab_type', '')})
for r in raw['sla']:
    rows.append({'src': 'sla', 'id': 'sla-' + r['licensepermitid'], 'name': r.get('dba') or r.get('legalname', ''), 'alt': r.get('legalname', ''), 'addr': r.get('actualaddressofpremises', ''),
                 'zip': r.get('zipcode', ''), 'lat': None, 'lng': None, 'cat': r.get('description', ''), 'expires': r.get('expirationdate', '')})
for r in raw['appearance']:
    if r.get('license_type') == 'DOSAERENTER': continue
    rows.append({'src': 'salons', 'id': 'dos-' + r['license_number'], 'name': r.get('business_name') or r.get('license_holder_name', ''), 'alt': r.get('license_holder_name', ''),
                 'addr': r.get('business_address_1', ''), 'zip': (r.get('business_zip') or '')[:5], 'lat': None, 'lng': None,
                 'cat': 'Barber shop' if r.get('license_type') == 'DOSBARSHOPOWNER' else 'Appearance enhancement business', 'expires': r.get('license_expiration_date', '')})
for r in raw['npi']:
    b = r.get('basic', {}); loc = next((a for a in r.get('addresses', []) if a.get('address_purpose') == 'LOCATION'), None)
    if not loc or b.get('status') != 'A' or (b.get('last_updated') or '') < '2021-01-01': continue
    if (loc.get('postal_code') or '')[:5] not in ZIPS: continue
    dba = next((o.get('organization_name') for o in r.get('other_names', []) if o.get('type') == 'Doing Business As'), '')
    tx = next((t.get('desc') for t in r.get('taxonomies', []) if t.get('primary')), '') or next((t.get('desc') for t in r.get('taxonomies', [])), '')
    rows.append({'src': 'npi', 'id': 'npi-' + str(r['number']), 'name': dba or b.get('organization_name', ''), 'alt': b.get('organization_name', ''), 'addr': loc.get('address_1', ''),
                 'zip': (loc.get('postal_code') or '')[:5], 'lat': None, 'lng': None, 'phone': loc.get('telephone_number', ''), 'cat': tx})
for r in raw['fdic']:
    rows.append({'src': 'fdic', 'id': 'fdic-' + str(r['ID']), 'name': re.sub(r',? National Association$|,? N\.?A\.?$', '', r['NAME']), 'alt': r.get('OFFNAME', ''), 'addr': r.get('ADDRESS', ''), 'zip': str(r.get('ZIP', '')),
                 'lat': None, 'lng': None, 'cat': r.get('SERVTYPE_DESC', ''), 'branch': r.get('OFFNAME', '')})
keep = []
for r in rows:
    if r['src'] not in ('restaurants', 'dcwp') or not r.get('lat'):
        g = geo(r['addr'], r['zip'])
        if g: r['lat'], r['lng'] = g
    s = where(r.get('lat'), r.get('lng'))
    if s: r['bid'] = s; r['cd'] = cd_of(r['lat'], r['lng']); keep.append(r)
json.dump(GEO, open(GEO_F, 'w'), indent=0)
json.dump(keep, open(P(OUT, 'registers.json'), 'w'), indent=0)
import collections
print('inside a BID, outside District 6:', len(keep), collections.Counter((r['bid'], r['src']) for r in keep))
