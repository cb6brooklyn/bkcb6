#!/usr/bin/env python3
"""The proposed Gowanus BID's map page (/gowanusbid/): its boundary, and the business and property lists inside it.

Boundary: the Gowanus BID Formation Steering Committee's draft boundary, traced from the committee's own map
("Future Public Realm Map", gowanusimprovementdistrict.org home page, and page 8 of its 2026 Outreach Deck,
gowanusimprovementdistrict.org/s/2026-Gowanus-BID-Outreach-Deck.pdf). The committee publishes the boundary only as a
picture. PX below is the boundary line's corners in that picture's pixels (2500 px wide copy); CP ties 16 street corners
in the picture to their coordinates from the city's Geoclient, which places the picture within 6 meters. Corners of the
boundary that are street corners take the Geoclient coordinate itself. Written to data/bids/gowanus-proposed-boundary.geojson.

Businesses: the listings already on this page and on the Gowanus rezoning map (both cleaned of closed, moved and duplicate
listings on Nov 17, 2026) that fall inside the boundary, plus the bkcb6.app business directory
(app/data/civic/business/business-cb6.json) for the parts of the boundary neither page covered.
Properties: every tax lot inside the boundary, from PLUTO (64uk-42ks), with its shape from MapPLUTO.
New housing is left as it is (the new buildings of the rezoning area).
Named sites: the six places the committee's map labels (Heyward Park, CSO Tank Site, Thomas Greene Park, Gowanus Green,
CSO Tank Site + Salt Lot, Transit Plaza), drawn from the city's park properties and tax lots under each label.
Run: python3 scripts/gowanus_bid_map.py     then scripts/bid_maps.py and scripts/cb6_map.py are unaffected (they only
read this page as their template)."""
import json, os, re, html, math, urllib.request, urllib.parse, time
import numpy as np
from shapely.geometry import Polygon, Point, mapping
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
TOKEN = 'HvFoIfzodzpRML7a1104Ca2tM'; GEOKEY = 'b913bdfb9c47466589d0f08c99c75b21'
PAGE = 'gowanusbid/index.html'; OUT = 'data/bids/gowanus-proposed-boundary.geojson'

def get(u, data=None, hdr=None):
    for i in range(4):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, data=data, headers=hdr or {'X-App-Token': TOKEN, 'User-Agent': 'bkcb6.app'}), timeout=180).read())
        except Exception:
            if i == 3: raise
            time.sleep(4)
def corner(a, b):
    d = get('https://api.nyc.gov/geoclient/v2/intersection.json?' + urllib.parse.urlencode({'crossStreetOne': a, 'crossStreetTwo': b, 'borough': 'Brooklyn'}),
            hdr={'Ocp-Apim-Subscription-Key': GEOKEY})['intersection']
    return float(d['latitude']), float(d['longitude'])

# street corners that tie the committee's picture to the ground: (street, cross street, x, y) in the picture
CP = [('Hoyt Street', 'Wyckoff Street', 518, 521), ('Bond Street', 'Wyckoff Street', 886, 521), ('Nevins Street', 'Wyckoff Street', 1268, 519),
      ('4 Avenue', 'St Marks Place', 2016, 516), ('Hoyt Street', 'Douglass Street', 518, 1090), ('Bond Street', 'Douglass Street', 884, 1090),
      ('Bond Street', 'Carroll Street', 887, 1814), ('4 Avenue', 'Carroll Street', 2012, 1814), ('Bond Street', '3 Street', 850, 2233),
      ('Hoyt Street', '3 Street', 514, 2204), ('Hoyt Street', '5 Street', 512, 2492), ('Smith Street', '5 Street', 171, 2458),
      ('Smith Street', '9 Street', 243, 3042), ('3 Avenue', '3 Street', 1564, 2306), ('4 Avenue', '3 Street', 1973, 2345), ('Bond Street', 'Warren Street', 886, 671)]
# the boundary line, clockwise from Hoyt and Wyckoff: (x, y, street corner or None)
PX = [(518, 521, ('Hoyt Street', 'Wyckoff Street')), (886, 521, ('Bond Street', 'Wyckoff Street')), (886, 671, ('Bond Street', 'Warren Street')),
      (977, 671, None), (977, 734, None), (1266, 734, None),                      # Warren Street part way to Nevins, then the rear lot line to Nevins
      (1268, 519, ('Nevins Street', 'Wyckoff Street')),
      (1668, 518, None), (1668, 441, None), (1935, 441, None), (1935, 517, None),  # the north side of St. Marks Place between 3rd and 4th Avenues
      (2016, 516, ('4 Avenue', 'St Marks Place')), (2012, 1814, ('4 Avenue', 'Carroll Street')), (1973, 2345, ('4 Avenue', '3 Street')),
      (1564, 2306, ('3 Avenue', '3 Street')),
      (1550, 2495, None), (1238, 2462, None), (1186, 2405, None), (1110, 2420, None),  # 3rd Avenue to the 4th Street basin, west to the canal
      (1084, 2685, None),                                                          # 2nd Avenue at 6th Street
      (532, 2632, None), (517, 2658, None), (496, 2725, None), (479, 2842, None), (467, 3054, None),   # 6th Street's line west to the canal, the canal to 9th Street
      (243, 3042, ('Smith Street', '9 Street')), (171, 2458, ('Smith Street', '5 Street')), (512, 2492, ('Hoyt Street', '5 Street')),
      (514, 2204, ('Hoyt Street', '3 Street')), (850, 2233, ('Bond Street', '3 Street')), (887, 1814, ('Bond Street', 'Carroll Street')),
      (884, 1090, ('Bond Street', 'Douglass Street')), (518, 1090, ('Hoyt Street', 'Douglass Street'))]

def boundary():
    G = {(a, b): corner(a, b) for a, b, _, _ in CP}
    A = np.array([[x, y, 1] for _, _, x, y in CP])
    cla = np.linalg.lstsq(A, np.array([G[(a, b)][0] for a, b, _, _ in CP]), rcond=None)[0]
    clo = np.linalg.lstsq(A, np.array([G[(a, b)][1] for a, b, _, _ in CP]), rcond=None)[0]
    worst = max(math.hypot((cla @ [x, y, 1] - G[(a, b)][0]) * 111320, (clo @ [x, y, 1] - G[(a, b)][1]) * 84400) for a, b, x, y in CP)
    assert worst < 8, worst
    ring = []
    for x, y, c in PX:
        la, lo = G[c] if c else (float(cla @ [x, y, 1]), float(clo @ [x, y, 1]))
        ring.append([round(la, 6), round(lo, 6)])
    ring.append(ring[0])
    return ring, worst

LUN = {'01': 'One & Two Family', '02': 'Multi-Family Walkup', '03': 'Multi-Family Elevator', '04': 'Mixed Residential/Commercial', '05': 'Commercial/Office', '06': 'Industrial/Manufacturing',
       '07': 'Transportation/Utility', '08': 'Public Facilities/Institutions', '09': 'Parks/Open Space', '10': 'Parking', '11': 'Vacant Land'}
# a lot the city's file lists under its side-street address, shown under the address the building goes by
ADDR = {'3003997502': '450 WARREN STREET'}      # PLUTO: 193 Bond Street; Geoclient puts 450 Warren Street on this lot
def lots(g):
    x0, y0, x1, y1 = g.bounds
    pl = get('https://data.cityofnewyork.us/resource/64uk-42ks.json?' + urllib.parse.urlencode({'$where': "borough='BK' AND latitude between %f and %f AND longitude between %f and %f" % (y0 - .002, y1 + .002, x0 - .002, x1 + .002), '$limit': 50000}))
    assert len(pl) < 50000
    pl = [r for r in pl if r.get('latitude') and g.contains(Point(float(r['longitude']), float(r['latitude'])))]
    shp = {}; bbls = ['%d' % int(float(r['bbl'])) for r in pl]
    for i in range(0, len(bbls), 150):
        data = urllib.parse.urlencode({'where': 'BBL in (%s)' % ','.join(bbls[i:i + 150]), 'outFields': 'BBL', 'outSR': 4326, 'f': 'geojson', 'geometryPrecision': 6}).encode()
        for f in get('https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/MAPPLUTO/FeatureServer/0/query', data)['features']:
            shp['%d' % int(float(f['properties']['BBL']))] = f['geometry']
    out = []
    for r in pl:
        b = '%d' % int(float(r['bbl'])); gm = shp.get(b); rings = None
        if gm:
            polys = gm['coordinates'] if gm['type'] == 'MultiPolygon' else [gm['coordinates']]
            rings = [[[[round(y, 5), round(x, 5)] for x, y in poly[0]]] for poly in polys]
            rings = rings[0] if len(rings) == 1 else rings
        z = r.get('zonedist1', '') + ('/' + r['zonedist2'] if r.get('zonedist2') else '')
        lu = LUN.get((r.get('landuse') or '').zfill(2), 'No land use on file') if r.get('landuse') else 'No land use on file'
        n = lambda k: int(float(r[k])) if r.get(k) not in (None, '') else 0
        out.append([r.get('address', ''), b, lu, z, r.get('ownername', ''), n('yearbuilt'), round(float(r['numfloors']), 1) if r.get('numfloors') else 0, n('unitsres'), n('lotarea'),
                    round(float(r['latitude']), 6), round(float(r['longitude']), 6), rings])
    for l in out: l[0] = ADDR.get(l[1], l[0])
    out.sort(key=lambda l: (re.sub(r'^[\d\-]+\s+', '', l[0] or 'zzz'), int(re.match(r'\d*', l[0] or '').group() or 0)))
    return out

# the places the committee's map names: (label, what it is, park property numbers, tax lots, its profile page on the site)
SITES = [('Heyward Park', 'Nicholas Naquan Heyward Jr. Park · NYC Parks', ['B230'], [], '/park/nicholas-naquan-heyward-jr-park.html'),
         ('CSO Tank Site', '242 Nevins Street · NYC Department of Environmental Protection', [], ['3004180001'], ''),
         ('Thomas Greene Park', 'Thomas Greene Playground · NYC Parks', ['B145'], [], '/park/thomas-greene-playground.html'),
         ('Gowanus Green', 'Hoyt Street and 5th Street · NYC Housing Preservation and Development', [], ['3004710001', '3004710100'], '/lift-site/gowanus-building-d-fac-gowanus-green.html'),
         ('CSO Tank Site + Salt Lot', '2nd Avenue and 5th Street · NYC Department of Environmental Protection and Department of Sanitation', [],
          ['3009770003', '3009770001', '3009900001', '3009900016', '3009900021'], '/biz/salt-lot.html'),
         ('Transit Plaza', '9th Street at the canal · NYC Parks', ['B607'], [], '/park/park-b607.html')]
def sites(L):
    from shapely.geometry import shape
    from shapely.ops import unary_union
    parks = {f['properties'].get('gispropnum'): shape(f['geometry']) for f in json.load(open('Parks_Properties_20260414.geojson'))['features']}
    lot = {l[1]: l[11] for l in L}
    out = []
    for name, what, pk, bbls, href in SITES:
        assert not href or os.path.exists(href[1:]), href
        gs = [parks[k] for k in pk]
        for b in bbls:
            assert lot.get(b), b
            gs += [Polygon([(lo, la) for la, lo in ring[0]]) for ring in (lot[b] if isinstance(lot[b][0][0][0], list) else [lot[b]])]
        u = unary_union([x.buffer(0) for x in gs]).buffer(0.00003).buffer(-0.00003)      # lots of one site drawn as one shape
        polys = [u] if u.geom_type == 'Polygon' else list(u.geoms)
        c = max(polys, key=lambda q: q.area).representative_point()
        out.append([name, what, round(c.y, 6), round(c.x, 6), [[[[round(y, 6), round(x, 6)] for x, y in q.exterior.coords]] for q in polys], href])
    return out
SITE_CSS = ".sitel{transform:translate(-50%,-50%);width:max-content;max-width:118px;text-align:center;font:800 11px/1.15 'DM Sans',sans-serif;letter-spacing:.03em;text-transform:uppercase;color:#fff;background:#1f6b2a;border-radius:5px;padding:3px 7px;box-shadow:0 1px 3px rgba(0,0,0,.4);cursor:pointer}\n#map.zlo .sitel{font-size:8.5px;padding:2px 5px;max-width:92px}\n"
SITE_JS = """<!--sites--><script>(function(){try{var S=[];SITES.forEach(function(x){var pop='<div class="pop"><b>'+esc(x[0])+'</b><div>'+esc(x[1])+'</div>'+(x[5]?'<a class="go" href="'+esc(x[5])+'">Profile</a>':'')+'</div>';var p=L.polygon(x[4],{color:'#1f6b2a',weight:2,fillColor:'#4c9a2a',fillOpacity:.4}).addTo(map);p.bindPopup(pop);
var m=L.marker([x[2],x[3]],{icon:L.divIcon({className:'',html:'<div class="sitel">'+esc(x[0])+'</div>',iconSize:[0,0],iconAnchor:[0,0]})}).addTo(map);m.bindPopup(pop);S.push(p,m)});
function f(){S.forEach(function(l){try{l.bringToFront()}catch(x){}})}setTimeout(f,500);setTimeout(f,1800);map.on('zoomend',function(){setTimeout(f,250)});map.on('moveend',function(){setTimeout(f,250)});
[].forEach.call(document.querySelectorAll('.tog .pill'),function(b){b.addEventListener('click',function(){setTimeout(f,250)})})}catch(x){}})();</script><!--/sites-->"""
def slugify(s): return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', html.unescape(s).lower().replace("'", '').replace('&', ' and '))).strip('-')[:70]
def var(s, name):
    m = re.search(r'\b%s=' % name, s); return json.JSONDecoder().raw_decode(s, m.end())[0]

if __name__ == '__main__':
    s = open(PAGE, encoding='utf-8').read()
    old_ring = var(s, 'RING'); old_rows = var(s, 'ROWS'); old_lots = var(s, 'LOTS')
    ring, worst = boundary()
    g = Polygon([(lo, la) for la, lo in ring]); assert g.is_valid
    json.dump({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {
        'name': 'Proposed Gowanus BID (draft boundary)', 'source': "Gowanus BID Formation Steering Committee, Future Public Realm Map and 2026 Outreach Deck page 8; traced from the committee's map",
        'traced': '2026-11-23', 'fit_m': round(worst, 1)}, 'geometry': mapping(g)}]}, open(OUT, 'w'), separators=(',', ':'))
    # businesses
    rz = open('gowanusrezoning/index.html', encoding='utf-8').read(); rz_rows = var(rz, 'ROWS')
    oldp = Polygon([(lo, la) for la, lo in old_ring]) if isinstance(old_ring[0][0], float) else None
    rzb = json.load(open('data/gowanus_rezoning_boundary.geojson')); from shapely.geometry import shape
    rzp = shape(rzb['features'][0]['geometry'] if 'features' in rzb else rzb.get('geometry', rzb))
    key = lambda r: (r[0].strip().lower(), r[3].strip().lower())
    L = lots(g); inb = {l[1] for l in L}
    # which side of a boundary street: a listing with an address counts by the tax lot the city puts that address on
    near = g.buffer(0.0004); memo = {}; flips = []
    def inside(name, addr, la, lo):
        pt = Point(lo, la)
        if not near.contains(pt): return False
        plain = g.contains(pt)
        if not re.match(r'\d', addr or ''): return plain
        if addr not in memo:
            try:
                d = get('https://api.nyc.gov/geoclient/v2/search.json?' + urllib.parse.urlencode({'input': addr + ', Brooklyn, NY'}), hdr={'Ocp-Apim-Subscription-Key': GEOKEY})
                r0 = (d.get('results') or [{}])[0].get('response', {})
                ok = r0.get('latitude') and math.hypot((float(r0['latitude']) - la) * 111320, (float(r0['longitude']) - lo) * 84400) < 60   # the city's match must be the same place
                memo[addr] = [x for x in (r0.get('bbl'), r0.get('condominiumBillingBbl')) if x] if ok else []
            except Exception: memo[addr] = []
            time.sleep(.05)
        if not memo[addr]: return plain
        res = any(x in inb for x in memo[addr])
        if res != plain: flips.append((name, addr, 'in' if res else 'out'))
        return res
    rows, seen, src = [], set(), {'page': 0, 'rezoning map': 0, 'directory': 0}
    for name, rs in (('page', old_rows), ('rezoning map', rz_rows)):
        for r in rs:
            if key(r) in seen or not inside(r[0], r[3], r[4], r[5]): continue
            seen.add(key(r)); rows.append(r[:11]); src[name] += 1
    B = json.load(open('app/data/civic/business/business-cb6.json'))['rows']
    taken = {r[7] for r in rows}
    for b in B:
        pt = Point(b[6], b[5]); k = (b[0].strip().lower(), b[3].strip().lower())
        if k in seen or not near.contains(pt): continue
        if (oldp is not None and oldp.contains(pt)) or rzp.contains(pt): continue      # those two areas were already cleaned by hand: a listing missing there was removed
        if not inside(b[0], b[3], b[5], b[6]): continue
        href = '/biz/' + slugify(b[0] + ' ' + b[3]) + '.html'
        if not os.path.exists(href[1:]) or href in taken: href = ''
        seen.add(k); taken.add(href); rows.append([b[0], b[1], b[2], b[3], b[5], b[6], b[7], href, b[8], b[9], b[4]]); src['directory'] += 1
    rows.sort(key=lambda r: (r[1], r[0].lower()))
    s = re.sub(r'var RING=\[.*?\];\n', lambda m: 'var RING=%s;\n' % json.dumps(ring), s, count=1, flags=re.S)
    s = re.sub(r'var ROWS=\[.*?\];\n', lambda m: 'var ROWS=%s;\n' % json.dumps(rows, ensure_ascii=False, separators=(',', ':')), s, count=1, flags=re.S)
    s = re.sub(r'var LOTS=\[.*?\];\n', lambda m: 'var LOTS=%s;\n' % json.dumps(L, ensure_ascii=False, separators=(',', ':')), s, count=1, flags=re.S)
    s, n = re.subn(r'Boundary: .*? Businesses: ', "Boundary: the Gowanus BID Formation Steering Committee's draft boundary, traced from the committee's own map: "
                   'Wyckoff Street and St. Marks Place down to 3rd, 6th and 9th Streets, from Smith, Hoyt and Bond Streets to 4th Avenue. Businesses: ', s, count=1, flags=re.S)
    assert n == 1
    ST = 'var SITES=%s;\n' % json.dumps(sites(L), ensure_ascii=False, separators=(',', ':'))
    if re.search(r'var SITES=\[', s): s = re.sub(r'var SITES=\[.*?\];\n', lambda m: ST, s, count=1, flags=re.S)
    else: s = re.sub(r'(var HOUSING=\[.*?\];\n)', lambda m: m.group(1) + ST, s, count=1, flags=re.S)
    assert 'var SITES=[[' in s
    s = re.sub(r'\.sitel\{[^}]*\}\n#map\.zlo \.sitel\{[^}]*\}\n', '', s)
    s = s.replace('.gwlbl{', SITE_CSS + '.gwlbl{', 1)
    s = re.sub(r'<!--sites-->.*?<!--/sites-->', '', s, flags=re.S)
    s = s.replace('</body>', SITE_JS + '</body>', 1)
    assert '.sitel{' in s and '<!--sites-->' in s
    # a listing with no profile page gets no Profile link (instead of a link to nowhere)
    for a, b in (("""'<a class="go" href="'+esc(r[7])+'">Profile</a>'+(r[6]?""", """(r[7]?'<a class="go" href="'+esc(r[7])+'">Profile</a>':'')+(r[6]?"""),
                 ("""</span></div><a class="go" href="'+esc(r[7])+'">Profile</a></div>'})})""", """</span></div>'+(r[7]?'<a class="go" href="'+esc(r[7])+'">Profile</a>':'')+'</div>'})})""")):
        if b not in s:
            assert a in s; s = s.replace(a, b, 1)
    open(PAGE, 'w', encoding='utf-8').write(s)
    old_b = {l[1] for l in old_lots}; new_b = {l[1] for l in L}
    print('fit: worst street corner %.1f m' % worst)
    print('businesses %d (was %d): %s' % (len(rows), len(old_rows), src))
    kept = {key(r) for r in rows}
    print('  dropped from the page:', len([r for r in old_rows if key(r) not in kept]), '| without a profile page:', sum(1 for r in rows if not r[7]))
    print('  side of the street settled by tax lot:', flips)
    json.dump({'rows': rows, 'old': old_rows}, open('/tmp/gbid_rows.json', 'w'))
    print('lots %d (was %d): kept %d, added %d, dropped %d, with shapes %d' % (len(L), len(old_lots), len(old_b & new_b), len(new_b - old_b), len(old_b - new_b), sum(1 for l in L if l[11])))
