#!/usr/bin/env python3
"""Builds the app's daily CB6 feeds: 311, crime, tickets and permits (DOB, DOT street work, film, permitted events
incl. block parties). Every record from the last 365 days inside Brooklyn Community Board 6 is kept; nothing is
sampled. Output goes to app/data/civic/feeds/*.json and app/manifest.json is updated so installed apps download
the new files. Run daily by .github/workflows/app-feeds.yml.
"""
import datetime as dt, hashlib, json, os, sys, time, urllib.parse, urllib.request

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
    return dict(generated=NOW.strftime('%Y-%m-%dT%H:%MZ'), since=START[:10], source=source, url=url, count=len(rows), **kw)

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

# permits: the daily feeds bkcb6.app already builds
def site_file(name):
    f = os.path.join(ROOT, 'data', name)
    if os.path.exists(f): return json.load(open(f))
    return get('https://bkcb6.app/data/' + name)

def build_permits():
    rows, K = [], Table()
    dob = site_file('cb6_dob_now_recent.json')
    for x in dob['rows']:
        rows.append(['dob-' + (x.get('tracking_number') or x.get('job_filing_number') or ''), day(x.get('issued_date')), day(x.get('expired_date')), K('Building (DOB)'),
                     x.get('work_type') or '', f"{x.get('house_no') or ''} {(x.get('street_name') or '').title()}".strip(), x.get('permit_status') or '',
                     ' '.join(p for p in [(x.get('applicant_first_name') or '').title(), (x.get('applicant_last_name') or '').title()] if p),
                     num(x.get('latitude')), num(x.get('longitude')), x.get('job_filing_number') or ''])
    dot = site_file('cb6_dot_recent.json')
    try:
        from pyproj import Transformer
        sp = Transformer.from_crs('EPSG:2263', 'EPSG:4326', always_xy=True)
    except Exception:
        sp = None
    def wkt_mid(w):
        # DOT gives the permit's street segment in State Plane feet; its midpoint marks the permit.
        try:
            nums = [float(v) for v in w.replace('(', ' ').replace(')', ' ').replace(',', ' ').split()[1:] if v.replace('.', '').replace('-', '').isdigit()]
            pts = list(zip(nums[0::2], nums[1::2]))
            x, y = pts[len(pts) // 2] if len(pts) > 2 else ((pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2)
            lo, la = sp.transform(x, y)
            return round(la, 5), round(lo, 5)
        except Exception:
            return None, None
    def msdate(s):
        try: return dt.datetime.utcfromtimestamp(int(str(s).split('(')[1].split(')')[0][:10])).strftime('%Y-%m-%d')
        except Exception: return ''
    for x in dot['rows']:
        where = (x.get('onstreetname') or '').title()
        if x.get('fromstreetname'): where += f" between {(x.get('fromstreetname') or '').title()} and {(x.get('tostreetname') or '').title()}"
        la, lo = wkt_mid(x.get('wkt') or '') if sp else (None, None)
        rows.append(['dot-' + (x.get('permitnumber') or ''), x.get('permitissuedate') or msdate(x.get('PermitIssueDateFrom')), msdate(x.get('IssuedWorkEndDate')),
                     K('Street work (DOT)'), (x.get('permittypedesc') or '').capitalize(), where, '', (x.get('permitteename') or '').title(), la, lo, x.get('permitnumber') or ''])
    film = site_file('cb6_film_permits.json')
    for x in film['rows']:
        rows.append(['film-' + str(x.get('event_id')), day(x.get('start_datetime')), day(x.get('end_datetime')), K('Film'), ' · '.join(p for p in [x.get('category'), x.get('subcategory')] if p and p != 'Not Applicable'),
                     x.get('parking_held') or '', x.get('event_type') or '', '', None, None, str(x.get('event_id'))])
    ev = site_file('cb6_permitted_events.json')
    for x in ev['rows']:
        kind = 'Block party' if 'block party' in (x.get('event_type') or '').lower() else ('Street event' if (x.get('street_closure_type') or 'N/A') != 'N/A' else 'Event')
        rows.append(['evt-' + str(x.get('event_id')), day(x.get('start_datetime')), day(x.get('end_datetime')), K(kind), f"{x.get('event_name') or ''} · {x.get('event_type') or ''}".strip(' ·'),
                     x.get('event_location') or x.get('address') or '', x.get('street_closure_type') if x.get('street_closure_type') not in (None, 'N/A') else '', x.get('event_agency') or '',
                     num(x.get('lat')), num(x.get('lng')), str(x.get('event_id'))])
    rows.sort(key=lambda r: r[1] or '', reverse=True)
    write('permits.json', dict(meta('DOB NOW permits, DOT street permits, Film permits and Permitted Event Information', 'https://bkcb6.app/permits', rows,
                                    sources={'Building (DOB)': dob.get('generated_at'), 'Street work (DOT)': dot.get('generated_at'), 'Film': film.get('generated_at'), 'Events': ev.get('generated_at')}),
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
