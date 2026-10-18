#!/usr/bin/env python3
"""Citywide point layers for the profile maps (assets/profile-map.js), from the Department of City Planning
Facilities Database on NYC Open Data (ji82-xba5): every K-12 school and every day care and pre-K site, with
coordinates. Writes data/nyc-facdb-schools.json and data/nyc-facdb-childcare.json as
{"source", "updated", "n", "rows": [[name, type, address, lat, lon], ...]}.
Every row with coordinates is kept; the counts printed are checked against the dataset's own count."""
import json, os, time, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = 'HvFoIfzodzpRML7a1104Ca2tM'
BASE = 'https://data.cityofnewyork.us/resource/ji82-xba5.json'


def get(params):
    u = BASE + '?' + urllib.parse.urlencode(params)
    for i in range(4):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'X-App-Token': TOKEN}), timeout=120).read())
        except Exception as e:
            if i == 3:
                raise
            print('retry', i + 1, e); time.sleep(10 * (i + 1))


meta = json.loads(urllib.request.urlopen('https://data.cityofnewyork.us/api/views/ji82-xba5.json', timeout=60).read())
updated = time.strftime('%Y-%m-%d', time.gmtime(meta['rowsUpdatedAt']))
for group, out in [('SCHOOLS (K-12)', 'nyc-facdb-schools.json'), ('DAY CARE AND PRE-KINDERGARTEN', 'nyc-facdb-childcare.json')]:
    where = "facgroup='%s'" % group
    total = int(get({'$select': 'count(*)', '$where': where})[0]['count'])
    rows, off = [], 0
    while True:
        page = get({'$select': 'facname,factype,address,latitude,longitude', '$where': where, '$order': 'uid', '$limit': 5000, '$offset': off})
        rows += page
        if len(page) < 5000:
            break
        off += 5000
    assert len(rows) == total, (group, len(rows), total)
    keep, nocoord = [], 0
    for r in rows:
        try:
            lat, lon = round(float(r['latitude']), 6), round(float(r['longitude']), 6)
        except (KeyError, TypeError, ValueError):
            nocoord += 1
            continue
        keep.append([r.get('facname') or '', r.get('factype') or '', r.get('address') or '', lat, lon])
    json.dump({'source': 'NYC Department of City Planning Facilities Database (NYC Open Data ji82-xba5), facgroup ' + group,
               'updated': updated, 'n': len(keep), 'no_coordinates': nocoord, 'rows': keep},
              open(os.path.join(ROOT, 'data', out), 'w'), separators=(',', ':'), ensure_ascii=False)
    print(out, total, 'rows in the dataset,', len(keep), 'with coordinates,', nocoord, 'without')
