#!/usr/bin/env python3
"""Profiles for Brooklyn's police precincts and community school districts, the same kind of profile every
community organization has: a page on bkcb6.app built by build_org_pages.py (from data/gov-profiles.json) and a
profile the apps open (the site page, through app/data/civic/profile-index.json). The 76th and 78th Precincts
already have hand-written profiles and are left as they are.

Sources: data/precinct-directory.json (NYPD precinct pages: commander, address, phones, description),
data/school-districts.json (each Brooklyn district office's address and phones, from insideschools.org),
data/police-precincts-lite.geojson, data/school-districts-brooklyn.geojson and cd-boundaries-simple.geojson
(which community districts each one covers), NYC Planning GeoSearch (the office's location).

Rerunnable: its own entries (marked "from": "district_profiles") are replaced. Then run build_org_pages.py and
scripts/one_profile.py."""
import json, os, re, shutil, time, urllib.parse, urllib.request
from PIL import Image
from shapely.geometry import shape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
J = lambda p: json.load(open(p, encoding='utf-8'))
GEO_CACHE = 'data/district-profiles-geo.json'
geo = J(GEO_CACHE) if os.path.exists(GEO_CACHE) else {}


def geocode(addr):
    if addr in geo: return geo[addr]
    u = 'https://geosearch.planninglabs.nyc/v2/search?size=1&text=' + urllib.parse.quote(addr)
    f = json.load(urllib.request.urlopen(u, timeout=20))['features'][0]
    lng, lat = f['geometry']['coordinates']
    geo[addr] = [round(lat, 6), round(lng, 6)]
    time.sleep(0.15)
    return geo[addr]


def ordinal(n):
    return '%d%s' % (n, 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'))


def digits(p): return re.sub(r'\D', '', p)


def plain(s): return re.sub(r'<[^>]+>', '', s).replace('&middot;', '·').replace('&amp;', '&')


# community districts each area covers, by land area
cds = [(shape(f['geometry']), f['properties']) for f in J('cd-boundaries-simple.geojson')['features'] if f['properties']['cd'].startswith('3')]


def covers(g):
    out = []
    for s, p in cds:
        a = g.intersection(s).area / g.area
        if a >= 0.01: out.append((int(p['cd'][1:]), round(a * 100)))
    return sorted(out, key=lambda x: -x[1])


def cd_links(cov):
    return ', '.join('<a href="/cb-bk-%d.html">BKCB%d</a>' % (n, n) for n, _ in cov)


def cd_text(cov):
    return ', '.join('BKCB%d (%d%%)' % (n, a) for n, a in cov)


NYPD = {"dark": "#142b43", "mid": "#428cd7", "light": "#bad1e8", "wash": "#f0f5fa", "accent": "#256bb1", "ink": "#1b4c7e"}
SCHOOL = {"dark": "#141443", "mid": "#4242d7", "light": "#babae8", "wash": "#f0f0fa", "accent": "#2525b1", "ink": "#1b1b7e"}
PH = [('community', 'Community Affairs'), ('prevention', 'Crime Prevention'), ('dv', 'Domestic Violence Squad'),
      ('youth', 'Youth Coordination Officers'), ('aux', 'Auxiliary'), ('squad', 'Detective Squad')]
HAND = {76, 78}  # hand-written profiles already

layers = {l['k']: l for l in J('bkcompplan/layers.json')}
pct_geo = {int(f['properties']['precinct']): shape(f['geometry']) for f in J('data/police-precincts-lite.geojson')['features']}
csd_geo = {int(f['properties']['schooldist']): shape(f['geometry']) for f in J('data/school-districts-brooklyn.geojson')['features']}
pdir = J('data/precinct-directory.json')
sdir = J('data/school-districts.json')

recs = []  # (site record, app record)

for f in layers['precinct']['f']:
    n = f['n']
    if n in HAND: continue
    d = pdir[str(n)]
    name = '%s Precinct' % ordinal(n)
    slug = '%s-precinct' % ordinal(n)
    m = re.match(r'^(.*?)\s+Brooklyn, NY,? (\d{5})', d['addr'])
    street, zipc = m.group(1), m.group(2)
    if street == '2575 Coney Island': street += ' Avenue'  # NYPD's page drops the word
    lat, lng = geocode('%s, Brooklyn, NY %s' % (street, zipc))
    cov = covers(pct_geo[n])
    # NYPD's page has no description for some precincts; then the intro says where the precinct sits
    hood = re.sub(r'^The %s Precinct ' % ordinal(n), '', d['desc']) if d.get('desc') else 'sits in %s, by land area.' % cd_text(cov)
    calls = ' '.join('%s: %s.' % (lab, d['ph'][k].replace('(', '').replace(') ', '-')) for k, lab in PH if d['ph'].get(k))
    main = d['ph'].get('main', '').replace('(', '').replace(') ', '-')
    kv = [['Commanding officer', d['co']], ['Community districts', cd_links(cov)]]
    site = {
        'slug': slug, 'unsigned': True, 'from': 'district_profiles', 'name': name,
        'seat': 'NYPD precinct &middot; Brooklyn', 'title': name,
        'desc': '%s, NYPD precinct · Brooklyn. %s' % (name, d.get('desc') or 'The %s %s' % (name, hood)),
        'lat': '%.6f' % lat, 'lng': '%.6f' % lng, 'addr': street, 'zip': zipc, 'addr_note': '', 'cityline': '',
        'phone': main, 'tel': digits(main), 'email': '', 'web': 'nyc.gov/nypd', 'weburl': d['url'], 'since': '',
        'intro': ['The <b>%s</b> %s' % (name, hood)],
        'does_title': 'Reaching the %s' % name, 'does': [calls],
        'kv': kv, 'brand': NYPD, 'does_btns': [['Crime and safety in the precinct', '/precinct/%d/' % n, False]],
        'links': [['Precinct page', d['url'], True]] + ([['@' + d['x'], 'https://x.com/' + d['x'], True]] if d.get('x') else []) +
                 [['Crime and safety in the precinct', '/precinct/%d/' % n, False], ['Search an address', '/citywide-search.html', False]],
        'area': {'chamber': 'precinct', 'district': str(n), 'noun': 'precinct', 'caption': 'the station house and the %s Precinct' % ordinal(n)},
        'logo_src': 'elected/precinct/%d.png' % n,
    }
    recs.append(site)

for f in layers['school']['f']:
    n = f['n']
    d = sdir[str(n)]
    name = 'Community School District %d' % n
    slug = 'school-district-%d' % n
    lat, lng = geocode('%s, Brooklyn, NY %s' % (d['addr'], d['zip']))
    g = csd_geo[n]
    cov = covers(g)
    main = d['phones'][0][1]
    kv = [['Community districts', cd_links(cov)]]
    site = {
        'slug': slug, 'unsigned': True, 'from': 'district_profiles', 'name': name,
        'seat': 'NYC Public Schools &middot; Brooklyn', 'title': name,
        'desc': '%s, NYC Public Schools · Brooklyn. It reaches into %s.' % (name, cd_text(cov)),
        'lat': '%.6f' % lat, 'lng': '%.6f' % lng, 'addr': d['addr'], 'zip': d['zip'], 'addr_note': d.get('room', ''), 'cityline': '',
        'phone': main, 'tel': digits(main), 'email': d.get('email', ''), 'web': re.sub(r'^https?://(www\.)?', '', d['web']).rstrip('/') if d.get('web') else '',
        'weburl': d.get('web', ''), 'since': '',
        'intro': ['<b>%s</b> is one of the 32 community school districts of NYC Public Schools, for the public elementary and middle schools in its area. It reaches into %s.' % (name, cd_text(cov))],
        'does_title': 'Reaching %s' % name, 'does': [' '.join('%s: %s.' % (k, v) for k, v in d['phones'])],
        'kv': kv, 'brand': SCHOOL, 'does_btns': [['Schools and childcare in the district', '/eduhub-csd-%d.html' % n, False]],
        'links': ([['District website', d['web'], True]] if d.get('web') else []) +
                 [['Schools and childcare in the district', '/eduhub-csd-%d.html' % n, False], ['Search an address', '/citywide-search.html', False]],
        'area': {'chamber': 'school', 'district': str(n), 'noun': 'district', 'caption': 'the district office and School District %d' % n},
        'logo_src': 'elected/school/%d.png' % n,
    }
    recs.append(site)

json.dump(geo, open(GEO_CACHE, 'w'), indent=0, sort_keys=True)

# logos: the site's 200 px icon and the apps' org logo
for r in recs:
    im = Image.open(r.pop('logo_src')).convert('RGBA')
    im.thumbnail((200, 200), Image.LANCZOS)
    im.save('site-icons/%s.png' % r['slug'], optimize=True)

# the site's records
gp = [r for r in J('data/gov-profiles.json') if r.get('from') != 'district_profiles']
json.dump(gp + recs, open('data/gov-profiles.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0); open('data/gov-profiles.json', 'a').write('\n')

# the apps open these as the site page (its map is the precinct's or the district's own boundary, which the apps'
# native profile map cannot draw): scripts/one_profile.py points their links at web:<slug>/index.html?app=1.
# No native copies in the Organizations tab, so there is one profile, not two.
P = 'app/data/civic/orgs/orgs-profiles.json'
op = J(P)
n0 = len(op['profiles'])
op['profiles'] = [p for p in op['profiles'] if p.get('from') != 'district_profiles']
if len(op['profiles']) != n0: json.dump(op, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for r in recs: os.path.exists('app/data/civic/orgs/logos/%s.png' % r['slug']) and os.remove('app/data/civic/orgs/logos/%s.png' % r['slug'])
print(len(recs), 'profiles:', ', '.join(r['slug'] for r in recs))
