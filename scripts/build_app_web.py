#!/usr/bin/env python3
"""The web versions of the two apps, built from the same data the apps carry.

  bkcb6.app/cb6app10226/   BKCB6: Home, Meetings, Land Use & Landmarks, Orgs, Jobs, Board
  bkcb6.app/bkcball18/     BKCB:  Home (pick a board), Calendar, Boards, Brooklyn

Each folder is self-contained: index.html (the app shell with its tabs), official/<slug>.html (every official's
profile: map, bio, in numbers, bills, committees, contact, overlap), board/<cd>.html (every board's page),
directory.html, orgs.html, data/ (the apps' JSON) and img/ (the logos). Maps are Leaflet. Site pages the apps
embed (the calendar, the CB6 map, land use, jobs, the board) open inside the shell.

Run on the Mac, where the app repo is:  python3 scripts/build_app_web.py
"""
import json, os, re, shutil, sys, html as H
from datetime import date

SRC = os.path.expanduser('~/bkcivics/BKCB6/Resources')      # the BKCB app carries every board's data
SRC6 = os.path.expanduser('~/bkcb6app/BKCB6/Resources')
SITE = '/tmp/bkf'
CIVIC = os.path.join(SRC, 'civic')
TODAY = date.today().isoformat()

def J(p): return json.load(open(p, encoding='utf-8'))
def esc(s): return H.escape(str(s or ''), quote=True)
def slug(s): return re.sub(r'[^a-z0-9]+', '-', str(s).lower()).strip('-')

officials = J(f'{CIVIC}/officials.json')
boards = {b['borocd']: b for b in J(f'{CIVIC}/boards.json')}
shapes = J(f'{CIVIC}/district-shapes.json')
board_shapes = J(f'{CIVIC}/board-shapes.json')
stats = J(f'{CIVIC}/stats.json')
orgs = J(f'{CIVIC}/orgs/orgs-profiles.json')['profiles']
directory = J(f'{CIVIC}/directory/directory.json')
culture = J(f'{CIVIC}/culture.json')
biz = J(f'{SRC6}/civic/business/business-cb6.json')
by_slug = {o['slug']: o for o in officials}

LEVEL = {'council': ('City Council', 'office-council', '#ed6b1a'), 'assembly': ('State Assembly', 'office-assembly', '#7d4dc2'),
         'senate': ('State Senate', 'office-senate', '#2e8c57'), 'congress': ('Congress', 'office-house', '#2966d9'),
         'bp': ('Borough President', 'bp-reynoso', '#0d1b4b'), 'da': ('District Attorney', 'seal-nyc', '#0d1b4b'),
         'citywide': ('Citywide', 'seal-nyc', '#0d1b4b'), 'statewide': ('New York State', 'office-assembly', '#0d1b4b'),
         'ussenate': ('United States Senate', 'office-house', '#2966d9')}
BORO = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}
def board_short(cd): return f"{BORO.get(cd[0], '')} CB{int(cd[1:])}"
def board_title(cd): return f"{BORO.get(cd[0], '')} Community Board {int(cd[1:])}"
def seal(cd): return 'img/CB6_540.png' if cd == '306' else f'img/cb{cd}.png'

def covers_cb6(o): return any(b.get('cd') == '306' for b in o.get('cbs', []))
def covers_bk(o):
    if any(str(b.get('cd', '')).startswith('3') for b in o.get('cbs', [])): return True
    if o['type'] in ('bp', 'da'): return 'brooklyn' in o.get('boro', '').lower()
    return o['type'] in ('citywide', 'statewide', 'ussenate')

# ---------------------------------------------------------------- stats (mirrors PlaceStats in the apps)
def scope_key(o):
    t, d = o['type'], o.get('district')
    if t == 'assembly' and d: return f'ad{d}'
    if t == 'senate' and d: return f'sd{d}'
    if t == 'congress' and d: return f'cd{d}'
    if t in ('bp', 'da'): return 'b3' if 'brooklyn' in o.get('boro', '').lower() else None
    if t == 'citywide': return 'nyc'
    if t in ('statewide', 'ussenate'): return 'ny'
    return None
def scope_title(o):
    t, d = o['type'], o.get('district')
    return {'assembly': f'Assembly District {d}', 'senate': f'State Senate District {d}', 'congress': f'Congressional District {d}',
            'bp': 'Brooklyn', 'da': 'Brooklyn', 'citywide': 'New York City', 'statewide': 'New York State', 'ussenate': 'New York State',
            'council': f'Council District {d}'}.get(t, 'The district')
def money(v): return '$' + f'{int(round(v)):,}'
def pct(v): return f'{v:.1f}%'
def fred_month(d):
    m = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    p = d.split('-'); return f'{m[int(p[1]) - 1]} {p[0]}' if len(p) >= 2 else d

def tile(v, label, src, color):
    return f'<div class="tile" style="background:{color}"><div class="v">{esc(v)}</div><div class="l">{esc(label)}</div><div class="s">{esc(src)}</div></div>'

def stats_card(key, title, color='#f47920', council_cds=None, council_n=None, base=''):
    acs = 'ACS 2019–2023'
    if council_cds is not None:
        rows = []
        for cd in council_cds:
            a = stats['areas'].get(cd)
            bits = []
            if a:
                if a.get('pop'): bits.append(f"{int(a['pop']):,} residents")
                if a.get('median_income'): bits.append(money(a['median_income']) + ' median income')
                if a.get('median_rent'): bits.append(money(a['median_rent']) + ' median rent')
            rows.append(f'<a class="row" href="{base}board/{cd}.html"><img src="{base}{seal(cd)}" alt=""><div><b>{esc(board_title(cd))}</b><span>{esc(" · ".join(bits))}</span></div><i>›</i></a>')
        note = f'The Census publishes no figures for council districts. These are the community districts Council District {council_n} covers.'
        return f'<section class="card"><h2 style="--c:{color}">{esc(title)} in numbers</h2><p class="muted">{esc(note)}</p><div class="rows">{"".join(rows)}</div><p class="src">{esc(stats["acs"]["source"])}.</p></section>'
    a = stats['areas'].get(key)
    if not a: return ''
    f = stats['fred']['series'].get(key)
    t = []
    navy, purple, blue, green, red, brown, pg = '#0d1b4b', '#7d4dc2', '#1f70eb', '#2e8c57', '#bf2e33', '#8c5933', '#203d27'
    if a.get('pop'): t.append(tile(f"{int(a['pop']):,}", 'residents', acs, navy))
    if a.get('median_age'): t.append(tile(f"{a['median_age']:.1f}", 'median age', acs, navy))
    if a.get('median_income'): t.append(tile(money(a['median_income']), 'median household income', acs, purple))
    if a.get('median_rent'): t.append(tile(money(a['median_rent']), 'median rent a month, what renters pay', acs, color))
    if f: t.append(tile(pct(f['value']), f"unemployment, {f['label']}" + (f", {pct(f['year_ago'])} a year earlier" if f.get('year_ago') else ''), f"BLS, {fred_month(f['date'])}", blue))
    elif a.get('unemployment_pct') is not None: t.append(tile(pct(a['unemployment_pct']), 'unemployment', acs, blue))
    if a.get('poverty_pct') is not None: t.append(tile(pct(a['poverty_pct']), 'living below the poverty line', acs, red))
    if a.get('renter_pct') is not None: t.append(tile(pct(a['renter_pct']), 'of homes are rented', acs, brown))
    if a.get('rent_burden_pct') is not None: t.append(tile(pct(a['rent_burden_pct']), 'of renters pay 30% or more of income in rent', acs, brown))
    if a.get('median_home_value'): t.append(tile(money(a['median_home_value']), 'median value of an owned home', acs, green))
    if a.get('units'): t.append(tile(f"{int(a['units']):,}", 'homes', acs, pg))
    r = stats['rents']['areas'].get(key)
    rent = ''
    if r:
        chips = ''.join(f'<span class="chip"><em>{l}</em>{money(r[k])}</span>' for l, k in [('Studio', 'rent_studio'), ('1 BR', 'rent_1br'), ('2 BR', 'rent_2br'), ('3 BR', 'rent_3br'), ('All', 'rent_all')] if r.get(k))
        spread = ''
        if r.get('sub_lo') and r.get('sub_hi'):
            spread = f'<p class="muted">Across the boards: {money(r["sub_lo"])} in {esc(r["sub_lo_name"])} to {money(r["sub_hi"])} in {esc(r["sub_hi_name"])}.</p>'
        hoods = f' in {esc(r["neighborhoods"])}' if r.get('neighborhoods') else ''
        rent = f'<a class="row" href="https://bkcb6.app/bkrents/"><div><b>Housing costs on the rent map</b><span>Median asking rents{hoods}</span><div class="chips">{chips}</div>{spread}</div><i>↗</i></a>'
    links = ''
    if key.isdigit() or key == 'b3':
        hp = f'https://bkcb6.app/health/' if key == 'b3' else f'https://bkcb6.app/health/'
        links = (f'<a class="row" href="https://bkcb6.app/health-services.html"><img src="{base}img/agency-dohmh.png" alt=""><div><b>Health and population profile</b><span>Age, income, housing and health outcomes against the city</span></div><i>↗</i></a>'
                 f'<a class="row" href="https://bkcb6.app/landuse-map-cb6.html"><img src="{base}img/agency-dcp.png" alt=""><div><b>Land use and zoning</b><span>What the land is used for, lot by lot, and how it is zoned</span></div><i>↗</i></a>')
    src = stats['acs']['source'] + '.' + (' ' + stats['acs']['note'] if a.get('shared') else '') + (f" Unemployment: {stats['fred']['source']}, series {f['series']}, {fred_month(f['date'])}." if f else '')
    return f'<section class="card"><h2 style="--c:{color}">{esc(title)} in numbers</h2><div class="tiles">{"".join(t)}</div><div class="rows">{rent}{links}</div><p class="src">{esc(src)}</p></section>'

# ---------------------------------------------------------------- bills (mirrors BillStatus.plain)
def bill_status(raw):
    r = (raw or '').lower()
    def committee():
        i = r.find('referred to ')
        if i < 0: return None
        c = raw[i + len('referred to '):].strip(' .,;')
        for p in ['the house committee on ', 'the senate committee on ', 'the committee on ', 'the subcommittee on ', 'committee on ']:
            if c.lower().startswith(p): c = c[len(p):]
        for a in [', and in addition', ' and in addition']:
            if a in c: c = c[:c.index(a)]
        return c[:1].upper() + c[1:].lower() if c else None
    if 'veto' in r: return ('Vetoed', '#bf2e33')
    if 'signed chap' in r or 'chaptered' in r or 'signed by governor' in r or 'signed by the governor' in r: return ('Signed into law by the Governor', '#2e8c57')
    if 'became public law' in r or 'signed by president' in r or 'signed by the president' in r: return ('Signed into law by the President', '#2e8c57')
    if 'signed' in r or 'enacted' in r or 'became law' in r: return ('Signed into law by the Mayor' if 'mayor' in r else 'Signed into law', '#2e8c57')
    if 'presented to president' in r or 'presented to the president' in r: return ('Sent to the President', '#0d1b4b')
    if 'delivered to governor' in r or 'delivered to the governor' in r: return ('Sent to the Governor', '#0d1b4b')
    if 'passed both' in r or 'passed legislature' in r or 'cleared for white house' in r: return ('Passed both houses', '#0d1b4b')
    if 'substituted by' in r: return ('Replaced by the Senate version', '#6b6760')
    if 'returned to assembly' in r or 'returned to senate' in r: return ('Passed both houses', '#0d1b4b')
    if 'passed assembly' in r: return ('Passed the Assembly', '#0d1b4b')
    if 'passed senate' in r: return ('Passed the Senate', '#0d1b4b')
    if 'passed/agreed to in house' in r or 'passed house' in r: return ('Passed the House', '#0d1b4b')
    if 'passed/agreed to in senate' in r: return ('Passed the Senate', '#0d1b4b')
    if 'adopted' in r or 'approved by council' in r: return ('Passed by the Council', '#0d1b4b')
    if 'approved by committee' in r or 'reported' in r or 'third reading' in r or 'ordered to be reported' in r or ('placed on' in r and 'calendar' in r): return ('Passed by committee', '#f47920')
    if 'hearing' in r: return ('Committee hearing held', '#f47920')
    if 'end of session' in r: return ('Died at end of session', '#6b6760')
    if 'withdrawn' in r: return ('Withdrawn', '#6b6760')
    if 'enacting clause stricken' in r: return ('Killed', '#6b6760')
    c = committee()
    if c: return (f'In committee: {c}', '#6b6760')
    if 'committee' in r or 'referred' in r or 'introduced' in r: return ('In committee', '#6b6760')
    return (raw, '#6b6760')

# ---------------------------------------------------------------- page chrome
CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap');
:root{--navy:#0d1b4b;--orange:#f47920;--paper:#f8f7f4;--ink:#14141c;--muted:#6b6760;--rule:#e1dfd8;--green:#203d27}
*{box-sizing:border-box}html,body{margin:0;background:#e9e7e1;font-family:'DM Sans',system-ui,sans-serif;color:var(--ink);-webkit-text-size-adjust:100%}
.phone{max-width:430px;margin:0 auto;min-height:100vh;background:var(--paper);position:relative;box-shadow:0 0 0 1px var(--rule)}
header.hero{background:var(--navy);color:#fff;padding:18px 16px 16px;border-bottom:4px solid var(--orange)}
header.hero .t{display:flex;gap:12px;align-items:center}header.hero img{width:52px;height:52px;border-radius:12px;background:#fff;object-fit:contain}
header.hero h1{font-size:22px;margin:0;line-height:1.15}header.hero p{margin:4px 0 0;font-size:13px;opacity:.9}
header.hero a.back{color:#fff;text-decoration:none;font-weight:700;font-size:14px;display:inline-block;margin-bottom:8px}
main{padding:12px 16px 110px}
h2{font-size:20px;margin:18px 0 10px;padding-left:12px;border-left:4px solid var(--c,var(--orange));line-height:1.1}
.card{background:#fff;border:1px solid var(--rule);border-radius:16px;padding:14px;margin:12px 0}
.card h2{margin-top:0}
.muted{color:var(--muted);font-size:13px;margin:6px 0}.src{color:var(--muted);font-size:11px;margin:10px 0 0}
.tiles{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.tile{border-radius:12px;padding:12px;color:#fff;min-height:92px}.tile .v{font:500 22px 'DM Mono',monospace}.tile .l{font-size:12px;font-weight:500;opacity:.95;margin-top:2px}.tile .s{font:500 9px 'DM Mono',monospace;letter-spacing:.5px;opacity:.75;margin-top:4px}
.rows{display:flex;flex-direction:column;gap:8px;margin-top:10px}
.row{display:flex;gap:12px;align-items:center;background:#fff;border:1px solid var(--rule);border-radius:12px;padding:10px 12px;text-decoration:none;color:var(--ink)}
.row img{width:40px;height:40px;border-radius:8px;object-fit:contain;background:#fff;flex:none}.row b{display:block;color:var(--navy);font-size:15px}.row span{display:block;color:var(--muted);font-size:12px}.row i{margin-left:auto;color:var(--orange);font-style:normal;font-weight:700}
.row div{min-width:0;flex:1}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}.chip{border:1px solid var(--rule);border-radius:999px;padding:4px 9px;font-size:13px;font-weight:700;color:var(--navy);background:var(--paper)}.chip em{font:500 10px 'DM Mono',monospace;color:var(--muted);margin-right:5px}
.map{height:320px;border-radius:16px;border:1px solid var(--rule);overflow:hidden}
.toggles{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.tg{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--rule);border-radius:999px;padding:4px 11px 4px 5px;background:#fff;color:var(--navy);font-size:13px;font-weight:500;cursor:pointer}
.tg img{width:22px;height:22px;border-radius:6px;object-fit:contain}.tg.on{color:#fff;border-color:var(--c)}.tg.on{background:var(--c)}
.hint{color:var(--muted);font-size:11px;margin-top:6px}
.pill{display:inline-block;border-radius:999px;padding:3px 10px;font:500 11px 'DM Mono',monospace;color:#fff;background:#6b6760}
.bill{border:1px solid var(--rule);border-radius:12px;padding:10px;background:#fff;margin-top:8px}.bill .n{font:500 12px 'DM Mono',monospace;color:var(--c,var(--orange))}.bill .d{font:400 11px 'DM Mono',monospace;color:var(--muted);float:right}
.fold>button{width:100%;text-align:left;background:#fff;border:1px solid var(--rule);border-radius:12px;padding:12px 14px;font:500 12px 'DM Mono',monospace;letter-spacing:1px;color:var(--orange);display:flex;justify-content:space-between;cursor:pointer}
.fold>button b{color:var(--orange)}.fold .body{display:none;margin-top:8px}.fold.open .body{display:block}.fold{margin:10px 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.tool{background:#fff;border:1px solid var(--rule);border-radius:12px;padding:12px;min-height:118px;text-decoration:none;color:var(--ink);font-size:14px;font-weight:500;display:flex;flex-direction:column;gap:10px}
.tool img{width:44px;height:44px;border-radius:8px;object-fit:contain}
.big{display:flex;gap:12px;align-items:center;background:linear-gradient(135deg,var(--orange),#d95a14);color:#fff;border:2px solid var(--navy);border-radius:14px;padding:14px;text-decoration:none;box-shadow:0 4px 10px rgba(244,121,32,.35);margin:12px 0}
.big img{width:40px;height:40px;border-radius:8px;background:#fff;object-fit:contain}.big b{font-size:18px;display:block}.big span{font-size:12px;opacity:.9}
nav.tabs{position:fixed;bottom:12px;left:50%;transform:translateX(-50%);width:min(430px,100% - 24px);background:rgba(255,255,255,.96);border:1px solid var(--rule);border-radius:999px;display:flex;padding:6px;box-shadow:0 6px 18px rgba(0,0,0,.12);z-index:50}
nav.tabs a{flex:1;text-align:center;text-decoration:none;color:var(--ink);font-size:10px;font-weight:600;padding:8px 2px;border-radius:999px;line-height:1.15}
nav.tabs a.on{color:var(--orange);background:rgba(20,20,28,.08)}nav.tabs a .ic{display:block;font-size:18px}
section.tab{display:none}section.tab.on{display:block}
iframe.site{width:100%;height:calc(100vh - 230px);min-height:560px;border:1px solid var(--rule);border-radius:14px;background:#fff}
.seals{display:flex;gap:8px;overflow-x:auto;padding:10px 0}.seals a{flex:none;text-align:center;text-decoration:none;color:var(--navy);font-size:10px;font-weight:700}.seals img{width:44px;height:44px;border-radius:10px;border:2px solid var(--rule);background:#fff;object-fit:contain;display:block;margin:0 auto 2px}.seals a.on img{border-color:var(--orange)}
.hero2{background:linear-gradient(135deg,var(--c,var(--orange)),var(--navy));color:#fff;padding:22px 20px;text-align:center;border-bottom:4px solid var(--orange)}
.hero2 img{width:92px;height:92px;border-radius:50%;background:#fff;object-fit:contain;box-shadow:0 4px 8px rgba(0,0,0,.25)}.hero2 h1{font-size:26px;margin:10px 0 2px}.hero2 p{margin:0;font-size:15px;opacity:.92}
.hero2 .pills{margin-top:8px}.hero2 .pills span{display:inline-block;background:#fff;color:var(--navy);border-radius:999px;padding:3px 10px;font:500 11px 'DM Mono',monospace;margin:0 3px}
table{width:100%;border-collapse:collapse;font-size:13px}td,th{padding:6px 4px;border-bottom:1px solid var(--rule);text-align:left}th{font:500 10px 'DM Mono',monospace;letter-spacing:1px;color:var(--muted)}
.bar{height:6px;background:var(--rule);border-radius:3px;overflow:hidden}.bar i{display:block;height:100%;background:var(--orange)}
.leaflet-container{font-family:'DM Sans',sans-serif}.lbl{background:var(--navy);color:#fff;border-radius:999px;padding:2px 8px;font-size:11px;font-weight:700;white-space:nowrap;border:1px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.3)}
.mk{width:30px;height:30px;border-radius:7px;background:#fff;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.35);object-fit:contain}
.mkwrap{text-align:center;width:120px;margin-left:-60px}.mkwrap img{width:30px;height:30px;border-radius:7px;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.35);object-fit:contain}.mkwrap .lbl{display:inline-block;margin-top:2px}
a{color:var(--navy)}
"""

JS = r"""
function fold(btn){btn.parentElement.classList.toggle('open')}
function tabTo(id){document.querySelectorAll('section.tab').forEach(s=>s.classList.toggle('on',s.id==='tab-'+id));document.querySelectorAll('nav.tabs a').forEach(a=>a.classList.toggle('on',a.dataset.tab===id));
  var s=document.getElementById('tab-'+id); if(s){s.querySelectorAll('iframe[data-src]').forEach(f=>{f.src=f.dataset.src;f.removeAttribute('data-src')}); if(s.dataset.map&&!s.dataset.mapped){s.dataset.mapped=1; window['init_'+s.dataset.map]&&window['init_'+s.dataset.map]()}}
  if(location.hash!=='#'+id) history.replaceState(null,'','#'+id); window.scrollTo(0,0)}
function startTabs(def){var h=(location.hash||'').slice(1); tabTo(document.getElementById('tab-'+h)?h:def); document.querySelectorAll('nav.tabs a').forEach(a=>a.onclick=function(e){e.preventDefault();tabTo(a.dataset.tab)})}
function ll(r){return r.map(p=>[p[1],p[0]])}
function polyLayer(rings,opt){return L.polygon(rings.map(ll),opt)}
function iconMarker(latlng,img,label,href){var m=L.marker(latlng,{icon:L.divIcon({className:'',html:'<div class="mkwrap"><img src="'+img+'" onerror="this.style.display=\'none\'"><div class="lbl">'+label+'</div></div>',iconAnchor:[0,15]})}); if(href) m.on('click',()=>location.href=href); return m}
var dataCache={};function getJSON(u){return dataCache[u]||(dataCache[u]=fetch(u).then(r=>r.json()))}
// A district map with toggles: own outline, boards, the four legislatures, subway, Citi Bike, NYC Ferry.
function districtMap(el, cfg){
  var map=L.map(el,{scrollWheelZoom:false,attributionControl:true}); L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=cb1_2hyw_1_9cda1572a3817275ed412c0e',{attribution:'© CARTO © OpenStreetMap',subdomains:'abcd',maxZoom:19}).addTo(map); map.setView([40.65,-73.95],11);
  var groups={}, on={boards:true}, fit=null, own=null;
  Promise.all([getJSON(cfg.base+'data/district-shapes.json'),getJSON(cfg.base+'data/board-shapes.json')]).then(function(r){cfg.shapes=r[0];cfg.boardShapes=r[1];
    if(cfg.ownKey&&cfg.shapes[cfg.ownKey]){own=polyLayer(cfg.shapes[cfg.ownKey],{color:cfg.color||'#f47920',weight:3.5,fill:false}).addTo(map); fit=own.getBounds()}
    else if(cfg.ownCD&&cfg.boardShapes[cfg.ownCD]){own=polyLayer(cfg.boardShapes[cfg.ownCD],{color:cfg.color||'#f47920',weight:3.5,fill:false}).addTo(map); fit=own.getBounds()}
    if(fit) map.fitBounds(fit.pad(.08)); draw();
    var tg=el.parentElement.querySelector('.toggles'); if(tg) tg.querySelectorAll('.tg').forEach(b=>{b.classList.toggle('on',!!on[b.dataset.k]); b.onclick=()=>{on[b.dataset.k]=!on[b.dataset.k]; b.classList.toggle('on',!!on[b.dataset.k]); draw()}});
  });
  function draw(){Object.keys(groups).forEach(k=>{map.removeLayer(groups[k])}); groups={};
    var cds=cfg.cds||[];
    if(on.boards){var g=L.layerGroup(); cds.forEach(cd=>{var r=cfg.boardShapes[cd]; if(!r) return; var p=polyLayer(r,{color:'#0d1b4b',weight:1.5,fill:false,opacity:.6}).addTo(g); var c=p.getBounds().getCenter(); iconMarker(c, cd==='306'?cfg.base+'img/CB6_540.png':cfg.base+'img/cb'+cd+'.png', cfg.boardShort(cd), cfg.base+'board/'+cd+'.html').addTo(g)}); groups.boards=g.addTo(map); if(!fit&&g.getLayers().length){fit=L.featureGroup(g.getLayers().filter(x=>x.getBounds)).getBounds()}}
    ['council','assembly','senate','congress'].forEach(k=>{if(!on[k]) return; var g=L.layerGroup(); (cfg.districts[k]||[]).forEach(d=>{var r=cfg.shapes[k+'-'+d.n]; if(!r) return; polyLayer(r,{color:cfg.levelColor[k],weight:2.5,fill:true,fillOpacity:.05,dashArray:'8 5'}).addTo(g); var c=L.polygon(r.map(ll)).getBounds().getCenter(); iconMarker(c,cfg.base+'img/o/'+d.slug+'.png',d.label,cfg.base+'official/'+d.slug+'.html').addTo(g)}); groups[k]=g.addTo(map)});
    if(on.subway){var g=L.layerGroup(); getJSON(cfg.base+'data/subway-routes.json').then(rs=>{rs.forEach(r=>{(r.l||[]).forEach(seg=>{var pl=L.polyline(ll(seg),{color:r.p.color||'#333',weight:4,opacity:.9}); if(fit&&pl.getBounds().intersects(fit.pad(.15))) pl.addTo(g)})})}); groups.subway=g.addTo(map)}
    if(on.citibike){var g=L.layerGroup(); getJSON(cfg.base+'data/citibike.json').then(ds=>{var b=fit?fit.pad(.1):null; ds.forEach(d=>{var p=L.latLng(d[0],d[1]); if(b&&!b.contains(p)) return; L.marker(p,{icon:L.divIcon({className:'',html:'<img class="mk" style="width:18px;height:18px" src="'+cfg.base+'img/citibike.png">',iconAnchor:[9,9]})}).bindPopup('<b>'+d[3]+'</b><br>Citi Bike · '+d[2]+' docks').addTo(g)})}); groups.citibike=g.addTo(map)}
    if(on.ferry){var g=L.layerGroup(); getJSON(cfg.base+'data/ferry.json').then(f=>{f.routes.filter(r=>r.kind==='ferry').forEach(r=>r.lines.forEach(seg=>L.polyline(seg,{color:r.color,weight:3,opacity:.9}).addTo(g))); f.stops.forEach(s=>L.marker([s.lat,s.lng],{icon:L.divIcon({className:'',html:'<img class="mk" style="width:26px;height:26px;border-radius:50%" src="'+cfg.base+'img/ferry.png">',iconAnchor:[13,13]})}).bindPopup('<b>'+s.name+'</b><br>NYC Ferry · '+s.routes.join(', ')).addTo(g))}); groups.ferry=g.addTo(map)}
    if(own) setTimeout(function(){try{own.bringToFront()}catch(e){}},50);
  }
  return map;
}
"""

LEAF = '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'

def page(title, body, base='', hero='', desc='', extra=''):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">{LEAF}<link rel="stylesheet" href="{base}app.css"><script src="{base}app.js"></script>{extra}</head>
<body><div class="phone">{hero}<main>{body}</main></div></body></html>'''

def toggles(color, own_level=None, base=''):
    t = [('boards', 'Community boards', None, '#0d1b4b')]
    for k, (name, logo, c) in [('council', LEVEL['council']), ('assembly', LEVEL['assembly']), ('senate', LEVEL['senate']), ('congress', LEVEL['congress'])]:
        if k != own_level: t.append((k, name, f'{base}img/{logo}.png', c))
    t += [('subway', 'Subway', f'{base}img/mta.png', '#0b4ea6'), ('citibike', 'Citi Bike', f'{base}img/citibike.png', '#0f7ac2'), ('ferry', 'NYC Ferry', f'{base}img/ferry.png', '#0f8fcf')]
    out = ''.join(f'<span class="tg" data-k="{k}" style="--c:{c}">{("<img src=%s alt=%s>" % (chr(34) + img + chr(34), chr(34) + chr(34))) if img else ""}{esc(n)}</span>' for k, n, img, c in t)
    return f'<div class="toggles">{out}</div><p class="hint">Turn layers on and off. Tap an official\'s logo or a board\'s seal for its page. Zoning and land use lot by lot are on the <a href="https://bkcb6.app/landuse-map-cb6.html">land use map</a>.</p>'

def district_cfg(o_or_cds, own_key, color, base=''):
    """The map config for an official (its own shape and the districts touching its boards) or a board."""
    cds = o_or_cds if isinstance(o_or_cds, list) else [b['cd'] for b in o_or_cds.get('cbs', [])]
    dist = {k: [] for k in LEVEL if k in ('council', 'assembly', 'senate', 'congress')}
    for o in officials:
        if o['type'] in dist and o.get('district') and any(b.get('cd') in cds for b in o.get('cbs', [])):
            lab = {'council': 'Council', 'assembly': 'Assembly', 'senate': 'Senate', 'congress': 'NY-'}[o['type']]
            dist[o['type']].append({'n': o['district'], 'slug': o['slug'], 'label': (lab + ('' if lab.endswith('-') else ' ') + str(o['district']))})
    cfg = {'cds': cds, 'districts': dist, 'color': color, 'base': base, 'levelColor': {k: LEVEL[k][2] for k in ('council', 'assembly', 'senate', 'congress')}}
    if own_key and own_key.isdigit(): cfg['ownCD'] = own_key
    elif own_key: cfg['ownKey'] = own_key
    return cfg

def map_block(cfg, color, own_level=None, base='', mid='m1'):
    bs = json.dumps({'short': {cd: board_short(cd) for cd in cfg['cds']}})
    return (f'<div class="map" id="{mid}"></div>{toggles(color, own_level, base)}'
            f'<script>(function(){{var cfg={json.dumps(cfg)};var bs={bs};cfg.boardShort=function(cd){{return bs.short[cd]||cd}};'
            f'window.addEventListener("load",function(){{districtMap(document.getElementById("{mid}"),cfg)}})}})()</script>')

# ---------------------------------------------------------------- official pages
def official_page(o, base, app_title):
    t = o['type']; lvl = LEVEL.get(t, ('', 'seal-nyc', '#0d1b4b'))
    color = lvl[2]
    key = f"{t}-{o['district']}" if o.get('district') and t in ('council', 'assembly', 'senate', 'congress') else None
    own = shapes.get(key, []) if key else []
    cfg = district_cfg(o, key if own else None, color, base)
    hero = (f'<header class="hero" style="padding-bottom:0;border:0"><a class="back" href="{base}index.html">‹ {esc(app_title)}</a></header>'
            f'<div class="hero2" style="--c:{color}"><img src="{base}img/o/{o["slug"]}.png" alt=""><h1>{esc(o["name"])}</h1><p>{esc(o["seat"])}</p>'
            f'<div class="pills"><span>{esc(lvl[0])}</span>{("<span>" + esc(o["boro"]) + "</span>") if o.get("boro") else ""}</div></div>')
    body = [f'<h2 style="--c:{color}">{"The district" if own else "Where they serve"}</h2>', map_block(cfg, color, t if own else None, base, 'm1')]
    about = (o.get('bio') or []) + (o.get('about') or [])
    if about: body.append(f'<h2 style="--c:{color}">About</h2><div class="card">' + ''.join(f'<p>{esc(p)}</p>' for p in about) + '</div>')
    sk = scope_key(o)
    if t == 'council': body.append(stats_card(None, f"Council District {o['district']}", color, council_cds=[b['cd'] for b in o.get('cbs', [])], council_n=o['district'], base=base))
    elif sk: body.append(stats_card(sk, scope_title(o), color, base=base))
    bills = o.get('bills') or []
    if bills:
        rows = ''
        for b in bills:
            st, c = bill_status(b.get('status', '')) if b.get('status') else ('', '')
            rows += f'<div class="bill"><span class="d">{esc(b.get("date", ""))}</span><span class="n">{esc(b["num"])}</span> {("<span class=pill style=background:%s>%s</span>" % (c, esc(st))) if st else ""}<div>{esc(b.get("title", ""))}</div></div>'
        body.append(f'<h2 style="--c:{color}">Bills</h2>{rows}')
    com = o.get('committees') or []
    if com:
        body.append(f'<h2 style="--c:{color}">Committees</h2><div class="chips">' + ''.join(f'<span class="chip">{("<em>" + esc(c["role"]) + "</em>") if c.get("role") and c["role"] != "Member" else ""}{esc(c["name"])}</span>' for c in com) + '</div>')
    of = o.get('office') or {}
    if any(of.get(k) for k in ('a1', 'a2', 'phone', 'site')):
        ph = of.get('phone', '')
        phs = f'({ph[:3]}) {ph[3:6]}-{ph[6:]}' if len(ph) == 10 else ph
        body.append(f'<h2 style="--c:{color}">Contact</h2><div class="card">' + (f'<p><b>{esc(of.get("a1", ""))}</b><br>{esc(of.get("a2", ""))}</p>' if of.get('a1') else '')
                    + (f'<p><a href="tel:{esc(ph)}">{esc(phs)}</a></p>' if ph else '') + (f'<p><a href="{esc(of["site"])}">Website ↗</a></p>' if of.get('site') else '') + '</div>')
    # Overlap
    cbs = o.get('cbs') or []; dists = o.get('dists') or []
    ov = [f'<h2 style="--c:{color}">Overlap</h2>']
    if cbs:
        tot = sum(b.get('eds', 0) for b in cbs) or 1
        ov.append('<div class="card"><h2 style="--c:#0d1b4b;font-size:16px">Community boards</h2><div class="rows">' + ''.join(
            f'<a class="row" href="{base}board/{b["cd"]}.html"><img src="{base}{seal(b["cd"])}" alt=""><div><b>{esc(board_title(b["cd"]))}</b><span>{b.get("eds", 0)} election districts</span><div class="bar"><i style="width:{100 * b.get("eds", 0) / tot:.0f}%"></i></div></div><i>›</i></a>' for b in cbs) + '</div><p class="muted">Bars show how many of the district\'s election districts fall in each board.</p></div>')
    if dists:
        ov.append('<div class="card"><h2 style="--c:#0d1b4b;font-size:16px">Overlapping elected officials</h2><div class="rows">' + ''.join(
            f'<a class="row" href="{base}official/{d["slug"]}.html"><img src="{base}img/o/{d["slug"]}.png" alt=""><div><b>{esc(d["name"])}</b><span>{esc(d["label"])} · {d.get("eds", 0)} election districts</span></div><i>›</i></a>' for d in dists if d.get('slug') in by_slug) + '</div></div>')
    for g in o.get('overlaps') or []:
        rows = ''.join(f'<tr><td>{esc(r.get("n", ""))}</td><td>{esc(r.get("a", ""))}</td><td>{esc(r.get("b", ""))}</td></tr>' for r in g.get('rows', []))
        ov.append(f'<div class="fold"><button onclick="fold(this)"><b>{esc(g.get("t", "")).upper()}</b><span>+</span></button><div class="body"><table>{rows}</table></div></div>')
    body += ov
    return page(f'{o["name"]} · {app_title}', ''.join(body), base, hero, o['seat'])

# ---------------------------------------------------------------- board pages
def board_page(cd, base, app_title, is_cb6_app):
    b = boards.get(cd, {}); color = '#f47920'
    cfg = district_cfg([cd], cd, color, base)
    hero = (f'<header class="hero"><a class="back" href="{base}index.html">‹ {esc(app_title)}</a><div class="t"><img src="{base}{seal(cd)}" alt=""><div><h1>{esc(board_title(cd))}</h1><p>Brooklyn Community District {int(cd[1:])}</p></div></div></header>')
    body = [f'<h2>The district</h2>', map_block(cfg, color, None, base, 'm1')]
    about = b.get('about') or []
    if isinstance(about, str): about = [about]
    if about: body.append('<h2>About</h2><div class="card">' + ''.join(f'<p>{esc(p)}</p>' for p in about) + '</div>')
    body.append(stats_card(cd, board_short(cd), color, base=base))
    con = ''
    if b.get('chair'): con += f'<p><em>Chairperson</em><br><b>{esc(b["chair"])}</b></p>'
    if b.get('dm'): con += f'<p><em>District Manager</em><br><b>{esc(b["dm"])}</b></p>'
    if b.get('office'): con += f'<p><em>District office</em><br>{esc(b["office"])}</p>'
    if b.get('website'): con += f'<p><a href="{esc(b["website"])}">Board website ↗</a></p>'
    if con: body.append(f'<h2>Contact</h2><div class="card">{con}</div>')
    n = int(cd[1:])
    body.append(f'<h2>Meetings</h2><div class="rows"><a class="row" href="https://bkcb6.app/calendar.html?cd=bk-{n}"><img src="{base}{seal(cd)}" alt=""><div><b>{esc(board_short(cd))} on the calendar</b><span>Every meeting of the board and its committees</span></div><i>↗</i></a></div>')
    tools = [('Who represents ' + board_short(cd), f'{base}directory.html', 'img/office-council.png'), ('Block cards: parking, trash, poll site, subway', 'https://bkcb6.app/address.html', 'img/nyc-parking.png'),
             ('Parks, playgrounds, fields and courts', f'https://bkcb6.app/parks/bk-{n}.html', 'img/agency-dpr.png'), ('311, crime, tickets and permits', f'https://bkcb6.app/311-district.html?cd=bk-{n}', 'img/agency-311.png'),
             ('Transportation: streets, transit, bikes', 'https://bkcb6.app/transport', 'img/mta.png'), ('Weather, flood maps and alerts', 'https://bkcb6.app/weather.html', 'img/agency-dep.png'),
             ('Land use and zoning charts', f'https://bkcb6.app/zoning-housing-cb6.html' if cd == '306' else 'https://bkcb6.app/landuse-lumap.html', 'img/agency-dcp.png'),
             ('Zoning explained: what you can build, how review works', 'https://bkcb6.app/useofland/', 'img/agency-bsa.png'),
             ('Health profile', 'https://bkcb6.app/health-services.html', 'img/agency-dohmh.png'), ('Every lot: zoning, owner, what is built', 'https://bkcb6.app/landuse-lots.html', 'img/agency-dob.png')]
    body.append('<h2>Around you in ' + esc(board_short(cd)) + '</h2><div class="grid">' + ''.join(f'<a class="tool" href="{u}"><img src="{base}{i}" alt="">{esc(t)}</a>' for t, u, i in tools) + '</div>')
    reps = b.get('reps')
    if isinstance(reps, str):
        try: reps = json.loads(reps.replace("'", '"'))
        except Exception: reps = []
    return page(f'{board_title(cd)} · {app_title}', ''.join(body), base, hero, f'Brooklyn Community District {n}')

# ---------------------------------------------------------------- directory and orgs
def directory_page(base, app_title, cb6_app):
    order = directory['order']; rows = directory['rows']
    def official_for(name, cat):
        parts = name.split(' · ')
        if len(parts) != 2: return None
        last, tag = parts
        def norm(t): return re.sub(r'[.’\']', '', t).lower()
        def pick(level, n):
            for o in officials:
                if o['type'] == level and (n is None or o.get('district') == n) and norm(o['name']).endswith(norm(last)): return o
        num = re.sub(r'^\D*', '', tag); num = int(num) if num.isdigit() else None
        if tag.startswith('CD'): return pick('council', num)
        if tag.startswith('AD'): return pick('assembly', num)
        if tag.startswith('SD'): return pick('senate', num)
        if tag.startswith('NY-'): return pick('congress', num)
        if tag.endswith('BP'): return pick('bp', None)
        if tag.endswith('DA'): return pick('da', None)
        if cat == 'Citywide': return pick('citywide', None) or pick('statewide', None) or pick('ussenate', None)
    secs = []
    have = set(os.listdir(os.path.join(OUT, 'official'))) if os.path.isdir(os.path.join(OUT, 'official')) else set()
    for cat in order:
        items = []
        for r in sorted([r for r in rows if r[1] == cat], key=lambda r: r[0]):
            name, url, desc, area = r[0], r[3], r[4] if len(r) > 4 else '', r[6] if len(r) > 6 else ''
            if cb6_app and cat != 'Community Boards' and area not in ('BK', 'citywide', 'statewide') and cat not in ('Citywide',): pass
            href, img, inapp = url, None, False
            m = re.match(r'(Manhattan|Bronx|Brooklyn|Queens|Staten Island) Community Board (\d+)', name)
            if cat == 'Community Boards' and m:
                cd = {'Manhattan': '1', 'Bronx': '2', 'Brooklyn': '3', 'Queens': '4', 'Staten Island': '5'}[m.group(1)] + f'{int(m.group(2)):02d}'
                if cd.startswith('3') and (not cb6_app or cd == '306'): href, inapp = f'{base}board/{cd}.html', True
                img = seal(cd) if cd.startswith('3') else None
            o = official_for(name, cat) if cat in ('Citywide', 'Borough Presidents', 'NYC Council', 'State Assembly', 'State Senate', 'U.S. Congress', 'District Attorneys') else None
            label = f"{o['name']} · {o['seat']}" if o else name
            if o and f"{o['slug']}.html" in have: href, inapp, img = f'{base}official/{o["slug"]}.html', True, f'img/o/{o["slug"]}.png'
            items.append(f'<a class="row" href="{esc(href)}">{("<img src=%s%s%s alt=%s%s>" % (chr(34), base + img, chr(34), chr(34), chr(34))) if img else ""}<div><b>{esc(label)}</b><span>{esc(desc or cat)}</span></div><i>{"›" if inapp else "↗"}</i></a>')
        if items: secs.append(f'<div class="fold"><button onclick="fold(this)"><b>{esc(cat).upper()} · {len(items)}</b><span>+</span></button><div class="body"><div class="rows">{"".join(items)}</div></div></div>')
    org_items = ''.join(f'<a class="row" href="https://bkcb6.app/{esc(p["slug"])}/"><div><b>{esc(p["name"])}</b><span>{esc(p.get("seat", ""))}</span></div><i>↗</i></a>' for p in sorted(orgs, key=lambda p: p['name'].lower()) if p.get('kind', 'org') not in ('official', 'agency'))
    secs.append(f'<div class="fold"><button onclick="fold(this)"><b>COMMUNITY ORGANIZATIONS · {len([p for p in orgs if p.get("kind", "org") not in ("official", "agency")])}</b><span>+</span></button><div class="body"><div class="rows">{org_items}</div></div></div>')
    hero = f'<header class="hero"><a class="back" href="{base}index.html">‹ {esc(app_title)}</a><div class="t"><img src="{base}img/{"CB6_540" if cb6_app else "BKCIVICS"}.png" alt=""><div><h1>Government Directory</h1><p>Every board, official, agency and organization, each with its page</p></div></div></header>'
    return page(f'Government Directory · {app_title}', '<p class="muted">Each section is closed until you tap it.</p>' + ''.join(secs) + f'<p class="src">{esc(directory.get("note", ""))}</p>', base, hero)

def orgs_page(base, app_title):
    topics = {}
    for p in orgs:
        if p.get('kind') == 'official': continue
        t = 'Government and agencies' if p.get('kind') == 'agency' else 'Community organizations'
        topics.setdefault(t, []).append(f'<a class="row" href="https://bkcb6.app/{esc(p["slug"])}/"><div><b>{esc(p["name"])}</b><span>{esc(p.get("seat", ""))}</span></div><i>↗</i></a>')
    for o in officials:
        if covers_cb6(o): topics.setdefault('Elected officials', []).append(f'<a class="row" href="{base}official/{o["slug"]}.html"><img src="{base}img/o/{o["slug"]}.png" alt=""><div><b>{esc(o["name"])}</b><span>{esc(o["seat"])}</span></div><i>›</i></a>')
    cols = biz['cols']; rows = biz['rows']
    ci = {c: i for i, c in enumerate(cols)}
    for r in sorted(rows, key=lambda r: str(r[ci.get('name', 0)]).lower()):
        name = r[ci['name']] if 'name' in ci else r[0]
        kind = r[ci['kind']] if 'kind' in ci else ''
        addr = r[ci['address']] if 'address' in ci else ''
        topics.setdefault('Local shops and restaurants', []).append(f'<a class="row" href="https://bkcb6.app/biz-{slug(name)}/"><div><b>{esc(name)}</b><span>{esc(" · ".join(x for x in [kind, addr] if x))}</span></div><i>↗</i></a>')
    for c in culture:
        if c.get('boro') != 'BK': continue
        k = (c.get('category_group') or c.get('category') or '').lower()
        t = 'Youth, schools and libraries' if 'library' in k else 'Music and film' if 'movie' in k else 'Parks, gardens and the environment' if 'park' in k else 'Arts and culture'
        topics.setdefault(t, []).append(f'<a class="row" href="https://bkcb6.app/culture-map.html?cb={esc(c.get("cb", ""))}"><div><b>{esc(c["name"])}</b><span>{esc(" · ".join(x for x in [c.get("category_group") or c.get("category", ""), c.get("address", "")] if x))}</span></div><i>↗</i></a>')
    order = ['Community organizations', 'Arts and culture', 'Music and film', 'Parks, gardens and the environment', 'Youth, schools and libraries', 'Local shops and restaurants', 'Government and agencies', 'Elected officials']
    secs = ''.join(f'<div class="fold"><button onclick="fold(this)"><b>{esc(t).upper()} · {len(topics[t])}</b><span>+</span></button><div class="body"><div class="rows">{"".join(topics[t])}</div></div></div>' for t in order if topics.get(t))
    hero = f'<header class="hero"><a class="back" href="{base}index.html">‹ {esc(app_title)}</a><div class="t"><img src="{base}img/CB6_540.png" alt=""><div><h1>Organizations</h1><p>Community groups, officials, agencies, businesses and cultural places</p></div></div></header>'
    total = sum(len(v) for v in topics.values())
    return page(f'Organizations · {app_title}', f'<p class="muted">{total:,} entries. Each section is closed until you tap it.</p>' + secs, base, hero)

# ---------------------------------------------------------------- the shells
def tabbar(tabs, active=None):
    return '<nav class="tabs">' + ''.join(f'<a href="#{k}" data-tab="{k}"><span class="ic">{ic}</span>{esc(n)}</a>' for k, n, ic in tabs) + '</nav>'

def tool_grid(items, base=''):
    return '<div class="grid">' + ''.join(f'<a class="tool" href="{esc(u)}"><img src="{base}{i}" alt="">{esc(t)}</a>' for t, u, i in items) + '</div>'

def iframe(url): return f'<iframe class="site" data-src="{esc(url)}" loading="lazy" title="{esc(url)}"></iframe><p class="hint">Opens inside the app. <a href="{esc(url)}">Open the page on its own ↗</a></p>'

ABOUT = ["Community boards are the official, independent, and advisory bodies of New York City Government. There are 59 across NYC: 18 in Brooklyn, 14 in Queens, 12 in Manhattan, 12 in the Bronx, and 3 in Staten Island. They vote on issues across policy areas such as land use (first stop in ULURP), landmarks, liquor licenses, transportation, and budgets (past votes and minutes). Members are appointed by the borough president (half) and the city council members overlapping with the community district.",
         "This app focuses on Brooklyn Community Board 6 (CB6), which encompasses the neighborhoods of Park Slope, Carroll Gardens, Cobble Hill, the Columbia Waterfront, Red Hook, and Gowanus. Please note that the numbers start over in every borough, so there is a CB6 in Manhattan, Queens, and the Bronx.",
         "But like I said, this app focuses on Brooklyn’s 6th community district, but we have apps that go beyond those boundaries if you're interested."]

def cb6_shell(base=''):
    tabs = [('home', 'Home', '⌂'), ('meetings', 'Meetings', '▦'), ('landuse', 'Land Use & Landmarks', '▤'), ('orgs', 'Orgs', '☷'), ('jobs', 'Jobs', '▣'), ('board', 'Board', '☰')]
    hero = '<header class="hero"><div class="t"><img src="img/CB6_540.png" alt=""><div><h1>Brooklyn Community Board 6</h1><p>Park Slope, Carroll Gardens, Cobble Hill, Red Hook, Gowanus, Columbia Street Waterfront District</p></div></div></header>'
    cfg = district_cfg(['306'], '306', '#f47920', base)
    around = [('Who represents CB6', 'board/306.html#reps', 'img/office-council.png'), ('Block cards: parking, trash, poll site, subway for any block', 'https://bkcb6.app/address.html', 'img/nyc-parking.png'),
              ('Parks, playgrounds, fields and courts', 'https://bkcb6.app/parks/bk-6.html', 'img/agency-dpr.png'), ('311, crime, tickets and permits', 'https://bkcb6.app/311-district.html?cd=bk-6', 'img/agency-311.png'),
              ('Transportation: streets, transit, bikes, Vision Zero', 'https://bkcb6.app/transport-map-cb6.html', 'img/mta.png'), ('Weather, flood maps and alerts', 'https://bkcb6.app/weather.html', 'img/agency-dep.png'),
              ('Safety and alerts: NYPD, FDNY, DSNY, 311, weather', 'https://bkcb6.app/safety.html', 'img/agency-nypd.png')]
    services = [('Healthcare and social services', 'https://bkcb6.app/healthcare.html', 'img/agency-dohmh.png'), ('Schools, libraries, childcare and other facilities', 'https://bkcb6.app/eduhub-bk-6', 'img/agency-nycps.png'),
                ('Business directory', 'orgs.html', 'img/agency-sbs.png'), ('Liquor licenses', 'https://bkcb6.app/liquor-map-cb6.html', 'img/nysla.png'), ('Jobs and funding', '#jobs', 'img/agency-dycd.png')]
    gov = [('Zoning and land use review', 'https://bkcb6.app/useofland/', 'img/agency-dcp.png'), ('Permits, buildings and landmarks', 'https://bkcb6.app/landmarks-cb6.html', 'img/agency-lpc.png'),
           ('Housing: renting in CB6, NYCHA, every building', 'https://bkcb6.app/allhousing/', 'img/agency-hpd.png'), ('City and state budgets', 'https://bkcb6.app/budget.html', 'img/seal-nyc.png'),
           ('The NYC City Charter', 'https://bkcb6.app/charter.html', 'img/seal-nyc.png'), ('Government org charts', 'https://bkcb6.app/govhub.html', 'img/seal-nyc.png'), ('Government directory', 'directory.html', 'img/office-council.png')]
    projects = [('Gowanus rezoning', 'https://bkcb6.app/gowanus.html', 'img/agency-dcp.png'), ('Brooklyn Marine Terminal', 'https://bkcb6.app/bmt.html', 'img/agency-dcp.png'), ('The BQE', 'https://bkcb6.app/bqe.html', 'img/agency-dot.png'),
                ('Brooklyn Comprehensive Plan', 'https://bkcb6.app/bkcompplan/', 'img/bp-reynoso.png'), ('Fair Housing Growth Strategy', 'https://bkcb6.app/fhgs/', 'img/agency-hpd.png')]
    elections = [('November 3, 2026: what is on the ballot', 'https://bkcb6.app/2026electioncb6.html', 'img/agency-boe.png'), ('Find your poll site', 'https://bkcb6.app/poll-finder-bk.html', 'img/agency-boe.png'), ('Election results and maps', 'https://bkcb6.app/elections.html', 'img/agency-boe.png')]
    home = (f'<div class="fold"><button onclick="fold(this)"><b>WHAT IS A COMMUNITY BOARD?</b><span>+</span></button><div class="body card">' + ''.join(f'<p>{esc(p)}</p>' for p in ABOUT) + '<p><b>Mike Racioppo</b></p><div class="rows"><a class="row" href="https://bkcb6.app/apps/"><div><b>Not in CB6?</b><span>BKCB covers all 18 Brooklyn boards; CB6 &amp; Beyond covers all 59</span></div><i>↗</i></a></div></div></div>'
            f'<h2>The district</h2>{map_block(cfg, "#f47920", None, base, "mhome")}'
            f'<div class="rows" style="margin-top:12px"><a class="row" href="https://bkcb6.app/cb6-map.html"><img src="img/CB6_540.png" alt=""><div><b>The CB6 map</b><span>Every overlay and district, zoning and land use lot by lot, address search and pin drop</span></div><i>↗</i></a>'
            f'<a class="row" href="https://bkcb6.app/calendar.html"><img src="img/CB6_540.png" alt=""><div><b>Next meeting</b><span>The CB6 calendar: full board, committees and the community</span></div><i>↗</i></a>'
            f'<a class="row" href="https://bkcb6.app/2026electioncb6.html"><img src="img/agency-boe.png" alt=""><div><b>Election Day, November 3</b><span>Register by October 24. Your poll site and ballot</span></div><i>↗</i></a></div>'
            f'<h2>Around you</h2>{tool_grid(around)}<h2>Services and business</h2>{tool_grid(services)}<h2>Land use and government</h2>{tool_grid(gov)}<h2>Projects and plans</h2>{tool_grid(projects)}<h2>Elections and voting</h2>{tool_grid(elections)}')
    landmarks = ('<section class="card"><div class="t" style="display:flex;gap:12px;align-items:center"><img src="img/lpc.png" style="width:44px;height:44px;border-radius:8px" alt=""><div><b style="font-size:18px;color:var(--navy)">Landmarks &amp; Historic Districts</b><p class="muted">CB6 has 6 historic districts. The Landmarks &amp; Land Use Committee reviews all Certificate of Appropriateness applications before they go to LPC.</p></div></div>'
                 '<div class="fold"><button onclick="fold(this)"><b>WHAT THE COMMITTEE DOES</b><span>+</span></button><div class="body"><p>An NYC Historic District is a defined area designated by the Landmarks Preservation Commission for its architectural, cultural, or historic significance. Places like large parts of Park Slope and Cobble Hill reflect distinct periods of the city\'s history, and exterior changes generally require LPC approval to preserve that character. A good rule of thumb is to check the street signs: brown with white lettering usually means you are in a historic district, while green with white lettering usually means you are not. In Brooklyn Community Board 6, that often means we are part of the review process for applications seeking LPC approval, including Certificates of Appropriateness for proposed changes to landmarked properties.</p></div></div>'
                 '<div class="fold"><button onclick="fold(this)"><b>THE CERTIFICATE OF APPROPRIATENESS PROCESS</b><span>+</span></button><div class="body"><p class="muted">Required for any exterior work on a landmarked building or property in a historic district.</p><ol><li><b>Application</b>: Owner submits drawings, photos, and material samples to LPC.</li><li><b>CB6 Review</b>: Landmarks &amp; Land Use Committee reviews and recommends. Full board votes. Advisory, but part of the official record.</li><li><b>LPC Public Hearing</b>: Presented to all 11 commissioners. Public may testify.</li><li><b>Commission Vote</b>: Approve, modify, or deny.</li><li><b>Permit Issued</b>: If approved, work can proceed.</li></ol><p><a href="https://www.nyc.gov/site/lpc/index.page">More at nyc.gov/lpc ↗</a></p></div></div>'
                 '<div class="rows"><a class="row" href="https://bkcb6.app/calendar.html"><img src="img/CB6_540.png" alt=""><div><b>Next Landmarks committee meeting</b><span>On the CB6 calendar: Landmarks, Land Use &amp; Housing</span></div><i>↗</i></a></div></section>'
                 + iframe('https://bkcb6.app/landmarks-cb6.html'))
    landuse = (landmarks + '<h2>Land use</h2>' + tool_grid([('CB6 map', 'https://bkcb6.app/cb6-map.html', 'img/CB6_540.png'), ('Zoning and land use review', 'https://bkcb6.app/useofland/', 'img/agency-dcp.png'),
               ('Every lot: zoning, owner, what is built', 'https://bkcb6.app/landuse-lots.html', 'img/agency-dob.png'), ('Housing', 'https://bkcb6.app/allhousing/', 'img/agency-hpd.png'),
               ('Land use and zoning charts', 'https://bkcb6.app/zoning-housing-cb6.html', 'img/agency-dcp.png'), ('Glossary', 'https://bkcb6.app/glossary.html', 'img/agency-dcp.png')])
               + '<h2>Projects</h2>' + tool_grid(projects[:3]))
    body = (f'<section class="tab" id="tab-home">{home}</section>'
            f'<section class="tab" id="tab-meetings"><h2>Meetings and the calendar</h2>{iframe("https://bkcb6.app/calendar.html")}</section>'
            f'<section class="tab" id="tab-landuse"><h2>Land Use &amp; Landmarks</h2>{landuse}</section>'
            f'<section class="tab" id="tab-orgs"><h2>Organizations</h2><div class="rows"><a class="row" href="orgs.html"><img src="img/CB6_540.png" alt=""><div><b>Open the directory</b><span>Community groups, cultural places, every local business, every elected official who covers CB6</span></div><i>›</i></a><a class="row" href="directory.html"><img src="img/office-council.png" alt=""><div><b>Government Directory</b><span>Every board, official and agency, each with its page</span></div><i>›</i></a></div>{iframe("https://bkcb6.app/orgs.html")}</section>'
            f'<section class="tab" id="tab-jobs"><h2>Jobs and funding</h2>{iframe("https://bkcb6.app/activities.html")}</section>'
            f'<section class="tab" id="tab-board"><h2>The Board</h2>{iframe("https://bkcb6.app/minutes.html")}</section>')
    return page('BKCB6 · the app on the web', body + tabbar(tabs) + '<script>startTabs("home")</script>', base, hero, 'BKCB6, the Brooklyn Community Board 6 app, on the web')

def bk_shell(base=''):
    tabs = [('home', 'Home', '⌂'), ('calendar', 'Calendar', '▦'), ('boards', 'Boards', '☰'), ('brooklyn', 'Brooklyn', '▤')]
    hero = '<header class="hero"><div class="t"><img src="img/BKCIVICS.png" alt=""><div><h1>BKCB</h1><p>Brooklyn\'s 18 community boards, block by block</p></div></div></header>'
    cds = [f'3{n:02d}' for n in range(1, 19)]
    seals = '<div class="seals">' + ''.join(f'<a href="board/{cd}.html"><img src="{seal(cd)}" alt="">CB{int(cd[1:])}</a>' for cd in cds) + '</div>'
    cfg = district_cfg(cds, None, '#0d1b4b', base)
    bp = by_slug.get('bpbrooklyn')
    home = (f'<div class="card"><b style="font-size:17px;color:var(--navy)">What\'s your district?</b><p class="muted">Tap a seal for the board\'s page. The whole app follows the community district you pick.</p>{seals}</div>'
            f'<h2 style="--c:#0d1b4b">Brooklyn</h2>{map_block(cfg, "#0d1b4b", None, base, "mhome")}'
            + (f'<a class="big" href="official/bpbrooklyn.html"><img src="img/bp-reynoso.png" alt=""><div><b>Borough President Antonio Reynoso</b><span>Brooklyn in numbers, the Comprehensive Plan, Borough Hall</span></div></a>' if bp else '')
            + '<h2 style="--c:#0d1b4b">Brooklyn</h2>' + tool_grid([('Brooklyn Comprehensive Plan', 'https://bkcb6.app/bkcompplan/', 'img/bp-reynoso.png'), ('Fair Housing Growth Strategy', 'https://bkcb6.app/fhgs/', 'img/agency-hpd.png'),
                ('City and state budgets', 'https://bkcb6.app/budget.html', 'img/seal-nyc.png'), ('Government directory: agencies, officials, boards', 'directory.html', 'img/office-council.png'),
                ('The NYC City Charter', 'https://bkcb6.app/charter.html', 'img/seal-nyc.png'), ('Government org charts: NYC and New York State', 'https://bkcb6.app/govhub.html', 'img/seal-nyc.png'),
                ('The BQE', 'https://bkcb6.app/bqe.html', 'img/agency-dot.png'), ('Brooklyn Marine Terminal', 'https://bkcb6.app/bmt.html', 'img/agency-dcp.png'),
                ('Gowanus rezoning', 'https://bkcb6.app/gowanus.html', 'img/agency-dcp.png'), ('Every elected official in the city', 'directory.html', 'img/office-council.png')])
            + '<div class="fold"><button onclick="fold(this)"><b>WHAT IS A COMMUNITY BOARD?</b><span>+</span></button><div class="body card">' + f'<p>{esc(ABOUT[0])}</p><p>BKCB covers the 18 community districts of Brooklyn, from Greenpoint and Williamsburg (CB1) to Canarsie and Flatlands (CB18). Pick your board and the whole app follows it: its map, meetings, officials, blocks, parks, streets, land use and health. The Brooklyn tab holds what is borough wide.</p><p>Please note that the numbers start over in every borough, so there is a CB6 in Manhattan, Queens, and the Bronx.</p><p><b>Mike Racioppo</b></p></div></div>')
    board_rows = '<div class="rows">' + ''.join(f'<a class="row" href="board/{cd}.html"><img src="{seal(cd)}" alt=""><div><b>{esc(board_title(cd))}</b><span>{esc(boards.get(cd, {}).get("office", ""))}</span></div><i>›</i></a>' for cd in cds) + '</div>'
    brooklyn = ('<div class="rows">' + ''.join(f'<a class="row" href="official/{o["slug"]}.html"><img src="img/o/{o["slug"]}.png" alt=""><div><b>{esc(o["name"])}</b><span>{esc(o["seat"])}</span></div><i>›</i></a>' for o in officials if o['type'] in ('bp', 'da') and 'brooklyn' in o.get('boro', '').lower()) + '</div>'
                + '<h2 style="--c:#0d1b4b">Borough wide</h2>' + tool_grid([('Brooklyn Comprehensive Plan', 'https://bkcb6.app/bkcompplan/', 'img/bp-reynoso.png'), ('Fair Housing Growth Strategy', 'https://bkcb6.app/fhgs/', 'img/agency-hpd.png'),
                  ('City and state budgets', 'https://bkcb6.app/budget.html', 'img/seal-nyc.png'), ('The NYC City Charter', 'https://bkcb6.app/charter.html', 'img/seal-nyc.png'), ('Government org charts', 'https://bkcb6.app/govhub.html', 'img/seal-nyc.png'),
                  ('The BQE', 'https://bkcb6.app/bqe.html', 'img/agency-dot.png'), ('Brooklyn Marine Terminal', 'https://bkcb6.app/bmt.html', 'img/agency-dcp.png'), ('Gowanus rezoning', 'https://bkcb6.app/gowanus.html', 'img/agency-dcp.png'),
                  ('Brooklyn land use and zoning, lot by lot', 'https://bkcb6.app/landuse-lumap.html', 'img/agency-dcp.png'), ('Brooklyn health and population profile', 'https://bkcb6.app/health-services.html', 'img/agency-dohmh.png'),
                  ('Government directory', 'directory.html', 'img/office-council.png'), ('Weather, flood maps and alerts', 'https://bkcb6.app/weather.html', 'img/agency-dep.png')]))
    body = (f'<section class="tab" id="tab-home">{home}</section>'
            f'<section class="tab" id="tab-calendar"><h2 style="--c:#0d1b4b">Calendar</h2>{iframe("https://bkcb6.app/calendar.html")}</section>'
            f'<section class="tab" id="tab-boards"><h2 style="--c:#0d1b4b">All 18 Brooklyn community boards</h2>{board_rows}</section>'
            f'<section class="tab" id="tab-brooklyn"><h2 style="--c:#0d1b4b">Brooklyn</h2>{brooklyn}</section>')
    return page('BKCB · the app on the web', body + tabbar(tabs) + '<script>startTabs("home")</script>', base, hero, 'BKCB, the app for Brooklyn\'s 18 community districts, on the web')

# ---------------------------------------------------------------- assets
IMGS = ['CB6_540', 'BKCIVICS', 'bp-reynoso', 'office-council', 'office-assembly', 'office-senate', 'office-house', 'seal-nyc', 'agency-dohmh', 'agency-dcp', 'agency-lpc', 'agency-dep', 'agency-dpr', 'agency-311', 'agency-bsa', 'agency-dob', 'agency-nypd', 'agency-hpd', 'agency-sbs', 'agency-dycd', 'agency-boe', 'agency-dot', 'agency-nycps', 'nyc-parking']
def copy_assets(out, offs):
    os.makedirs(f'{out}/img/o', exist_ok=True); os.makedirs(f'{out}/data', exist_ok=True)
    for n in IMGS:
        for src in (f'{SRC}/Logos/{n}.png', f'{SRC6}/Logos/{n}.png'):
            if os.path.exists(src): shutil.copy(src, f'{out}/img/{n}.png'); break
    for n in ('citibike', 'ferry', 'mta', 'nysla', 'lpc'):
        src = f'{CIVIC}/mapicons/{n}.png'
        if os.path.exists(src): shutil.copy(src, f'{out}/img/{n}.png')
    # Marks the app carries under other names.
    for want, cands in {'nyc-parking': ['blk-asp-symbol'], 'agency-nycps': ['blk-school-nycps'], 'agency-dot': []}.items():
        if os.path.exists(f'{out}/img/{want}.png'): continue
        for cand in cands:
            src = f'{SRC}/Logos/{cand}.png'
            if os.path.exists(src): shutil.copy(src, f'{out}/img/{want}.png'); break
    src = f'{CIVIC}/orgs/logos/nycdot.png'
    if not os.path.exists(f'{out}/img/agency-dot.png') and os.path.exists(src): shutil.copy(src, f'{out}/img/agency-dot.png')
    for cd in [f'3{n:02d}' for n in range(1, 19)]:
        src = f'{CIVIC}/boardlogos/cb{cd}.png'
        if os.path.exists(src): shutil.copy(src, f'{out}/img/cb{cd}.png')
    for o in offs:
        src = f'{CIVIC}/officials/{o["slug"]}.png'
        if os.path.exists(src): shutil.copy(src, f'{out}/img/o/{o["slug"]}.png')
    for n in ('subway-routes.json', 'citibike.json', 'ferry.json', 'stats.json', 'district-shapes.json', 'board-shapes.json'):
        shutil.copy(f'{CIVIC}/{n}', f'{out}/data/{n}')
    open(f'{out}/app.css', 'w').write(CSS); open(f'{out}/app.js', 'w').write(JS)

def build(out, app_title, cb6_app):
    global OUT
    OUT = out
    if os.path.isdir(out): shutil.rmtree(out)
    os.makedirs(f'{out}/official'); os.makedirs(f'{out}/board')
    offs = [o for o in officials if (covers_cb6(o) if cb6_app else covers_bk(o))]
    # Every official linked from an overlap row needs a page too.
    extra = set()
    for o in offs:
        for d in o.get('dists', []):
            if d.get('slug') in by_slug: extra.add(d['slug'])
    offs = list({o['slug']: o for o in offs + [by_slug[s] for s in extra]}.values())
    copy_assets(out, offs)
    for o in offs: open(f'{out}/official/{o["slug"]}.html', 'w').write(official_page(o, '../', app_title))
    cds = ['306'] if cb6_app else [f'3{n:02d}' for n in range(1, 19)]
    for cd in cds: open(f'{out}/board/{cd}.html', 'w').write(board_page(cd, '../', app_title, cb6_app))
    open(f'{out}/directory.html', 'w').write(directory_page('', app_title, cb6_app))
    if cb6_app: open(f'{out}/orgs.html', 'w').write(orgs_page('', app_title))
    open(f'{out}/index.html', 'w').write(cb6_shell() if cb6_app else bk_shell())
    print(out, 'officials', len(offs), 'boards', len(cds))

if __name__ == '__main__':
    build(f'{SITE}/cb6app10226', 'BKCB6', True)
    build(f'{SITE}/bkcball18', 'BKCB', False)
