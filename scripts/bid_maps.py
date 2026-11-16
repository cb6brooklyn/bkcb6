#!/usr/bin/env python3
"""A map and directory page for each business improvement district in CB6, built like the proposed Gowanus BID's page
(/gowanusbid/, which is the template): the district's boundary on the map, every business listing inside it by category
with its logo or an icon for what it is, and every property and lot inside it.

  /parkslopefifthavebid/   Park Slope 5th Avenue BID (2008)
  /northflatbushbid/       North Flatbush BID (1986)
  /atlanticavebid/         Atlantic Avenue BID (2011)

Boundaries: the city's BID file (NYC SBS), exported Nov 16, 2026 (data/bids/<slug>-boundary.geojson); these three are the
only BIDs that reach into Community District 6.
Businesses: the Directory's entries (profiles/dir.json, one per business after directory_dedupe.py) inside the boundary,
each linked to its profile page. The parts of each BID outside District 6 are filled from the official registers by
bid_audit.py and bid_register_profiles.py; the Park Slope Fifth Avenue BID's own directory is in the Directory the same way.
Properties: every tax lot inside the boundary, from PLUTO (64uk-42ks), with its shape from MapPLUTO, and its storefronts, occupied or
vacant, from the city's storefront registry (92iy-9c3n).
Run after app_directory_tiles.py: python3 scripts/bid_maps.py"""
import json, os, re, sys, html, urllib.request, urllib.parse, time, collections
from shapely.geometry import shape, Point, mapping
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
sys.path.insert(0, P('scripts'))
os.chdir(ROOT)
import directory_grid as G
TOKEN = 'HvFoIfzodzpRML7a1104Ca2tM'
EDGE = 0.00022   # about 20 meters: a storefront's map point often sits in the street in front of its lot
BIDS = [
    {'slug': 'park-slope-5th-avenue', 'dir': 'parkslopefifthavebid', 'name': 'Park Slope Fifth Avenue BID', 'long': 'Park Slope Fifth Avenue Business Improvement District',
     'year': 2008, 'profile': '/bid-park-slope-5th-avenue/', 'logo': '/site-icons/bid-park-slope-fifth-ave.png', 'web': 'https://parkslopefifthavenuebid.com/', 'office': '157 13th Street, Brooklyn, NY 11215',
     'phone': '718-551-5545', 'email': 'info@parkslopefifthavenuebid.com', 'cbs': [6, 7],
     'where': 'Fifth Avenue from Dean Street to 18th Street', 'own': 'the BID\'s own business directory (parkslopefifthavenuebid.com, read Aug 27, 2026)'},
    {'slug': 'north-flatbush', 'dir': 'northflatbushbid', 'name': 'North Flatbush BID', 'long': 'North Flatbush Avenue Business Improvement District',
     'year': 1986, 'profile': '/bid-north-flatbush/', 'logo': '/site-icons/bid-north-flatbush.png', 'web': 'https://northflatbushbid.nyc/', 'office': '282 Flatbush Avenue, Brooklyn, NY 11217',
     'phone': '718-783-1685', 'email': 'info@northflatbushbid.nyc', 'cbs': [2, 6, 8], 'where': 'Flatbush Avenue from Atlantic Avenue to Grand Army Plaza', 'own': ''},
    {'slug': 'atlantic-avenue', 'dir': 'atlanticavebid', 'name': 'Atlantic Avenue BID', 'long': 'Atlantic Avenue Business Improvement District',
     'year': 2011, 'profile': '/bid-atlantic-avenue/', 'logo': '/site-icons/bid-atlantic-avenue.png', 'web': 'https://www.atlanticavebid.org/', 'office': '306 Atlantic Avenue, Brooklyn, NY 11201',
     'phone': '929-283-5989', 'email': 'info@atlanticavebid.org', 'cbs': [2, 6], 'where': 'Atlantic Avenue from Fourth Avenue to the Brooklyn-Queens Expressway', 'own': ''},
]
def get(u, data=None):
    for i in range(4):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, data=data, headers={'X-App-Token': TOKEN, 'User-Agent': 'bkcb6.app'}), timeout=180).read())
        except Exception:
            if i == 3: raise
            time.sleep(4)
def esc(s): return html.escape(str(s), quote=True)
def tc_(s): return re.sub(r'^No Business Activity Identified$', '', s.strip().capitalize()) if s else ''
TPL = open(P('gowanusbid/index.html'), encoding='utf-8').read()
# the Directory, one entry per business, and the profile behind each entry
DIR = json.load(open(P('profiles/dir.json')))
PROF = json.load(open(P('app/data/civic/orgs/orgs-profiles.json'), encoding='utf-8'))['profiles']
BYHREF = {}
for p in PROF:
    if p.get('group') not in ('Local businesses', 'Health', 'Food', 'Child care'): continue
    if p.get('topic') in ('Houses of worship', 'Pre-K site', 'Hospitals', 'Preschool for students with disabilities', 'Day camp'): continue
    h = G.site_page(p)
    if h: BYHREF.setdefault(h, p)
def logo(p):
    l = p.get('logo') or ''
    if not l or 'Logos/' in l: return ''
    f = os.path.normpath(os.path.join('app/data/civic/orgs/logos', l))
    return '/' + f if os.path.exists(f) else ''
TOPIC = {'Pharmacies': 'Health and medical', 'Supermarkets': 'Supermarkets', 'Preschool child care': 'Child care', 'Infants and toddlers': 'Child care'}
def kind(p):
    if p.get('cuisine'): return p['cuisine']
    for k, v in p.get('kv', []):
        if k == 'Kind': return v
    return {'Pharmacies': 'Pharmacy', 'Preschool child care': 'Childcare', 'Infants and toddlers': 'Childcare'}.get(p.get('topic'), '')
def nb(p):
    for k, v in p.get('kv', []):
        if k == 'Neighborhood': return v
    return ''
CAT_EXTRA = {'Restaurants, cafes and food': '🍽️', 'Supermarkets': '🛒', 'Delis and bodegas': '🥪', 'Groceries and food stores': '🛒', 'Stores': '🛍️', 'Smoke, vape and cannabis shops': '💨',
             'Markets': '🧺', 'Venues': '🎟️', 'Services and offices': '🏢', 'Trades, workshops and industrial': '🛠️', 'Child care': '🧸', 'Fitness and recreation': '🏋️'}
LUN = {'01': 'One & Two Family', '02': 'Multi-Family Walkup', '03': 'Multi-Family Elevator', '04': 'Mixed Residential/Commercial', '05': 'Commercial/Office', '06': 'Industrial/Manufacturing',
       '07': 'Transportation/Utility', '08': 'Public Facilities/Institutions', '09': 'Parks/Open Space', '10': 'Parking', '11': 'Vacant Land'}
def lots(g):
    x0, y0, x1, y1 = g.bounds
    pl = get('https://data.cityofnewyork.us/resource/64uk-42ks.json?' + urllib.parse.urlencode({'$where': "borough='BK' AND latitude between %f and %f AND longitude between %f and %f" % (y0 - .002, y1 + .002, x0 - .002, x1 + .002), '$limit': 50000}))
    gb = g.buffer(0.00002)
    pl = [r for r in pl if r.get('latitude') and gb.contains(Point(float(r['longitude']), float(r['latitude'])))]
    shp = {}
    bbls = ['%d' % int(float(r['bbl'])) for r in pl]
    for i in range(0, len(bbls), 150):
        part = bbls[i:i + 150]
        data = urllib.parse.urlencode({'where': 'BBL in (%s)' % ','.join(part), 'outFields': 'BBL', 'outSR': 4326, 'f': 'geojson', 'geometryPrecision': 6}).encode()
        for f in get('https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/MAPPLUTO/FeatureServer/0/query', data)['features']:
            shp['%d' % int(float(f['properties']['BBL']))] = f['geometry']
    out = []
    for r in pl:
        b = '%d' % int(float(r['bbl'])); gm = shp.get(b); rings = None
        if gm:
            polys = gm['coordinates'] if gm['type'] == 'MultiPolygon' else [gm['coordinates']]
            rings = [[[[round(y, 6), round(x, 6)] for x, y in poly[0]]] for poly in polys]
        z = r.get('zonedist1', '') + ('/' + r['zonedist2'] if r.get('zonedist2') else '')
        lu = LUN.get((r.get('landuse') or '').zfill(2), 'No land use on file') if r.get('landuse') else 'No land use on file'
        n = lambda k: int(float(r[k])) if r.get(k) not in (None, '') else 0
        out.append([r.get('address', ''), b, lu, z, r.get('ownername', ''), n('yearbuilt'), round(float(r['numfloors']), 1) if r.get('numfloors') else 0, n('unitsres'), n('lotarea'),
                    round(float(r['latitude']), 6), round(float(r['longitude']), 6), rings])
    # the city's storefront registry (Local Law 157): each ground and second floor storefront, occupied or vacant, by its latest filing
    SF = collections.defaultdict(list)
    for i in range(0, len(bbls), 200):
        for r in get('https://data.cityofnewyork.us/resource/92iy-9c3n.json?' + urllib.parse.urlencode({'$where': 'bbl in(%s)' % ','.join("'%s'" % b for b in bbls[i:i + 200]), '$limit': 50000})):
            SF[r['bbl']].append(r)
    for l in out:
        rs = SF.get(l[1])
        if not rs: l.append(''); continue
        yr = max(r['reporting_year'] for r in rs); cur = [r for r in rs if r['reporting_year'] == yr]
        occ = collections.Counter(tc_(r.get('primary_business_activity', '')) for r in cur if r.get('vacant_on_12_31') == 'NO')
        vac = sum(1 for r in cur if r.get('vacant_on_12_31') == 'YES')
        parts = ['%s in use%s' % (('%d storefronts' % sum(occ.values())) if sum(occ.values()) > 1 else 'Storefront', ' (%s)' % ', '.join(occ) if occ and any(occ) else '')] if occ else []
        if vac: parts.append('%s vacant' % ('%d storefronts' % vac if vac > 1 else 'storefront' if occ else 'Storefront'))
        l.append('%s, as the owner reported to the city for %s' % ('; '.join(parts), yr))
    out.sort(key=lambda l: (re.sub(r'^[\d\-]+\s+', '', l[0] or 'zzz'), int(re.match(r'\d*', l[0] or '').group() or 0)))
    return out
CD6 = shape(json.load(open(P('data/cb6-audit/cd306.geojson'))))
for B in BIDS:
    g = shape(json.load(open(P('data/bids/%s-boundary.geojson' % B['slug'])))['features'][0]['geometry'])
    near = g.buffer(EDGE); close = g.buffer(0.00012)
    MAIN = {'park-slope-5th-avenue': r'\b(5th|fifth|5)\s+av', 'north-flatbush': r'flatbush', 'atlantic-avenue': r'atlantic'}[B['slug']]
    rows, seen = [], set()
    for e in DIR['E']:
        if e[1] not in BYHREF or e[1] in seen: continue
        pt = Point(e[12], e[11])
        if not near.contains(pt): continue
        if not close.contains(pt) and not re.search(MAIN, BYHREF[e[1]].get('addr') or '', re.I): continue   # past the lot line: only a storefront on the BID's own avenue
        p = BYHREF[e[1]]; seen.add(e[1])
        t = TOPIC.get(p.get('topic'), p.get('topic') or 'Other businesses')
        rows.append([e[0], t, kind(p), p.get('addr') or '', e[11], e[12], p.get('weburl') or '', e[1], logo(p), 0, nb(p)])
    rows.sort(key=lambda r: (r[1], r[0].lower()))
    L = lots(g)
    polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
    ring = [[[[round(y, 6), round(x, 6)] for x, y in poly.exterior.coords]] for poly in polys]
    cbs = ', '.join('%d' % c for c in B['cbs'][:-1]) + ' and %d' % B['cbs'][-1]
    s = TPL
    s = s.replace('<meta name="robots" content="noindex,nofollow">\n', '')
    s = re.sub(r'<title>.*?</title>', '<title>%s: map, businesses and properties</title>' % esc(B['name']), s)
    s = re.sub(r'<header>.*?</header>', '<header><div class="hb"><img class="hlogo" src="%s" alt="%s logo"><div><div class="k">Business improvement district · Established %d</div><h1>%s</h1></div></div><p>%s. The boundary, every business listing and every property inside it.</p>'
               '<p class="hl"><a href="%s">BID profile</a> · <a href="%s" target="_blank" rel="noopener">Their website</a> · %s · <a href="tel:%s">%s</a> · <a href="mailto:%s">%s</a></p></header>'
               % (B['logo'], esc(B['name']), B['year'], esc(B['long']), esc(B['where']), B['profile'], B['web'], esc(B['office']), B['phone'], B['phone'], B['email'], B['email']), s, flags=re.S)
    s = s.replace('header p{margin:6px 0 0;font-size:.9rem;opacity:.9}', 'header p{margin:6px 0 0;font-size:.9rem;opacity:.9}\nheader .hl{font-size:.8rem;line-height:1.6}header .hl a{color:#fff}\n.hb{display:flex;gap:14px;align-items:center}.hlogo{flex:0 0 84px;width:84px;height:84px;object-fit:contain;background:#fff;border-radius:12px;padding:6px}')
    s = s.replace('<button class="pill on" id="th">New housing on the map</button>', '')
    s = s.replace('<button class="tab" data-t="h">New housing</button>', '')
    src = ('Boundary: the city\'s file of business improvement districts (NYC Department of Small Business Services), Nov 16, 2026. The district spans Community Boards %s. '
           'Businesses: the bkcb6.app Directory, which draws on NYC Health Department restaurant inspections, NYC Department of Consumer and Worker Protection licenses, '
           'New York State food store, liquor and salon licenses, the federal health provider and bank branch registers, and OpenStreetMap (read Nov 16, 2026)%s. '
           'Properties: every tax lot inside the boundary, from the Department of City Planning\'s PLUTO file, with its storefronts, occupied or vacant, from the city\'s storefront registry.' % (cbs, ', and ' + B['own'] if B['own'] else ''))
    s = re.sub(r'<p class="src">.*?</p>', '<p class="src">%s</p>' % esc(src), s, flags=re.S)
    s = re.sub(r'var RING=\[.*?\];\n', 'var RING=%s;\n' % json.dumps(ring, separators=(',', ':')), s, flags=re.S)
    s = re.sub(r'var ROWS=\[.*?\];\n', lambda m: 'var ROWS=%s;\n' % json.dumps(rows, ensure_ascii=False, separators=(',', ':')), s, flags=re.S)
    s = re.sub(r'var LOTS=\[.*?\];\n', lambda m: 'var LOTS=%s;\n' % json.dumps(L, ensure_ascii=False, separators=(',', ':')), s, flags=re.S)
    s = re.sub(r'var HOUSING=\[.*?\];\n', 'var HOUSING=[];\n', s, flags=re.S)
    s = s.replace("(l[8]?'<div>Lot area '", "(l[12]?'<div>'+esc(l[12])+'</div>':'')+(l[8]?'<div>Lot area '", 1)
    assert "l[12]?'<div>'" in s
    s = s.replace("var CAT={", "var CAT=" + json.dumps(CAT_EXTRA, ensure_ascii=False)[:-1] + ",", 1)
    s = s.replace("function icon(r){return r[8]?'<img src=\"/app/data/civic/business/logos/'+esc(r[8])+'.png\" alt=\"\" loading=\"lazy\">':glyph(r)}",
                  "function icon(r){return r[8]?'<img src=\"'+esc(r[8])+'\" alt=\"\" loading=\"lazy\">':glyph(r)}")
    assert "esc(r[8])+'\" alt" in s
    s = s.replace("document.getElementById('th').addEventListener", "if(document.getElementById('th'))document.getElementById('th').addEventListener")
    os.makedirs(P(B['dir']), exist_ok=True)
    open(P(B['dir'], 'index.html'), 'w', encoding='utf-8').write(s)
    inn = sum(1 for r in rows if CD6.contains(Point(r[5], r[4])))
    print('%-28s businesses %4d (in District 6: %d) | lots %4d (with shapes %d)' % (B['name'], len(rows), inn, len(L), sum(1 for l in L if l[11])))

# a link to each map from the BID's profile pages on the site and its profile in the apps
LINKS = {'parkslopefifthavebid': (['bid-park-slope-5th-avenue', 'park-slope-fifth-avenue-bid'], ['cbo-park-slope-fifth-avenue-district-management-association']),
         'northflatbushbid': (['bid-north-flatbush'], ['north-flatbush-bid']), 'atlanticavebid': (['bid-atlantic-avenue'], ['atlantic-avenue-bid'])}
LBL = 'Map of every business and property in the BID'
for d, (pages, profs) in LINKS.items():
    for pg in pages:
        f = P(pg, 'index.html'); s = open(f, encoding='utf-8').read()
        s = re.sub(r'<!--bidmap-->.*?<!--/bidmap-->', '', s, flags=re.S)
        a = ('<!--bidmap--><a href="/%s/" style="display:block;margin:12px 0 4px;padding:12px 14px;border-radius:12px;background:#06024D;color:#fff;font:700 .95rem \'DM Sans\',sans-serif;'
             'text-decoration:none">&#128506;&#65039; %s &rarr;</a><!--/bidmap-->' % (d, LBL))
        m = re.search(r'<div class="pseat">.*?</div>\s*</span>\s*</div>', s, flags=re.S)
        s = s[:m.end()] + a + s[m.end():]
        open(f, 'w', encoding='utf-8').write(s)
    pf = P('app/data/civic/orgs/orgs-profiles.json'); DD = json.load(open(pf, encoding='utf-8'))
    for p in DD['profiles']:
        if p['slug'] in profs:
            p['links'] = [['Map of businesses and properties', 'https://bkcb6.app/%s/' % d]] + [l for l in p.get('links', []) if l[0] != 'Map of businesses and properties']
    open(pf, 'w', encoding='utf-8').write(json.dumps(DD, ensure_ascii=False, indent=1) + '\n')
print('linked from the BID profile pages and app profiles')
