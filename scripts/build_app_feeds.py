#!/usr/bin/env python3
"""Builds the app's daily CB6 feeds: 311, crime, tickets and permits (DOB, DOT street work, film, permitted events
incl. block parties). Every record from the last 365 days inside Brooklyn Community Board 6 is kept; nothing is
sampled. Output goes to app/data/civic/feeds/*.json and app/manifest.json is updated so installed apps download
the new files. Run daily by .github/workflows/app-feeds.yml.
"""
import collections, datetime as dt, hashlib, json, os, sys, time, urllib.parse, urllib.request

ROOT = os.environ.get('ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'app/data/civic/feeds')
SOC = 'https://data.cityofnewyork.us/resource/'
TOKEN = os.environ.get('SOCRATA_TOKEN', 'HvFoIfzodzpRML7a1104Ca2tM')
NOW = dt.datetime.utcnow()
START = (NOW - dt.timedelta(days=365)).strftime('%Y-%m-%dT00:00:00')

# CB6 boundary
def load_poly():
    for p in ('cb6_boundary.geojson', 'data/cb6_boundary.geojson'):
        f = os.path.join(ROOT, p)
        if os.path.exists(f):
            g = json.load(open(f))
            geom = g['features'][0]['geometry'] if 'features' in g else g['geometry']
            polys = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
            return [[[pt[:2] for pt in ring] for ring in poly] for poly in polys]
    raise SystemExit('cb6_boundary.geojson not found')
POLY = load_poly()
LONS = [x for poly in POLY for ring in poly for x, _ in ring]
LATS = [y for poly in POLY for ring in poly for _, y in ring]
BOX = (max(LATS) + 0.002, min(LONS) - 0.002, min(LATS) - 0.002, max(LONS) + 0.002)  # N, W, S, E

def inside(lon, lat):
    hit = False
    for poly in POLY:
        for ring in poly:
            j = len(ring) - 1
            for i in range(len(ring)):
                xi, yi = ring[i]; xj, yj = ring[j]
                if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi:
                    hit = not hit
                j = i
    return hit

def get(url, tries=5):
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={'X-App-Token': TOKEN, 'User-Agent': 'bkcb6-app-feeds'})
            return json.loads(urllib.request.urlopen(req, timeout=300).read())
        except Exception as e:
            print('  retry', t + 1, e, file=sys.stderr); time.sleep(10 * (t + 1))
    raise SystemExit('failed: ' + url)

def fetch(ds, select, where, order, page=50000):
    rows, off = [], 0
    while True:
        q = urllib.parse.urlencode({'$select': select, '$where': where, '$order': order, '$limit': page, '$offset': off})
        chunk = get(SOC + ds + '.json?' + q)
        rows += chunk
        print(f'  {ds}: {len(rows)}', file=sys.stderr)
        if len(chunk) < page: return rows
        off += page

def num(v, nd=5):
    try: return round(float(v), nd)
    except Exception: return None

class Table:
    """Repeated strings stored once."""
    def __init__(self): self.vals, self.ix = [], {}
    def __call__(self, s):
        s = (s or '').strip()
        if s not in self.ix: self.ix[s] = len(self.vals); self.vals.append(s)
        return self.ix[s]

def day(s): return (s or '')[:10]
def hm(s): return (s or '')[11:16]

def write(name, obj):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), 'w') as f: json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
    print(name, obj.get('count'), file=sys.stderr)

def meta(source, url, rows, **kw):
    d = dict(generated=NOW.strftime('%Y-%m-%dT%H:%MZ'), since=START[:10], source=source, url=url, count=len(rows)); d.update(kw); return d

# 311
def build_311():
    r = fetch('erm2-nwe9', 'unique_key,created_date,closed_date,agency,complaint_type,descriptor,incident_address,street_name,cross_street_1,cross_street_2,status,latitude,longitude',
              f"community_board='06 BROOKLYN' AND created_date >= '{START}'", 'created_date DESC')
    T, D, A, S = Table(), Table(), Table(), Table()
    rows = [[x.get('unique_key'), day(x.get('created_date')), hm(x.get('created_date')), day(x.get('closed_date')),
             T(x.get('complaint_type')), D(x.get('descriptor')), A(x.get('agency')), S(x.get('status')),
             (x.get('incident_address') or '').title(), (x.get('street_name') or '').title(),
             (x.get('cross_street_1') or '').title(), (x.get('cross_street_2') or '').title(),
             num(x.get('latitude')), num(x.get('longitude'))] for x in r]
    write('311.json', dict(meta('NYC 311 Service Requests from 2010 to Present', 'https://data.cityofnewyork.us/d/erm2-nwe9', rows),
                           cols=['id', 'date', 'time', 'closed', 'type', 'descriptor', 'agency', 'status', 'address', 'street', 'cross1', 'cross2', 'lat', 'lon'],
                           types=T.vals, descriptors=D.vals, agencies=A.vals, statuses=S.vals, rows=rows))

# crime: year to date plus the historic file for the rest of the 365 days
def build_crime():
    sel = 'cmplnt_num,cmplnt_fr_dt,cmplnt_fr_tm,addr_pct_cd,ofns_desc,pd_desc,law_cat_cd,prem_typ_desc,loc_of_occur_desc,latitude,longitude'
    box = 'within_box(lat_lon, %f, %f, %f, %f)' % BOX
    ytd = fetch('5uac-w243', sel, f"{box} AND cmplnt_fr_dt >= '{START}'", 'cmplnt_fr_dt DESC')
    seen = {x['cmplnt_num'] for x in ytd}
    hist = fetch('qgea-i56i', sel, f"{box} AND cmplnt_fr_dt >= '{START}'", 'cmplnt_fr_dt DESC')
    allr = ytd + [x for x in hist if x['cmplnt_num'] not in seen]
    O, P, L, M = Table(), Table(), Table(), Table()
    rows = []
    for x in allr:
        la, lo = num(x.get('latitude')), num(x.get('longitude'))
        if la is None or lo is None or not inside(lo, la): continue
        rows.append([x.get('cmplnt_num'), day(x.get('cmplnt_fr_dt')), (x.get('cmplnt_fr_tm') or '')[:5], O(x.get('ofns_desc')), P(x.get('pd_desc')),
                     L({'FELONY': 'Felony', 'MISDEMEANOR': 'Misdemeanor', 'VIOLATION': 'Violation'}.get(x.get('law_cat_cd'), x.get('law_cat_cd'))),
                     M((x.get('prem_typ_desc') or '').title()), x.get('addr_pct_cd'), la, lo])
    rows.sort(key=lambda r: r[1], reverse=True)
    write('crime.json', dict(meta('NYPD Complaint Data, Current (Year to Date) and Historic', 'https://data.cityofnewyork.us/d/5uac-w243', rows,
                                  note='Complaints reported to NYPD, located inside the CB6 boundary. NYPD offsets locations to the middle of the block and withholds the location of some offenses.'),
                             cols=['id', 'date', 'time', 'offense', 'description', 'level', 'premises', 'precinct', 'lat', 'lon'],
                             offenses=O.vals, descriptions=P.vals, levels=L.vals, premises=M.vals, rows=rows))

# tickets: moving violation (B) summonses, year to date plus historic
def build_tickets():
    sel = 'evnt_key,violation_date,violation_time,chg_law_cd,violation_code,veh_category,rpt_owning_cmd,latitude,longitude'
    ytd = fetch('57p3-pdcj', sel, "within_box(location_point, %f, %f, %f, %f) AND violation_date >= '%s'" % (*BOX, START), 'violation_date DESC')
    seen = {x.get('evnt_key') for x in ytd}
    hist = fetch('bme5-7ty4', sel, "within_box(location, %f, %f, %f, %f) AND violation_date >= '%s'" % (*BOX, START), 'violation_date DESC')
    allr = ytd + [x for x in hist if x.get('evnt_key') not in seen]
    C, V = Table(), Table()
    rows = []
    for x in allr:
        la, lo = num(x.get('latitude')), num(x.get('longitude'))
        if la is None or lo is None or not inside(lo, la): continue
        code = ' '.join(p for p in [(x.get('chg_law_cd') or '').strip(), (x.get('violation_code') or '').strip()] if p)
        rows.append([x.get('evnt_key'), day(x.get('violation_date')), (x.get('violation_time') or '')[:5], C(code), V((x.get('veh_category') or '').title()),
                     x.get('rpt_owning_cmd'), la, lo])
    rows.sort(key=lambda r: r[1], reverse=True)
    write('tickets.json', dict(meta('NYPD Moving Violation (B) Summonses, Year to Date and Historic', 'https://data.cityofnewyork.us/d/57p3-pdcj', rows,
                                    note='Moving violation summonses written by NYPD, located inside the CB6 boundary. Parking tickets carry no location and are not included.'),
                               cols=['id', 'date', 'time', 'code', 'vehicle', 'command', 'lat', 'lon'], codes=C.vals, vehicles=V.vals, rows=rows))

# permits: every permit in the last 365 days, straight from NYC Open Data
def site_file(name):
    f = os.path.join(ROOT, 'data', name)
    try:
        if os.path.exists(f): return json.load(open(f))
        return get('https://bkcb6.app/data/' + name, tries=2)
    except BaseException:
        return {'rows': []}

def mdY(s):
    try: return dt.datetime.strptime((s or '').strip()[:10], '%m/%d/%Y').strftime('%Y-%m-%d')
    except Exception: return ''

def has_cb6(s):
    return '6' in [p.strip().lstrip('0') for p in (s or '').split(',')]

def build_permits():
    rows, K = [], Table()
    def name(*p): return ' '.join(x.strip().title() for x in p if x and x.strip())
    # Building permits, DOB NOW
    for x in fetch('rbx6-tga4', 'job_filing_number,work_permit,tracking_number,issued_date,expired_date,house_no,street_name,work_type,permit_status,applicant_first_name,applicant_last_name,applicant_business_name,job_description,latitude,longitude',
                   f"c_b_no='306' AND issued_date >= '{START}'", 'issued_date DESC'):
        what = x.get('work_type') or ''
        if x.get('job_description'): what += ' · ' + x['job_description'].strip()[:240]
        rows.append(['dob-' + (x.get('work_permit') or x.get('tracking_number') or x.get('job_filing_number') or ''), day(x.get('issued_date')), day(x.get('expired_date')), K('Building (DOB)'),
                     what, name(x.get('house_no'), x.get('street_name')), x.get('permit_status') or '',
                     name(x.get('applicant_business_name')) or name(x.get('applicant_first_name'), x.get('applicant_last_name')),
                     num(x.get('latitude')), num(x.get('longitude')), x.get('job_filing_number') or ''])
    # Building permits, DOB BIS (older jobs still issuing and renewing permits there)
    BIS_WORK = {'OT': 'Other', 'PL': 'Plumbing', 'MH': 'Mechanical', 'SP': 'Sprinkler', 'SD': 'Standpipe', 'BL': 'Boiler', 'FA': 'Fire alarm', 'EQ': 'Equipment', 'FB': 'Fuel burning', 'FP': 'Fire suppression', 'FS': 'Fuel storage', 'CC': 'Curb cut', 'NB': 'New building', 'DM': 'Demolition', 'EW': 'Equipment work', 'FO': 'Foundation', 'AL': 'Alteration'}
    START_D = START[:10]
    for x in fetch('ipu4-2q9a', 'job__,permit_si_no,issuance_date,expiration_date,house__,street_name,job_type,permit_type,work_type,permit_status,filing_status,permittee_s_first_name,permittee_s_last_name,permittee_s_business_name,gis_latitude,gis_longitude',
                   "community_board='306' AND (issuance_date like '%/" + START[:4] + "' OR issuance_date like '%/" + str(int(START[:4]) + 1) + "')", 'job__ DESC'):
        d = mdY(x.get('issuance_date'))
        if d < START_D: continue
        what = ' · '.join(p for p in [BIS_WORK.get(x.get('permit_type') or '', x.get('permit_type') or ''), BIS_WORK.get(x.get('work_type') or '', x.get('work_type') or ''), (x.get('filing_status') or '').title()] if p)
        rows.append(['bis-' + (x.get('permit_si_no') or ''), d, mdY(x.get('expiration_date')), K('Building (DOB)'), what,
                     name(x.get('house__'), ' '.join((x.get('street_name') or '').split())), (x.get('permit_status') or '').title(),
                     name(x.get('permittee_s_business_name')) or name(x.get('permittee_s_first_name'), x.get('permittee_s_last_name')),
                     num(x.get('gis_latitude')), num(x.get('gis_longitude')), 'BIS job ' + (x.get('job__') or '')])
    # DOT street permits. NYC Open Data no longer carries their geometry, so each permit is placed on CB6's block
    # faces by its street and cross streets (or house number), and NYC Streets' live map supplies exact locations for
    # every permit active now.
    from pyproj import Transformer
    sp = Transformer.from_crs('EPSG:2263', 'EPSG:4326', always_xy=True)
    to_sp = Transformer.from_crs('EPSG:4326', 'EPSG:2263', always_xy=True)
    import re
    ABBR = {'AVE': 'AVENUE', 'AV': 'AVENUE', 'ST': 'STREET', 'PL': 'PLACE', 'BLVD': 'BOULEVARD', 'PKWY': 'PARKWAY', 'RD': 'ROAD', 'DR': 'DRIVE',
            'E': 'EAST', 'W': 'WEST', 'N': 'NORTH', 'S': 'SOUTH', 'EXPWY': 'EXPRESSWAY', 'EXPY': 'EXPRESSWAY', 'SQ': 'SQUARE', 'TER': 'TERRACE', 'LN': 'LANE', 'CT': 'COURT'}
    def norm(s):
        t = re.sub(r'[^A-Z0-9 ]', ' ', (s or '').upper()).split()
        t = [re.sub(r'^(\d+)(ST|ND|RD|TH)$', r'\1', w) for w in t]
        t = [ABBR.get(w, w) if i else ({'E': 'EAST', 'W': 'WEST'}.get(w, w)) for i, w in enumerate(t)]
        if t and t[-1] in ('STREET',) and len(t) > 2 and t[-2] == 'STREET': t = t[:-1]
        return ' '.join(t)
    faces = json.load(open(os.path.join(ROOT, 'scripts', 'app_feeds_streets.json')))['rows']
    corner, ranges = {}, collections.defaultdict(list)
    for on, fr, to, la1, lo1, la2, lo2, lo_n, hi_n, _ in faces:
        n_on, n_fr, n_to = norm(on), norm(fr), norm(to)
        corner[(n_on, n_fr)] = (la1, lo1); corner[(n_fr, n_on)] = (la1, lo1)
        corner[(n_on, n_to)] = (la2, lo2); corner[(n_to, n_on)] = (la2, lo2)
        try: ranges[n_on].append((int(re.sub(r'\D.*', '', lo_n)), int(re.sub(r'\D.*', '', hi_n)), (la1 + la2) / 2, (lo1 + lo2) / 2))
        except ValueError: pass
    def hnum(s):
        m = re.match(r'\s*(\d+)', s or '')
        return int(m.group(1)) if m else None
    def place(on, fr, to, house):
        n_on = norm(on)
        p1, p2 = corner.get((n_on, norm(fr))), corner.get((n_on, norm(to)))
        if p1 and p2: return (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        if p1 or p2: return p1 or p2
        h = hnum(house)
        if h is not None:
            for lo_n, hi_n, la, lo in ranges.get(n_on, []):
                if min(lo_n, hi_n) - 1 <= h <= max(lo_n, hi_n) + 1: return la, lo
        return None
    def st(s):
        t = ' '.join((s or '').split()).title()
        return re.sub(r'\b(\d+)\b(?= (Street|Avenue|Place|Road|Drive|Terrace|Court))', lambda m: m.group(1) + ('th' if 10 <= int(m.group(1)) % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(int(m.group(1)) % 10, 'th')), t)
    def ms(s):
        m = re.search(r'Date\((\d+)\)', str(s or ''))
        return dt.datetime.utcfromtimestamp(int(m.group(1)) / 1000).strftime('%Y-%m-%d') if m else ''
    def wkt_pts(w):
        nums = []
        for v in (w or '').replace('(', ' ').replace(')', ' ').replace(',', ' ').split():
            try: nums.append(float(v))
            except ValueError: pass
        return [sp.transform(a, b) for a, b in zip(nums[0::2], nums[1::2])]
    dot = {}
    def add_dot(pn, start, end, what, house, on, fr, to, status, who, la, lo):
        where = ' '.join(v for v in [(house or '').strip(), st(on)] if v)
        if fr and to: where += f' between {st(fr)} and {st(to)}'
        elif fr: where += f' at {st(fr)}'
        dot[pn] = ['dot-' + pn, start, end, K('Street work (DOT)'), (what or '').strip().capitalize(), where, (status or '').title(), st(who), round(la, 5), round(lo, 5), pn]
    for x in fetch('tqtj-sjs8', 'permitnumber,permitissuedate,issuedworkstartdate,issuedworkenddate,permithousenumber,onstreetname,fromstreetname,tostreetname,permitteename,permitstatusshortdesc,permittypedesc,permitseriesshortdesc',
                   f"boroughname='BROOKLYN' AND permitissuedate >= '{START}'", 'permitissuedate DESC'):
        p = place(x.get('onstreetname'), x.get('fromstreetname'), x.get('tostreetname'), x.get('permithousenumber'))
        if not p: continue
        add_dot(x.get('permitnumber') or '', day(x.get('issuedworkstartdate') or x.get('permitissuedate')), day(x.get('issuedworkenddate')),
                x.get('permittypedesc') or x.get('permitseriesshortdesc'), x.get('permithousenumber'), x.get('onstreetname'), x.get('fromstreetname'), x.get('tostreetname'),
                x.get('permitstatusshortdesc'), x.get('permitteename'), p[0], p[1])
    placed = len(dot)
    try:
        xs, ys = zip(*[to_sp.transform(x, y) for x, y in zip(LONS, LATS)])
        box = f'POLYGON(({min(xs)} {min(ys)}, {max(xs)} {min(ys)}, {max(xs)} {max(ys)}, {min(xs)} {max(ys)}, {min(xs)} {min(ys)}))'
        live = get('https://nycstreets.net/Public/Permits/PermitSearchMobile/?' + urllib.parse.urlencode({'Wkt': box}), tries=3)
    except BaseException as e:
        print('  nycstreets.net unavailable:', e, file=sys.stderr); live = []
    n_live = 0
    for x in live:
        pts = wkt_pts(x.get('Wkt'))
        if len(pts) > 1: pts += [((pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2) for i in range(len(pts) - 1)]
        hits = [q for q in pts if inside(q[0], q[1])]
        if not hits: continue
        lo, la = hits[len(hits) // 2]
        pn = (x.get('PermitNumber') or '').strip()
        old = dot.get(pn)
        add_dot(pn, ms(x.get('IssuedWorkStartDate')) or ms(x.get('PermitIssueDateFrom')), ms(x.get('IssuedWorkEndDate')), x.get('PermitTypeDesc'), x.get('PermitHouseNumber'),
                x.get('OnStreetName'), x.get('FromStreetName'), x.get('ToStreetName'), x.get('Status'), x.get('PermitteeName'), la, lo)
        if old and old[1] and old[1] < dot[pn][1]: dot[pn][1] = old[1]
        n_live += 1
    print(f'  DOT: {placed} placed from Open Data, {n_live} from NYC Streets live, {len(dot)} total', file=sys.stderr)
    rows += list(dot.values())
    # Film permits: every Mayor's Office of Media & Entertainment notice CB6 has received (filmingpermits/permits.json,
    # kept from the board's email), plus any CB6 film permit in NYC Open Data that has no notice on file.
    def L(s): return ' '.join((s or '').split())
    notices = []
    for p in (os.path.join(ROOT, 'filmingpermits', 'permits.json'),):
        try: notices = json.load(open(p))
        except Exception: notices = get('https://bkcb6.app/filmingpermits/permits.json', tries=2)
    have = set()
    for x in notices:
        locs = x.get('locations') or []
        def lw(l):
            if l.get('address'): s = re.sub(r',\s*Brooklyn$', '', l['address'], flags=re.I)
            elif l.get('between'): s = f"{l['between'][0]} between {l['between'][1]} and {l['between'][2]}" if len(l['between']) == 3 else ' '.join(l['between'])
            else: s = ''
            return ': '.join(v for v in [L(l.get('name')), st(s)] if v)
        park = [f"{st(q.get('street'))} between {st(q.get('from'))} and {st(q.get('to'))} ({', '.join(v for v in [q.get('side'), q.get('control')] if v)})" for l in locs for q in l.get('parking', [])]
        pts = [(l['lat'], l['lng']) for l in locs if l.get('lat') is not None]
        inn = [q for q in pts if inside(q[1], q[0])]
        la, lo = (inn or pts or [(None, None)])[0]
        ends = sorted(mdY(l.get('end', '')[:10]) for l in locs if l.get('end'))
        rows.append(['film-' + str(x['permit']), x.get('shootDate', ''), ends[-1] if ends else x.get('shootDate', ''), K('Film'),
                     ' · '.join(v for v in [L(x.get('production')), x.get('type')] if v), ' / '.join(lw(l) for l in locs),
                     '; '.join(park), ('Locations Department ' + x['contact']) if x.get('contact') else '', la, lo, str(x['permit'])])
        have.add(str(x['permit']))
    for x in fetch('tg4x-b46p', 'eventid,eventtype,startdatetime,enddatetime,parkingheld,communityboard_s,category,subcategoryname',
                   f"borough='Brooklyn' AND startdatetime >= '{START}'", 'startdatetime DESC'):
        if not has_cb6(x.get('communityboard_s')) or str(x.get('eventid')) in have: continue
        rows.append(['film-' + str(x.get('eventid')), day(x.get('startdatetime')), day(x.get('enddatetime')), K('Film'),
                     ' · '.join(p for p in [x.get('category'), x.get('subcategoryname')] if p and p != 'Not Applicable'),
                     '', st(x.get('parkingheld')), "Mayor's Office of Media & Entertainment", None, None, str(x.get('eventid'))])
    # Permitted events incl. block parties: current file plus the historical one
    geo = {str(r.get('event_id')): (num(r.get('lat')), num(r.get('lng'))) for r in site_file('cb6_permitted_events.json').get('rows', [])}
    seen = set()
    sel = 'event_id,event_name,start_date_time,end_date_time,event_agency,event_type,event_location,street_closure_type,community_board'
    for ds, where in (('tvpp-9vvx', "event_borough='Brooklyn'"), ('bkfu-528j', f"event_borough='Brooklyn' AND start_date_time >= '{START}'")):
        for x in fetch(ds, sel, where, 'start_date_time DESC'):
            eid = str(x.get('event_id'))
            if eid in seen or not has_cb6(x.get('community_board')): continue
            if day(x.get('start_date_time')) < START[:10]: continue
            seen.add(eid)
            et = x.get('event_type') or ''
            closure = x.get('street_closure_type') or 'N/A'
            kind = 'Block party' if 'block party' in et.lower() else ('Street event' if closure != 'N/A' else 'Event')
            la, lo = geo.get(eid, (None, None))
            rows.append(['evt-' + eid, day(x.get('start_date_time')), day(x.get('end_date_time')), K(kind), f"{x.get('event_name') or ''} · {et}".strip(' ·'),
                         x.get('event_location') or '', closure if closure != 'N/A' else '', x.get('event_agency') or '', la, lo, eid])
    rows.sort(key=lambda r: r[1] or '', reverse=True)
    stamp = NOW.strftime('%Y-%m-%dT%H:%MZ')
    first = min([START[:10]] + [x.get('shootDate') for x in notices if x.get('shootDate')])
    write('permits.json', dict(meta('DOB NOW and DOB BIS permits, DOT Street Construction Permits, Mayor\'s Office of Media & Entertainment film notices to CB6, Film Permits and NYC Permitted Event Information', 'https://bkcb6.app/permits', rows,
                                    sources={'Building (DOB)': stamp, 'Street work (DOT)': stamp, 'Film': stamp, 'Events': stamp}, since=first),
                               cols=['id', 'start', 'end', 'kind', 'what', 'where', 'status', 'who', 'lat', 'lon', 'ref'], kinds=K.vals, rows=rows))

def manifest():
    mp = os.path.join(ROOT, 'app/manifest.json')
    m = json.load(open(mp)) if os.path.exists(mp) else {'files': {}}
    for n in sorted(os.listdir(OUT)):
        rel = 'civic/feeds/' + n
        b = open(os.path.join(OUT, n), 'rb').read()
        m.setdefault('files', {})[rel] = {'sha': hashlib.sha256(b).hexdigest(), 'size': len(b)}
    m['generated'] = NOW.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    # Same layout build_app_calendar.mjs writes, so the two jobs never fight over formatting.
    txt = '\n'.join(l.lstrip(' ') for l in json.dumps(m, indent=1).split('\n'))
    open(mp, 'w').write(txt)

if __name__ == '__main__':
    only = sys.argv[1:] or ['311', 'crime', 'tickets', 'permits']
    for k in only: {'311': build_311, 'crime': build_crime, 'tickets': build_tickets, 'permits': build_permits}[k]()
    if os.path.exists(os.path.join(ROOT, 'app')): manifest()
