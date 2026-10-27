#!/usr/bin/env python3
"""Every new building filed in the Gowanus rezoning area since the City Council
passed the rezoning (November 23, 2021): a map and directory at /gowanusbuildings/
and a profile for each building at /gowanusbuildings/<slug>/.

Sources, all fetched fresh on each run:
  DOB NOW job filings (w9ak-ipjd), New Building jobs, filed on or after 2021-11-23,
    located inside data/gowanus_rezoning_boundary.geojson; withdrawn jobs left out
  DOB NOW certificates of occupancy (pkdm-hqz6)
  HPD Affordable Housing Production by Building (hg8x-zxpr)
  PLUTO (64uk-42ks) and MapPLUTO (ArcGIS) for zoning, land use and lot shapes
Run: python3 scripts/build_gowanus_buildings.py
"""
import json, os, re, html, urllib.request, urllib.parse, datetime
from shapely.geometry import shape, Point, mapping

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'gowanusbuildings')
TOKEN = 'HvFoIfzodzpRML7a1104Ca2tM'
SINCE = '2021-11-23'

def soda(ds, where, limit=50000, select=None):
    q = {'$where': where, '$limit': limit}
    if select: q['$select'] = select
    u = f'https://data.cityofnewyork.us/resource/{ds}.json?' + urllib.parse.urlencode(q)
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'X-App-Token': TOKEN}), timeout=180).read())

def esc(s): return html.escape(str(s), quote=True)
def fmt(n): return f'{int(round(n)):,}'
def num(v):
    try: return float(v)
    except Exception: return 0.0
def tc(s):
    s = re.sub(r'\s+', ' ', str(s or '').strip()).title()
    s = re.sub(r'\b(\d+)(St|Nd|Rd|Th)\b', lambda m: m.group(1) + m.group(2).lower(), s)
    return s
def street(n, s):
    s = tc(s)
    s = re.sub(r'^(\d+) Avenue$', lambda m: ordn(m.group(1)) + ' Avenue', s)
    s = re.sub(r'^(\d+) Street$', lambda m: ordn(m.group(1)) + ' Street', s)
    s = re.sub(r'^(\d+)(st|nd|rd|th) Avenue$', lambda m: m.group(1) + m.group(2) + ' Avenue', s)
    s = s.replace('Third Avenue', '3rd Avenue').replace('Fourth Avenue', '4th Avenue').replace('Fifth Street', '5th Street')
    return f'{n} {s}'.strip()
def ordn(n):
    n = int(n); t = n % 100
    return f'{n}{"th" if 11 <= t <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")}'
def slugify(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
def dmy(s):
    if not s: return ''
    s = s[:10]
    try:
        if '/' in s: d = datetime.datetime.strptime(s[:8], '%m/%d/%y')
        else: d = datetime.datetime.strptime(s, '%Y-%m-%d')
        return d.strftime('%B %-d, %Y')
    except Exception: return s
def iso(s):
    if not s: return ''
    try:
        if '/' in s[:10]: return datetime.datetime.strptime(s[:8], '%m/%d/%y').strftime('%Y-%m-%d')
        return s[:10]
    except Exception: return ''

def units_of(rs):
    """The unit count the job's filings agree on: the value on the most rows,
    ties going to the most recent row. (An initial filing can carry a site-wide
    figure that its later filings correct.)"""
    from collections import Counter
    vals = [num(x.get('proposed_dwelling_units')) for x in rs]
    c = Counter(vals); top = max(c.values())
    for x in reversed(rs):
        v = num(x.get('proposed_dwelling_units'))
        if c[v] == top: return v
    return 0

B = shape(json.load(open(os.path.join(ROOT, 'data/gowanus_rezoning_boundary.geojson')))['features'][0]['geometry'])

# ---------- DOB NOW new building jobs ----------
rows = soda('w9ak-ipjd', f"job_type='New Building' AND borough='Brooklyn' AND filing_date>='{SINCE}T00:00:00'")
jobs = {}
for r in rows:
    try: p = Point(float(r['longitude']), float(r['latitude']))
    except Exception: continue
    if not B.contains(p): continue
    jobs.setdefault(r['job_filing_number'].split('-')[0], []).append(r)
J = []
for jn, rs in jobs.items():
    rs.sort(key=lambda r: (r.get('current_status_date') or r.get('filing_date') or ''))
    last = rs[-1]
    if last.get('filing_status') == 'Filing Withdrawn': continue
    bbl = last.get('bbl') or ('3%05d%04d' % (int(last['block']), int(last['lot'])))
    permits = sorted(iso(x.get('first_permit_date')) for x in rs if x.get('first_permit_date'))
    J.append(dict(job=jn, bbl=bbl, addr=street(last.get('house_no', ''), last.get('street_name', '')),
                  status=last.get('filing_status', ''), du=units_of(rs),
                  gfa=max(num(x.get('total_construction_floor_area')) for x in rs),
                  filed=min(iso(x.get('filing_date')) for x in rs), permit=permits[0] if permits else '',
                  loc=any(x.get('filing_status') == 'LOC Issued' for x in rs),
                  owner=tc(last.get('owner_s_business_name') or '') if (last.get('owner_s_business_name') or '').strip().upper() not in ('PR', 'NOT APPLICABLE', 'N/A', '') else '',
                  lat=float(last['latitude']), lng=float(last['longitude']),
                  desc=max(((x.get('job_description') or '').strip() for x in rs), key=lambda t: (bool(re.search(r'stor(y|ies)|new building|dwelling|residential|mixed.use|apartment', t, re.I)), len(t)))))
bbls = sorted({j['bbl'] for j in J})
inq = ','.join(f"'{b}'" for b in bbls)

# ---------- certificates of occupancy ----------
co = soda('pkdm-hqz6', f'bbl in ({inq})')
COS = {}
for c in co:
    COS.setdefault(c.get('job_filing_name', ''), []).append(c)
for j in J:
    cs = COS.get(j['job'], [])
    ini = sorted(iso(c.get('c_of_o_issuance_date')) for c in cs if c.get('c_of_o_status') == 'CO Issued')
    fin = sorted(iso(c.get('c_of_o_issuance_date')) for c in cs if c.get('c_of_o_status') == 'CO Issued' and (c.get('c_of_o_filing_type') or '').lower() == 'final')
    j['co_first'] = ini[0] if ini else ''
    j['co_final'] = fin[0] if fin else ''
    j['co_units'] = max([num(c.get('number_of_dwelling_units')) for c in cs] or [0])
    if j['co_first'] or j['loc']: j['k'] = 'open'
    elif j['permit']: j['k'] = 'building'
    else: j['k'] = 'filed'
    j['units'] = j['co_units'] or j['du']

# ---------- HPD affordable ----------
hpd = soda('hg8x-zxpr', f'bbl in ({inq})')
H = {}
for h in hpd: H.setdefault(h['bbl'], []).append(h)
BANDS = [('extremely_low_income_units', 'Extremely low income'), ('very_low_income_units', 'Very low income'), ('low_income_units', 'Low income'),
         ('moderate_income_units', 'Moderate income'), ('middle_income_units', 'Middle income'), ('other_income_units', 'Other')]
SIZES = [('studio_units', 'Studios'), ('_1_br_units', '1 bedroom'), ('_2_br_units', '2 bedrooms'), ('_3_br_units', '3 bedrooms'), ('_4_br_units', '4 bedrooms'), ('unknown_br_units', 'Size not reported')]

# ---------- PLUTO and MapPLUTO ----------
pl = soda('64uk-42ks', "borough='BK' AND (" + ' OR '.join(f"(block={int(b[1:6])} AND lot={int(b[6:])})" for b in bbls) + ')')
PL = {'3%05d%04d' % (int(r['block']), int(r['lot'])): r for r in pl}
def arc(where):
    u = 'https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/MAPPLUTO/FeatureServer/0/query'
    data = urllib.parse.urlencode({'where': where, 'outFields': 'BBL,Block,Lot,Address', 'outSR': 4326, 'f': 'geojson', 'geometryPrecision': 6}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, data=data), timeout=180).read())['features']
GEO = {}
for f in arc("Borough='BK' AND (" + ' OR '.join(f'(Block={int(b[1:6])} AND Lot={int(b[6:])})' for b in bbls) + ')'):
    GEO['3%05d%04d' % (int(f['properties']['Block']), int(f['properties']['Lot']))] = f['geometry']
# a job whose lot is not in PLUTO (merged or apportioned since filing): use the lot that holds its point
for j in J:
    if j['bbl'] in PL and j['bbl'] in GEO: j['lot'] = j['bbl']; continue
    u = 'https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services/MAPPLUTO/FeatureServer/0/query?' + urllib.parse.urlencode(
        {'geometry': f"{j['lng']},{j['lat']}", 'geometryType': 'esriGeometryPoint', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
         'outFields': 'BBL,Block,Lot', 'outSR': 4326, 'f': 'geojson', 'geometryPrecision': 6})
    fs = json.loads(urllib.request.urlopen(u, timeout=120).read())['features']
    if fs:
        k = '3%05d%04d' % (int(fs[0]['properties']['Block']), int(fs[0]['properties']['Lot']))
        GEO[k] = fs[0]['geometry']; j['lot'] = k
        if k not in PL:
            r = soda('64uk-42ks', f"borough='BK' AND block={int(k[1:6])} AND lot={int(k[6:])}")
            if r: PL[k] = r[0]
    else: j['lot'] = j['bbl']

LU = {'1': 'One and two family buildings', '2': 'Multi-family walk-up buildings', '3': 'Multi-family elevator buildings', '4': 'Mixed residential and commercial buildings',
      '5': 'Commercial and office buildings', '6': 'Industrial and manufacturing', '7': 'Transportation and utility', '8': 'Public facilities and institutions',
      '9': 'Open space and outdoor recreation', '10': 'Parking facilities', '11': 'Vacant land'}
SP = {'G': 'Special Gowanus Mixed Use District'}
CM = {'33': ('Lincoln Restler', '/cmrestler/'), '38': ('Alexa Avilés', '/cmaviles/'), '39': ('Shahana Hanif', '/cmhanif/')}
def zdesc(z):
    if '/' in z: return f'{z}, a paired mixed use district: {z.split("/")[0]} manufacturing with {z.split("/")[1]} residence'
    k = {'R': 'residence district', 'C': 'commercial district', 'M': 'manufacturing district'}.get(z[:1], 'district')
    return f'{z}, a {k}'
def zrows(k):
    r = PL.get(k)
    if not r: return []
    zs = [r[f] for f in ('zonedist1', 'zonedist2', 'zonedist3', 'zonedist4') if r.get(f)]
    out = []
    if zs: out.append(('Zoning', '; '.join(zdesc(z) for z in zs) + (' (the lot is split between districts)' if r.get('splitzone') in (True, 'true', 'True') and len(zs) > 1 else '')))
    ov = [r[f] for f in ('overlay1', 'overlay2') if r.get(f)]
    if ov: out.append(('Commercial overlay', ', '.join(ov)))
    sp = [SP.get(r[f], r[f]) for f in ('spdist1', 'spdist2', 'spdist3') if r.get(f)]
    if sp: out.append(('Special district', ', '.join(sp)))
    rf, cf, ff = num(r.get('residfar')), num(r.get('commfar')), num(r.get('facilfar'))
    out.append(('What city zoning allows', (f'Housing up to {rf:g} times the lot area' if rf else 'No housing as of right') + (f'; commercial up to {cf:g}' if cf else '; no commercial') + (f'; community facilities up to {ff:g}' if ff else '')))
    if r.get('landuse'): out.append(('Land use, tax records', LU.get(str(int(r['landuse'])), r['landuse'])))
    if num(r.get('lotarea')): out.append(('Lot area', f'{fmt(num(r["lotarea"]))} square feet'))
    if num(r.get('bldgarea')): out.append(('Building area, tax records', f'{fmt(num(r["bldgarea"]))} square feet, {num(r["bldgarea"])/num(r["lotarea"]):.1f} times the lot area'))
    if num(r.get('numfloors')): out.append(('Floors, tax records', f'{num(r["numfloors"]):g}'))
    if r.get('yearbuilt') and r['yearbuilt'] != '0': out.append(('Year built, tax records', r['yearbuilt']))
    if r.get('ownername'): out.append(('Owner of record', tc(r['ownername'])))
    c = r.get('council')
    if c: out.append(('City Council', f'District {c}' + (f', <a href="{CM[c][1]}">{CM[c][0]}</a>' if c in CM else '')))
    if r.get('policeprct'): out.append(('Police precinct', f'<a href="/precinct/{r["policeprct"]}/">{ordn(r["policeprct"])} Precinct</a>'))
    if r.get('schooldist'): out.append(('School district', f'<a href="/eduhub-csd-{r["schooldist"]}.html">District {r["schooldist"]}</a>'))
    fc = r.get('firecomp')
    if fc: out.append(('Fire company', f'{ {"L": "Ladder", "E": "Engine"}.get(fc[0], "")} {fc[1:]}'.strip()))
    if r.get('zipcode'): out.append(('ZIP code', r['zipcode']))
    return out

DOBNOW = 'https://data.cityofnewyork.us/Housing-Development/DOB-NOW-Build-Job-Application-Filings/w9ak-ipjd'
DOBCO = 'https://data.cityofnewyork.us/Housing-Development/DOB-NOW-Certificate-of-Occupancy/pkdm-hqz6'
HPD = 'https://data.cityofnewyork.us/Housing-Development/Affordable-Housing-Production-by-Building/hg8x-zxpr'
PLUTO = 'https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks'
VOTE = 'https://brooklyneagle.com/articles/2021/11/23/city-council-as-expected-passes-gowanus-rezoning-plan/'
STAT = {'open': 'Open', 'building': 'Permitted, not yet open', 'filed': 'Filed, not yet permitted'}

# ---------- one record per building ----------
EXTRA = json.load(open(os.path.join(ROOT, 'data/gowanusbuildings-extras.json')))['buildings']
HC = 'https://housingconnect.nyc.gov/PublicWeb/search-lotteries'
FAC = 'https://fifthave.org/lottery-and-leasing/'
seen = {}
for j in sorted(J, key=lambda j: j['addr']):
    s = slugify(j['addr'])
    if s in seen: s = f'{s}-{j["job"].lower()}'
    seen[s] = 1; j['slug'] = s
    hs = H.get(j['bbl'], []) or H.get(j.get('lot'), [])
    j['aff'] = sum(num(h.get('all_counted_units')) for h in hs) if hs else 0
    j['bands'] = [(lab, sum(num(h.get(f)) for h in hs)) for f, lab in BANDS if sum(num(h.get(f)) for h in hs)]
    j['sizes'] = [(lab, sum(num(h.get(f)) for h in hs)) for f, lab in SIZES if sum(num(h.get(f)) for h in hs)]
    j['mih'] = any('MIH' in (h.get('project_name') or '').upper() for h in hs)
    j['z'] = zrows(j.get('lot', j['bbl']))
    x = EXTRA.get(s, {})
    j['name'], j['web'], j['logo'], j['websrc'], j['lottery'] = x.get('name'), x.get('website'), x.get('logo'), x.get('src'), x.get('lottery')
    j['title'] = f'{j["name"]}, {j["addr"]}' if j['name'] and j['name'] != j['addr'] else j['addr']
    when = (f'opened with a certificate of occupancy on {dmy(j["co_first"])}' + (f', made final on {dmy(j["co_final"])}' if j['co_final'] else '') if j['co_first']
            else 'completed under a DOB letter of completion' if j['loc']
            else f'permitted, with its first permit on {dmy(j["permit"])}' if j['permit'] else 'not permitted yet')
    j['d'] = (f'<p>{esc(j["addr"])}{(" (" + esc(j["name"]) + ")") if j["name"] else ""} is a new building in the Gowanus rezoning area, filed with the Department of Buildings on {dmy(j["filed"])}: '
              + (f'{fmt(j["units"])} apartments' if j['units'] else 'no apartments')
              + (f', {fmt(j["aff"])} of them affordable' if j['aff'] else '')
              + (f', {fmt(j["gfa"])} square feet of construction' if j['gfa'] else '') + f'. It is {when}.</p>')

def key(j): return {'open': 0, 'building': 1, 'filed': 2}[j['k']]
J.sort(key=lambda j: (key(j), -j['units'], j['addr']))

# ---------- shared page pieces ----------
HEAD = '''<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<link rel="stylesheet" href="/atlanticyards/profile.css?v=2">
<link rel="stylesheet" href="/gowanusbuildings/gb.css?v=3">'''
BAR = '''<body><script src="/assets/site-bar.js?v=1" defer></script><a id="asb" href="https://apps.apple.com/us/app/bkcb6/id6813967208" target="_blank" rel="noopener" style="display:block;background:#0d1b4b;text-align:center;padding:8px 0;line-height:0;text-decoration:none"><img src="/appstore-badge.png" alt="Download BKCB6 on the App Store" width="121" height="40" style="height:40px;width:auto;border:0;display:inline-block"></a><script>(function(){try{var a=document.getElementById("asb"),q=/[?&]app=1\\b/.test(location.search);if(q)sessionStorage.setItem("bkapp","1");if(location.protocol==="bkcb:"||q||sessionStorage.getItem("bkapp")==="1"||/^bkcb:/.test(document.referrer)){a.style.display="none"}}catch(e){}})();</script>'''
SRC = f'''<div class="src"><b>Sources</b>
<a href="{DOBNOW}" target="_blank" rel="noopener">NYC DOB NOW job application filings</a> (New Building jobs filed since {dmy(SINCE)} inside the rezoning boundary; withdrawn filings left out)<br>
<a href="{DOBCO}" target="_blank" rel="noopener">NYC DOB NOW certificates of occupancy</a><br>
<a href="{HPD}" target="_blank" rel="noopener">NYC HPD, Affordable Housing Production by Building</a><br>
<a href="{PLUTO}" target="_blank" rel="noopener">NYC DCP, PLUTO and MapPLUTO</a> (zoning, land use, lot shapes)<br>
<a href="{VOTE}" target="_blank" rel="noopener">Brooklyn Eagle, City Council passes the Gowanus rezoning, November 23, 2021</a><br>
<a href="{HC}" target="_blank" rel="noopener">NYC Housing Connect</a>; <a href="{FAC}" target="_blank" rel="noopener">Fifth Avenue Committee, lottery and leasing</a>
</div>'''

def table(rows): return '<div class="ftab"><table>' + ''.join(f'<tr><td>{a}</td><td>{b}</td></tr>' for a, b in rows) + '</table></div>'
def bars(rows):
    if not rows: return ''
    mx = max(n for _, n in rows) or 1
    return '<div class="bars">' + ''.join(f'<div class="br"><span class="bl">{l}</span><span class="bt"><i style="width:{n*100/mx:.1f}%"></i></span><span class="bn">{fmt(n)}</span></div>' for l, n in rows) + '</div>'

def facts(j):
    r = [('Status', STAT[j['k']]), ('DOB job', f'{esc(j["job"])}, {esc(j["status"])}'),
         ('Filed', dmy(j['filed']))]
    if j['permit']: r.append(('First permit', dmy(j['permit'])))
    if j['co_first']: r.append(('Certificate of occupancy', dmy(j['co_first']) + (f', final {dmy(j["co_final"])}' if j['co_final'] else ', temporary')))
    if j['units']: r.append(('Apartments', fmt(j['units'])))
    if j['aff']: r.append(('Affordable', f'{fmt(j["aff"])}' + (', under Mandatory Inclusionary Housing' if j['mih'] else '')))
    if j['gfa']: r.append(('Construction floor area', f'{fmt(j["gfa"])} square feet'))
    if j['owner']: r.append(('Owner on the filing', esc(j['owner'])))
    r.append(('Tax lot', f'Brooklyn block {int(j["bbl"][1:6])}, lot {int(j["bbl"][6:])}'))
    r.append(('Community board', 'BKCB6'))
    if j['web']: r.insert(0, ('Website', f'<a href="{esc(j["web"])}" target="_blank" rel="noopener">{esc(re.sub(r"^https?://(www[.])?", "", j["web"]).rstrip("/"))}</a>'))
    return r
def lotteries(j):
    own = f'<li><a href="{esc(j["lottery"])}" target="_blank" rel="noopener">This buildingThis building&rsquo;s lottery</a>rsquo;s lottery on Housing Connect</a></li>' if j.get('lottery') else ''
    return ('<section class="sec"><h2>Affordable housing lotteries</h2><div class="lede">Affordable apartments in new buildings are rented through the city&rsquo;s housing lottery.</div></section>'
            f'<div class="lot"><a class="lotb" href="{HC}" target="_blank" rel="noopener">Search open lotteries on Housing Connect &rarr;</a>'
            f'<a class="lotb alt" href="{FAC}" target="_blank" rel="noopener">Fifth Avenue Committee: lottery and leasing help &rarr;</a></div>' + (f'<ul class="pts">{own}</ul>' if own else ''))

# ---------- profiles ----------
for j in J:
    kp = [(fmt(j['units']) if j['units'] else 'none', 'apartments'),
          (fmt(j['aff']) if j['aff'] else 'none', f'affordable, {round(j["aff"]*100/j["units"])}% of the building' if j['aff'] and j['units'] else 'affordable in HPD&rsquo;s data'),
          (STAT[j['k']], dmy(j['co_first'] or j['permit'] or j['filed']))]
    k = ''.join(f'<div class="kp"><div class="v">{v}</div><div class="k">{t}</div></div>' for v, t in kp)
    logo = f'<div class="blogo"><img src="{j["logo"]}" alt="{esc(j["name"] or j["addr"])}"></div>' if j['logo'] else ''
    body = logo + f'<section class="sec"><h2>The building</h2></section><div class="pts">{j["d"]}</div>' + table(facts(j)) + lotteries(j)
    if j['desc']: body += f'<section class="sec"><h2>What was filed</h2><div class="lede">{esc(j["desc"])}</div></section>'
    if j['bands']:
        body += f'<section class="sec"><h2>Who the affordable apartments are for</h2><div class="lede">By household income, as counted in <a href="{HPD}" target="_blank" rel="noopener">HPD&rsquo;s production data</a>.</div></section>' + bars(j['bands'])
        if j['sizes']: body += '<section class="sec"><h2>Their sizes</h2></section>' + bars(j['sizes'])
    if j['z']: body += '<section class="sec"><h2>Zoning and land use</h2></section>' + table(j['z'])
    desc = re.sub('<[^>]+>', '', j['d'])
    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
{HEAD}
<title>{esc(j["title"])}, Gowanus rezoning &mdash; bkcb6.app</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="https://bkcb6.app/gowanusbuildings/{j["slug"]}/">
</head>
{BAR}
<div class="wrap">
<div class="top-bar"><div class="top-txt"><h1>{esc(j["name"] or j["addr"])}</h1><p>{(esc(j["addr"]) + " &middot; ") if j["name"] else ""}{STAT[j["k"]]} &middot; BKCB6 &middot; Gowanus rezoning</p></div><a class="back-link" href="/gowanusbuildings/">&larr; New buildings</a></div>
<div class="finder"><div class="hm-card"><div class="key" id="key"></div><div id="map" data-slug="{j["slug"]}"></div></div></div>
<div class="kpis">{k}</div>
{body}
<div class="others"><div class="lbl">EVERY NEW BUILDING IN THE REZONING</div><div id="others" data-self="{j["slug"]}"></div></div>
{SRC.replace('</div>', (f'<br>Website: <a href="{esc(j["websrc"])}" target="_blank" rel="noopener">{esc(j["websrc"])}</a>' if j.get('websrc') else '') + '</div>')}
</div>
<script src="/gowanusbuildings/gb.js?v=5"></script>
</body>
</html>
'''
    os.makedirs(os.path.join(OUT, j['slug']), exist_ok=True)
    open(os.path.join(OUT, j['slug'], 'index.html'), 'w').write(page)

# ---------- map data ----------
def rnd(m, p=6):
    def r(c):
        if isinstance(c[0], (int, float)): return [round(c[0], p), round(c[1], p)]
        return [r(x) for x in c]
    return {'type': m['type'], 'coordinates': r(m['coordinates'])}
feats = []
for j in J:
    g = GEO.get(j.get('lot')) or GEO.get(j['bbl'])
    feats.append({'type': 'Feature', 'geometry': rnd(g) if g else {'type': 'Point', 'coordinates': [round(j['lng'], 6), round(j['lat'], 6)]},
                  'properties': {'slug': j['slug'], 't': j['addr'], 'nm': j['name'], 'logo': j['logo'], 'web': j['web'], 'k': j['k'], 'u': j['units'], 'a': j['aff'], 'st': STAT[j['k']], 'd': j['d'], 'z': j['z'],
                                 'pt': [round(j['lat'], 6), round(j['lng'], 6)]}})
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(OUT, 'buildings.json'), 'w'), separators=(',', ':'))
bnd = json.load(open(os.path.join(ROOT, 'data/gowanus_rezoning_boundary.geojson')))
json.dump({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {}, 'geometry': rnd(mapping(B.simplify(0.00002)))}]},
          open(os.path.join(OUT, 'boundary.json'), 'w'), separators=(',', ':'))

# ---------- places with logos, NYCHA, subway and buses around the rezoning ----------
NEAR = B.buffer(0.004)
orgs = json.load(open(os.path.join(ROOT, 'app/data/civic/orgs/orgs-profiles.json')))
items = next(v for v in orgs.values() if isinstance(v, list))
GK = {'Community groups': 'groups', 'Local businesses': 'biz', 'Schools, parks and facilities': 'fac'}
places = []
for o in items:
    g = GK.get(o.get('group'))
    if g == 'groups' and o.get('name') in ('Principles', 'Bark Slope'): g = 'biz'
    if not g or not o.get('logo'): continue
    try: pt = Point(float(o['lng']), float(o['lat']))
    except Exception: continue
    if not NEAR.contains(pt): continue
    places.append({'g': g, 'n': o['name'], 'slug': o['slug'], 'grp': o['group'], 'logo': '/app/data/civic/orgs/logos/' + o['logo'],
                   'addr': o.get('addr') or '', 'll': [round(float(o['lat']), 6), round(float(o['lng']), 6)], 'in': B.contains(pt)})
for x in json.load(open(os.path.join(ROOT, 'data/gowanus_cb6_nycha_lookup.json'))):
    pt = Point(x['lng'], x['lat'])
    if NEAR.contains(pt): places.append({'g': 'nycha', 'n': x['name'].replace('NYCHA ', ''), 'logo': '/assets/map-icons/nycha.png', 'addr': x.get('type', ''), 'll': [x['lat'], x['lng']], 'in': B.contains(pt)})
BOX = 'POLYGON((-74.004 40.660,-73.972 40.660,-73.972 40.690,-74.004 40.690,-74.004 40.660))'
def ny(ds, where):
    u = f'https://data.ny.gov/resource/{ds}.json?' + urllib.parse.urlencode({'$where': where, '$limit': 1000})
    return json.loads(urllib.request.urlopen(u, timeout=120).read())
from shapely.geometry import box as sbox
from shapely.ops import unary_union
BB = sbox(-74.004, 40.660, -73.972, 40.690)
COLR = {'2': '#EE352E', '3': '#EE352E', '4': '#00933C', '5': '#00933C', 'B': '#FF6319', 'D': '#FF6319', 'F': '#FF6319', 'M': '#FF6319', 'N': '#FCCC0A', 'Q': '#FCCC0A', 'R': '#FCCC0A', 'W': '#FCCC0A', 'A': '#0039A6', 'C': '#0039A6', 'E': '#0039A6', 'G': '#6CBE45'}
grp = {}
for x in ny('s692-irgq', f"intersects(geometry,'{BOX}')"):
    c = COLR.get(x['service'])
    if c: grp.setdefault(c, []).append(shape(x['geometry']).intersection(BB).simplify(0.00003))
sub = [{'type': 'Feature', 'properties': {'c': c}, 'geometry': rnd(mapping(unary_union(gs)), 5)} for c, gs in grp.items()]
st = {}
for e in ny('i9wp-a4ja', 'within_box(entrance_georeference,40.690,-74.004,40.660,-73.972)'):
    v = st.setdefault(e['stop_name'], {'r': set(), 'p': []})
    v['r'].update(e['daytime_routes'].split()); v['p'].append((float(e['entrance_latitude']), float(e['entrance_longitude'])))
ORD = '2345BDFMNQRWACEG'
stations = [{'n': k, 'r': sorted(v['r'], key=lambda r: ORD.index(r) if r in ORD else 99), 'll': [round(sum(p[0] for p in v['p']) / len(v['p']), 5), round(sum(p[1] for p in v['p']) / len(v['p']), 5)]} for k, v in st.items()]
bus = {}
for x in json.load(open(os.path.join(ROOT, 'app/data/civic/transport/cb-bk-6.json')))['bus']:
    rt, col, nm = x['p']
    from shapely.geometry import MultiLineString
    g = MultiLineString(x['l']).intersection(BB)
    if g.is_empty: continue
    bus.setdefault(rt, {'c': '#' + col.lstrip('#'), 'n': nm, 'g': []})['g'].append(g)
buses = [{'r': k, 'c': v['c'], 'n': v['n'], 'g': rnd(mapping(unary_union(v['g']).simplify(0.00003)), 5)} for k, v in sorted(bus.items())]
json.dump({'places': places, 'subway': {'type': 'FeatureCollection', 'features': sub}, 'stations': stations, 'bus': buses},
          open(os.path.join(OUT, 'around.json'), 'w'), separators=(',', ':'))
json.dump([{'slug': j['slug'], 't': j['addr'], 'k': j['k']} for j in J], open(os.path.join(OUT, 'profiles.json'), 'w'), separators=(',', ':'))

# ---------- the map page ----------
n = {k: [j for j in J if j['k'] == k] for k in ('open', 'building', 'filed')}
u = {k: sum(j['units'] for j in v) for k, v in n.items()}
a = {k: sum(j['aff'] for j in v) for k, v in n.items()}
cnt = {g: sum(1 for p in places if p['g'] == g) for g in ('groups', 'biz', 'fac', 'nycha')}
kp = [(str(len(n['open'])), f'buildings open, with {fmt(u["open"])} apartments, {fmt(a["open"])} of them affordable'),
      (str(len(n['building'])), f'permitted and not yet open, with {fmt(u["building"])} apartments planned'),
      (str(len(n['filed'])), f'filed and not yet permitted, with {fmt(u["filed"])} apartments planned'),
      (fmt(sum(u.values())), f'apartments in all {len(J)} new building filings since the <a href="{VOTE}" target="_blank" rel="noopener">Council passed the rezoning</a> on November 23, 2021')]
K = ''.join(f'<div class="kp"><div class="v">{v}</div><div class="k">{t}</div></div>' for v, t in kp)
index = f'''<!DOCTYPE html>
<html lang="en">
<head>
{HEAD}
<title>New buildings in the Gowanus rezoning &mdash; bkcb6.app</title>
<meta name="description" content="Every new building filed in the Gowanus rezoning area since it passed in November 2021, on one map: open, permitted or filed, with apartments, affordable units, zoning and land use for each.">
<link rel="canonical" href="https://bkcb6.app/gowanusbuildings/">
</head>
{BAR}
<div class="wrap">
<div class="top-bar"><div class="top-txt"><h1>New buildings in the <span>Gowanus rezoning</span></h1><p>Every new building filed since the rezoning passed, open, permitted or filed</p></div><a class="back-link" href="/gowanus.html">&larr; Gowanus</a></div>
<div class="finder"><div class="hm-card">
  <div class="hm-top"><div class="hm-l">Tap any building for its description, zoning and land use.</div></div>
  <div class="key" id="key"></div>
  <div id="map" data-index="1"></div>
  <div id="res" class="result"></div>
  <div class="hm-foot">
    <div class="lbl">PROFILES: EVERY NEW BUILDING</div>
    <div class="profs" id="profs"></div>
    <div class="lbl">NEW BUILDINGS</div>
    <div class="pills">
      <button class="pill on" type="button" data-l="open" style="--c:#0d1b4b"><i></i>Open<span class="n">{len(n["open"])}</span></button>
      <button class="pill on" type="button" data-l="building" style="--c:#f47920"><i></i>Permitted<span class="n">{len(n["building"])}</span></button>
      <button class="pill on" type="button" data-l="filed" style="--c:#0e7490"><i></i>Filed<span class="n">{len(n["filed"])}</span></button>
    </div>
    <div class="lbl">AROUND THE REZONING</div>
    <div class="pills">
      <button class="pill on" type="button" data-l="groups" style="--c:#16a34a"><i></i>Community groups<span class="n">{cnt["groups"]}</span></button>
      <button class="pill on" type="button" data-l="nycha" style="--c:#1d4ed8"><i></i>NYCHA<span class="n">{cnt["nycha"]}</span></button>
      <button class="pill" type="button" data-l="biz" style="--c:#b45309"><i></i>Local businesses<span class="n">{cnt["biz"]}</span></button>
      <button class="pill" type="button" data-l="fac" style="--c:#7c3aed"><i></i>Schools, parks and facilities<span class="n">{cnt["fac"]}</span></button>
    </div>
    <div class="lbl">TRAINS AND BUSES</div>
    <div class="pills">
      <button class="pill on" type="button" data-l="subway" style="--c:#FF6319"><i></i>Subway<span class="n">{len(stations)}</span></button>
      <button class="pill" type="button" data-l="bus" style="--c:#0039a6"><i></i>Bus routes<span class="n">{len(buses)}</span></button>
    </div>
  </div>
</div></div>
<div class="kpis">{K}</div>
{lotteries({"lottery": None})}
{SRC}
</div>
<script src="/gowanusbuildings/gb.js?v=5"></script>
</body>
</html>
'''
open(os.path.join(OUT, 'index.html'), 'w').write(index)

# ---------- the directory ----------
def card(j):
    z = dict(j['z'])
    zz = ''.join(f'<span><b>{k}</b> {re.sub("</?a[^>]*>", "", z[k])}</span>' for k in ('Zoning', 'Special district', 'What city zoning allows', 'Land use, tax records') if k in z)
    lg = f'<img class="dlogo" src="{j["logo"]}" alt="">' if j['logo'] else ''
    return (f'<a class="dc {j["k"]}" href="/gowanusbuildings/{j["slug"]}/" data-app="1"><div class="dh">{lg}<span class="dt">{esc(j["name"] or j["addr"])}</span>{("<span class=ds>" + esc(j["addr"]) + "</span>") if j["name"] else ""}'
            f'<span class="ds">{STAT[j["k"]]} &middot; {fmt(j["units"])} apartments{(" &middot; " + fmt(j["aff"]) + " affordable") if j["aff"] else ""}</span></div>'
            f'<div class="dd">{j["d"]}</div><div class="dz">{zz}</div><div class="dg">Open the profile &rarr;</div></a>')
groups = ''.join(f'<section class="sec" id="{k}"><h2>{STAT[k]}</h2><div class="lede">{len(n[k])} buildings, {fmt(u[k])} apartments</div></section><div class="dgrid">' + ''.join(card(j) for j in n[k]) + '</div>' for k in ('open', 'building', 'filed') if n[k])
d = f'''<!DOCTYPE html>
<html lang="en">
<head>
{HEAD}
<title>Gowanus rezoning directory &mdash; bkcb6.app</title>
<meta name="description" content="Every new building filed in the Gowanus rezoning area since November 2021: what it is, its zoning and land use, each with its own profile.">
<link rel="canonical" href="https://bkcb6.app/gowanusbuildings/directory/">
</head>
{BAR}
<div class="wrap">
<div class="top-bar"><div class="top-txt"><h1>Gowanus rezoning directory</h1><p>Every new building since the rezoning, its zoning and land use</p></div><a class="back-link" href="/gowanusbuildings/">&larr; The map</a></div>
{groups}
{SRC}
</div>
<script>(function(){{try{{if(/[?&]app=1\\b/.test(location.search)||sessionStorage.getItem('bkapp')==='1')document.querySelectorAll('a[data-app]').forEach(function(a){{a.href+='?app=1'}})}}catch(e){{}}}})();</script>
</body>
</html>
'''
os.makedirs(os.path.join(OUT, 'directory'), exist_ok=True)
open(os.path.join(OUT, 'directory', 'index.html'), 'w').write(d)
print(len(J), 'buildings:', {k: len(v) for k, v in n.items()}, 'apartments', {k: int(v) for k, v in u.items()}, 'affordable', {k: int(v) for k, v in a.items()}, 'places', cnt, 'stations', len(stations), 'buses', len(buses))

# ---------- the Gowanus rezoning map (the home page map card), for the site and the apps' Gowanus screen ----------
GM = os.path.join(ROOT, 'gowanusmap')
os.makedirs(GM, exist_ok=True)
gm = f'''<!DOCTYPE html>
<html lang="en">
<head>
{HEAD}
<title>Gowanus rezoning map &mdash; bkcb6.app</title>
<meta name="description" content="The Gowanus rezoning on one map: zoning, land use, every new building since the rezoning with its profile, NYCHA, community groups, subway and buses. Search any address.">
<link rel="canonical" href="https://bkcb6.app/gowanusmap/">
<style>
.finder{{padding:14px}}
#map{{height:560px}}
@media(max-width:600px){{#map{{height:480px}}}}
.embed .finder{{padding:0;background:transparent}}
.embed .wrap{{background:transparent}}
</style>
</head>
{BAR}
<script>try{{if(/[?&]embed=1\\b/.test(location.search))document.documentElement.className+=' embed'}}catch(e){{}}</script>
<div class="wrap">
<div class="finder"><div class="hm-card">
  <div class="hm-top">
    <div class="hm-h">The Gowanus rezoning</div>
    <div class="hm-l">Search an address or a corner to see its zoning and any new building there. Tap a building for its description, zoning and land use.</div>
    <div class="seg"><button id="m-addr" class="on" type="button">Address</button><button id="m-corner" type="button">Street and cross street</button></div>
    <div id="addr-wrap"><div class="box"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0d1b4b" stroke-width="2.6" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/></svg><input id="q" type="search" placeholder="Address, e.g. 420 Carroll Street" autocomplete="off" aria-label="Address"></div><div class="drop"><ul id="ac"></ul></div></div>
    <div id="corner-wrap" class="corner"><select id="st" aria-label="Street"><option value="">Loading streets</option></select><select id="cx" aria-label="Cross street"><option value="">Cross street</option></select><button id="go" type="button">Go</button></div>
  </div>
  <div class="key" id="key"></div>
  <div id="map" data-index="1" data-rezoning="1"></div>
  <div id="res" class="result"></div>
  <div class="hm-foot">
    <div class="lbl">ZONING AND LAND USE</div>
    <div class="pills">
      <button class="pill on" type="button" data-l="zoning" style="--c:#238b45"><i></i>Zoning</button>
      <button class="pill" type="button" data-l="landuse" style="--c:#a855f7"><i></i>Land use</button>
    </div>
    <div class="lbl">NEW BUILDINGS SINCE THE REZONING</div>
    <div class="pills">
      <button class="pill on" type="button" data-l="open" style="--c:#0d1b4b"><i></i>Open<span class="n">{len(n["open"])}</span></button>
      <button class="pill on" type="button" data-l="building" style="--c:#f47920"><i></i>Permitted<span class="n">{len(n["building"])}</span></button>
      <button class="pill on" type="button" data-l="filed" style="--c:#0e7490"><i></i>Filed<span class="n">{len(n["filed"])}</span></button>
    </div>
    <div class="lbl">AROUND THE REZONING</div>
    <div class="pills">
      <button class="pill on" type="button" data-l="groups" style="--c:#16a34a"><i></i>Community groups<span class="n">{cnt["groups"]}</span></button>
      <button class="pill on" type="button" data-l="nycha" style="--c:#1d4ed8"><i></i>NYCHA<span class="n">{cnt["nycha"]}</span></button>
      <button class="pill" type="button" data-l="biz" style="--c:#b45309"><i></i>Local businesses<span class="n">{cnt["biz"]}</span></button>
      <button class="pill" type="button" data-l="fac" style="--c:#7c3aed"><i></i>Schools, parks and facilities<span class="n">{cnt["fac"]}</span></button>
    </div>
    <div class="lbl">TRAINS AND BUSES</div>
    <div class="pills">
      <button class="pill on" type="button" data-l="subway" style="--c:#FF6319"><i></i>Subway<span class="n">{len(stations)}</span></button>
      <button class="pill" type="button" data-l="bus" style="--c:#0039a6"><i></i>Bus routes<span class="n">{len(buses)}</span></button>
    </div>
    <div class="lbl">PROFILES: EVERY NEW BUILDING</div>
    <div class="profs" id="profs"></div>
  </div>
</div></div>
</div>
<script src="/gowanusbuildings/gb.js?v=5"></script>
</body>
</html>
'''
open(os.path.join(GM, 'index.html'), 'w').write(gm)
