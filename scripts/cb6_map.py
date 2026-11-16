#!/usr/bin/env python3
"""bkcb6.app/cb6map/: every business and every lot in Community Board 6 on one map, built like the BID maps
(/parkslopefifthavebid/ and the others, which follow the Gowanus BID map, the template).

  Businesses: every Directory business inside District 6 (profiles/dir.json, one entry per business after
    directory_dedupe.py), with its logo or photo or an icon for what it is, each linked to its profile page.
  Properties: every tax lot in District 6, from the lot map's file (cb6lots/lots.json: PLUTO and MapPLUTO), with its
    storefronts, occupied or vacant, from the city's storefront registry (92iy-9c3n), and the businesses on it.
Writes cb6map/index.html and cb6map/lots.json. Run after app_directory_tiles.py: python3 scripts/cb6_map.py"""
import json, os, re, sys, html, urllib.request, urllib.parse, time, collections
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
sys.path.insert(0, P('scripts'))
os.chdir(ROOT)
import directory_grid as G
TOKEN = 'HvFoIfzodzpRML7a1104Ca2tM'
def get(u):
    for i in range(4):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'X-App-Token': TOKEN, 'User-Agent': 'bkcb6.app'}), timeout=180).read())
        except Exception:
            if i == 3: raise
            time.sleep(4)
def esc(s): return html.escape(str(s), quote=True)
CD6 = shape(json.load(open(P('data/cb6-audit/cd306.geojson'))))
TPL = open(P('gowanusbid/index.html'), encoding='utf-8').read()
DIR = json.load(open(P('profiles/dir.json')))
PROF = json.load(open(P('app/data/civic/orgs/orgs-profiles.json'), encoding='utf-8'))['profiles']
BYHREF = {}
for p in PROF:
    if p.get('group') not in ('Local businesses', 'Health', 'Food', 'Child care'): continue
    if p.get('topic') in ('Houses of worship', 'Pre-K site', 'Hospitals', 'Preschool for students with disabilities', 'Day camp'): continue
    h = G.site_page(p)
    if h: BYHREF.setdefault(h, p)
def logo(p):
    l = p.get('logo') or ''
    if not l or 'Logos/' in l: return ''
    f = os.path.normpath(os.path.join('app/data/civic/orgs/logos', l))
    return '/' + f if os.path.exists(f) else ''
TOPIC = {'Pharmacies': 'Health and medical', 'Supermarkets': 'Supermarkets', 'Preschool child care': 'Child care', 'Infants and toddlers': 'Child care'}
def kind(p):
    if p.get('cuisine'): return p['cuisine']
    for k, v in p.get('kv', []):
        if k == 'Kind': return v
    return {'Pharmacies': 'Pharmacy', 'Preschool child care': 'Childcare', 'Infants and toddlers': 'Childcare'}.get(p.get('topic'), '')
def nb(p):
    for k, v in p.get('kv', []):
        if k == 'Neighborhood': return v
    return ''
CAT_EXTRA = {'Restaurants, cafes and food': '🍽️', 'Supermarkets': '🛒', 'Delis and bodegas': '🥪', 'Groceries and food stores': '🛒', 'Stores': '🛍️', 'Smoke, vape and cannabis shops': '💨',
             'Markets': '🧺', 'Venues': '🎟️', 'Services and offices': '🏢', 'Trades, workshops and industrial': '🛠️', 'Child care': '🧸', 'Fitness and recreation': '🏋️'}
# businesses
rows, seen = [], set()
for e in DIR['E']:
    if e[1] not in BYHREF or e[1] in seen: continue
    if not CD6.contains(Point(e[12], e[11])): continue
    p = BYHREF[e[1]]; seen.add(e[1])
    rows.append([e[0], TOPIC.get(p.get('topic'), p.get('topic') or 'Other businesses'), kind(p), p.get('addr') or '', e[11], e[12], p.get('weburl') or '', e[1], logo(p), 0, nb(p)])
rows.sort(key=lambda r: (r[1], r[0].lower()))
# lots: the lot map's file, every lot in District 6, first 12 fields as the BID maps use them
LOTS = [l[:12] for l in json.load(open(P('cb6lots/lots.json')))['lots']]
SF = collections.defaultdict(list)
for r in get('https://data.cityofnewyork.us/resource/92iy-9c3n.json?' + urllib.parse.urlencode({'$where': "community_board='306'", '$limit': 50000})):
    SF[r['bbl']].append(r)
def tc_(s): return re.sub(r'^No business activity identified$', '', s.strip().capitalize()) if s else ''
for l in LOTS:
    rs = SF.get(l[1])
    if not rs: l.append(''); continue
    yr = max(r['reporting_year'] for r in rs); cur = [r for r in rs if r['reporting_year'] == yr]
    occ = collections.Counter(tc_(r.get('primary_business_activity', '')) for r in cur if r.get('vacant_on_12_31') == 'NO')
    vac = sum(1 for r in cur if r.get('vacant_on_12_31') == 'YES')
    parts = ['%s in use%s' % (('%d storefronts' % sum(occ.values())) if sum(occ.values()) > 1 else 'Storefront', ' (%s)' % ', '.join(k for k in occ if k) if any(occ) else '')] if occ else []
    if vac: parts.append('%s vacant' % ('%d storefronts' % vac if vac > 1 else 'storefront' if occ else 'Storefront'))
    l.append('%s, as the owner reported to the city for %s' % ('; '.join(parts), yr))
# the businesses on each lot
shapes, idx = [], []
for i, l in enumerate(LOTS):
    if l[11]:
        try:
            polys = [l[11]] if isinstance(l[11][0][0][0], (int, float)) else l[11]   # one polygon (rings) or several
            g = shape({'type': 'MultiPolygon', 'coordinates': [[[[x, y] for y, x in ring] for ring in poly] for poly in polys]}).buffer(0)
            shapes.append(g.buffer(0.00008)); idx.append(i)
        except Exception: pass
T = STRtree(shapes)
for l in LOTS: l.append([])
for j, r in enumerate(rows):
    pt = Point(r[5], r[4]); ks = list(T.query(pt, predicate='intersects'))
    if ks:
        k = min(ks, key=lambda k: shapes[k].centroid.distance(pt))
        LOTS[idx[k]][13].append(j)
os.makedirs(P('cb6map'), exist_ok=True)
json.dump(LOTS, open(P('cb6map/lots.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
ring = [[[[round(y, 6), round(x, 6)] for x, y in poly.exterior.coords]] for poly in ([CD6] if CD6.geom_type == 'Polygon' else list(CD6.geoms))]
# the page
s = TPL
s = s.replace('<meta name="robots" content="noindex,nofollow">\n', '')
s = re.sub(r'<title>.*?</title>', '<title>Every business and property in Brooklyn Community Board 6</title>', s)
s = re.sub(r'<header>.*?</header>', '<header><div class="hb"><img class="hlogo" src="/site-icons/brooklyn-community-board-6.png" alt="Brooklyn Community Board 6 logo"><div><div class="k">Brooklyn Community Board 6</div>'
           '<h1>Every business and every property in the district</h1></div></div><p>Carroll Gardens, Cobble Hill, Columbia Street Waterfront, Gowanus, Park Slope and Red Hook. '
           'Every business listing and every tax lot, with the storefronts on it, occupied or vacant.</p>'
           '<p class="hl"><a href="/profiles/bkcb6/">The BKCB6 Directory</a> · <a href="/cb6lots/">Homes built and lost, lot by lot</a> · BID maps: <a href="/parkslopefifthavebid/">Park Slope Fifth Avenue</a>, '
           '<a href="/northflatbushbid/">North Flatbush</a>, <a href="/atlanticavebid/">Atlantic Avenue</a>, <a href="/gowanusbid/">Gowanus (proposed)</a></p></header>', s, flags=re.S)
s = s.replace('header p{margin:6px 0 0;font-size:.9rem;opacity:.9}', 'header p{margin:6px 0 0;font-size:.9rem;opacity:.9}\nheader .hl{font-size:.8rem;line-height:1.6}header .hl a{color:#fff}\n'
              '.hb{display:flex;gap:14px;align-items:center}.hlogo{flex:0 0 84px;width:84px;height:84px;object-fit:contain;background:#fff;border-radius:12px;padding:6px}\n'
              '#map.zvlo .pin{display:none}.more{display:block;width:100%;margin:6px 0 2px;padding:10px;border:1.5px dashed #0d1b4b;border-radius:12px;background:#fff;color:#0d1b4b;font:700 .85rem \'DM Sans\',sans-serif;cursor:pointer}\n'
              '.pop .biz{margin-top:6px;padding-top:6px;border-top:1px solid #e2dfd6}.pop .biz a{display:block;color:#c85a0a;font-size:.84rem;margin-top:2px}')
s = s.replace('<button class="pill on" id="th">New housing on the map</button>', '').replace('<button class="tab" data-t="h">New housing</button>', '')
src = ('Boundary: Brooklyn Community District 6, from the Department of City Planning. Businesses: the bkcb6.app Directory, which draws on NYC Health Department restaurant inspections, '
       'NYC Department of Consumer and Worker Protection licenses, New York State food store, liquor and salon licenses, the federal health provider and bank branch registers, '
       'OpenStreetMap and the businesses\' own websites. Properties: every tax lot in the district, from the Department of City Planning\'s PLUTO file and MapPLUTO, with its '
       'storefronts, occupied or vacant, from the city\'s storefront registry (owners report every ground and second floor storefront each year).')
s = re.sub(r'<p class="src">.*?</p>', '<p class="src">%s</p>' % esc(src), s, flags=re.S)
s = re.sub(r'var RING=\[.*?\];\n', 'var RING=%s;\n' % json.dumps(ring, separators=(',', ':')), s, flags=re.S)
s = re.sub(r'var ROWS=\[.*?\];\n', lambda m: 'var ROWS=%s;\n' % json.dumps(rows, ensure_ascii=False, separators=(',', ':')), s, flags=re.S)
s = re.sub(r'var LOTS=\[.*?\];\n', 'var LOTS=[];\n', s, flags=re.S)   # loaded from lots.json
s = re.sub(r'var HOUSING=\[.*?\];\n', 'var HOUSING=[];\n', s, flags=re.S)
s = s.replace("var CAT={", "var CAT=" + json.dumps(CAT_EXTRA, ensure_ascii=False)[:-1] + ",", 1)
s = s.replace("function icon(r){return r[8]?'<img src=\"/app/data/civic/business/logos/'+esc(r[8])+'.png\" alt=\"\" loading=\"lazy\">':glyph(r)}",
              "function icon(r){return r[8]?'<img src=\"'+esc(r[8])+'\" alt=\"\" loading=\"lazy\">':glyph(r)}")
s = s.replace("document.getElementById('th').addEventListener", "if(document.getElementById('th'))document.getElementById('th').addEventListener")
# lot popups: the storefronts and the businesses on the lot
s = s.replace("(l[8]?'<div>Lot area '", "(l[12]?'<div>'+esc(l[12])+'</div>':'')+(l[13]&&l[13].length?'<div class=\"biz\"><b style=\"font-size:.8rem\">Businesses here</b>'+l[13].map(function(j){var r=ROWS[j];return '<a href=\"'+esc(r[7])+'\">'+esc(r[0])+'</a>'}).join('')+'</div>':'')+(l[8]?'<div>Lot area '", 1)
# a canvas for 13,000 lots; business pins from street level in
s = s.replace("var map=L.map('map',{scrollWheelZoom:false})", "var map=L.map('map',{scrollWheelZoom:false,preferCanvas:true})")
s = s.replace("function zc(){var z=map.getZoom(),e=document.getElementById('map');", "function zc(){var z=map.getZoom(),e=document.getElementById('map');e.classList.toggle('zvlo',z<15);")
# lots arrive after the page: their layers, counts and key are built then
old_lay = """var lotLayers=[];
LOTS.forEach(function(l,i){if(!l[11]){lotLayers.push(null);return}
  var p=L.polygon(l[11],{color:'#0d1b4b',weight:.6,opacity:.55,fillColor:LU[l[2]]||'#ececec',fillOpacity:.6});
  p.bindPopup(lotPop(l));lotLayers.push(p)});"""
assert old_lay in s
s = s.replace(old_lay, """var lotLayers=[];
function buildLots(){lotLayers=[];LOTS.forEach(function(l,i){if(!l[11]){lotLayers.push(null);return}
  var p=L.polygon(l[11],{color:'#0d1b4b',weight:.4,opacity:.45,fillColor:LU[l[2]]||'#ececec',fillOpacity:.55});
  p.bindPopup(function(){return lotPop(l)});lotLayers.push(p)})}""")
old_cnt = """var bc=cnt(ROWS,1),lc=cnt(LOTS,2);
var bcats=Object.keys(bc).sort(function(a,b){return bc[b]-bc[a]||a.localeCompare(b)}),lcats=Object.keys(lc).sort(function(a,b){return lc[b]-lc[a]||a.localeCompare(b)});
document.getElementById('key').innerHTML=lcats.map(function(c){return '<span><i style="background:'+LU[c]+'"></i>'+esc(c)+'</span>'}).join('');"""
assert old_cnt in s
s = s.replace(old_cnt, """var bc=cnt(ROWS,1),lc={};
var bcats=Object.keys(bc).sort(function(a,b){return bc[b]-bc[a]||a.localeCompare(b)}),lcats=[];
function countLots(){lc=cnt(LOTS,2);lcats=Object.keys(lc).sort(function(a,b){return lc[b]-lc[a]||a.localeCompare(b)});
document.getElementById('key').innerHTML=lcats.map(function(c){return '<span><i style="background:'+LU[c]+'"></i>'+esc(c)+'</span>'}).join('')}""")
# long lists open a group at a time: the first 60 of each, then the rest on a tap
s = s.replace("function draw(){var shown=0,by={},h='';", "var LIM=60,openG={};\nfunction draw(){var shown=0,by={},h='';")
old_b = """      by[c].forEach(function(i){var r=ROWS[i];h+='<div class="row\""""
assert old_b in s
s = s.replace(old_b, """      by[c].forEach(function(i,j){if(j>=LIM&&!openG['b'+c]&&!term)return;var r=ROWS[i];h+='<div class="row\"""")
s = s.replace("""<a class="go" href="'+esc(r[7])+'">Profile</a></div>'})});""", """<a class="go" href="'+esc(r[7])+'">Profile</a></div>'});if(by[c].length>LIM&&!openG['b'+c]&&!term)h+='<button class="more" data-g="b'+esc(c)+'">Show all '+by[c].length.toLocaleString()+'</button>'});""")
old_l = """      by[c].forEach(function(i){var l=LOTS[i];h+='<div class="row\""""
assert old_l in s
s = s.replace(old_l, """      by[c].forEach(function(i,j){if(j>=LIM&&!openG['l'+c]&&!term)return;var l=LOTS[i];h+='<div class="row\"""")
s = s.replace("""+encodeURIComponent(tc(l[0])+', Brooklyn')+'">Address card</a>':'')+'</div>'})});""", """+encodeURIComponent(tc(l[0])+', Brooklyn')+'">Address card</a>':'')+'</div>'});if(by[c].length>LIM&&!openG['l'+c]&&!term)h+='<button class="more" data-g="l'+esc(c)+'">Show all '+by[c].length.toLocaleString()+'</button>'});""")
assert s.count('class="more"') == 2
s = s.replace("document.getElementById('list').addEventListener('click',function(e){if(e.target.closest('a'))return;",
              "document.getElementById('list').addEventListener('click',function(e){var mo=e.target.closest('.more');if(mo){openG[mo.getAttribute('data-g')]=1;draw();return}if(e.target.closest('a'))return;")
assert "openG[mo.getAttribute" in s
s = s.replace("chips();draw();\n</script>", """chips();draw();
fetch('lots.json').then(function(r){return r.json()}).then(function(d){LOTS=d;buildLots();countLots();chips();draw()});
</script>""")
assert "fetch('lots.json')" in s
open(P('cb6map/index.html'), 'w', encoding='utf-8').write(s)
print('businesses %d (with logo or photo %d) | lots %d (with shapes %d, storefronts on file %d, with businesses %d)' % (
    len(rows), sum(1 for r in rows if r[8]), len(LOTS), sum(1 for l in LOTS if l[11]), sum(1 for l in LOTS if l[12]), sum(1 for l in LOTS if l[13])))
