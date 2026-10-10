"""Every business in the CB6 business directory (civic/business/business-cb6.json) as a profile in the apps' Organizations
tab, under Local businesses by kind of business, each with its logo, address, map, website, category, license and the
business improvement district it is in. Run after orgs_by_bid.py and bid_profiles.py; rerunnable (its own entries are
replaced). Writes civic/orgs/orgs-profiles.json and copies the directory's logos into civic/orgs/logos/biz-*.png."""
import json, os, hashlib, shutil
from shapely.geometry import shape, Point

C = 'app/data/civic'
P = f'{C}/orgs/orgs-profiles.json'
d = json.load(open(P))
rows = json.load(open(f'{C}/business/business-cb6.json'))['rows']  # name, category, kind, address, nb, lat, lng, web, logo, dark, new, newdate, legal, license, source

# the districts
bids = {f['properties']['name']: shape(f['geometry']).buffer(0.00018) for f in json.load(open(f'{C}/bids.geojson'))['features']}
gowanus = shape(json.load(open('data/gowanus_rezoning_boundary.geojson'))['features'][0]['geometry']).buffer(0.00018)
BIDNAME = {'Park Slope 5th Avenue': 'Park Slope Fifth Avenue BID', 'Atlantic Avenue': 'Atlantic Avenue BID', 'North Flatbush': 'North Flatbush BID'}
def district(lat, lng):
    p = Point(lng, lat)
    for n, g in bids.items():
        if g.contains(p): return BIDNAME[n]
    if gowanus.contains(p): return 'Proposed Gowanus BID'
    return ''

# the headings, by kind of business
TOPIC = {
    'Bar or restaurant (liquor license)': 'Restaurants, cafes and food', 'Restaurants and cafes': 'Restaurants, cafes and food',
    'Bars and nightlife': 'Restaurants, cafes and food', 'Brewery, distillery, winery': 'Restaurants, cafes and food',
    'Home, goods and general retail': 'Stores', 'Clothing, shoes and jewelry': 'Stores', 'Hardware stores': 'Stores', 'Liquor or wine store': 'Stores',
    'Food stores': 'Groceries and food stores', 'Groceries and food shops': 'Groceries and food stores',
    'Food stores with beer or liquor license': 'Groceries and food stores', 'Grocery beer license': 'Groceries and food stores',
    'Health and medical': 'Health and medical', 'Hair, beauty and personal care': 'Hair, beauty and personal care',
    'Fitness and recreation': 'Fitness and recreation', 'Services': 'Services and offices', 'Offices and professional': 'Services and offices',
    'Trades and workshops': 'Trades, workshops and industrial', 'Warehouses, logistics and industrial': 'Trades, workshops and industrial',
    'Wholesale or temporary liquor license': 'Trades, workshops and industrial', 'Auto and transportation': 'Auto and transportation',
    'Hotels and tourism': 'Hotels and tourism', 'Other businesses': 'Other businesses', 'Government offices': 'Other businesses'}
ORDER = ['Restaurants, cafes and food', 'Groceries and food stores', 'Stores', 'Markets', 'Venues', 'Health and medical',
         'Hair, beauty and personal care', 'Fitness and recreation', 'Services and offices', 'Trades, workshops and industrial',
         'Auto and transportation', 'Hotels and tourism', 'Other businesses']
SHORT = {'Bar or restaurant (liquor license)': 'Bar or restaurant', 'Food stores with beer or liquor license': 'Food store with a beer or liquor license',
         'Grocery beer license': 'Grocery with a beer license', 'Food stores': 'Food store', 'Restaurants and cafes': 'Restaurant or cafe',
         'Offices and professional': 'Office or professional', 'Home, goods and general retail': 'Retail', 'Hair, beauty and personal care': 'Hair, beauty or personal care',
         'Groceries and food shops': 'Grocery or food shop', 'Fitness and recreation': 'Fitness or recreation', 'Trades and workshops': 'Trade or workshop',
         'Clothing, shoes and jewelry': 'Clothing, shoes or jewelry', 'Auto and transportation': 'Auto or transportation', 'Other businesses': 'Business',
         'Bars and nightlife': 'Bar or nightlife', 'Warehouses, logistics and industrial': 'Warehouse, logistics or industrial', 'Hotels and tourism': 'Hotel or tourism',
         'Hardware stores': 'Hardware store', 'Brewery, distillery, winery': 'Brewery, distillery or winery', 'Government offices': 'Government office'}
SOURCE = {'licensed': 'New York State license records', 'osm': 'OpenStreetMap', 'bkcb6': 'bkcb6.app'}

have = {p['name'].strip().lower() for p in d['profiles'] if not p['slug'].startswith('biz-')}
keep = [p for p in d['profiles'] if not p['slug'].startswith('biz-')]
os.makedirs(f'{C}/orgs/logos', exist_ok=True)
seen = set(); made = []; logos = 0
for r in rows:
    name, cat, kind, addr, nb, lat, lng, web, logo, dark, new, newdate, legal, license, source = r
    name = name.strip()
    if not name or name.lower() in have: continue
    key = (name.lower(), addr.lower())
    if key in seen: continue
    seen.add(key)
    slug = 'biz-' + hashlib.sha1(f'{name}|{addr}'.encode()).hexdigest()[:10]
    bid = district(lat, lng)
    where = bid if bid else (f'{nb}, no BID' if nb else 'No BID')
    label = kind or SHORT.get(cat, cat)
    lf = ''
    if logo:
        src = f'{C}/business/logos/{logo}.png'
        if os.path.exists(src):
            lf = f'biz-{logo}.png'; dst = f'{C}/orgs/logos/{lf}'
            if not os.path.exists(dst): shutil.copyfile(src, dst)
            logos += 1
    kv = [['Category', cat]]
    if kind: kv.append(['Kind', kind])
    if nb: kv.append(['Neighborhood', nb])
    kv.append(['Business improvement district', bid if bid else 'None'])
    if legal and legal.strip().lower() != name.lower(): kv.append(['Legal name', legal])
    if license: kv.append(['License', license])
    if new: kv.append(['Liquor license', f'Applied for in {newdate[:4]}' if newdate else 'Applied for recently'])
    kv += [['Community board', 'Brooklyn Community Board 6'], ['Source', SOURCE.get(source, source)]]
    w = (web or '').strip()
    made.append({'slug': slug, 'type': slug, 'name': name, 'seat': f'{label} · {where}',
                 'desc': f'{name}. {cat}. {addr}, {nb}.', 'lat': lat, 'lng': lng, 'addr': addr, 'zip': '', 'addr_note': '',
                 'phone': '', 'email': '', 'web': w.replace('https://', '').replace('http://', '').strip('/'), 'weburl': w,
                 'since': '', 'intro': [], 'does': [], 'kv': kv, 'links': [], 'logo': lf, 'cal': None, 'n': 0, 'going': [],
                 'kind': 'org', 'official': '', 'group': 'Local businesses', 'topic': TOPIC.get(cat, 'Other businesses'), 'sort': 0})
d['profiles'] = keep + made
# the BID pages' business lists open each business's profile ("kvdest": {"<row value>": "org:<slug>"}, read from 1.17 on)
by_key = {(m['name'].lower(), m['addr'].lower()): m['slug'] for m in made}
by_name = {p['name'].lower(): p['slug'] for p in keep if p.get('group') == 'Local businesses'}
linked = 0
for p in d['profiles']:
    if p.get('group') != 'Business improvement districts' or len(p.get('kv', [])) <= 2: continue
    dest = {}
    for k, v in p['kv'][2:]:
        parts = v.split(' \u00b7 '); name = parts[0].strip().lower(); addr = ' \u00b7 '.join(parts[1:]).strip().lower()
        slug = by_key.get((name, addr)) or by_name.get(name)
        if slug: dest[v] = 'org:' + slug; linked += 1
    p['kvdest'] = dest
print(linked, 'BID page rows linked to profiles')
for g in d['groups']:
    if g['name'] == 'Local businesses': g['topics'] = ORDER
note = ' Every business in the CB6 business directory is a profile too (slug biz-*, scripts/biz_profiles.py), under Local businesses by kind, with its district in seat.'
if 'biz_profiles.py' not in d['about']: d['about'] += note
json.dump(d, open(P, 'w'), ensure_ascii=False, indent=1)
print(len(made), 'businesses as profiles,', logos, 'with logos;', len(d['profiles']), 'profiles in all')
