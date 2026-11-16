#!/usr/bin/env python3
"""BKCB6: every business on the official registers is in the Directory, and every restaurant carries its cuisine.
Uses scripts/cb6_audit.py (DOHMH restaurant inspections, DCWP licenses, NYS Ag & Markets food stores, NYS Liquor
Authority licenses, each limited to Community District 306).
  - a register record with no Directory profile gets one (slug reg-...), under Local businesses;
    records of one business on several registers make one profile
  - state records are placed by the city's address points (GeoSearch) before the district test, since the state
    places them on the street centerline and the district's edges run down streets
  - every restaurant matched to a DOHMH record gets its cuisine ('cuisine', and a Cuisine row)
Rerunnable: its own profiles (reg-) are replaced. Run before biz_site_profiles.py and app_directory_tiles.py."""
import json, os, re, sys, hashlib, collections, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
sys.path.insert(0, P('scripts'))
import cb6_audit as A
from biz_kind import SUPERMARKET, DELI, SMOKE
from shapely.geometry import shape, Point
POLY = shape(json.load(open(P('data/cb6-audit/cd306.geojson'))))
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith('reg-')]
GEO_F = P('data/cb6-audit/geosearch.json'); GEO = json.load(open(GEO_F)) if os.path.exists(GEO_F) else {}
def geo(addr, zip_):
    k = '%s|%s' % (addr, zip_)
    if k not in GEO:
        try:
            u = 'https://geosearch.planninglabs.nyc/v2/search?' + urllib.parse.urlencode({'text': '%s, Brooklyn, NY %s' % (re.sub(r'\s*#+\s*', ' ', addr), zip_), 'size': 1})
            ft = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'bkcb6.app directory'}), timeout=30).read())['features']
            GEO[k] = ft[0]['geometry']['coordinates'][::-1] if ft else None
        except Exception: GEO[k] = None
    return GEO[k]
SMALL = {'of', 'and', 'the', 'for', 'at', 'in', 'on', 'a', 'de', 'la', 'el', 'by'}
def tc(s):
    s = re.sub(r'\s+', ' ', re.sub(r'\s*#+\s*', ' ', s or '')).strip()
    if s != s.upper(): return s
    out = []
    for i, w in enumerate(s.split(' ')):
        lw = w.lower()
        if re.fullmatch(r'(llc|inc|nyc|ny|bbq|ii|iii|iv|usa|cvs|bk|dba|j\.?t\.?c\.?)\.?,?', lw): out.append(w.upper() if lw.rstrip('.,') not in ('inc',) else 'Inc.')
        elif i and lw in SMALL: out.append(lw)
        else: out.append(re.sub(r"(^|[-/(.&+])([a-z])", lambda m: m.group(1) + m.group(2).upper(), lw))
    return ' '.join(out).replace("'S", "'s").replace("’S", "’s")
def addr_tc(a): return re.sub(r'\b(\d+)(St|Nd|Rd|Th)\b', lambda m: m.group(1) + m.group(2).lower(), tc(a))
R = A.rows(); got, miss = A.match(R, D['profiles'])
BY = {p['slug']: p for p in D['profiles']}
# cuisines onto the restaurants that are there
n_c = 0
for r in R:
    if r['src'] == 'restaurants' and r['id'] in got and r.get('cuisine') and r['cuisine'] != 'Other':
        p = BY[got[r['id']]]
        p['cuisine'] = r['cuisine']; p['kv'] = [kv for kv in p.get('kv', []) if kv[0] != 'Cuisine'] + [['Cuisine', r['cuisine']]]; n_c += 1
# state records: on the district's side of its boundary streets?
keep = []; out_of = 0
for r in miss:
    if r['src'] in ('agmarkets', 'sla', 'npi', 'salons', 'fdic', 'irs'):
        g = geo(r['addr'], r['zip'])
        if g: r['lat'], r['lng'] = g
        if not (r.get('lat') and POLY.contains(Point(r['lng'], r['lat']))): out_of += 1; continue
    elif not r.get('lat'):
        g = geo(r['addr'], r['zip'])
        if g: r['lat'], r['lng'] = g
    keep.append(r)
json.dump(GEO, open(GEO_F, 'w'), indent=0)
# one business, one profile
import directory_dedupe as dd
cl = []
for r in keep:
    k = dd._ak({'addr': r['addr']})
    for c in cl:
        if k and c['k'] == k and max(A.sim(r['name'], x['name']) for x in c['rows']) >= .62: c['rows'].append(r); break
    else: cl.append({'k': k, 'rows': [r]})
SLA_TOPIC = {'Restaurant': 'Restaurants, cafes and food', 'Food & Beverage Business': 'Restaurants, cafes and food', 'Additional Bar': 'Restaurants, cafes and food', 'Club': 'Restaurants, cafes and food',
             'Catering Establishment': 'Restaurants, cafes and food', 'Liquor Store': 'Stores', 'Wine Store': 'Stores', 'Hotel': 'Hotels and tourism', 'Drug Store': 'Health and medical'}
DCWP_TOPIC = {'Home Improvement Contractor': 'Trades, workshops and industrial', 'Garage & Parking Lot': 'Auto and transportation', 'Tow Truck Company': 'Auto and transportation',
              'Secondhand Dealer - Auto': 'Auto and transportation', 'Car Wash': 'Auto and transportation', 'Hotel': 'Hotels and tourism', 'Scrap Metal Processor': 'Trades, workshops and industrial',
              'Construction Labor Provider': 'Trades, workshops and industrial', 'Self-Storage Facility': 'Services and offices', 'Storage Warehouse': 'Services and offices',
              'Process Serving Agency': 'Services and offices', 'Scale Dealer/Repairer': 'Services and offices'}
SRCNAME = {'npi': 'National Provider Identifier registry (CMS)', 'salons': 'NYS Department of State licenses', 'fdic': 'FDIC bank branch list', 'irs': 'IRS list of nonprofits', 'restaurants': 'NYC Health Department restaurant inspections', 'dcwp': 'NYC Department of Consumer and Worker Protection licenses',
           'agmarkets': 'NYS Agriculture and Markets retail food stores', 'sla': 'NYS Liquor Authority licenses'}
def topic(rows, name):
    srcs = {r['src'] for r in rows}
    if 'npi' in srcs: return 'Health and medical'
    if 'salons' in srcs: return 'Hair, beauty and personal care'
    if 'fdic' in srcs: return 'Services and offices'
    if srcs == {'irs'}: return 'Nonprofits'
    if SUPERMARKET.search(name): return 'Supermarkets'
    if 'restaurants' in srcs: return 'Restaurants, cafes and food'
    for r in rows:
        if r['src'] == 'sla' and r.get('cat') in SLA_TOPIC: return SLA_TOPIC[r['cat']]
    if 'agmarkets' in srcs or any(r['src'] == 'sla' and r.get('cat') == 'Grocery Store' for r in rows) or any(r.get('cat') in ('Tobacco Retail Dealer', 'Electronic Cigarette Dealer', 'Stoop Line Stand') for r in rows):
        if SMOKE.search(name): return 'Smoke, vape and cannabis shops'
        return 'Delis and bodegas' if DELI.search(name) else 'Groceries and food stores'
    for r in rows:
        if r['src'] == 'dcwp': return DCWP_TOPIC.get(r.get('cat'), 'Stores')
    return 'Trades, workshops and industrial' if 'sla' in srcs else 'Other businesses'
made = collections.Counter()
for c in cl:
    rows = c['rows']; first = sorted(rows, key=lambda r: ['restaurants', 'sla', 'agmarkets', 'dcwp', 'fdic', 'salons', 'npi', 'irs'].index(r['src']))[0]
    name = tc(re.sub(r'\s+\d{4,}$', '', first['name'])); addr = addr_tc(first['addr']); zip_ = first.get('zip') or ''
    t = topic(rows, name); lat = next((r['lat'] for r in rows if r.get('lat')), None); lng = next((r['lng'] for r in rows if r.get('lng')), None)
    cuisine = next((r['cuisine'] for r in rows if r.get('cuisine') and r['cuisine'] != 'Other'), '')
    ph = re.sub(r'\D', '', next((r.get('phone') for r in rows if r.get('phone')), '') or ''); phone = '(%s) %s-%s' % (ph[:3], ph[3:6], ph[6:]) if len(ph) == 10 else ''
    kv = [['Category', t]] + ([['Cuisine', cuisine]] if cuisine else []) + [['Address', '%s, Brooklyn %s' % (addr, zip_)], ['Community board', 'Brooklyn Community Board 6']]
    for r in rows:
        if r['src'] == 'restaurants': kv.append(['Health Department record', 'Restaurant permit %s' % r['id'][6:] + ('. On the register, not yet inspected.' if r.get('last', '').startswith('1900') else '. Last inspected %s.' % r['last'][:10])])
        if r['src'] == 'dcwp': kv.append(['City license', '%s, %s' % (r['cat'], r['id'][5:])])
        if r['src'] == 'sla': kv.append(['Liquor license', '%s, %s%s' % (r['cat'], r['id'][4:], ', expires %s' % r['expires'][:10] if r.get('expires') else '')])
        if r['src'] == 'npi': kv.append(['Health practice', '%sNPI %s' % (r['cat'] + ', ' if r.get('cat') else '', r['id'][4:])])
        if r['src'] == 'salons': kv.append(['State license', '%s, %s%s' % (r['cat'], r['id'][4:], ', expires %s' % r['expires'][:10] if r.get('expires') else '')])
        if r['src'] == 'fdic': kv.append(['Bank branch', '%s (FDIC)' % tc(r.get('branch') or '')])
        if r['src'] == 'irs': kv.append(['Nonprofit', 'EIN %s%s' % (r['id'][4:], ', a church' if r.get('church') else '')])
        if r['src'] == 'agmarkets': kv.append(['Food store license', 'NYS Agriculture and Markets, %s' % r['id'][3:]])
        if r.get('alt') and A.nn(r['alt']) != A.nn(first['name']) and ['Legal name', tc(r['alt'])] not in kv: kv.append(['Legal name', tc(r['alt'])])
    kv.append(['Source', '; '.join(sorted({SRCNAME[r['src']] for r in rows}))])
    what = {'Restaurants, cafes and food': 'a restaurant, cafe or bar', 'Supermarkets': 'a supermarket', 'Delis and bodegas': 'a deli or bodega', 'Groceries and food stores': 'a food store',
            'Trades, workshops and industrial': 'a trades business', 'Auto and transportation': 'an auto and transportation business', 'Hotels and tourism': 'a hotel',
            'Stores': 'a store', 'Services and offices': 'a services business', 'Smoke, vape and cannabis shops': 'a smoke or vape shop', 'Health and medical': 'a health practice' if any(r['src'] == 'npi' for r in rows) else 'a pharmacy',
            'Hair, beauty and personal care': 'a salon or barber shop', 'Nonprofits': 'a nonprofit'}.get(t, 'a business')
    if any(r['src'] == 'fdic' for r in rows): what = 'a bank branch'
    intro = ['%s is %s at %s in Brooklyn Community District 6.' % (name, what, addr)]
    slug = 'reg-' + hashlib.md5('|'.join(sorted(r['id'] for r in rows)).encode()).hexdigest()[:10]
    p = {'slug': slug, 'type': slug, 'kind': 'org', 'official': '', 'name': name, 'seat': '%s · Brooklyn' % t.split(',')[0], 'desc': intro[0], 'lat': lat, 'lng': lng,
         'addr': addr, 'zip': zip_, 'addr_note': '', 'phone': phone, 'email': '', 'web': '', 'weburl': '', 'since': '', 'intro': intro, 'does': [], 'kv': kv, 'links': [], 'logo': '',
         'cal': None, 'n': 0, 'going': [], 'group': 'Schools, parks and facilities' if t == 'Nonprofits' else 'Local businesses', 'topic': t, 'sort': 0, 'registers': sorted(r['id'] for r in rows)}
    if cuisine: p['cuisine'] = cuisine
    D['profiles'].append(p); made[t] += 1
# each new business's page on the site (/biz/<name-and-address>.html, the Directory's business page)
import importlib.util as _iu
_sp = _iu.spec_from_file_location('bsp', P('scripts/biz_site_profiles.py')); BSP = _iu.module_from_spec(_sp); _sp.loader.exec_module(BSP)
os.chdir(ROOT)
OLD_F = P('data/cb6-audit/reg-pages.json'); OLD = json.load(open(OLD_F)) if os.path.exists(OLD_F) else {}
for u in OLD.values():
    if os.path.exists(u[1:]): os.remove(u[1:])
pages = {}
for p in D['profiles']:
    if not p['slug'].startswith('reg-'): continue
    s_ = BSP.slugify(p['name'] + ' ' + (p.get('addr') or '')); k_ = 2; base = s_
    while os.path.exists('biz/%s.html' % s_) or '/biz/%s.html' % s_ in pages.values(): s_ = '%s-%d' % (base, k_); k_ += 1
    path = '/biz/%s.html' % s_
    open(path[1:], 'w').write(BSP.page(p, None, path)); pages[p['slug']] = path
    p['links'] = [['Profile and map', 'https://bkcb6.app' + path]]
json.dump(pages, open(OLD_F, 'w'), indent=0)
for g in D['groups']:
    if g['name'] == 'Schools, parks and facilities' and 'Nonprofits' not in g['topics']: g['topics'].append('Nonprofits')
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('cuisine set on restaurants already there:', n_c)
print('register records with no profile:', len(miss), '| outside the district on the city address points:', out_of, '| profiles made:', sum(made.values()), dict(made))
