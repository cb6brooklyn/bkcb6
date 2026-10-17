#!/usr/bin/env python3
"""The apps' four feeds (311, crime, tickets, permits; every record of the last 365 days) for every community board,
in the same files the apps build on the phone (FeedFetch.swift) and the daily CB6 job builds (build_app_feeds.py),
gzipped: out/<borocd>-<kind>.json.gz, plus out/index.json. Published daily as assets of the GitHub release
"board-feeds" by .github/workflows/board-feeds.yml, so a phone pulls a ready file instead of querying Open Data.
Nothing is sampled: every row Open Data returns for the board is kept.
usage: build_board_feeds.py [outdir] [borocd ...]
"""
import concurrent.futures as cf, datetime as dt, gzip, json, os, re, sys, threading, time, urllib.parse, urllib.request

ROOT = os.environ.get('ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOC = 'https://data.cityofnewyork.us/resource/'
TOKEN = os.environ.get('SOCRATA_TOKEN', 'HvFoIfzodzpRML7a1104Ca2tM')
NOW = dt.datetime.utcnow()
START = (NOW - dt.timedelta(days=365)).strftime('%Y-%m-%dT00:00:00')
BORO = {'1': ('MANHATTAN', 'Manhattan', 'mn'), '2': ('BRONX', 'Bronx', 'bx'), '3': ('BROOKLYN', 'Brooklyn', 'bk'),
        '4': ('QUEENS', 'Queens', 'qn'), '5': ('STATEN ISLAND', 'Staten Island', 'si')}
CODE = {'MN': '1', 'BX': '2', 'BK': '3', 'QN': '4', 'SI': '5'}

def log(*a): print(*a, file=sys.stderr, flush=True)

def get(url, tries=6):
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={'X-App-Token': TOKEN, 'User-Agent': 'bkcb6-board-feeds'})
            return json.loads(urllib.request.urlopen(req, timeout=600).read())
        except Exception as e:
            log('  retry', t + 1, str(e)[:120]); time.sleep(15 * (t + 1))
    raise RuntimeError('failed: ' + url[:200])

def fetch(ds, select, where, order, page=50000):
    rows, off = [], 0
    while True:
        q = urllib.parse.urlencode({'$select': select, '$where': where, '$order': order, '$limit': page, '$offset': off})
        chunk = get(SOC + ds + '.json?' + q)
        rows += chunk
        if len(chunk) < page: return rows
        off += page

def num(v, nd=5):
    try: return round(float(v), nd)
    except Exception: return None

class Table:
    def __init__(self): self.vals, self.ix = [], {}
    def __call__(self, s):
        s = (s or '').strip()
        if s not in self.ix: self.ix[s] = len(self.vals); self.vals.append(s)
        return self.ix[s]

def day(s): return (s or '')[:10]
def hm(s): return (s or '')[11:16]
def title(s): return ' '.join((s or '').split()).title()

# Board outlines
def load_boards():
    g = json.load(open(os.path.join(ROOT, 'app/data/civic/useofland/cd-polygons.geojson')))
    names = {b['borocd']: b['name'] for b in json.load(open(os.path.join(ROOT, 'app/data/civic/boards.json')))}
    out = {}
    for f in g['features']:
        c = f['properties']['cb_code']; cd = CODE[c[:2]] + '%02d' % int(c[4:])
        geom = f['geometry']
        polys = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
        polys = [[[pt[:2] for pt in ring] for ring in poly] for poly in polys]
        lons = [x for p in polys for r in p for x, _ in r]; lats = [y for p in polys for r in p for _, y in r]
        out[cd] = {'name': names.get(cd, cd), 'poly': polys, 'box': (max(lats) + 0.002, min(lons) - 0.002, min(lats) - 0.002, max(lons) + 0.002)}
    return out

def inside(polys, lon, lat):
    hit = False
    for poly in polys:
        for ring in poly:
            j = len(ring) - 1
            for i in range(len(ring)):
                xi, yi = ring[i]; xj, yj = ring[j]
                if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi: hit = not hit
                j = i
    return hit

def meta(b, source, url, rows, **kw):
    d = dict(generated=NOW.strftime('%Y-%m-%dT%H:%MZ'), since=START[:10], source=source, url=url, count=len(rows), board=b['name']); d.update(kw); return d

def f311(cd, b):
    n2 = cd[1:]
    r = fetch('erm2-nwe9', 'unique_key,created_date,closed_date,agency,complaint_type,descriptor,incident_address,street_name,cross_street_1,cross_street_2,status,latitude,longitude',
              f"community_board='{n2} {BORO[cd[0]][0]}' AND created_date >= '{START}'", 'created_date DESC')
    T, D, A, S = Table(), Table(), Table(), Table()
    rows = [[x.get('unique_key'), day(x.get('created_date')), hm(x.get('created_date')), day(x.get('closed_date')),
             T(x.get('complaint_type')), D(x.get('descriptor')), A(x.get('agency')), S(x.get('status')),
             title(x.get('incident_address')), title(x.get('street_name')), title(x.get('cross_street_1')), title(x.get('cross_street_2')),
             num(x.get('latitude')), num(x.get('longitude'))] for x in r]
    return dict(meta(b, 'NYC 311 Service Requests from 2010 to Present', 'https://data.cityofnewyork.us/d/erm2-nwe9', rows),
                cols=['id', 'date', 'time', 'closed', 'type', 'descriptor', 'agency', 'status', 'address', 'street', 'cross1', 'cross2', 'lat', 'lon'],
                types=T.vals, descriptors=D.vals, agencies=A.vals, statuses=S.vals, rows=rows)

def fcrime(cd, b):
    sel = 'cmplnt_num,cmplnt_fr_dt,cmplnt_fr_tm,addr_pct_cd,ofns_desc,pd_desc,law_cat_cd,prem_typ_desc,latitude,longitude'
    box = 'within_box(lat_lon, %f, %f, %f, %f)' % b['box']
    ytd = fetch('5uac-w243', sel, f"{box} AND cmplnt_fr_dt >= '{START}'", 'cmplnt_fr_dt DESC')
    seen = {x.get('cmplnt_num') for x in ytd}
    hist = fetch('qgea-i56i', sel, f"{box} AND cmplnt_fr_dt >= '{START}'", 'cmplnt_fr_dt DESC')
    O, P, L, M = Table(), Table(), Table(), Table()
    rows = []
    for x in ytd + [x for x in hist if x.get('cmplnt_num') not in seen]:
        la, lo = num(x.get('latitude')), num(x.get('longitude'))
        if la is None or lo is None or not inside(b['poly'], lo, la): continue
        rows.append([x.get('cmplnt_num'), day(x.get('cmplnt_fr_dt')), (x.get('cmplnt_fr_tm') or '')[:5], O(x.get('ofns_desc')), P(x.get('pd_desc')),
                     L({'FELONY': 'Felony', 'MISDEMEANOR': 'Misdemeanor', 'VIOLATION': 'Violation'}.get(x.get('law_cat_cd'), x.get('law_cat_cd'))),
                     M(title(x.get('prem_typ_desc'))), x.get('addr_pct_cd'), la, lo])
    rows.sort(key=lambda r: r[1] or '', reverse=True)
    return dict(meta(b, 'NYPD Complaint Data, Current (Year to Date) and Historic', 'https://data.cityofnewyork.us/d/5uac-w243', rows,
                     note='Complaints reported to NYPD, located inside the %s boundary. NYPD offsets locations to the middle of the block and withholds the location of some offenses.' % b['name']),
                cols=['id', 'date', 'time', 'offense', 'description', 'level', 'premises', 'precinct', 'lat', 'lon'],
                offenses=O.vals, descriptions=P.vals, levels=L.vals, premises=M.vals, rows=rows)

def ftickets(cd, b):
    sel = 'evnt_key,violation_date,violation_time,chg_law_cd,violation_code,veh_category,rpt_owning_cmd,latitude,longitude'
    ytd = fetch('57p3-pdcj', sel, "within_box(location_point, %f, %f, %f, %f) AND violation_date >= '%s'" % (*b['box'], START), 'violation_date DESC')
    seen = {x.get('evnt_key') for x in ytd}
    hist = fetch('bme5-7ty4', sel, "within_box(location, %f, %f, %f, %f) AND violation_date >= '%s'" % (*b['box'], START), 'violation_date DESC')
    C, V = Table(), Table()
    rows = []
    for x in ytd + [x for x in hist if x.get('evnt_key') not in seen]:
        la, lo = num(x.get('latitude')), num(x.get('longitude'))
        if la is None or lo is None or not inside(b['poly'], lo, la): continue
        code = ' '.join(p for p in [(x.get('chg_law_cd') or '').strip(), (x.get('violation_code') or '').strip()] if p)
        rows.append([x.get('evnt_key'), day(x.get('violation_date')), (x.get('violation_time') or '')[:5], C(code), V(title(x.get('veh_category'))),
                     x.get('rpt_owning_cmd'), la, lo])
    rows.sort(key=lambda r: r[1] or '', reverse=True)
    return dict(meta(b, 'NYPD Moving Violation (B) Summonses, Year to Date and Historic', 'https://data.cityofnewyork.us/d/57p3-pdcj', rows,
                     note='Moving violation summonses written by NYPD, located inside the %s boundary. Parking tickets carry no location and are not included.' % b['name']),
                cols=['id', 'date', 'time', 'code', 'vehicle', 'command', 'lat', 'lon'], codes=C.vals, vehicles=V.vals, rows=rows)

# Borough-wide permit sources, fetched once per borough and shared by its boards.
_cache, _locks, _lock = {}, {}, threading.Lock()
def once(key, f):
    with _lock: lk = _locks.setdefault(key, threading.Lock())
    with lk:
        if key not in _cache:
            try: _cache[key] = f()
            except Exception as e: log('  source failed', key, e); _cache[key] = []
        return _cache[key]

ABBR = {'AVE': 'AVENUE', 'AV': 'AVENUE', 'ST': 'STREET', 'PL': 'PLACE', 'BLVD': 'BOULEVARD', 'PKWY': 'PARKWAY', 'RD': 'ROAD', 'DR': 'DRIVE',
        'E': 'EAST', 'W': 'WEST', 'N': 'NORTH', 'S': 'SOUTH', 'EXPWY': 'EXPRESSWAY', 'EXPY': 'EXPRESSWAY', 'SQ': 'SQUARE', 'TER': 'TERRACE', 'LN': 'LANE', 'CT': 'COURT'}
def norm(s):
    t = re.sub(r'[^A-Z0-9 ]', ' ', (s or '').upper()).split()
    t = [re.sub(r'^(\d+)(ST|ND|RD|TH)$', r'\1', w) for w in t]
    t = [ABBR.get(w, w) if i else ({'E': 'EAST', 'W': 'WEST'}.get(w, w)) for i, w in enumerate(t)]
    return ' '.join(t)
def st(s):
    t = ' '.join((s or '').split()).title()
    return re.sub(r'\b(\d+)\b(?= (Street|Avenue|Place|Road|Drive|Terrace|Court))',
                  lambda m: m.group(1) + ('th' if 10 <= int(m.group(1)) % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(int(m.group(1)) % 10, 'th')), t)
def has_board(s, n): return str(n) in [p.strip().lstrip('0') for p in (s or '').split(',')]

def mdY(s):
    try: return dt.datetime.strptime((s or '').strip()[:10], '%m/%d/%Y').strftime('%Y-%m-%d')
    except Exception: return ''

BIS_WORK = {'OT': 'Other', 'PL': 'Plumbing', 'MH': 'Mechanical', 'SP': 'Sprinkler', 'SD': 'Standpipe', 'BL': 'Boiler', 'FA': 'Fire alarm', 'EQ': 'Equipment',
            'FB': 'Fuel burning', 'FP': 'Fire suppression', 'FS': 'Fuel storage', 'NB': 'New building', 'DM': 'Demolition', 'A1': 'Alteration 1', 'A2': 'Alteration 2', 'A3': 'Alteration 3'}

def fpermits(cd, b):
    K, rows = Table(), []
    n = int(cd[1:]); boro_up, boro, key = BORO[cd[0]]
    def name(*p): return ' '.join(title(x) for x in p if x and x.strip())
    for x in fetch('rbx6-tga4', 'job_filing_number,work_permit,tracking_number,issued_date,expired_date,house_no,street_name,work_type,permit_status,applicant_first_name,applicant_last_name,applicant_business_name,job_description,latitude,longitude',
                   f"c_b_no='{cd}' AND issued_date >= '{START}'", 'issued_date DESC'):
        what = x.get('work_type') or ''
        if x.get('job_description'): what += ' · ' + x['job_description'].strip()[:240]
        rows.append(['dob-' + (x.get('work_permit') or x.get('tracking_number') or x.get('job_filing_number') or ''), day(x.get('issued_date')), day(x.get('expired_date')), K('Building (DOB)'),
                     what, name(x.get('house_no'), x.get('street_name')), x.get('permit_status') or '',
                     name(x.get('applicant_business_name')) or name(x.get('applicant_first_name'), x.get('applicant_last_name')),
                     num(x.get('latitude')), num(x.get('longitude')), x.get('job_filing_number') or ''])
    y1 = START[:4]; y2 = str(int(y1) + 1)
    try:
        bis = fetch('ipu4-2q9a', 'job__,permit_si_no,issuance_date,expiration_date,house__,street_name,job_type,permit_type,work_type,permit_status,filing_status,permittee_s_first_name,permittee_s_last_name,permittee_s_business_name,gis_latitude,gis_longitude',
                    f"community_board='{cd}' AND (issuance_date like '%/{y1}' OR issuance_date like '%/{y2}')", 'job__ DESC')
    except Exception as e:
        log('  BIS failed', cd, e); bis = []
    for x in bis:
        d = mdY(x.get('issuance_date'))
        if not d or d < START[:10]: continue
        what = ' · '.join(p for p in [BIS_WORK.get(x.get('permit_type') or '', x.get('permit_type') or ''), BIS_WORK.get(x.get('work_type') or '', x.get('work_type') or ''), title(x.get('filing_status'))] if p)
        rows.append(['bis-' + (x.get('permit_si_no') or ''), d, mdY(x.get('expiration_date')), K('Building (DOB)'), what,
                     name(x.get('house__'), x.get('street_name')), title(x.get('permit_status')),
                     name(x.get('permittee_s_business_name')) or name(x.get('permittee_s_first_name'), x.get('permittee_s_last_name')),
                     num(x.get('gis_latitude')), num(x.get('gis_longitude')), 'BIS job ' + (x.get('job__') or '')])
    # DOT street permits, placed on the board's block faces by street and cross streets (or house number)
    faces = once('faces-' + key, lambda: json.load(open(os.path.join(ROOT, 'assets/blocks/%s-geo.json' % key))))
    corner, by_street = {}, {}
    for r in faces:
        if len(r) < 9 or r[1] != int(cd): continue
        on, fr, to = norm(r[6]), norm(r[7]), norm(r[8])
        corner[(on, fr)] = (r[2], r[3]); corner[(fr, on)] = (r[2], r[3]); corner[(on, to)] = (r[4], r[5]); corner[(to, on)] = (r[4], r[5])
        by_street[on] = True
    dot = once('dot-' + key, lambda: fetch('tqtj-sjs8', 'permitnumber,permitissuedate,issuedworkstartdate,issuedworkenddate,permithousenumber,onstreetname,fromstreetname,tostreetname,permitteename,permitstatusshortdesc,permittypedesc,permitseriesshortdesc',
                                           f"boroughname='{boro_up}' AND permitissuedate >= '{START}'", 'permitissuedate DESC'))
    for x in dot:
        on = norm(x.get('onstreetname'))
        if on not in by_street: continue
        p1, p2 = corner.get((on, norm(x.get('fromstreetname')))), corner.get((on, norm(x.get('tostreetname'))))
        p = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2) if p1 and p2 else (p1 or p2)
        if not p: continue
        where = ' '.join(v for v in [(x.get('permithousenumber') or '').strip(), st(x.get('onstreetname'))] if v)
        if x.get('fromstreetname'): where += f" between {st(x.get('fromstreetname'))} and {st(x.get('tostreetname'))}"
        what = (x.get('permittypedesc') or x.get('permitseriesshortdesc') or '').strip().capitalize()
        rows.append(['dot-' + (x.get('permitnumber') or ''), day(x.get('issuedworkstartdate') or x.get('permitissuedate')), day(x.get('issuedworkenddate')), K('Street work (DOT)'),
                     what, where, title(x.get('permitstatusshortdesc')), st(x.get('permitteename')), round(p[0], 5), round(p[1], 5), x.get('permitnumber') or ''])
    film = once('film-' + key, lambda: fetch('tg4x-b46p', 'eventid,eventtype,startdatetime,enddatetime,parkingheld,communityboard_s,category,subcategoryname',
                                             f"borough='{boro}' AND startdatetime >= '{START}'", 'startdatetime DESC'))
    for x in film:
        if not has_board(x.get('communityboard_s'), n): continue
        rows.append(['film-' + str(x.get('eventid')), day(x.get('startdatetime')), day(x.get('enddatetime')), K('Film'),
                     ' · '.join(p for p in [x.get('category'), x.get('subcategoryname')] if p and p != 'Not Applicable'),
                     '', st(x.get('parkingheld')), "Mayor's Office of Media & Entertainment", None, None, str(x.get('eventid'))])
    sel = 'event_id,event_name,start_date_time,end_date_time,event_agency,event_type,event_location,street_closure_type,community_board'
    seen = set()
    for ds, where in (('tvpp-9vvx', f"event_borough='{boro}'"), ('bkfu-528j', f"event_borough='{boro}' AND start_date_time >= '{START}'")):
        for x in once(ds + key, lambda ds=ds, where=where: fetch(ds, sel, where, 'start_date_time DESC')):
            eid = str(x.get('event_id'))
            if eid in seen or not has_board(x.get('community_board'), n) or day(x.get('start_date_time')) < START[:10]: continue
            seen.add(eid)
            et = x.get('event_type') or ''; closure = x.get('street_closure_type') or 'N/A'
            kind = 'Block party' if 'block party' in et.lower() else ('Street event' if closure != 'N/A' else 'Event')
            rows.append(['evt-' + eid, day(x.get('start_date_time')), day(x.get('end_date_time')), K(kind), f"{x.get('event_name') or ''} · {et}".strip(' ·'),
                         x.get('event_location') or '', closure if closure != 'N/A' else '', x.get('event_agency') or '', None, None, eid])
    rows.sort(key=lambda r: r[1] or '', reverse=True)
    stamp = NOW.strftime('%Y-%m-%dT%H:%MZ')
    return dict(meta(b, "DOB NOW and DOB BIS permits, DOT Street Construction Permits, Film Permits and NYC Permitted Event Information", 'https://data.cityofnewyork.us/d/rbx6-tga4', rows,
                     sources={'Building (DOB)': stamp, 'Street work (DOT)': stamp, 'Film': stamp, 'Events': stamp},
                     note='Building permits (DOB), street construction permits (DOT), film shoots and permitted events, placed where the permit says.'),
                cols=['id', 'start', 'end', 'kind', 'what', 'where', 'status', 'who', 'lat', 'lon', 'ref'], kinds=K.vals, rows=rows)

KINDS = {'311': f311, 'crime': fcrime, 'tickets': ftickets, 'permits': fpermits}

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'board-feeds')
    only = set(sys.argv[2:])
    os.makedirs(out, exist_ok=True)
    boards = load_boards()
    jobs = [(cd, k) for cd in sorted(boards) if not only or cd in only for k in KINDS]
    index, failed, t0 = {}, [], time.time()
    def run(job):
        cd, k = job
        o = KINDS[k](cd, boards[cd])
        body = gzip.compress(json.dumps(o, ensure_ascii=False, separators=(',', ':')).encode(), 9)
        with open(os.path.join(out, f'{cd}-{k}.json.gz'), 'wb') as f: f.write(body)
        return cd, k, o['count'], len(body)
    with cf.ThreadPoolExecutor(max_workers=int(os.environ.get('WORKERS', '6'))) as ex:
        futs = {ex.submit(run, j): j for j in jobs}
        for f in cf.as_completed(futs):
            cd, k = futs[f]
            try:
                _, _, n, size = f.result()
                index.setdefault(cd, {})[k] = {'count': n, 'size': size}
                log(f'{cd} {k}: {n} records, {size // 1024} KB gz ({int(time.time() - t0)}s)')
            except Exception as e:
                failed.append(f'{cd}-{k}'); log(f'{cd} {k} FAILED: {e}')
    json.dump({'generated': NOW.strftime('%Y-%m-%dT%H:%MZ'), 'since': START[:10], 'boards': index, 'failed': failed},
              open(os.path.join(out, 'index.json'), 'w'), separators=(',', ':'))
    log(f'done: {sum(len(v) for v in index.values())} files, {len(failed)} failed, {int(time.time() - t0)}s')
    if not index: sys.exit(1)

if __name__ == '__main__':
    main()
