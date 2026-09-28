#!/usr/bin/env python3
"""Make every profile card in the CB6 block of /orgs/ searchable by name, address
and interest category. Adds data-s (search text) and data-c (categories) to each
card, one search box and a row of interest chips above all the sections. Re-run
after new cards are added; cards with no category entry below fail loudly."""
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

addr = {'oldstonehouse': '336 3rd Street'}
for f in ('org-profiles-cal.json', 'gov-profiles.json', 'place-profiles.json'):
    for r in json.load(open(os.path.join(ROOT, 'data', f), encoding='utf-8')):
        addr[r['slug']] = ' '.join(x for x in [(r.get('addr') or '').replace('<br>', ', '), r.get('addr_note') or '',
                                               r.get('zip') or ''] if x)
src = open(os.path.join(ROOT, 'build_org_pages.py'), encoding='utf-8').read()
for m in re.finditer(r"'slug':'([^']+)'.*?'addr':'([^']*)'.*?'zip':'([^']*)'", src, re.S):
    addr.setdefault(m.group(1), m.group(2).replace('<br>', ', ') + ' ' + m.group(3))

s = open(P, encoding='utf-8').read()
a = s.index('<!--cb6profiles-->'); b = s.index('<!--/cb6profiles-->')
block = s[a:b]
LABEL = dict(CATS)
counts = {k: 0 for k, _ in CATS}

def card(m):
    slug, rest = m.group(1), m.group(2)
    nm = re.search(r'<span class="cbpn">([^<]*)</span>', rest).group(1)
    seat = re.search(r'<span class="cbps">([^<]*)</span>', rest).group(1)
    cs = cats_for(slug, html.unescape(seat))
    for c in cs: counts[c] += 1
    text = ' '.join([html.unescape(nm), html.unescape(seat), addr.get(slug, ''), ' '.join(LABEL[c] for c in cs)])
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.escape(re.sub(r'\s+', ' ', text).strip().lower(), quote=True)
    return '<a class="cbp" href="/%s/" data-c="%s" data-s="%s">%s</a>' % (slug, ' '.join(cs), text, rest)

block = re.sub(r'<a class="cbp" href="/([^"/]+)/?"(?: data-c="[^"]*")?(?: data-s="[^"]*")?>(.*?)</a>', card, block, flags=re.S)

# where each profile is, for the map; places with no fixed spot stay in the list only
NOPIN = {'cobble-hill-association', 'red-hook-business-alliance', 'resilient-red-hook', 'atlantic-avenue-ldc',
         'forth-on-fourth-avenue', 'park-slope-fifth-avenue-bid', 'park-slope-open-streets', 'bergen-bike-bus',
         'house-pepper', 'porch-stomp', 'pacemakers-dance-team', 'street-lab', 'south-brooklyn-dsa',
         'bird-collective', 'artichoke-dance-company', 'brooklyn-pride'}
LL = {'oldstonehouse': (40.672958, -73.984625)}
for f in ('org-profiles-cal.json', 'gov-profiles.json', 'place-profiles.json'):
    for r in json.load(open(os.path.join(ROOT, 'data', f), encoding='utf-8')):
        if r.get('lat') and r.get('lng'): LL[r['slug']] = (float(r['lat']), float(r['lng']))
for m in re.finditer(r"'slug':'([^']+)'.*?'lat':'([^']*)','lng':'([^']*)'", src, re.S):
    LL.setdefault(m.group(1), (float(m.group(2)), float(m.group(3))))
LOGO = {}
for m in re.finditer(r'<a class="cbp" href="/([^"/]+)/?"[^>]*><img src="([^"]*)"', block):
    LOGO[m.group(1)] = m.group(2)
PTS = []
for m in re.finditer(r'<a class="cbp" href="/([^"/]+)/?"[^>]*>.*?<span class="cbpn">([^<]*)</span><span class="cbps">([^<]*)</span>', block, re.S):
    sl = m.group(1)
    if sl in NOPIN or sl not in LL: continue
    PTS.append([sl, html.unescape(m.group(2)), html.unescape(m.group(3)), round(LL[sl][0], 6), round(LL[sl][1], 6), LOGO.get(sl, '')])

# several schools share one building; fan their logos out around it so each can be tapped
import math
_grp = {}
for pt in PTS: _grp.setdefault((pt[3], pt[4]), []).append(pt)
for (la, ln), g in _grp.items():
    if len(g) < 2: continue
    for k, pt in enumerate(g):
        ang = 2 * math.pi * k / len(g)
        pt[3] = round(la + 0.00016 * math.sin(ang), 6); pt[4] = round(ln + 0.00021 * math.cos(ang), 6)

# one search box, the map, then the interest toggles, above every section
block = re.sub(r'<div class="cbpx">.*?</div><!--/cbpx-->', '', block, flags=re.S)
block = block.replace('<input id="cbpq" type="search" placeholder="Search CB6 organizations" autocomplete="off">', '')
chips = ''.join('<button type="button" class="cbpc" data-k="%s">%s</button>' % (k, l) for k, l in CATS if counts[k])
tools = ('<div class="cbpx"><input id="cbpq" type="search" placeholder="Search by name, address or interest" autocomplete="off">'
         '<div class="cbpkey"><span class="cbpk6"></span>Brooklyn Community Board 6 &middot; tap a logo to open its profile'
         ' &middot; <b id="cbpcount"></b></div>'
         '<div id="cbpmap"></div>'
         '<div class="cbpcs">' + chips + '<button type="button" class="cbpc cbpall" id="cbpall">Show all</button></div>'
         '<div class="cbpn0" id="cbpn0" hidden>Nothing matches that.</div></div><!--/cbpx-->')
block = block.replace('<section class="cb6p">', '<section class="cb6p">' + tools, 1)

# the old search scripts, replaced by one that drives the cards and the map together
block = re.sub(r'<script>\(function\(\)\{var q=document.getElementById\("cbpq"\).*?</script>', '', block, flags=re.S)
block = re.sub(r'<style>\.cbpx\{.*?</style>', '', block, flags=re.S)
block = re.sub(r'<script>/\*cbpsearch\*/.*?</script>', '', block, flags=re.S)
block = re.sub(r'<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/?><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>', '', block)
block += ('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'
          '<style>.cbpx{margin:0 0 14px}.cbpcs{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}'
          '.cbpc{font-family:"DM Mono",monospace;font-size:.62rem;letter-spacing:.04em;text-transform:uppercase;background:#fff;'
          'border:1.5px solid #e1dfd8;color:#555;border-radius:999px;padding:6px 11px;cursor:pointer}'
          '.cbpc.on{background:#0d1b4b;border-color:#0d1b4b;color:#fff}.cbpall{border-color:#f47920;color:#f47920}'
          '.cbpn0{padding:12px 2px;font-size:.88rem;color:#666}'
          '#cbpmap{height:460px;border:1px solid #e1dfd8;border-radius:12px;overflow:hidden;background:#eef0f2}'
          '.cbpkey{display:flex;align-items:center;gap:7px;flex-wrap:wrap;font-family:"DM Mono",monospace;font-size:.64rem;color:#555;margin:8px 0 6px}'
          '.cbpkey b{color:#f47920}.cbpk6{display:inline-block;width:22px;height:0;border-top:3px solid #0d1b4b;box-shadow:0 2px 0 #f47920}'
          '.cbplogo{width:30px;height:30px;border-radius:7px;background:#fff;border:2px solid #0d1b4b;box-shadow:0 1px 4px rgba(0,0,0,.3);overflow:hidden;display:flex;align-items:center;justify-content:center}'
          '.cbplogo img{max-width:26px;max-height:26px;display:block}'
          '.cbppop{display:flex;gap:10px;align-items:center;font-family:"DM Sans",sans-serif;min-width:200px}.cbppop img{width:44px;height:44px;object-fit:contain;border-radius:8px;border:1px solid #e1dfd8}'
          '.cbppop b{display:block;color:#0d1b4b;font-size:.9rem}.cbppop span{display:block;font-size:.72rem;color:#666;margin:2px 0 5px}.cbppop a{color:#f47920;font-weight:700;font-size:.78rem}'
          '@media(max-width:600px){#cbpmap{height:380px}}</style>'
          '<script>/*cbpsearch*/(function(){var PTS=' + json.dumps(PTS, ensure_ascii=False) + ';'
          'var q=document.getElementById("cbpq"),none=document.getElementById("cbpn0"),cnt=document.getElementById("cbpcount"),on={};'
          'var root=q.closest(".cb6p").parentNode,M=null,marks={},pin=null,geoT=null;'
          'function esc(v){return String(v).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;"}[c];});}'
          'function head(g){var e=g.previousElementSibling;while(e&&e.tagName!=="H2")e=e.previousElementSibling;return e;}'
          'function map(){if(M||typeof L==="undefined")return;M=L.map("cbpmap",{scrollWheelZoom:false});'
          'L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e",{maxZoom:19,attribution:"&copy; OpenStreetMap &copy; CARTO"}).addTo(M);'
          'M.setView([40.676,-73.99],13);'
          'fetch("/data/districts/cb-306.geojson").then(function(r){return r.json();}).then(function(g){'
          'L.geoJSON(g,{interactive:false,style:{stroke:false,fillColor:"#0d1b4b",fillOpacity:.05}}).addTo(M);'
          'L.geoJSON(g,{interactive:false,style:{color:"#fff",weight:6,opacity:.9,fill:false}}).addTo(M);'
          'var cb=L.geoJSON(g,{interactive:false,style:{color:"#0d1b4b",weight:3.5,fill:false}}).addTo(M);'
          'L.geoJSON(g,{interactive:false,style:{color:"#f47920",weight:1.4,fill:false,dashArray:"6 5"}}).addTo(M);'
          'L.marker([40.6760,-74.0085],{interactive:false,zIndexOffset:-1000,icon:L.divIcon({className:"",iconSize:[40,40],iconAnchor:[20,20],html:\'<img src="/cb6-logo-square.png" alt="Brooklyn Community Board 6" style="width:40px;height:40px;display:block;border-radius:7px;box-shadow:0 2px 6px rgba(0,0,0,.3)">\'})}).addTo(M);'
          'M.fitBounds(cb.getBounds(),{padding:[10,10]});}).catch(function(){});'
          'PTS.forEach(function(p){var mk=L.marker([p[3],p[4]],{icon:L.divIcon({className:"",iconSize:[30,30],iconAnchor:[15,15],popupAnchor:[0,-14],'
          'html:\'<div class="cbplogo"><img src="\'+esc(p[5])+\'" alt=""></div>\'})});'
          'mk.bindPopup(\'<div class="cbppop"><img src="\'+esc(p[5])+\'" alt=""><div><b>\'+esc(p[1])+\'</b><span>\'+esc(p[2])+\'</span><a href="/\'+p[0]+\'/">Open the profile &rarr;</a></div></div>\');'
          'mk.bindTooltip(esc(p[1]),{direction:"top",offset:[0,-14]});marks[p[0]]=mk;mk.addTo(M);});}'
          'function slugOf(a){var m=/^\\/([^\\/]+)/.exec(a.getAttribute("href")||"");return m?m[1]:"";}'
          'function run(){var t=q.value.toLowerCase().trim().replace(/\\s+/g," "),keys=Object.keys(on),total=0,vis={};'
          'var cards=[].slice.call(root.querySelectorAll(".cbp")),words=t?[t]:[];'
          'var textHit=!t||cards.some(function(a){return (a.getAttribute("data-s")||"").indexOf(t)>-1;});'
          'if(!textHit)words=t.split(" ");'
          'var addr=/^\\d/.test(t);if(addr)words=textHit?[t]:[];'
          'root.querySelectorAll(".cbpg").forEach(function(g){var n=0;g.querySelectorAll(".cbp").forEach(function(a){'
          'var s=a.getAttribute("data-s")||a.textContent.toLowerCase(),c=" "+(a.getAttribute("data-c")||"")+" ";'
          'var ok=words.every(function(w){return s.indexOf(w)>-1;})&&(!keys.length||keys.some(function(k){return c.indexOf(" "+k+" ")>-1;}));'
          'a.style.display=ok?"":"none";if(ok){n++;vis[slugOf(a)]=1;}});'
          'g.style.display=n?"":"none";var h=head(g);if(h)h.style.display=n?"":"none";'
          'var p=h&&h.nextElementSibling;if(p&&p.tagName==="P")p.style.display=n?"":"none";total+=n;});'
          'none.hidden=total>0;var shown=0;'
          'if(M){PTS.forEach(function(p){var mk=marks[p[0]];if(vis[p[0]]){shown++;if(!M.hasLayer(mk))mk.addTo(M);}else if(M.hasLayer(mk))M.removeLayer(mk);});}'
          'cnt.textContent=total+" of "+cards.length+" profiles"+(M?", "+shown+" on the map":"");'
          'clearTimeout(geoT);if(addr){geoT=setTimeout(function(){geo(t);},450);}else if(pin&&M){M.removeLayer(pin);pin=null;}'
          'if(M&&!addr&&(t||keys.length)){var b=[];PTS.forEach(function(p){if(vis[p[0]])b.push([p[3],p[4]]);});'
          'if(b.length)M.fitBounds(L.latLngBounds(b).pad(.15),{maxZoom:16});}}'
          'function geo(t){var qq=/brooklyn|manhattan|queens|bronx|staten|new york|\\bny\\b/.test(t)?t:t+", Brooklyn";fetch("https://geosearch.planninglabs.nyc/v2/search?text="+encodeURIComponent(qq)).then(function(r){return r.json();}).then(function(j){'
          'var fs=j.features||[],f=(qq!==t&&fs.filter(function(x){return /Brooklyn/.test(x.properties.label||"");})[0])||fs[0];if(!f||!M)return;var c=f.geometry.coordinates;if(pin)M.removeLayer(pin);'
          'pin=L.circleMarker([c[1],c[0]],{radius:9,color:"#fff",weight:3,fillColor:"#f47920",fillOpacity:1}).bindTooltip(esc(f.properties.label||t),{permanent:true,direction:"top",offset:[0,-8]}).addTo(M);'
          'M.setView([c[1],c[0]],16);}).catch(function(){});}'
          'q.addEventListener("input",run);'
          'document.querySelectorAll(".cbpc[data-k]").forEach(function(b){b.addEventListener("click",function(){var k=b.getAttribute("data-k");'
          'if(on[k]){delete on[k];b.classList.remove("on");}else{on[k]=1;b.classList.add("on");}run();});});'
          'document.getElementById("cbpall").addEventListener("click",function(){on={};q.value="";document.querySelectorAll(".cbpc.on").forEach(function(b){b.classList.remove("on");});run();'
          'if(M){if(pin){M.removeLayer(pin);pin=null;}M.setView([40.676,-73.99],13);}});'
          'function go(){map();run();}if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",go);else go();})();</script>')
s = s[:a] + block + s[b:]
open(P, 'w', encoding='utf-8').write(s)
print('cards', block.count('class="cbp"'), 'pins', len(PTS), counts)
