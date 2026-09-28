#!/usr/bin/env python3
"""Build the CB6 directory block on /orgs/: every profile located in Brooklyn Community
Board 6 (plus CB6 calendar groups with no fixed spot), a map isolated to the district,
search by name, address or interest, interest toggles, and the directory grouped by
category in alphabetical order. Cards with no category entry below fail loudly."""
import json, re, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'orgs', 'index.html')

CATS = [
    ('arts', 'Arts and culture'),
    ('parks', 'Parks, gardens and environment'),
    ('water', 'Waterfront'),
    ('schools', 'Schools'),
    ('childcare', 'Childcare and preschools'),
    ('libraries', 'Libraries'),
    ('youth', 'Youth and families'),
    ('housing', 'Housing and tenants'),
    ('food', 'Food'),
    ('streets', 'Streets, bikes and transit'),
    ('business', 'Business and development'),
    ('civic', 'Civic and neighborhood groups'),
    ('health', 'Health and social services'),
    ('safety', 'Public safety and justice'),
    ('elected', 'Elected officials'),
    ('gov', 'Government agencies'),
]

C = {
 '6-15-green': 'parks', 'artichoke-dance-company': 'arts parks', 'artsgowanus': 'arts',
 'atlantic-avenue-ldc': 'business civic', 'bark-slope': 'business', 'bergen-bike-bus': 'streets youth',
 'bird-collective': 'parks business', 'books-are-magic': 'arts business', 'bric': 'arts',
 'brooklyn-botanic-garden': 'parks', 'brooklyn-bridge-park': 'parks water', 'brooklyn-conservatory-of-music': 'arts youth',
 'brooklyn-pop-up': 'business arts', 'brooklyn-pride': 'civic arts', 'brooklyn-public-library-cb6': 'libraries',
 'camp-friendship': 'food youth health', 'carroll-gardens-association': 'housing civic', 'chips': 'food health housing',
 'churches-united-for-fair-housing': 'housing', 'cobble-hill-association': 'civic', 'columbia-street-waterfront-association': 'civic water',
 'dubois-bunche-center': 'civic', 'fifth-avenue-committee': 'housing civic', 'fort-defiance-sidewalk-galleries': 'arts',
 'forth-on-fourth-avenue': 'streets civic', 'friends-of-firefighters': 'health safety', 'gowanus-canal-conservancy': 'parks water',
 'gowanus-dredgers': 'water parks', 'grown-up-bike-bus': 'streets', 'hook-arts-media': 'arts youth',
 'house-pepper': 'food business', 'jalopy-theatre': 'arts', 'nitehawk-prospect-park': 'arts business',
 'oldstonehouse': 'arts parks', 'pacemakers-dance-team': 'arts', 'park-slope-civic-council': 'civic',
 'park-slope-farmers-market': 'food', 'park-slope-fifth-avenue-bid': 'business streets', 'park-slope-food-coop': 'food',
 'park-slope-open-streets': 'streets', 'pioneer-works': 'arts', 'porch-stomp': 'arts', 'portside-newyork': 'water arts',
 'powerhouse-arts': 'arts', 'principles-gi-coffee-house': 'civic food', 'prospect-park-alliance': 'parks',
 'record-shop': 'arts business', 'red-hook-art-project': 'arts youth', 'red-hook-business-alliance': 'business',
 'red-hook-initiative': 'youth health', 'red-hook-lobster-pound': 'food business', 'resilient-red-hook': 'civic water',
 'rooftop-films': 'arts', 'sbidc': 'business', 'the-secret-garden': 'parks', 'smith-street-stage': 'arts',
 'south-brooklyn-dsa': 'civic', 'south-brooklyn-soccer': 'parks youth', 'southwest-brooklyn-tenant-union': 'housing',
 'street-lab': 'streets youth', 'strong-rope-brewery': 'food business', 'van-alen-institute': 'civic arts',
 'waterfront-museum': 'water arts', 'why-not-art': 'arts', 'wytchonymous-arts': 'arts',
 'brooklyn-community-board-6': 'gov civic', '76th-precinct': 'safety gov', '78th-precinct': 'safety gov',
 'dsny-brooklyn-6': 'gov streets', 'nyc-dot': 'gov streets', 'nyc-dep': 'gov water', 'nyc-hpd': 'gov housing',
 'nyc-parks-brooklyn': 'gov parks', 'nyc-planning': 'gov business', 'landmarks-preservation-commission': 'gov',
 'mta': 'gov streets', 'brooklyn-marine-terminal-development-corporation': 'gov water business',
 'cec-district-15': 'gov schools', 'rent-guidelines-board': 'gov housing', 'nycha-cb6': 'gov housing',
 'red-hook-community-justice-center': 'safety gov', 'new-york-city-council': 'gov elected', 'nyc-votes': 'gov civic',
 'nyc-public-schools-cb6': 'gov schools', 'eric-gonzalez': 'elected safety', 'letitia-james': 'elected safety',
}

def cats_for(slug, seat):
    if slug in C: return C[slug].split()
    s = seat.lower()
    if 'library' in s: return ['libraries']
    if any(k in s for k in ('council member', 'assembly member', 'senator', 'representative', 'borough president',
                            'mayor', 'public advocate', 'comptroller', 'governor', 'attorney general', 'district attorney')):
        return ['elected']
    if any(k in s for k in ('preschool', 'child care', 'infant', 'early childhood', 'pre-k center', 'childcare')):
        return ['childcare', 'youth']
    if 'school' in s or 'learning center' in s:
        return ['schools', 'youth']
    raise SystemExit('no category for %s (%s)' % (slug, seat))

import math
from shapely.geometry import shape, Point

LABEL = dict(CATS)

# ---------------------------------------------------------------- inventory
# every profile, straight from the data the profile pages are built from
recs = []
for f in ('org-profiles-cal.json', 'gov-profiles.json', 'place-profiles.json'):
    recs += json.load(open(os.path.join(ROOT, 'data', f), encoding='utf-8'))
src = open(os.path.join(ROOT, 'build_org_pages.py'), encoding='utf-8').read()
for m in re.finditer(r"\{\n 'slug':'([^']+)',.*?'name':'([^']+)',\n 'seat':'([^']+)',.*?'lat':'([^']*)','lng':'([^']*)',\n 'addr':'([^']*)','zip':'([^']*)'", src, re.S):
    recs.append({'slug': m.group(1), 'name': m.group(2), 'seat': m.group(3), 'lat': m.group(4), 'lng': m.group(5),
                 'addr': m.group(6), 'zip': m.group(7)})
recs.append({'slug': 'oldstonehouse', 'name': 'Old Stone House', 'seat': 'Historic house museum &middot; Park Slope, Brooklyn',
             'lat': '40.672958', 'lng': '-73.984625', 'addr': '336 3rd Street', 'zip': '11215',
             'logo': '/app/data/civic/orgs/logos/old-stone-house.png', 'href': '/oldstonehouse'})
assert len({r['slug'] for r in recs}) == len(recs), 'duplicate slugs'
CAL = {r['slug'] for r in json.load(open(os.path.join(ROOT, 'data', 'org-profiles-cal.json'), encoding='utf-8'))}
CAL |= {m.group(1) for m in re.finditer(r"\{\n 'slug':'([^']+)'", src)} | {'oldstonehouse'}

# places with no fixed spot: CB6 calendar groups that stay in the directory but off the map
NOPIN = {'cobble-hill-association', 'red-hook-business-alliance', 'resilient-red-hook', 'atlantic-avenue-ldc',
         'forth-on-fourth-avenue', 'park-slope-fifth-avenue-bid', 'park-slope-open-streets', 'bergen-bike-bus',
         'house-pepper', 'porch-stomp', 'pacemakers-dance-team', 'street-lab', 'south-brooklyn-dsa',
         'bird-collective', 'artichoke-dance-company', 'brooklyn-pride'}

GOV = {r['slug'] for r in json.load(open(os.path.join(ROOT, 'data', 'gov-profiles.json'), encoding='utf-8'))}
cbg = json.load(open(os.path.join(ROOT, 'data', 'districts', 'cb-306.geojson'), encoding='utf-8'))
CB6 = shape(cbg['features'][0]['geometry'])
for ft in cbg['features'][1:]: CB6 = CB6.union(shape(ft['geometry']))

def txt(v): return html.unescape(re.sub(r'<[^>]+>', ' ', v or '')).replace('·', '·').strip()

items, out = [], []
for r in recs:
    sl = r['slug']
    inside = False
    if sl not in NOPIN and r.get('lat') and r.get('lng'):
        inside = CB6.contains(Point(float(r['lng']), float(r['lat'])))
    elif sl in NOPIN and sl in CAL:
        inside = True      # CB6 calendar groups whose work is in the district but has no single address
    serves = sl in GOV     # the officials who represent CB6 and the agencies that serve it, wherever their office is
    if not inside and not serves:
        out.append(sl); continue
    cs = cats_for(sl, txt(r['seat']))
    logo = r.get('logo') or '/site-icons/%s.png%s' % (sl, ('?v=' + r['logov']) if r.get('logov') else '')
    a = ' '.join(x for x in [(r.get('addr') or '').replace('<br>', ', '), r.get('addr_note') or '', r.get('zip') or ''] if x)
    items.append({'slug': sl, 'href': r.get('href') or '/%s/' % sl, 'name': txt(r['name']), 'seat': txt(r['seat']),
                  'addr': txt(a), 'cats': cs, 'logo': logo,
                  'pin': [round(float(r['lat']), 6), round(float(r['lng']), 6)] if inside and sl not in NOPIN else None})

# several places share one building; fan their logos out around it so each can be tapped
grp = {}
for it in items:
    if it['pin']: grp.setdefault(tuple(it['pin']), []).append(it)
for (la, ln), g in grp.items():
    if len(g) < 2: continue
    for k, it in enumerate(g):
        ang = 2 * math.pi * k / len(g)
        it['pin'] = [round(la + 0.00016 * math.sin(ang), 6), round(ln + 0.00021 * math.cos(ang), 6)]

# the CB6 logo goes on the open part of the district, as far from every logo as it can get
pins = [it['pin'] for it in items if it['pin']]
minx, miny, maxx, maxy = CB6.bounds
inner = CB6.buffer(-0.0025)
best, at = -1, None
for i in range(60):
    for j in range(60):
        x = minx + (maxx - minx) * i / 59; y = miny + (maxy - miny) * j / 59
        if not inner.contains(Point(x, y)): continue
        d = min(((y - p[0]) ** 2 + ((x - p[1]) * 0.76) ** 2) for p in pins)
        if d > best: best, at = d, [round(y, 6), round(x, 6)]

# ---------------------------------------------------------------- html
def esc(v): return html.escape(v, quote=True)
def card(it):
    s = ' '.join([it['name'], it['seat'], it['addr'], ' '.join(LABEL[c] for c in it['cats'])]).lower()
    s = re.sub(r'\s+', ' ', s)
    return ('<a class="cbp" href="%s" data-slug="%s" data-c="%s" data-s="%s"><img src="%s" alt="" loading="lazy">'
            '<span class="cbpn">%s</span><span class="cbps">%s</span></a>') % (
        esc(it['href']), it['slug'], ' '.join(it['cats']), esc(s), esc(it['logo']), esc(it['name']), esc(it['seat']))

groups = {}
for it in items: groups.setdefault(it['cats'][0], []).append(it)
secs = ''
for k in sorted(groups, key=lambda k: LABEL[k].lower()):
    g = sorted(groups[k], key=lambda it: re.sub(r'^the ', '', it['name'].lower()))
    secs += '<h2 class="cbph">%s <span>%d</span></h2><div class="cbpg">%s</div>' % (LABEL[k], len(g), ''.join(card(it) for it in g))
counts = {k: sum(1 for it in items if k in it['cats']) for k, _ in CATS}
chips = ''.join('<button type="button" class="cbpc" data-k="%s">%s</button>' % (k, l)
                for k, l in sorted(CATS, key=lambda c: c[1].lower()) if counts[k])
PTS = [[it['slug'], it['name'], it['seat'], it['pin'][0], it['pin'][1], it['logo'], it['href']] for it in items if it['pin']]

block = ('<!--cb6profiles--><section class="cb6p">'
 '<h2>Brooklyn Community Board 6 directory <span>%d profiles</span></h2>'
 '<p>Every organization, school, childcare program, library, agency and elected office in Brooklyn Community Board 6, '
 'each with a profile: what it does, where it is, what is coming up and how to reach it.</p>'
 '<div class="cbpx"><input id="cbpq" type="search" placeholder="Search by name, address or interest" autocomplete="off">'
 '<div class="cbpkey"><span class="cbpk6"></span>Brooklyn Community Board 6 &middot; tap a logo to open its profile &middot; <b id="cbpcount"></b></div>'
 '<div id="cbpmap"></div>'
 '<div class="cbpcs">%s<button type="button" class="cbpc cbpall" id="cbpall">Show all</button></div>'
 '<div class="cbpn0" id="cbpn0" hidden>Nothing matches that.</div></div>'
 '%s</section>') % (len(items), chips, secs)

block += ('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'
 '<style>.cb6p{margin:18px 0 26px}.cb6p>h2{font-size:1.15rem;font-weight:800;color:#0d1b4b;margin:0 0 6px}.cb6p>h2 span,.cbph span{font-family:"DM Mono",monospace;font-size:.7rem;color:#f47920;margin-left:6px}'
 '.cb6p>p{font-size:.88rem;color:#555;margin:0 0 10px}#cbpq{width:100%;box-sizing:border-box;padding:10px 12px;border:1.5px solid #e1dfd8;border-radius:10px;font:inherit}'
 '.cbph{font-size:1.02rem;font-weight:800;color:#0d1b4b;margin:22px 0 8px;padding-bottom:5px;border-bottom:2px solid #f47920}'
 '.cbpg{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}'
 '.cbp{display:flex;flex-direction:column;align-items:center;text-align:center;gap:5px;padding:10px;background:#fff;border:1px solid #e1dfd8;border-radius:12px;text-decoration:none;color:#14141c}'
 '.cbp img{width:64px;height:64px;object-fit:contain;border-radius:10px}.cbpn{font-weight:700;font-size:.85rem;line-height:1.2}.cbps{font-size:.7rem;color:#666;line-height:1.25}'
 '.cbpx{margin:0 0 14px}.cbpcs{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}'
 '.cbpc{font-family:"DM Mono",monospace;font-size:.62rem;letter-spacing:.04em;text-transform:uppercase;background:#fff;border:1.5px solid #e1dfd8;color:#555;border-radius:999px;padding:6px 11px;cursor:pointer}'
 '.cbpc.on{background:#0d1b4b;border-color:#0d1b4b;color:#fff}.cbpall{border-color:#f47920;color:#f47920}.cbpn0{padding:12px 2px;font-size:.88rem;color:#666}'
 '#cbpmap{height:480px;border:1px solid #e1dfd8;border-radius:12px;overflow:hidden;background:#eef0f2}'
 '.cbpkey{display:flex;align-items:center;gap:7px;flex-wrap:wrap;font-family:"DM Mono",monospace;font-size:.64rem;color:#555;margin:8px 0 6px}'
 '.cbpkey b{color:#f47920}.cbpk6{display:inline-block;width:18px;height:12px;background:rgba(13,27,75,.16);border:2px solid #0d1b4b;box-shadow:0 2px 0 #f47920}'
 '.cbplogo{width:30px;height:30px;border-radius:7px;background:#fff;border:2px solid #0d1b4b;box-shadow:0 1px 4px rgba(0,0,0,.3);overflow:hidden;display:flex;align-items:center;justify-content:center}'
 '.cbplogo img{max-width:26px;max-height:26px;display:block}'
 '.cbppop{display:flex;gap:10px;align-items:center;font-family:"DM Sans",sans-serif;min-width:200px}.cbppop img{width:44px;height:44px;object-fit:contain;border-radius:8px;border:1px solid #e1dfd8}'
 '.cbppop b{display:block;color:#0d1b4b;font-size:.9rem}.cbppop span{display:block;font-size:.72rem;color:#666;margin:2px 0 5px}.cbppop a{color:#f47920;font-weight:700;font-size:.78rem}'
 '.cbp6lab{font-family:"DM Sans",sans-serif;font-weight:800;font-size:.72rem;color:#0d1b4b;text-align:center;line-height:1.15;text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 3px #fff}'
 '@media(max-width:600px){#cbpmap{height:400px}}</style>'
 '<script>/*cbpsearch*/(function(){var PTS=' + json.dumps(PTS, ensure_ascii=False) + ',LAB=' + json.dumps(at) + ';'
 'var q=document.getElementById("cbpq"),none=document.getElementById("cbpn0"),cnt=document.getElementById("cbpcount"),on={};'
 'var root=q.closest(".cb6p"),M=null,marks={},pin=null,geoT=null,home=null;'
 'function esc(v){return String(v).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;"}[c];});}'
 'function head(g){var e=g.previousElementSibling;return e&&e.tagName==="H2"?e:null;}'
 'function goHome(){if(M&&home)M.fitBounds(home,{padding:[8,8]});}'
 'function map(){if(M||typeof L==="undefined")return;M=L.map("cbpmap",{scrollWheelZoom:false,minZoom:13});'
 'L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e",{maxZoom:19,attribution:"&copy; OpenStreetMap &copy; CARTO"}).addTo(M);'
 'M.setView([40.676,-73.99],13);'
 'fetch("/data/districts/cb-306.geojson").then(function(r){return r.json();}).then(function(g){'
 'var holes=[];g.features.forEach(function(f){var gm=f.geometry,ps=gm.type==="Polygon"?[gm.coordinates]:gm.coordinates;ps.forEach(function(p){holes.push(p[0].map(function(c){return [c[1],c[0]];}));});});'
 'L.polygon([[[41.2,-74.6],[41.2,-73.3],[40.2,-73.3],[40.2,-74.6]]].concat(holes),{interactive:false,stroke:false,fillColor:"#ffffff",fillOpacity:.6}).addTo(M);'
 'L.geoJSON(g,{interactive:false,style:{stroke:false,fillColor:"#0d1b4b",fillOpacity:.13}}).addTo(M);'
 'L.geoJSON(g,{interactive:false,style:{color:"#fff",weight:6,opacity:.9,fill:false}}).addTo(M);'
 'var cb=L.geoJSON(g,{interactive:false,style:{color:"#0d1b4b",weight:3.5,fill:false}}).addTo(M);'
 'L.geoJSON(g,{interactive:false,style:{color:"#f47920",weight:1.4,fill:false,dashArray:"6 5"}}).addTo(M);'
 'home=cb.getBounds();M.setMaxBounds(home.pad(.25));goHome();'
 'if(LAB)L.marker(LAB,{interactive:false,zIndexOffset:2000,icon:L.divIcon({className:"",iconSize:[120,78],iconAnchor:[60,26],'
 'html:\'<div style="display:flex;flex-direction:column;align-items:center;gap:3px"><img src="/cb6-logo-square.png" alt="" style="width:48px;height:48px;display:block;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,.3)"><div class="cbp6lab">Brooklyn Community<br>Board 6</div></div>\'})}).addTo(M);'
 '}).catch(function(){});'
 'PTS.forEach(function(p){var mk=L.marker([p[3],p[4]],{icon:L.divIcon({className:"",iconSize:[30,30],iconAnchor:[15,15],popupAnchor:[0,-14],'
 'html:\'<div class="cbplogo"><img src="\'+esc(p[5])+\'" alt=""></div>\'})});'
 'mk.bindPopup(\'<div class="cbppop"><img src="\'+esc(p[5])+\'" alt=""><div><b>\'+esc(p[1])+\'</b><span>\'+esc(p[2])+\'</span><a href="\'+esc(p[6])+\'">Open the profile &rarr;</a></div></div>\');'
 'mk.bindTooltip(esc(p[1]),{direction:"top",offset:[0,-14]});marks[p[0]]=mk;mk.addTo(M);});}'
 'function run(){var t=q.value.toLowerCase().trim().replace(/\\s+/g," "),keys=Object.keys(on),total=0,vis={};'
 'var cards=[].slice.call(root.querySelectorAll(".cbp")),words=t?[t]:[];'
 'var textHit=!t||cards.some(function(a){return (a.getAttribute("data-s")||"").indexOf(t)>-1;});'
 'if(!textHit)words=t.split(" ");var addr=/^\\d/.test(t);if(addr)words=textHit?[t]:[];'
 'root.querySelectorAll(".cbpg").forEach(function(g){var n=0;g.querySelectorAll(".cbp").forEach(function(a){'
 'var s=a.getAttribute("data-s")||"",c=" "+(a.getAttribute("data-c")||"")+" ";'
 'var ok=words.every(function(w){return s.indexOf(w)>-1;})&&(!keys.length||keys.some(function(k){return c.indexOf(" "+k+" ")>-1;}));'
 'a.style.display=ok?"":"none";if(ok){n++;vis[a.getAttribute("data-slug")]=1;}});'
 'g.style.display=n?"":"none";var h=head(g);if(h){h.style.display=n?"":"none";var sp=h.querySelector("span");if(sp)sp.textContent=n;}total+=n;});'
 'none.hidden=total>0;var shown=0;'
 'if(M){PTS.forEach(function(p){var mk=marks[p[0]];if(vis[p[0]]){shown++;if(!M.hasLayer(mk))mk.addTo(M);}else if(M.hasLayer(mk))M.removeLayer(mk);});}'
 'cnt.textContent=total+" of "+cards.length+" profiles"+(M?", "+shown+" on the map":"");'
 'clearTimeout(geoT);if(addr){geoT=setTimeout(function(){geo(t);},450);}else if(pin&&M){M.removeLayer(pin);pin=null;}'
 'if(M&&!addr){if(t||keys.length){var b=[];PTS.forEach(function(p){if(vis[p[0]])b.push([p[3],p[4]]);});if(b.length)M.fitBounds(L.latLngBounds(b).pad(.15),{maxZoom:16});}else goHome();}}'
 'function geo(t){var qq=/brooklyn|manhattan|queens|bronx|staten|new york|\\bny\\b/.test(t)?t:t+", Brooklyn";'
 'fetch("https://geosearch.planninglabs.nyc/v2/search?text="+encodeURIComponent(qq)).then(function(r){return r.json();}).then(function(j){'
 'var fs=j.features||[],f=(qq!==t&&fs.filter(function(x){return /Brooklyn/.test(x.properties.label||"");})[0])||fs[0];if(!f||!M)return;var c=f.geometry.coordinates;if(pin)M.removeLayer(pin);'
 'pin=L.circleMarker([c[1],c[0]],{radius:9,color:"#fff",weight:3,fillColor:"#f47920",fillOpacity:1}).bindTooltip(esc(f.properties.label||t),{permanent:true,direction:"top",offset:[0,-8]}).addTo(M);'
 'M.setView([c[1],c[0]],16);}).catch(function(){});}'
 'q.addEventListener("input",run);'
 'document.querySelectorAll(".cbpc[data-k]").forEach(function(b){b.addEventListener("click",function(){var k=b.getAttribute("data-k");'
 'if(on[k]){delete on[k];b.classList.remove("on");}else{on[k]=1;b.classList.add("on");}run();});});'
 'document.getElementById("cbpall").addEventListener("click",function(){on={};q.value="";document.querySelectorAll(".cbpc.on").forEach(function(b){b.classList.remove("on");});'
 'if(pin&&M){M.removeLayer(pin);pin=null;}run();});'
 'function go(){map();run();}if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",go);else go();})();</script>')

s = open(P, encoding='utf-8').read()
a = s.index('<!--cb6profiles-->'); b = s.index('<!--/cb6profiles-->')
s = s[:a] + block + s[b:]
# the page is isolated to CB6 for now: the citywide list stays in the file, hidden
s = s.replace('<div class="sub"><span id="total">&mdash;</span> community based organizations across the city</div>',
              '<div class="sub">Brooklyn Community Board 6<span id="total" hidden></span></div>')
s = re.sub(r'<style id="cb6only">.*?</style>', '', s, flags=re.S)
s = s.replace('<!--/cb6profiles-->', '<!--/cb6profiles--><style id="cb6only">.tools,#none,#groups,.foot{display:none!important}</style>', 1)
open(P, 'w', encoding='utf-8').write(s)
print('in CB6', len(items), 'on map', len(PTS), 'sections', len(groups), 'label at', at)
print('left out (outside CB6):', len(out), out)
