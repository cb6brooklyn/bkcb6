"""Build a single-neighborhood food and drink map from the CB6 page.

  python3 tools/build_food_drink_neighborhood.py Gowanus

Takes every place from the Brooklyn district files that falls inside the
neighborhood's shape in data/city-neighborhoods.geojson, writes
data/food-drink/<slug>.json (places plus the outline) and
food-drink/<slug>/index.html, using food-drink/cb6/index.html as the template.
"""
import json, glob, re, sys
from shapely.geometry import shape, Point, mapping

NAME = sys.argv[1] if len(sys.argv) > 1 else 'Gowanus'
SLUG = re.sub(r'[^a-z0-9]+', '-', NAME.lower()).strip('-')

feat = next(f for f in json.load(open('data/city-neighborhoods.geojson'))['features']
            if f['properties']['nb'] == NAME and f['properties'].get('boro') == 'Brooklyn')
poly = shape(feat['geometry']).buffer(0)

items, seen = [], set()
for fn in sorted(glob.glob('data/food-drink/cb*.json')) + ['data/food-drink/navyyard.json']:
    for p in json.load(open(fn))['items']:
        if p.get('lat') and p.get('lng') and poly.contains(Point(p['lng'], p['lat'])):
            k = (p.get('name'), p.get('address'), p.get('t'))
            if k in seen: continue
            seen.add(k); q = dict(p); q['nb'] = NAME; items.append(q)

food = sum(1 for p in items if p['t'] == 'food')
both = sum(1 for p in items if p['t'] == 'food' and p.get('liquor'))
liq = sum(1 for p in items if p['t'] == 'liquor') + both
new = sum(1 for p in items if p.get('new'))
logos = sum(1 for p in items if p.get('logo'))
json.dump({'meta': {'nb': NAME, 'slug': SLUG, 'places': len(items), 'food': food, 'liquor': liq,
                    'joined': both, 'new_licenses_2025_26': new, 'logos': logos},
           'geometry': mapping(shape(feat['geometry'])), 'items': items},
          open(f'data/food-drink/{SLUG}.json', 'w'), separators=(',', ':'))

s = open('food-drink/cb6/index.html', encoding='utf-8').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)
num = lambda n: f'{n:,}'
rep('<title>Food and Drink in Brooklyn Community District 6 &mdash; bkcb6.app</title>',
    f'<title>Food and Drink in {NAME} &mdash; bkcb6.app</title>')
rep('content="Every state licensed food store and every active liquor license in Brooklyn Community District 6, on one map with a searchable directory."',
    f'content="Every business in {NAME}, Brooklyn: licensed food stores, liquor licenses, hardware stores and every other mapped business, on one map with a searchable directory."')
rep('href="https://bkcb6.app/food-drink/cb6/"', f'href="https://bkcb6.app/food-drink/{SLUG}/"')
rep('content="Food and Drink in Brooklyn Community District 6"', f'content="Food and Drink in {NAME}"')
rep('content="https://bkcb6.app/food-drink/cb6/"', f'content="https://bkcb6.app/food-drink/{SLUG}/"')
rep('<h1>Brooklyn Community District 6</h1><p>Park Slope &middot; Carroll Gardens-Cobble Hill-Gowanus-Red Hook</p>',
    f'<h1>{NAME}</h1><p>Every business in {NAME}, Brooklyn Community Board 6</p>')
rep('&rsaquo; Community District 6</div>',
    f'&rsaquo; <a href="/food-drink/cb6/">Community District 6</a> &rsaquo; {NAME}</div>')
s = re.sub(r'<div class="tot">.*?</div></div>',
           f'<div class="tot"><div><b>{num(len(items))}</b>places</div><div><b>{num(food)}</b>food stores</div>'
           f'<div><b>{num(liq)}</b>liquor licensees</div><div><b>{num(both)}</b>hold both</div>'
           f'<div><b>{num(new)}</b>new liquor licenses, 2025 to 2026</div><div><b>{num(logos)}</b>logos</div></div>',
           s, count=1, flags=re.S)
# no BID reaches into this neighborhood unless one of its places carries a block label
rep('<div class="bids" id="bchips"></div>', '')
rep("var map=L.map('map',{scrollWheelZoom:false})", "var map=L.map('map',{scrollWheelZoom:false,zoomSnap:0.25})")
rep("var CD='306', SLUG='cb6';", f"var CD='306', SLUG='{SLUG}';")
# outline: the neighborhood shape from its own data file, not the community district
rep("fetch('/data/cd-boundaries-lite.geojson')", "fetch('/data/food-drink/'+SLUG+'.json')")
rep("  var ft=g.features.filter(function(x){return x.properties.c===CD;});\n", "  var ft=[{type:'Feature',properties:{},geometry:g.geometry}];\n")
rep("style:{color:'#0d1b4b',weight:2,fill:false,dashArray:'4 3'}", "style:{color:NBCOL[NBONE]||'#0d1b4b',weight:3,fill:false}")
rep("var NBORDER=", f"var NBONE={json.dumps(NAME)};\nvar NBORDER=")
rep("CDDATA=DATA=j.items; chips(); bchips(); shade(); render(); });", "CDDATA=DATA=j.items; chips(); shade(); render(); });")
s = s.replace("<a href=\"/food-stores-brooklyn.html\">Food stores only</a>",
              f"Places are put in {NAME} by point in polygon against the neighborhood outline on the bkcb6.app maps. <a href=\"/food-stores-brooklyn.html\">Food stores only</a>", 1)
import os
OG = f'og/food-drink/{SLUG}.jpg'
if os.path.exists(OG):
    from PIL import Image
    w, h = Image.open(OG).size
    url = f'https://bkcb6.app/{OG}?v=1'
    rep(f'<meta property="og:url" content="https://bkcb6.app/food-drink/{SLUG}/">',
        f'<meta property="og:url" content="https://bkcb6.app/food-drink/{SLUG}/"><meta property="og:type" content="website">'
        f'<meta property="og:description" content="Every business in {NAME}, Brooklyn, on one map with a searchable directory.">'
        f'<meta property="og:image" content="{url}"><meta property="og:image:width" content="{w}"><meta property="og:image:height" content="{h}">'
        f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="Food and Drink in {NAME}"><meta name="twitter:image" content="{url}">')
os.makedirs(f'food-drink/{SLUG}', exist_ok=True)
open(f'food-drink/{SLUG}/index.html', 'w', encoding='utf-8').write(s)
print(SLUG, len(items), 'places', food, 'food', liq, 'liquor', both, 'both', new, 'new', logos, 'logos')
