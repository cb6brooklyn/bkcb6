#!/usr/bin/env python3
"""Every business in the three BIDs that reach into CB6 gets a Directory profile, including the parts of each BID outside
District 6 (Community Districts 2, 7 and 8), which the BKCB6 register pass (cb6_register_profiles.py) does not cover.

  1. register records inside a BID and outside District 6 (data/bid-audit/registers.json, from bid_audit.py) that match no
     profile: one profile per business (slug bidreg-...), the same shape as the BKCB6 register profiles
  2. the Park Slope Fifth Avenue BID's own business directory (data/bids/park-slope-5th-avenue-businesses.json, read from
     the BID's site Aug 27, 2026): a listing that matches no profile gets one (slug bidlist-...)
Each new profile gets its business page (/biz/<name-and-address>.html), tracked in data/bid-audit/pages.json.
Rerunnable: its own profiles (bidreg-, bidlist-) are replaced. Run after cb6_register_profiles.py, before directory_dedupe.py."""
import json, os, re, sys, hashlib, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
sys.path.insert(0, P('scripts'))
os.chdir(ROOT)
import cb6_audit as A
import directory_dedupe as dd
from biz_kind import SUPERMARKET, DELI, SMOKE
from cb6_register_profiles_lib import tc, addr_tc
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith(('bidreg-', 'bidlist-'))]
BIDN = {'park-slope-5th-avenue': 'Park Slope Fifth Avenue BID', 'north-flatbush': 'North Flatbush BID', 'atlantic-avenue': 'Atlantic Avenue BID'}
SLA_TOPIC = {'Restaurant': 'Restaurants, cafes and food', 'Food & Beverage Business': 'Restaurants, cafes and food', 'Additional Bar': 'Restaurants, cafes and food', 'Club': 'Restaurants, cafes and food',
             'Catering Establishment': 'Restaurants, cafes and food', 'Liquor Store': 'Stores', 'Wine Store': 'Stores', 'Hotel': 'Hotels and tourism', 'Drug Store': 'Health and medical'}
DCWP_TOPIC = {'Home Improvement Contractor': 'Trades, workshops and industrial', 'Garage & Parking Lot': 'Auto and transportation', 'Tow Truck Company': 'Auto and transportation',
              'Secondhand Dealer - Auto': 'Auto and transportation', 'Car Wash': 'Auto and transportation', 'Hotel': 'Hotels and tourism', 'Scrap Metal Processor': 'Trades, workshops and industrial',
              'Construction Labor Provider': 'Trades, workshops and industrial', 'Self-Storage Facility': 'Services and offices', 'Storage Warehouse': 'Services and offices',
              'Process Serving Agency': 'Services and offices', 'Scale Dealer/Repairer': 'Services and offices'}
SRCNAME = {'npi': 'National Provider Identifier registry (CMS)', 'salons': 'NYS Department of State licenses', 'fdic': 'FDIC bank branch list', 'restaurants': 'NYC Health Department restaurant inspections',
           'dcwp': 'NYC Department of Consumer and Worker Protection licenses', 'agmarkets': 'NYS Agriculture and Markets retail food stores', 'sla': 'NYS Liquor Authority licenses',
           'bidlist': 'Park Slope Fifth Avenue BID business directory'}
def topic(rows, name):
    srcs = {r['src'] for r in rows}
    if 'npi' in srcs: return 'Health and medical'
    if 'salons' in srcs: return 'Hair, beauty and personal care'
    if 'fdic' in srcs: return 'Services and offices'
    if SUPERMARKET.search(name): return 'Supermarkets'
    if 'restaurants' in srcs: return 'Restaurants, cafes and food'
    for r in rows:
        if r['src'] == 'sla' and r.get('cat') in SLA_TOPIC: return SLA_TOPIC[r['cat']]
    if 'agmarkets' in srcs or any(r['src'] == 'sla' and r.get('cat') == 'Grocery Store' for r in rows) or any(r.get('cat') in ('Tobacco Retail Dealer', 'Electronic Cigarette Dealer', 'Stoop Line Stand') for r in rows):
        if SMOKE.search(name): return 'Smoke, vape and cannabis shops'
        return 'Delis and bodegas' if DELI.search(name) else 'Groceries and food stores'
    for r in rows:
        if r['src'] == 'dcwp': return DCWP_TOPIC.get(r.get('cat'), 'Stores')
        if r['src'] == 'bidlist': return r['topic']
    return 'Trades, workshops and industrial' if 'sla' in srcs else 'Other businesses'
WHAT = {'Restaurants, cafes and food': 'a restaurant, cafe or bar', 'Supermarkets': 'a supermarket', 'Delis and bodegas': 'a deli or bodega', 'Groceries and food stores': 'a food store',
        'Trades, workshops and industrial': 'a trades business', 'Auto and transportation': 'an auto and transportation business', 'Hotels and tourism': 'a hotel',
        'Stores': 'a store', 'Services and offices': 'a services business', 'Smoke, vape and cannabis shops': 'a smoke or vape shop',
        'Hair, beauty and personal care': 'a salon or barber shop', 'Fitness and recreation': 'a fitness business'}
def cbname(cd): return 'Brooklyn Community Board %d' % int(str(cd)[1:])
def make(rows, prefix):
    first = sorted(rows, key=lambda r: ['restaurants', 'sla', 'agmarkets', 'dcwp', 'fdic', 'salons', 'npi', 'bidlist'].index(r['src']))[0]
    name = tc(re.sub(r'\s+\d{4,}$', '', first['name'])); addr = addr_tc(first['addr']); zip_ = first.get('zip') or ''
    t = topic(rows, name); lat = next((r['lat'] for r in rows if r.get('lat')), None); lng = next((r['lng'] for r in rows if r.get('lng')), None)
    cuisine = next((r['cuisine'] for r in rows if r.get('cuisine') and r['cuisine'] != 'Other'), '')
    ph = re.sub(r'\D', '', next((r.get('phone') for r in rows if r.get('phone')), '') or ''); phone = '(%s) %s-%s' % (ph[:3], ph[3:6], ph[6:]) if len(ph) == 10 else ''
    web = next((r['web'] for r in rows if r.get('web')), '')
    cd, bid = first['cd'], first['bid']
    kv = [['Category', t]] + ([['Cuisine', cuisine]] if cuisine else []) + [['Address', ('%s, Brooklyn %s' % (addr, zip_)).rstrip()], ['Community board', cbname(cd)], ['Business improvement district', BIDN[bid]]]
    for r in rows:
        if r['src'] == 'restaurants': kv.append(['Health Department record', 'Restaurant permit %s' % r['id'][6:] + ('. On the register, not yet inspected.' if (r.get('last') or '').startswith('1900') else '. Last inspected %s.' % (r.get('last') or '')[:10])])
        if r['src'] == 'dcwp': kv.append(['City license', '%s, %s' % (r['cat'], r['id'][5:])])
        if r['src'] == 'sla': kv.append(['Liquor license', '%s, %s%s' % (r['cat'], r['id'][4:], ', expires %s' % r['expires'][:10] if r.get('expires') else '')])
        if r['src'] == 'npi': kv.append(['Health practice', '%sNPI %s' % (r['cat'] + ', ' if r.get('cat') else '', r['id'][4:])])
        if r['src'] == 'salons': kv.append(['State license', '%s, %s%s' % (r['cat'], r['id'][4:], ', expires %s' % r['expires'][:10] if r.get('expires') else '')])
        if r['src'] == 'fdic': kv.append(['Bank branch', '%s (FDIC)' % tc(r.get('branch') or '')])
        if r['src'] == 'agmarkets': kv.append(['Food store license', 'NYS Agriculture and Markets, %s' % r['id'][3:]])
        if r['src'] == 'bidlist': kv.append(['BID directory category', r['catname']])
        if r.get('alt') and A.nn(r['alt']) != A.nn(first['name']) and ['Legal name', tc(r['alt'])] not in kv: kv.append(['Legal name', tc(r['alt'])])
    kv.append(['Source', '; '.join(sorted({SRCNAME[r['src']] for r in rows}))])
    what = 'a health practice' if any(r['src'] == 'npi' for r in rows) else ('a bank branch' if any(r['src'] == 'fdic' for r in rows) else WHAT.get(t, 'a business'))
    if t == 'Health and medical' and what == 'a business': what = 'a pharmacy'
    intro = ['%s is %s at %s in Brooklyn Community District %d, in the %s.' % (name, what, addr, int(str(cd)[1:]), BIDN[bid])]
    slug = prefix + hashlib.md5('|'.join(sorted(r['id'] for r in rows)).encode()).hexdigest()[:10]
    p = {'slug': slug, 'type': slug, 'kind': 'org', 'official': '', 'name': name, 'seat': '%s · Brooklyn' % t.split(',')[0], 'desc': intro[0], 'lat': lat, 'lng': lng,
         'addr': addr, 'zip': zip_, 'addr_note': '', 'phone': phone, 'email': '', 'web': re.sub(r'^https?://(www\.)?', '', web).strip('/'), 'weburl': web, 'since': '', 'intro': intro,
         'does': [], 'kv': kv, 'links': [], 'logo': '', 'cal': None, 'n': 0, 'going': [], 'group': 'Local businesses', 'topic': t, 'sort': 0,
         'registers': sorted(r['id'] for r in rows), 'bid': bid}
    if cuisine: p['cuisine'] = cuisine
    return p
def cluster(rows):
    # one liquor licensee's many bars at one address (a stadium's concession stands): one business, under its legal name
    lic = collections.defaultdict(list)
    for r in rows:
        if r['src'] == 'sla' and r.get('alt'): lic[(dd._ak({'addr': r['addr']}), A.nn(r['alt']))].append(r)
    for k, rs in lic.items():
        if len(rs) > 1 and len({A.nn(r['name']) for r in rs}) > 1:
            for r in rs: r['name'] = r['alt']
    cl = []
    for r in rows:
        k = dd._ak({'addr': r['addr']})
        for c in cl:
            if k and c['k'] == k and max(A.sim(r['name'], x['name']) for x in c['rows']) >= .62: c['rows'].append(r); break
        else: cl.append({'k': k, 'rows': [r]})
    return cl
made = collections.Counter()
# 1. register records
R = json.load(open(P('data/bid-audit/registers.json')))
got, miss = A.match(R, D['profiles'])
for c in cluster(miss):
    p = make(c['rows'], 'bidreg-'); D['profiles'].append(p); made[(p['bid'], 'registers')] += 1
# 2. the Park Slope Fifth Avenue BID's own directory
from shapely.geometry import shape, Point
CD6 = shape(json.load(open(P('data/cb6-audit/cd306.geojson'))))
CDS = [(x['properties']['boro_cd'], shape(x['geometry'])) for x in json.load(open(P('data/community-districts.geojson')))['features'] if x['properties']['boro_cd'].startswith('3')]
PSB = json.load(open(P('data/bids/park-slope-5th-avenue-businesses.json'))); CATN = dict(PSB['cats'])
F_, ST, SV, HB, HM, FI, RT = 'Restaurants, cafes and food', 'Stores', 'Services and offices', 'Hair, beauty and personal care', 'Health and medical', 'Fitness and recreation', 'Groceries and food stores'
PS_TOPIC = {'american-british-cuisine': F_, 'asian-cuisine': F_, 'bagels-delis-bodegas': 'Delis and bodegas', 'banks-financial-institutions': SV, 'arts-music-schools': SV, 'bars': F_,
            'beauty-cosmetics': HB, 'bikes-repairs': ST, 'botanicas-churches': ST, 'cafes-bakeries-juice-bars': F_, 'car-services': 'Auto and transportation', 'clothing-accessories-jewelry': ST,
            'contractors-kitchen-bath': 'Trades, workshops and industrial', 'dispensary': 'Smoke, vape and cannabis shops', 'educational-services': SV, 'electronics-repairs-cell-phones': ST,
            'european-cuisine': F_, 'eyeglass-stores': HM, 'fitness-health': FI, 'florists': ST, 'framing-stain-glass': ST, 'galleries': ST, 'games-books-records': ST, 'gifts-party-supplies': ST,
            'grocery-speciality-foods': RT, 'hardware': ST, 'home-design-furnishing': ST, 'ice-cream-frozen-yogurt': F_, 'indian-cuisine': F_, 'italian-cuisine': F_, 'kids-baby': ST, 'korean': F_,
            'latin-caribbean-cuisine': F_, 'laundry-dry-cleaning': SV, 'lebanese': F_, 'medical-dental': HM, 'mediterranean-cuisine': F_, 'mexican-cuisine': F_, 'music-venues-event-space': 'Venues',
            'pet-care': SV, 'pharmacy': HM, 'professional-services': SV, 'real-estate': SV, 'record-store': ST, 'running-store': ST, 'salons-barbers': HB, 'schools-day-care': SV, 'seafood': F_,
            'shoe-shoe-repair': ST, 'spa-nails': HB, 'specialty-stores': ST, 'tobacco-store': 'Smoke, vape and cannabis shops', 'travel-agency': SV, 'variety-99-cent-stores': ST,
            'vintage-antiques': ST, 'wellness': HB, 'wine-liquors': ST}
TAGS = {'black-owned', 'women-owned', 'lgbtq-owned', 'south-slope-highlights', 'halal', 'vegan', 'delivery-concept'}
def ps_topic(cs):
    for c in cs:
        if c in PS_TOPIC: return PS_TOPIC[c]
    return 'Other businesses'
L = []
for b in PSB['biz']:
    if not b.get('y'): continue
    if not [c for c in b.get('c', []) if c not in TAGS and c != 'cultural-non-profit-government']: continue
    pt = Point(b['x'], b['y'])
    if CD6.contains(pt): cd = '306'
    else: cd = next((c for c, g in CDS if g.contains(pt)), min(CDS, key=lambda c: c[1].distance(pt))[0])
    L.append({'src': 'bidlist', 'id': 'psbid-' + b['s'], 'name': b['n'], 'alt': '', 'addr': b.get('a', ''), 'zip': '', 'lat': b['y'], 'lng': b['x'], 'phone': b.get('p', ''),
              'web': b.get('w', ''), 'topic': ps_topic(b.get('c', [])), 'catname': ', '.join(CATN.get(c, c) for c in b.get('c', []) if c not in TAGS), 'cd': cd, 'bid': 'park-slope-5th-avenue'})
got2, miss2 = A.match(L, D['profiles'])
# the BID's list is from August: a storefront the Directory already has under another name, at the same address and in the
# same line of business, is the same storefront (a new tenant, or the same shop by another name); offices share buildings
SAME = collections.defaultdict(set)
for p in D['profiles']:
    if p.get('group') in ('Local businesses', 'Health', 'Food') and p.get('addr'):
        k = dd._ak(p)
        if k: SAME[k].add(p.get('topic'))
FAM = {'Pharmacies': 'Health and medical', 'Supermarkets': 'Supermarkets'}
stale = 0; keep2 = []
for r in miss2:
    k = dd._ak({'addr': r['addr']})
    ts = {FAM.get(t, t) for t in SAME.get(k, ())}
    if k and r['topic'] in ts and r['topic'] not in ('Health and medical', 'Services and offices'): stale += 1; continue
    keep2.append(r)
miss2 = keep2
for c in cluster(miss2):
    p = make(c['rows'], 'bidlist-')
    D['profiles'].append(p); made[('park-slope-5th-avenue', 'BID directory')] += 1
# business pages
import importlib.util as _iu
_sp = _iu.spec_from_file_location('bsp', P('scripts/biz_site_profiles.py')); BSP = _iu.module_from_spec(_sp); _sp.loader.exec_module(BSP)
OLD_F = P('data/bid-audit/pages.json'); OLD = json.load(open(OLD_F)) if os.path.exists(OLD_F) else {}
for u in OLD.values():
    if os.path.exists(u[1:]): os.remove(u[1:])
pages = {}
for p in D['profiles']:
    if not p['slug'].startswith(('bidreg-', 'bidlist-')): continue
    s_ = BSP.slugify(p['name'] + ' ' + (p.get('addr') or '')); k_ = 2; base = s_
    while os.path.exists('biz/%s.html' % s_) or '/biz/%s.html' % s_ in pages.values(): s_ = '%s-%d' % (base, k_); k_ += 1
    path = '/biz/%s.html' % s_
    open(path[1:], 'w').write(BSP.page(p, None, path)); pages[p['slug']] = path
    p['links'] = [['Profile and map', 'https://bkcb6.app' + path]]
json.dump(pages, open(OLD_F, 'w'), indent=0)
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('register records inside the BIDs, outside District 6:', len(R), '| already in the Directory:', len(got), '| BID directory listings:', len(L), '| already in the Directory:', len(got2), '| same storefront as a Directory listing:', stale)
print('profiles made:', sum(made.values()), dict(made))
