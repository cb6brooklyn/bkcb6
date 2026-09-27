"""NYC DOT's Dean & Bergen Streets Feedback Map (nycdotprojects.info): every public comment's category, date,
location label and map point, read from the public comment pages. Comment text is not stored; each comment links back
to DOT's page. Writes data/bergendean/dotfeedback.json and assigns each comment to the nearest corridor block within 150 ft."""
import json, os, re, html, urllib.request, time, collections, datetime
from shapely.geometry import shape, Point
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import Transformer
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://nycdotprojects.info/project-feedback-map/dean-bergen-streets-feedback-map'
def get(u):
    for i in range(3):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (bkcb6.app)'}), timeout=120).read().decode('utf-8', 'replace')
        except Exception as e: time.sleep(3); err = e
    raise err
first = get(BASE)
m = re.search(r'<script type="application/json" data-drupal-selector="drupal-settings-json">(.*?)</script>', first, re.S)
settings = json.loads(m.group(1))['nyc_map']
total = settings['total_comment_count']; markers = {str(x['cid']): x for x in settings['markers']}
print('total', total, 'markers', len(markers))
rows = {}
ART = re.compile(r'<article([^>]*id="comment-\d+"[^>]*)>(.*?)</article>', re.S)
def attr(tag, k):
    m = re.search(k + r'="([^"]*)"', tag); return html.unescape(m.group(1)) if m else ''
def parse(h):
    for tag, body in ART.findall(h):
        cid = re.search(r' id="comment-(\d+)"', tag).group(1); cn = re.search(r'field--name-field-map-comment-category[^>]*>([^<]*)<', body); dt = re.search(r'submitted_date">([^<]*)<', body)
        lat, lng = attr(tag, 'data-comment-lat'), attr(tag, 'data-comment-lng')
        rows[cid] = {'cid': cid, 'cat': attr(tag, 'data-comment-category-id'), 'cat_name': html.unescape(cn.group(1).strip()) if cn else '', 'lat': float(lat) if lat else None, 'lng': float(lng) if lng else None, 'loc': attr(tag, 'data-comment-locsumm').strip(), 'date': dt.group(1).strip() if dt else ''}
parse(first)
page = 1
while len(rows) < total and page < 400:
    h = get(BASE + '?page=%d' % page); n0 = len(rows); parse(h); page += 1
    if len(rows) == n0: print('no new rows on page', page - 1); break
    if page % 20 == 0: print(page, len(rows))
print('parsed', len(rows), 'of', total)
for cid, x in markers.items():
    if cid not in rows: rows[cid] = {'cid': cid, 'cat': str(x['category_id']), 'cat_name': '', 'lat': float(x['lat']) if x.get('lat') else None, 'lng': float(x['lng']) if x.get('lng') else None, 'loc': '', 'date': ''}
print('with markers', len(rows))
# date to ISO
def iso(d):
    m = re.match(r'(\d\d)/(\d\d)/(\d{4}) - (\d\d):(\d\d)', d)
    return '%s-%s-%sT%s:%s' % (m.group(3), m.group(1), m.group(2), m.group(4), m.group(5)) if m else d
for r in rows.values(): r['date'] = iso(r['date'])
# icon per category from markers
icons = {}
for x in settings['markers']: icons[str(x['category_id'])] = x.get('marker_icon')
catnames = {}
for r in rows.values():
    if r['cat_name']: catnames[r['cat']] = r['cat_name']
for r in rows.values():
    if not r['cat_name']: r['cat_name'] = catnames.get(r['cat'], 'category ' + r['cat'])
# nearest corridor block within 150 ft
TO = Transformer.from_crs(4326, 2263, always_xy=True); P = lambda g: transform(lambda x, y, z=None: TO.transform(x, y), g)
BK = json.load(open(os.path.join(ROOT, 'data', 'bergendean', 'blocks.json')))
lines = [P(shape(f['geometry'])) for f in BK['geo']['features']]; tree = STRtree(lines)
for r in rows.values():
    r['block'] = None
    if r['lat'] and r['lng']:
        pt = P(Point(r['lng'], r['lat'])); i = int(tree.nearest(pt)); d = lines[i].distance(pt)
        if d <= 150: r['block'] = i; r['dist_ft'] = round(d)
bycat = collections.Counter(r['cat_name'] for r in rows.values())
bymonth = collections.Counter(r['date'][:7] for r in rows.values() if r['date'])
byblock = collections.Counter(r['block'] for r in rows.values() if r['block'] is not None)
byblockcat = collections.defaultdict(collections.Counter)
for r in rows.values():
    if r['block'] is not None: byblockcat[r['block']][r['cat_name']] += 1
dates = sorted(r['date'] for r in rows.values() if r['date']); nodate = sum(1 for r in rows.values() if not r['date'])
out = {'fetched': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'source': BASE, 'project': 'https://nycdotprojects.info/project/dean-bergen-bike-boulevard-project',
       'total': total, 'parsed': len(rows), 'first': dates[0], 'last': dates[-1], 'no_date': nodate, 'category_counts': dict(settings['category_comment_count']), 'category_names': catnames, 'icons': icons,
       'by_cat': bycat.most_common(), 'by_month': sorted(bymonth.items()), 'on_corridor': sum(byblock.values()), 'by_block': {str(k): v for k, v in byblock.items()},
       'by_block_cat': {str(k): v.most_common(5) for k, v in byblockcat.items()}, 'area': settings.get('pm_coordinates'),
       'comments': [[r['cid'], r['cat_name'], r['date'], r['lat'], r['lng'], r['loc'], r['block']] for r in sorted(rows.values(), key=lambda r: r['date'])]}
json.dump(out, open(os.path.join(ROOT, 'data', 'bergendean', 'dotfeedback.json'), 'w'), separators=(',', ':'))
print(out['first'], out['last'], out['on_corridor'], bycat.most_common(8), sorted(bymonth.items()))
