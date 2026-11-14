#!/usr/bin/env python3
"""The map on CrashCount's profile in the apps: this year's crashes by City Council district, drawn as CrashCount's
"How safe are your streets?" map draws them (darker red, more crashes), with the CrashCount.nyc banner on top.

Counts every crash this year in the NYPD's crash reports (NYC Open Data h9gi-nx95) that has a location, by the Council
district it falls in (data/city-council-districts-wgs84.geojson), and writes:
  app/data/civic/orgs/going/crashcount-citymap.png   the picture on the first card of CrashCount's profile
  app/data/civic/crashcount/council.json             the counts behind it (every district, crashes with no location)
and puts the card first on CrashCount's profile, with an Expand map button that opens the Apple crash map. Runs daily
in app-feeds.yml.
"""
import datetime, json, os, sys, time, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://data.cityofnewyork.us/resource/h9gi-nx95.json'
TOKEN = os.environ.get('SOCRATA_TOKEN', 'HvFoIfzodzpRML7a1104Ca2tM')
YEAR = datetime.date.today().year
WHERE = "crash_date>='%d-01-01'" % YEAR


def get(params):
    url = API + '?' + urllib.parse.urlencode(params)
    for i in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'X-App-Token': TOKEN}), timeout=180))
        except Exception:
            if i == 4: raise
            time.sleep(5 * (i + 1))


total = int(get({'$select': 'count(*)', '$where': WHERE})[0]['count'])
rows, off = [], 0
while off < total:
    page = get({'$select': 'collision_id,crash_date,latitude,longitude', '$where': WHERE, '$order': 'collision_id', '$limit': 50000, '$offset': off})
    if not page: break
    rows += page; off += len(page)
if len(rows) != total: sys.exit('got %d of %d crashes; files left as they were' % (len(rows), total))
last = max(r['crash_date'][:10] for r in rows)

gj = json.load(open(os.path.join(ROOT, 'data/city-council-districts-wgs84.geojson')))
dists = []
for f in gj['features']:
    pr = f['properties']
    n = int(next(pr[k] for k in ('coun_dist', 'CounDist', 'district', 'DISTRICT', 'council') if k in pr))
    dists.append((n, shape(f['geometry'])))
tree = STRtree([g for _, g in dists])
count = {n: 0 for n, _ in dists}
noloc = outside = 0
for r in rows:
    try: lat, lon = float(r['latitude']), float(r['longitude'])
    except Exception: noloc += 1; continue
    if not (40.4 < lat < 41.0 and -74.3 < lon < -73.6): noloc += 1; continue
    pt = Point(lon, lat); hit = None
    for i in tree.query(pt):
        if dists[i][1].contains(pt): hit = dists[i][0]; break
    if hit is None: outside += 1
    else: count[hit] += 1
assert sum(count.values()) + noloc + outside == total

# draw: CrashCount's reds, lightest to darkest by fifths of the districts
W = H = 1200
minx, miny, maxx, maxy = (min(g.bounds[i] for _, g in dists) if i < 2 else max(g.bounds[i] for _, g in dists) for i in range(4))
import math
ky = 1 / math.cos(math.radians((miny + maxy) / 2))
top = 150; pad = 40
sc = min((W - 2 * pad) / (maxx - minx), (H - top - pad) / ((maxy - miny) * ky))
ox = (W - (maxx - minx) * sc) / 2; oy = top + (H - top - pad - (maxy - miny) * ky * sc) / 2
xy = lambda x, y: (ox + (x - minx) * sc, oy + (maxy - y) * ky * sc)
REDS = ['#f6b3b3', '#ef7a7a', '#e5484d', '#cc1f24', '#a50d12']
order = sorted(count.values())
def color(v):
    for i in range(1, 5):
        if v < order[len(order) * i // 5]: return REDS[i - 1]
    return REDS[4]
img = Image.new('RGB', (W, H), '#e7e8ec')
dr = ImageDraw.Draw(img)
def polys(g): return list(g.geoms) if g.geom_type == 'MultiPolygon' else [g]
for n, g in dists:
    for p in polys(g):
        dr.polygon([xy(*c) for c in p.exterior.coords], fill=color(count[n]), outline='#ffffff')
        for h in p.interiors: dr.polygon([xy(*c) for c in h.coords], fill='#e7e8ec')
for n, g in dists:
    for p in polys(g): dr.line([xy(*c) for c in p.exterior.coords], fill='#ffffff', width=2)
# the CrashCount.nyc banner across the top, and the source at the foot
ban = Image.open(os.path.join(ROOT, 'app/data/civic/orgs/going/crashcount-banner.png')).convert('RGB')
ban = ban.resize((W, round(ban.height * W / ban.width)), Image.LANCZOS)
strip = Image.new('RGB', (W, 120), ban.getpixel((2, 2))); strip.paste(ban, (0, (120 - ban.height) // 2))
img.paste(strip, (0, 0))
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 21)
except Exception:
    font = ImageFont.load_default()
d0 = datetime.date(YEAR, 1, 1); d1 = datetime.date.fromisoformat(last)
lab = 'Crashes by City Council district, %s %d to %s %d, %d · CrashCount.nyc, from NYPD crash reports' % (d0.strftime('%b'), 1, d1.strftime('%b'), d1.day, YEAR)
dr.text((24, H - 40), lab, fill='#3b3f4a', font=font)
out = os.path.join(ROOT, 'app/data/civic/orgs/going/crashcount-citymap.png')
img.save(out, optimize=True)

os.makedirs(os.path.join(ROOT, 'app/data/civic/crashcount'), exist_ok=True)
json.dump({'year': YEAR, 'through': last, 'crashes': total, 'no_location': noloc, 'outside_districts': outside,
           'districts': {str(k): v for k, v in sorted(count.items())}}, open(os.path.join(ROOT, 'app/data/civic/crashcount/council.json'), 'w'), indent=1)

F = os.path.join(ROOT, 'app/data/civic/orgs/orgs-profiles.json')
d = json.load(open(F, encoding='utf-8'))
p = next(x for x in d['profiles'] if x['slug'] == 'crashcount')
top3 = sorted(count.items(), key=lambda kv: -kv[1])[:3]
card = {'id': 'crashcount-citymap', 'img': 'crashcount-citymap.png', 'kicker': 'CrashCount.nyc · How safe are your streets?',
        'title': 'Crashes by City Council district, %d' % YEAR,
        'text': 'Darker red, more crashes: %s of %s crashes this year through %s %d, by the Council district they happened in. '
                'Most: %s.' % ('{:,}'.format(sum(count.values())), '{:,}'.format(total), d1.strftime('%b'), d1.day,
                               '; '.join('District %d, %s' % (k, '{:,}'.format(v)) for k, v in top3)),
        'until': '', 'btns': [['Expand map', 'https://bkcb6.app/crashcount/map/', 'hot']]}
p['going'] = [card] + [g for g in (p.get('going') or []) if g.get('id') != 'crashcount-citymap']
open(F, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1) + '\n')
print('crashes', total, 'mapped', sum(count.values()), 'no location', noloc, 'outside', outside, 'through', last)
