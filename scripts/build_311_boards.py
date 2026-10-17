#!/usr/bin/env python3
"""311 for every community board, the way bkcb6.app does it for CB6 (civic/complaints311.json): seven years of
totals, the top 40 complaint types with a count per year, and the most recent requests (up to 1,200, from the
last 60 days) with their location, for the map. One file per board in app/data/civic/311/<borocd>.json, from NYC
Open Data 311 Service Requests (erm2-nwe9), counted on the server with SoQL group queries over the whole city at
once (three scans for all 59 boards instead of three per board), so every request in each board is in the totals.
Run daily by .github/workflows/app-feeds.yml. If a query fails, no file is touched.
"""
import datetime as dt, json, os, sys, time, urllib.parse, urllib.request

ROOT = os.environ.get('ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'app/data/civic/311')
SOC = 'https://data.cityofnewyork.us/resource/erm2-nwe9.json?'
TOKEN = os.environ.get('SOCRATA_TOKEN', 'HvFoIfzodzpRML7a1104Ca2tM')
YEAR0 = 2020
NOW = dt.datetime.now(dt.timezone(dt.timedelta(hours=-4)))
YEARS = [str(y) for y in range(YEAR0, NOW.year + 1)]
TOP = 40
RECENT = 1200
RECENT_DAYS = 60
BOROUGH = {'1': 'MANHATTAN', '2': 'BRONX', '3': 'BROOKLYN', '4': 'QUEENS', '5': 'STATEN ISLAND'}

def get(q, tries=6):
    url = SOC + urllib.parse.urlencode(q)
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={'X-App-Token': TOKEN, 'User-Agent': 'bkcb6-app-311'})
            return json.loads(urllib.request.urlopen(req, timeout=600).read())
        except Exception as e:
            print('  retry', t + 1, e, file=sys.stderr); time.sleep(20 * (t + 1))
    raise RuntimeError('failed: ' + url)

def pages(q, page=50000):
    rows, off = [], 0
    while True:
        chunk = get(dict(q, **{'$limit': page, '$offset': off}))
        rows += chunk
        print('  rows', len(rows), file=sys.stderr)
        if len(chunk) < page: return rows
        off += page

def cb_of(v):
    """'06 BROOKLYN' -> '306'; anything else (Unspecified, 0, 83 QUEENS) -> None."""
    parts = (v or '').strip().split(' ', 1)
    if len(parts) != 2 or not parts[0].isdigit(): return None
    n, boro = int(parts[0]), parts[1].strip().upper()
    code = {b: k for k, b in BOROUGH.items()}.get(boro)
    return '%s%02d' % (code, n) if code and 1 <= n <= 18 else None

def main():
    boards = {b['borocd']: b for b in json.load(open(os.path.join(ROOT, 'app/data/civic/boards.json')))}
    since = "created_date >= '%d-01-01T00:00:00'" % YEAR0
    t0 = time.time()
    print('totals by board and year', file=sys.stderr)
    totals = {}
    for r in pages({'$select': 'community_board AS cb, date_extract_y(created_date) AS y, count(*) AS n', '$where': since, '$group': 'cb, y', '$order': 'cb, y'}):
        cd = cb_of(r.get('cb'))
        if cd in boards and str(r['y']) in YEARS: totals.setdefault(cd, [0] * len(YEARS))[YEARS.index(str(r['y']))] += int(r['n'])
    print('types by board and year (%ds)' % (time.time() - t0), file=sys.stderr)
    series = {}
    for r in pages({'$select': 'community_board AS cb, complaint_type AS t, date_extract_y(created_date) AS y, count(*) AS n', '$where': since, '$group': 'cb, t, y', '$order': 'cb, t, y'}):
        cd = cb_of(r.get('cb')); t = (r.get('t') or '').strip()
        if cd in boards and t and str(r['y']) in YEARS:
            series.setdefault(cd, {}).setdefault(t, [0] * len(YEARS))[YEARS.index(str(r['y']))] += int(r['n'])
    print('recent requests, last %d days (%ds)' % (RECENT_DAYS, time.time() - t0), file=sys.stderr)
    start = (NOW - dt.timedelta(days=RECENT_DAYS)).strftime('%Y-%m-%dT00:00:00')
    recent = {}
    for r in pages({'$select': 'unique_key,created_date,closed_date,complaint_type,descriptor,status,incident_address,agency,latitude,longitude,community_board',
                    '$where': "created_date >= '%s'" % start, '$order': 'created_date DESC, unique_key'}):
        cd = cb_of(r.get('community_board'))
        if cd not in boards: continue
        lst = recent.setdefault(cd, [])
        if len(lst) >= RECENT: continue
        try: lat, lon = float(r['latitude']), float(r['longitude'])
        except (KeyError, TypeError, ValueError): lat = lon = None
        lst.append({'k': r.get('unique_key', ''), 'd': (r.get('created_date') or '')[:10], 'cl': (r.get('closed_date') or '')[:10],
                    't': r.get('complaint_type', ''), 'ds': r.get('descriptor', ''), 's': r.get('status', ''),
                    'a': r.get('incident_address', ''), 'ag': r.get('agency', ''), 'lat': lat, 'lon': lon})
    if len(totals) < 59:
        raise SystemExit('only %d boards in the totals, not writing' % len(totals))
    os.makedirs(OUT, exist_ok=True)
    for cd, b in sorted(boards.items()):
        s = series.get(cd, {})
        top = sorted(s, key=lambda t: -sum(s[t]))[:TOP]
        o = {'board': b['name'], 'borocd': cd, 'years': YEARS, 'total_by_year': totals.get(cd, [0] * len(YEARS)), 'top_types': top,
             'series': {t: s[t] for t in top}, 'grand_total': sum(totals.get(cd, [])), 'recent': recent.get(cd, []),
             'recent_days': RECENT_DAYS, 'generated': NOW.strftime('%Y-%m-%d'),
             'source': 'NYC Open Data 311 Service Requests (erm2-nwe9), %s.' % b['name']}
        with open(os.path.join(OUT, cd + '.json'), 'w') as f:
            json.dump(o, f, separators=(',', ':'), ensure_ascii=False)
        print(cd, o['grand_total'], 'since %d,' % YEAR0, len(o['recent']), 'recent', file=sys.stderr)
        if cd == '306':
            # The CB6 app reads civic/complaints311.json; keep it current from the same build.
            with open(os.path.join(ROOT, 'app/data/civic/complaints311.json'), 'w') as f:
                json.dump(o, f, separators=(',', ':'), ensure_ascii=False)
    manifest()
    print('311 boards: %d written in %ds' % (len(boards), time.time() - t0), file=sys.stderr)

def manifest():
    """Lists the 311 files in app/manifest.json the way build_app_feeds.py does, so phones download them before the
    next full pack build; build_app_pack.py rewrites the whole manifest on the next push anyway."""
    import hashlib
    mp = os.path.join(ROOT, 'app/manifest.json')
    if not os.path.exists(mp): return
    m = json.load(open(mp))
    for rel in ['civic/311/' + n for n in sorted(os.listdir(OUT))] + ['civic/complaints311.json']:
        b = open(os.path.join(ROOT, 'app/data', rel), 'rb').read()
        m.setdefault('files', {})[rel] = {'sha': hashlib.sha256(b).hexdigest(), 'size': len(b)}
    m['generated'] = dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    txt = '\n'.join(l.lstrip(' ') for l in json.dumps(m, indent=1).split('\n'))
    open(mp, 'w').write(txt)

if __name__ == '__main__':
    main()
