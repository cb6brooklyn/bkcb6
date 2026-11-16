#!/usr/bin/env python3
"""Storefronts and other places open to the public in the three BIDs that reach into CB6 that are on OpenStreetMap but not
yet in the Directory, whether or not they hold a license: shops, restaurants, offices, studios, clinics, salons, galleries.
OpenStreetMap is read fresh through Overpass (the maps.mail.ru mirror), so places mapped since the Directory's August
extract are included. A place that matches a Directory profile (same address and name, or within 60 meters by name) is
left alone; the rest get a profile (slug bidosm-...) and a business page (/biz/...), tracked in data/bid-audit/osm-pages.json.
Places of worship, schools, libraries, post offices and other public institutions are left to their own Directory passes.
Rerunnable: its own profiles are replaced. Run after bid_register_profiles.py."""
import json, os, re, sys, hashlib, collections, urllib.request, urllib.parse, time
from shapely.geometry import shape, Point
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
sys.path.insert(0, P('scripts'))
os.chdir(ROOT)
import cb6_audit as A
from biz_kind import SUPERMARKET, SMOKE
SLUGS = {'park-slope-5th-avenue': 'Park Slope Fifth Avenue BID', 'north-flatbush': 'North Flatbush BID', 'atlantic-avenue': 'Atlantic Avenue BID'}
BIDS = {s: shape(json.load(open(P('data/bids/%s-boundary.geojson' % s)))['features'][0]['geometry']) for s in SLUGS}
EDGE = 0.00012
CD6 = shape(json.load(open(P('data/cb6-audit/cd306.geojson'))))
CDS = [(x['properties']['boro_cd'], shape(x['geometry'])) for x in json.load(open(P('data/community-districts.geojson')))['features'] if x['properties']['boro_cd'].startswith('3')]
def get(u, data=None):
    for i in range(4):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, data=data, headers={'User-Agent': 'bkcb6.app directory'}), timeout=300).read())
        except Exception:
            if i == 3: raise
            time.sleep(5)
OSM = []
for g in BIDS.values():   # one query per BID: the three together time out
    x0, y0, x1, y1 = g.bounds
    bb = '(%f,%f,%f,%f)' % (y0 - .0005, x0 - .0005, y1 + .0005, x1 + .0005)
    Q = '[out:json][timeout:180];(' + ''.join('nwr[name][%s]%s;' % (k, bb) for k in ('shop', 'amenity', 'office', 'craft', 'healthcare', 'leisure', 'tourism')) + ');out center tags;'
    OSM += get('https://maps.mail.ru/osm/tools/overpass/api/interpreter?' + urllib.parse.urlencode({'data': Q}))['elements']
OSM = list({(e['type'], e['id']): e for e in OSM}.values())
json.dump(OSM, open(P('data/bid-audit/osm.json'), 'w'))
SKIP_AMENITY = {'place_of_worship', 'school', 'library', 'post_office', 'townhall', 'police', 'fire_station', 'bicycle_rental', 'parking', 'parking_entrance', 'bench', 'atm',
                'bicycle_parking', 'drinking_water', 'toilets', 'waste_basket', 'recycling', 'charging_station', 'vending_machine', 'public_bookcase', 'shelter', 'fountain',
                'grave_yard', 'courthouse', 'community_centre', 'social_facility', 'university', 'college', 'hospital', 'bus_station', 'ferry_terminal', 'clock', 'telephone',
                'post_box', 'loading_dock', 'motorcycle_parking', 'letter_box', 'kneipp_water_cure', 'bbq', 'give_box', 'device_charging_station'}
SKIP_LEISURE = {'park', 'playground', 'garden', 'pitch', 'dog_park', 'sports_hall', 'track', 'swimming_pool', 'picnic_table', 'outdoor_seating', 'common', 'nature_reserve'}
SKIP_TOURISM = {'attraction', 'artwork', 'information', 'viewpoint', 'picnic_site'}
SKIP_OFFICE = {'government', 'religion', 'diplomatic', 'political_party'}
FOOD_SHOP = {'bakery', 'coffee', 'tea', 'confectionery', 'pastry', 'chocolate', 'ice_cream', 'deli'}
GROC = {'greengrocer', 'butcher', 'seafood', 'cheese', 'spices', 'health_food', 'nutrition_supplements', 'frozen_food', 'farm', 'dairy', 'food'}
HB = {'hairdresser', 'beauty', 'cosmetics', 'massage', 'tattoo', 'nails', 'perfumery', 'hairdresser_supply', 'piercing'}
HM = {'optician', 'chemist', 'medical_supply', 'hearing_aids', 'pharmacy'}
SV_SHOP = {'dry_cleaning', 'laundry', 'shipping', 'copyshop', 'pet_grooming', 'funeral_directors', 'travel_agency', 'tailor', 'shoe_repair', 'locksmith', 'storage_rental',
           'money_lender', 'pawnbroker', 'repair', 'mobile_phone_repair', 'computer_repair', 'photo'}
AUTO = {'car_repair', 'car', 'tyres', 'car_parts', 'motorcycle'}
def classify(t):
    """(topic, kind) or None"""
    a, s, o, c, h, l, tr = (t.get(k) for k in ('amenity', 'shop', 'office', 'craft', 'healthcare', 'leisure', 'tourism'))
    k = lambda v: (v or '').split(';')[0].replace('_', ' ').capitalize()
    if a in SKIP_AMENITY or l in SKIP_LEISURE or tr in SKIP_TOURISM or o in SKIP_OFFICE: return None
    nm = t.get('name', '')
    if a in ('restaurant', 'fast_food', 'cafe', 'bar', 'pub', 'ice_cream', 'biergarten', 'food_court', 'juice_bar'): return 'Restaurants, cafes and food', k(t.get('cuisine') if a == 'restaurant' and t.get('cuisine') else a)
    if s in FOOD_SHOP: return 'Restaurants, cafes and food', k(s)
    if s == 'supermarket' or SUPERMARKET.search(nm): return 'Supermarkets', 'Supermarket'
    if s == 'convenience': return ('Smoke, vape and cannabis shops', 'Convenience') if SMOKE.search(nm) else ('Delis and bodegas', 'Convenience')
    if s in ('tobacco', 'cannabis', 'e-cigarette'): return 'Smoke, vape and cannabis shops', k(s)
    if s in GROC: return 'Groceries and food stores', k(s)
    if s in HB: return 'Hair, beauty and personal care', k(s)
    if h or a in ('doctors', 'dentist', 'clinic', 'pharmacy') or s in HM: return 'Health and medical', k(h or a or s)
    if l in ('fitness_centre', 'sports_centre', 'dance', 'fitness_station') or a == 'dojo' or s == 'sports' and False: return 'Fitness and recreation', k(l or a)
    if a in ('kindergarten', 'childcare'): return 'Child care', 'Childcare'
    if a in ('arts_centre', 'theatre', 'events_venue', 'cinema', 'nightclub', 'music_venue') or tr in ('gallery', 'museum'): return 'Venues', k(a or tr)
    if tr in ('hotel', 'guest_house', 'hostel', 'motel', 'apartment'): return 'Hotels and tourism', k(tr)
    if s in AUTO or a in ('car_rental', 'car_wash', 'fuel', 'taxi', 'car_sharing'): return 'Auto and transportation', k(s or a)
    if c: return 'Trades, workshops and industrial', k(c)
    if o or s in SV_SHOP or a in ('bank', 'veterinary', 'prep_school', 'driving_school', 'language_school', 'music_school', 'coworking_space', 'bureau_de_change', 'money_transfer', 'studio', 'animal_boarding', 'fortune_teller'):
        return 'Services and offices', k(o or s or a)
    if s: return 'Stores', k(s)
    if a or l or tr: return 'Other businesses', k(a or l or tr)
    return None
def which(lat, lng):
    pt = Point(lng, lat)
    for s, g in BIDS.items():
        if g.distance(pt) <= EDGE: return s
    return None
def cd_of(lat, lng):
    pt = Point(lng, lat)
    if CD6.contains(pt): return '306'
    return next((c for c, g in CDS if g.contains(pt)), min(CDS, key=lambda c: c[1].distance(pt))[0])
GEO_F = P('data/bid-audit/reverse.json'); REV = json.load(open(GEO_F)) if os.path.exists(GEO_F) else {}
def addr_at(lat, lng):
    k = '%.6f,%.6f' % (lat, lng)
    if k not in REV:
        try:
            f = get('https://geosearch.planninglabs.nyc/v2/reverse?' + urllib.parse.urlencode({'point.lat': lat, 'point.lon': lng, 'size': 1}))['features']
            REV[k] = [f[0]['properties'].get('housenumber', ''), f[0]['properties'].get('street', ''), f[0]['properties'].get('postalcode', '')] if f else None
        except Exception: REV[k] = None
    return REV[k]
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith('bidosm-')]
rows = []
for e in OSM:
    t = e.get('tags', {}); lat = e.get('lat') or (e.get('center') or {}).get('lat'); lng = e.get('lon') or (e.get('center') or {}).get('lon')
    if not lat: continue
    s = which(lat, lng)
    if not s: continue
    c = classify(t)
    if not c: continue
    addr = ('%s %s' % (t.get('addr:housenumber', ''), t.get('addr:street', ''))).strip() if t.get('addr:housenumber') else ''
    zip_ = t.get('addr:postcode', '')
    rows.append({'src': 'osm', 'id': 'osm-%s%d' % (e['type'][0], e['id']), 'name': t['name'], 'alt': '', 'addr': addr, 'zip': zip_, 'lat': lat, 'lng': lng,
                 'phone': t.get('phone') or t.get('contact:phone', ''), 'web': t.get('website') or t.get('contact:website', ''), 'topic': c[0], 'kind': c[1], 'bid': s,
                 'cuisine': t.get('cuisine', ''), 'hours': t.get('opening_hours', '')})
got, miss = A.match(rows, D['profiles'])
# a place with no house number on OpenStreetMap: placed at the city's nearest address, then checked against the Directory again
miss2 = []
for r in miss:
    if not r['addr']:
        a = addr_at(r['lat'], r['lng'])
        if a and a[0]: r['addr'] = '%s %s' % (a[0], a[1]); r['zip'] = r['zip'] or a[2]
    miss2.append(r)
json.dump(REV, open(GEO_F, 'w'), indent=0)
got2, miss = A.match(miss2, D['profiles'])
from cb6_register_profiles_lib import addr_tc
import importlib.util as _iu
_sp = _iu.spec_from_file_location('bsp', P('scripts/biz_site_profiles.py')); BSP = _iu.module_from_spec(_sp); _sp.loader.exec_module(BSP)
made = collections.Counter()
for r in miss:
    cd = cd_of(r['lat'], r['lng']); n = int(cd[1:])
    ph = re.sub(r'\D', '', r['phone'])[-10:]; phone = '(%s) %s-%s' % (ph[:3], ph[3:6], ph[6:]) if len(ph) == 10 else ''
    addr = addr_tc(r['addr']) if r['addr'] else ''
    kv = [['Category', r['topic']], ['Kind', r['kind']]] + ([['Address', ('%s, Brooklyn %s' % (addr, r['zip'])).strip()]] if addr else []) + \
         [['Community board', 'Brooklyn Community Board %d' % n], ['Business improvement district', SLUGS[r['bid']]]] + \
         ([['Hours', r['hours']]] if r['hours'] else []) + [['Source', 'OpenStreetMap (%s), read Nov 16, 2026' % r['id'][4:]]]
    what = {'Restaurants, cafes and food': 'a restaurant or cafe', 'Stores': 'a store', 'Services and offices': 'a business', 'Health and medical': 'a health practice',
            'Hair, beauty and personal care': 'a salon or spa', 'Venues': 'a venue', 'Child care': 'a child care program', 'Fitness and recreation': 'a fitness studio'}.get(r['topic'], 'a business')
    intro = ['%s is %s%s in Brooklyn Community District %d, in the %s.' % (r['name'], what, ' at %s' % addr if addr else '', n, SLUGS[r['bid']])]
    slug = 'bidosm-' + hashlib.md5(r['id'].encode()).hexdigest()[:10]
    web = r['web']
    p = {'slug': slug, 'type': slug, 'kind': 'org', 'official': '', 'name': r['name'], 'seat': '%s · Brooklyn' % r['kind'], 'desc': intro[0], 'lat': round(r['lat'], 6), 'lng': round(r['lng'], 6),
         'addr': addr, 'zip': r['zip'], 'addr_note': '', 'phone': phone, 'email': '', 'web': re.sub(r'^https?://(www\.)?', '', web).strip('/'), 'weburl': web, 'since': '', 'intro': intro,
         'does': [], 'kv': kv, 'links': [], 'logo': '', 'cal': None, 'n': 0, 'going': [], 'group': 'Local businesses' if r['topic'] != 'Child care' else 'Child care',
         'topic': r['topic'] if r['topic'] != 'Child care' else 'Preschool child care', 'sort': 0, 'osm': r['id'][4:], 'bid': r['bid']}
    D['profiles'].append(p); made[r['bid']] += 1
OLD_F = P('data/bid-audit/osm-pages.json'); OLD = json.load(open(OLD_F)) if os.path.exists(OLD_F) else {}
for u in OLD.values():
    if os.path.exists(u[1:]): os.remove(u[1:])
pages = {}
for p in D['profiles']:
    if not p['slug'].startswith('bidosm-'): continue
    s_ = BSP.slugify(p['name'] + ' ' + (p.get('addr') or '')); k_ = 2; base = s_
    while os.path.exists('biz/%s.html' % s_) or '/biz/%s.html' % s_ in pages.values(): s_ = '%s-%d' % (base, k_); k_ += 1
    path = '/biz/%s.html' % s_
    open(path[1:], 'w').write(BSP.page(p, None, path)); pages[p['slug']] = path
    p['links'] = [['Profile and map', 'https://bkcb6.app' + path]]
json.dump(pages, open(OLD_F, 'w'), indent=0)
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('OpenStreetMap places in the BIDs:', len(rows), '| already in the Directory:', len(got) + len(got2), '| profiles made:', sum(made.values()), dict(made))
