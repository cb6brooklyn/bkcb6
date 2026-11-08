#!/usr/bin/env python3
"""Profile pages for every NYC Parks property in CB6, at /park/<slug>.html (the same addresses the site already used).

Each page puts together, for one park:
  - NYC Parks' own page and History page (scripts/parks_policy/park_profiles_src.py, written from them in plain language)
  - the Parks Properties record, inspections, amenities, courts and fields and capital projects (parks-policy/cb6.json)
  - the hours and subjects of the signs posted in it (parks-policy/signs.json, NYC Parks sign inventory)
  - garden hours from GreenThumb (park_profiles_src.GT)
  - everything New Yorkers for Parks has published about it (park_profiles_src.NY4P, NY4P_LIST)

The four smallest pieces (Todd Triangle, Cough Triangle and the two unnamed lots Parks calls only "Park") share one page,
/park/cb6-small-spaces.html; their old addresses forward there. The second halves of DiMattina Playground and St. Mary's
Park (two Parks properties each, one park on the ground) forward to the main page.
"""
import collections, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import park_profiles_src as S

E = html.escape
J = lambda p: json.load(open(os.path.join(ROOT, p), encoding='utf-8'))
D = J('parks-policy/cb6.json')
SIGNS = J('parks-policy/signs.json')['signs']
NY = J('parks-policy/ny4p.json')
PINS = J('park/pins/pins.json') if os.path.exists(os.path.join(ROOT, 'park/pins/pins.json')) else {}
PRULES = J('scripts/parks_policy/park_rules.json')
PROF = {p['name']: p for p in J('app/data/civic/orgs/orgs-profiles.json')['profiles'] if p['slug'].startswith('place-')}
CAP = {c['id']: c for c in D['cap']}
PK = {p['id']: p for p in D['parks']}
WIN = D['win']

# one page per park on the ground
GROUPS = {'B223': ['B223A', 'B223B'], 'B118': ['B118B', 'B118A']}
SMALL = ['B126A', 'B210C', 'B610', 'B607']
SLUG = {'B126': 'red-hook-recreation-area', 'B077': 'coffey-park', 'B050': 'van-voorhees-playground', 'B418': 'valentino-pier',
        'B111': 'washington-park-b111', 'B145': 'thomas-greene-playground', 'B019': 'carroll-park', 'B210H': 'harold-ickes-playground',
        'B003': 'bartel-pritchard-square', 'B111A': 'washington-skate-park', 'B223': 'dimattina-playground', 'B230': 'nicholas-naquan-heyward-jr-park',
        'B320': 'park-slope-playground', 'B361': 'boerum-park', 'B326': 'cobble-hill-park', 'B095': 'ennis-playground', 'B390': 'mother-cabrini-park',
        'B210F': 'admiral-triangle', 'B118': 'st-mary-s-park', 'B410': 'the-backyard', 'B399': 'gardens-of-union', 'B409': 'the-amazing-garden',
        'B411': 'summit-street-community-garden', 'B559': 'south-brooklyn-children-s-garden', 'B408': 'human-compass-garden', 'B570': 'dolly-s-park',
        'B560': 'pirate-s-cove-garden'}
FORWARD = {'dimattina-playground-b223b': 'dimattina-playground', 'st-mary-s-park-b118a': 'st-mary-s-park',
           'todd-triangle': 'cb6-small-spaces#B126A', 'cough-triangle': 'cb6-small-spaces#B210C', 'park-b607': 'cb6-small-spaces#B607'}
SMALL_SLUG = 'cb6-small-spaces'
NO_PAGE = {'B607'}  # nycgovparks.org/parks/B607 returned 404 on 2026-11-07
NAME = {'B223': 'DiMattina Playground', 'B118': "St. Mary's Park", 'B111': 'Washington Park', 'B399': 'Gardens of Union'}
TYPE = {'Garden': 'Community garden', 'Playground': 'Playground', 'Jointly Operated Playground': 'Playground shared with a school',
        'Triangle/Plaza': 'Plaza or triangle', 'Neighborhood Park': 'Neighborhood park', 'Community Park': 'Community park',
        'Recreational Field/Courts': 'Fields and courts', 'Undeveloped': 'Undeveloped park land'}
SPORT_ORDER = ['Basketball', 'Handball', 'Tennis', 'Bocce', 'Volleyball', 'Soccer', 'Football', 'Baseball', 'Softball', 'Running track', 'Multi-purpose']
AMEN = [('play', 'playground', 'playgrounds'), ('spray', 'spray shower', 'spray showers'), ('restrooms', 'restroom building', 'restroom buildings'),
        ('fountains', 'drinking fountain', 'drinking fountains'), ('pools', 'pool', 'pools'), ('dogs', 'dog run', 'dog runs'),
        ('skate', 'skate park', 'skate parks'), ('monuments', 'monument', 'monuments')]
PH = {'proposed': 'Proposed', 'design': 'In design', 'design-procurement': 'In design', 'procurement': 'In procurement', 'construction': 'Under construction', 'completed': 'Done'}
SGL = {'dogs': 'dog rules', 'play': 'playground rules', 'fields': 'field, court and track rules and hours', 'restrooms': 'restrooms', 'gardens': 'community garden', 'pools': 'pool', 'skate': 'skate park', 'name': 'park name', 'other': 'other signs'}
DAYS = {'Mon': 'Monday', 'Tue': 'Tuesday', 'Wed': 'Wednesday', 'Thu': 'Thursday', 'Fri': 'Friday', 'Sat': 'Saturday', 'Sun': 'Sunday'}
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
dl = lambda d: f"{MONTHS[int(d[5:7]) - 1]} {int(d[8:10])}, {d[:4]}"
num = lambda n, a, b: f"{n} {a if n == 1 else b}"

def head(title, desc, slug):
    url = f'https://bkcb6.app/park/{slug}.html'
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta name="apple-itunes-app" content="app-id=6813967208"><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} &mdash; bkcb6.app</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="Brooklyn Community Board 6"><meta property="og:type" content="website">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://bkcb6.app/og-image.png">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://bkcb6.app/og-image.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/place-profile.css?v=2">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://cdn.apple-mapkit.com/mk/5.x.x/mapkit.js"></script><script src="/assets/mapkit-leaflet.js"></script>
<style>
.psn{{display:inline-flex;flex-direction:column;align-items:flex-start;background:#1D3425;border-radius:4px;margin:10px 0 4px;color:#fff;min-width:150px;max-width:260px}}
.psn i{{display:block;padding:9px 12px 7px}}.psn svg{{width:44px;height:44px;display:block}}
.psn b{{display:block;align-self:stretch;border-top:1px solid rgba(255,255,255,.8);padding:6px 12px 8px;font:800 15px 'DM Sans',sans-serif;letter-spacing:.02em;line-height:1.15}}
.prl{{background:#1D3425;color:#fff;border-radius:6px;padding:14px 16px;font-size:.88rem;line-height:1.4}}.prl b{{display:block;color:#fff;font-weight:800;margin-top:8px}}.prl b:first-child{{margin-top:0}}.prl p{{margin:3px 0;color:#fff}}.prl ul{{margin:3px 0 0;padding-left:18px}}
.prp{{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px;padding-top:10px;border-top:1px solid rgba(255,255,255,.7)}}.prp svg{{width:44px;height:44px}}
.hl{{margin:0;padding-left:18px}}.hl li{{margin:4px 0;line-height:1.5}}
.rc{{border-left:3px solid #2e7d32;padding:2px 0 2px 10px;margin:10px 0}}.rc b{{display:block}}.rc a{{font-size:.8rem}}
.ins{{font-size:.9rem;margin:6px 0;line-height:1.45}}.ins.u b{{color:#c62828}}
.sm{{border-top:1px solid var(--border,#e2e2e2);padding-top:14px;margin-top:14px}}.sm:first-child{{border:0;margin:0;padding:0}}
.sm h3{{margin:0 0 4px;font-size:1.05rem}}
{RULES_CSS}{BANNER_CSS}</style>
</head><body><script src="/assets/site-bar.js?v=1" defer></script><a id="asb" href="https://apps.apple.com/us/app/bkcb6/id6813967208" target="_blank" rel="noopener" style="display:block;background:#0d1b4b;text-align:center;padding:8px 0;line-height:0;text-decoration:none"><img src="/appstore-badge.png" alt="Download BKCB6 on the App Store" width="121" height="40" style="height:40px;width:auto;border:0;display:inline-block"></a><script>(function(){{try{{var a=document.getElementById("asb"),q=/[?&]app=1\\b/.test(location.search);if(q)sessionStorage.setItem("bkapp","1");if(location.protocol==="bkcb:"||q||sessionStorage.getItem("bkapp")==="1"||/^bkcb:/.test(document.referrer)){{a.style.display="none"}}}}catch(e){{}}}})();</script>
<div class="pwrap">
'''

LEAF = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parks_logo_leaf100.txt')).read().strip()  # NYC Parks leaf, traced from a Parks sign
LOGO = f'<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="47.1" fill="none" stroke="#fff" stroke-width="5.8"/><path fill="#fff" d="{LEAF}"/></svg>'
BANNER_PICS = ['litter', 'smoking', 'alcohol', 'poop']
BANNER_CSS = """.pbn{background:#1D3425;color:#fff;border-radius:8px;overflow:hidden;font-family:'DM Sans',sans-serif;margin:10px 0 6px;max-width:640px}
.pbn-top{display:flex;align-items:center;gap:14px;padding:12px 16px;border-bottom:1.5px solid rgba(255,255,255,.85)}
.pbn-logo svg{width:58px;height:58px;display:block}
.pbn-name{font-weight:800;font-size:26px;line-height:1.05;letter-spacing:.01em;text-transform:uppercase}
.pbn-bot{display:flex;align-items:center;justify-content:space-between;gap:10px 14px;padding:9px 16px 10px;flex-wrap:wrap}
.pbn-hrs b{display:block;font-size:11px;font-weight:800;letter-spacing:.04em}.pbn-hrs span{display:block;font-weight:800;font-size:17px;line-height:1.15}
.pbn-pics{display:flex;gap:7px}.pbn-pics svg{width:34px;height:34px;display:block}
@media(max-width:420px){.pbn-name{font-size:21px}.pbn-logo svg{width:48px;height:48px}.pbn-pics svg{width:30px;height:30px}}
"""

def park_hours(pid):
    hs = sorted({x['hours'] for x in signs_for(pid) if x.get('hours') and (x.get('what') or '').startswith('Park ')})
    return hs[0] if hs else ''

def banner(name, pid=None, hours=None):
    if hours is None: hours = park_hours(pid) if pid else ''
    T = {x['id']: x for x in PRULES['tiles']}
    pics = ''.join(f'<svg viewBox="0 0 40 40" role="img" aria-label="{E(T[k]["l"])}"><title>{E(T[k]["l"])}</title>{T[k]["pic"]}</svg>' for k in BANNER_PICS)
    hrs = (f'<div class="pbn-hrs"><b>OPERATING HOURS</b><span>{E(hours.replace(" to ", "–"))}</span></div>' if hours else '<div class="pbn-hrs"><b>NYC PARKS</b></div>')
    return f'<div class="pbn"><div class="pbn-top"><div class="pbn-logo">{LOGO}</div><div class="pbn-name">{E(name)}</div></div><div class="pbn-bot">{hrs}<div class="pbn-pics">{pics}</div></div></div>'

def sign(name):
    w = name.upper().split()
    return (f'<div class="psn" aria-hidden="true"><i>{LOGO}</i><b>{E(" ".join(w))}</b></div>')

def sec(title, body, id_=''):
    return f'  <div class="sec"{f" id={chr(34)}{id_}{chr(34)}" if id_ else ""}><h2>{title}</h2><div class="bio">{body}</div></div>\n'

def kv(rows):
    return '<ul class="kv">' + ''.join(f'<li><span class="k">{E(k)}</span><span class="v">{v}</span></li>' for k, v in rows if v) + '</ul>'

def ul(xs): return '<ul class="hl">' + ''.join(f'<li>{E(x)}</li>' for x in xs) + '</ul>'

def parts(pid): return [PK[i] for i in GROUPS.get(pid, [pid])]

def signs_for(pid):
    ids = set(GROUPS.get(pid, [pid]))
    return [s for s in SIGNS if s.get('pid') in ids]

def hood(name):
    p = PROF.get(name)
    if p and ' · ' in p['seat']: return p['seat'].split(' · ', 1)[1]
    return ''

def facts(pid, ps):
    p0 = ps[0]
    acres = sum(p['acres'] for p in ps)
    rows = [('Where', E(p0['loc'] or '')), ('Address', E(p0['addr'].title() if p0.get('addr') and p0['addr'].isupper() else (p0.get('addr') or ''))),
            ('Size', f"{acres:,.2f} acres" + (f" ({round(sum(p['acres'] * p['inCB6'] for p in ps), 2)} acres of it in CB6)" if any(p['inCB6'] < .95 for p in ps) else '')),
            ('Type', E(TYPE.get(p0['type'], p0['type']))), ('Neighborhood', E(hood(PK[ps[0]['id']]['n']) or hood(NAME.get(pid, '')))),
            ('A park since', E(p0['acq']) if p0.get('acq') and p0['acq'] > '1800' else ''),
            ('Parks ID', E(', '.join(p['id'] for p in ps)))]
    return rows

def hours(pid):
    out = []
    if pid in S.GT:
        g = S.GT[pid]
        out.append(('Garden hours', '<br>'.join(f"{DAYS[d]}: {E(h)}" for d, h in g[3]) + '<br><span class="raw">Open hours as listed by GreenThumb.</span>'))
    hs = collections.defaultdict(set)
    for s in signs_for(pid):
        if s.get('hours'): hs[s['hours'].replace(' to ', ' to ')].add(s['what'])
    if hs:
        out.append(('Posted hours', '<br>'.join(f"{E(h)} <span class=\"raw\">(on the {E(', '.join(sorted(w.lower() for w in ws)))})</span>" for h, ws in sorted(hs.items()))))
    return out

def whats_here(pid, ps, src):
    am = collections.Counter(); sp = collections.Counter()
    for p in ps:
        am.update(p['amen']); sp.update(p['sports'])
    bits = [num(am[k], a, b) for k, a, b in AMEN if am.get(k)]
    courts = [num(sp[k], k.lower() + (' court' if k in ('Basketball', 'Handball', 'Tennis', 'Bocce', 'Volleyball') else ' field' if k not in ('Running track', 'Multi-purpose') else ''),
                  k.lower() + (' courts' if k in ('Basketball', 'Handball', 'Tennis', 'Bocce', 'Volleyball') else ' fields' if k not in ('Running track', 'Multi-purpose') else 's'))
              for k in SPORT_ORDER if sp.get(k)]
    courts = [c.replace('multi-purpose', 'multi-purpose field').replace('running track', 'running track') for c in courts]
    body = ''
    if src.get('facilities'): body += f'<p><b>NYC Parks lists:</b> {E(", ".join(src["facilities"]).lower().capitalize())}.</p>'
    if bits or courts: body += f'<p><b>In Parks\' facility records:</b> {E(", ".join(bits + courts))}.</p>'
    if pid in S.GT_IN:
        g = S.GT_IN[pid]
        body += f'<p><b>Community garden inside:</b> {E(g[0])}, {E(g[1])}' + (f" (open {E('; '.join(DAYS[d] + ' ' + h for d, h in g[2]))}, per GreenThumb)" if g[2] else '') + '.</p>'
    if src.get('highlights'): body += f'<p><b>Parks highlights:</b> {E(", ".join(src["highlights"]))}.</p>'
    return body

def inspections(ps):
    rows = sorted([dict(r, park=p['n']) for p in ps for r in p['insp']['rows']], key=lambda r: r['d'], reverse=True)
    if not rows: return ''
    n = len(rows); ok = sum(r['o'] == 'A' for r in rows); cl = sum(r['c'] == 'A' for r in rows)
    body = (f'<p>Parks inspectors rated it <b>{n}</b> time{"s" if n > 1 else ""} from {dl(WIN[0])} to {dl(WIN[1])}: acceptable overall '
            f'{ok} of {n} times, clean {cl} of {n} times.</p>')
    for r in rows:
        body += (f'<div class="ins{" u" if r["o"] == "U" else ""}"><b>{dl(r["d"])}:</b> {"acceptable" if r["o"] == "A" else "unacceptable"} overall, '
                 f'{"clean" if r["c"] == "A" else "not clean"}{". Rated unacceptable: " + E(", ".join(r["bad"]).lower()) if r["bad"] and r["o"] == "U" else ""}.</div>')
    return body + '<p class="subnote">From the Parks Inspection Program (NYC Open Data). An inspection is unacceptable overall when a feature fails or several are rated poorly.</p>'

def capital(ps):
    ids = [i for p in ps for i in p['cap']]
    cs = [CAP[i] for i in dict.fromkeys(ids) if i in CAP]
    if not cs: return ''
    cs.sort(key=lambda c: (c['ph'] == 'completed', c['t']))
    return ''.join(f'<div class="ins"><b>{E(PH.get(c["ph"], c["ph"]))}:</b> {E(c["t"])}{" &middot; " + E(c["fund"]) if c.get("fund") else ""}'
                   f'{"<br><span class=raw>" + E(c["s"]) + "</span>" if c.get("s") else ""}</div>' for c in cs) + \
        '<p class="subnote">From NYC Parks\' Capital Project Tracker. Citywide projects that include this park are listed too.</p>'

def signs_sec(pid, slug):
    ss = signs_for(pid)
    if not ss: return ''
    c = collections.Counter(SGL.get(s['cat'], 'other signs') for s in ss)
    return (f'<p>{len(ss)} Parks Department sign{"s" if len(ss) > 1 else ""} posted here: ' + E('; '.join(f'{k} ({v})' for k, v in c.most_common())) + '.</p>'
            f'<div class="chips"><a class="chip" href="/parks-policy/#sign-{ss[0]["id"]}">See the signs on the map</a></div>')

def ny4p(pid):
    body = ''
    for t, u, s in S.NY4P.get(pid, []):
        body += f'<div class="rc"><b>{E(t)}</b>{E(s)}<br><a href="{u}" target="_blank" rel="noopener">Read the report (PDF) &#8599;</a></div>'
    if pid in S.NY4P_LIST:
        body += (f'<p>Listed{" as &ldquo;" + E(S.NY4P_LIST[pid]) + "&rdquo;" if S.NY4P_LIST[pid] != NAME.get(pid, PK.get(pid, {}).get("n")) else ""} among the parks of Community District 6 in NY4P\'s {NY["year"]} Open Space Profile, '
                 f'which measures the district\'s park land per person, walking access, tree canopy and more. '
                 f'<a href="/parks-policy/#ny4p-sec">See the district\'s numbers</a> &middot; <a href="{NY["pdf"].replace("{CODE}", "BK6")}" target="_blank" rel="noopener">profile PDF &#8599;</a></p>')
    if not S.NY4P.get(pid):
        body += '<p class="subnote">New Yorkers for Parks has not graded this park in any of its report cards (2003 to 2016).</p>'
    return body

def chips(pid, ps, slug):
    p0 = ps[0]
    c = [f'<a class="chip hot" href="/parks-policy/#park-{p0["id"]}">See it on the CB6 parks map</a>']
    if pid not in S.GT:
        c.append(f'<a class="chip" href="https://www.nycgovparks.org/parks/{p0["id"]}" target="_blank" rel="noopener">NYC Parks page &#8599;</a>')
        if S.P.get(pid, {}).get('history'):
            c.append(f'<a class="chip" href="https://www.nycgovparks.org/parks/{p0["id"]}/history" target="_blank" rel="noopener">History on NYC Parks &#8599;</a>')
        c.append(f'<a class="chip" href="https://www.nycgovparks.org/parks/{p0["id"]}/events" target="_blank" rel="noopener">Events here &#8599;</a>')
    else:
        c.append('<a class="chip" href="https://greenthumb.nycgovparks.org/" target="_blank" rel="noopener">GreenThumb &#8599;</a>')
    c.append('<a class="chip" href="/parks-policy/">Parks in CB6</a>')
    return '<div class="chips">' + ''.join(c) + '</div>'

ICO = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ico.json')))
AMK = {'play': ('slide', '#e65100', 'Playground'), 'spray': ('shower', '#00838f', 'Spray shower'), 'pools': ('pool', '#1565c0', 'Pool'),
       'skate': ('skate', '#6a1b9a', 'Skatepark'), 'dogs': ('dog', '#795548', 'Dog run')}
SPK = {'Basketball': ('basketball', '#ef6c00'), 'Handball': ('handball', '#5d4037'), 'Tennis': ('tennis', '#9e9d24'), 'Soccer': ('soccer', '#2e7d32'),
       'Baseball': ('baseball', '#c62828'), 'Softball': ('baseball', '#ad1457'), 'Football': ('football', '#4e342e'), 'Volleyball': ('volleyball', '#f9a825'),
       'Running track': ('track', '#1565c0'), 'Bocce': ('bocce', '#6d4c41'), 'Pickleball': ('pickle', '#558b2f'), 'Cricket': ('cricket', '#33691e')}

def roundel(g, c):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><circle cx="20" cy="20" r="19" fill="{c}" stroke="#fff" stroke-width="1.5"/>'
            f'<circle cx="20" cy="20" r="15.2" fill="none" stroke="#fff" stroke-width="2"/><g transform="translate(10.4 10.4) scale(.8)"><path fill="#fff" d="{ICO.get(g, ICO["track"])}"/></g></svg>')

def acts(pid):
    ids = set(GROUPS.get(pid, [pid]))
    out = {}
    for k, L in D['pins'].items():
        for x in L:
            if x[-1] not in ids: continue
            if k == 'athletic':
                g, c = SPK.get(x[3], ('track', '#546e7a')); lab = x[3]
            elif k in AMK:
                g, c, lab = AMK[k]
            else: continue
            key = (lab, round(x[0], 4), round(x[1], 4))
            if key in out: out[key]['n'] += 1
            else: out[key] = {'lat': x[0], 'lon': x[1], 'g': g, 'c': c, 'l': lab, 'n': 1}
    return list(out.values())

def acts_script(pid):
    A = acts(pid)
    if not A: return ''
    icons = {}
    for a in A:
        icons.setdefault(a['g'] + a['c'], roundel(a['g'], a['c']))
    p0 = PK[GROUPS.get(pid, [pid])[0]]
    import math
    near = [a for a in A if math.hypot((a['lat'] - p0['lat']) * 111000, (a['lon'] - p0['lon']) * 84000) < 30]
    pts = []
    for a in A:
        dx, dy = 0, 0
        if a in near:
            k = near.index(a); dx = round((k - (len(near) - 1) / 2) * 24); dy = 46
        pts.append([a['lat'], a['lon'], a['g'] + a['c'], a['l'] + (f' ({a["n"]})' if a['n'] > 1 else ''), dx, dy])
    return ('<script>(function(){var I=' + json.dumps(icons) + ',P=' + json.dumps(pts) + ';'
            'function go(el){var m=el._pmap&&el._pmap.map;if(!m||!window.L)return;if(!m.getPane("acts")){m.createPane("acts");m.getPane("acts").style.zIndex=430}var M=[];P.forEach(function(p){var mk=L.marker([p[0],p[1]],{pane:"acts",icon:L.divIcon({className:"pk-act",iconSize:[20,20],iconAnchor:[10-p[4],10-p[5]],html:I[p[2]].replace("<svg ","<svg width=\\"20\\" height=\\"20\\" style=\\"display:block;filter:drop-shadow(0 1px 2px rgba(0,0,0,.35))\\" ")}),title:p[3],zIndexOffset:-1100});mk.bindTooltip(p[3],{direction:"top",offset:[0,-10]});mk.addTo(m);M.push(mk)});(function(){for(var k in m._layers){var x=m._layers[k];var ic=x&&x.options&&x.options.icon;if(ic&&ic.options&&String(ic.options.html||"").search(/park-pin|\\/park\\/pins\\//)>=0){m.removeLayer(x);x.addTo(m)}}})()}'
            'document.addEventListener("profile-map-ready",function(e){var el=e.target;if(el&&el.id==="map-' + (GROUPS.get(pid, [pid])[0]) + '")go(el)});'
            '})();</script>\n')

def money(n): return f'${n:,}'

def tile(x, compact=False):
    pic = f'<span class="rpic"><svg viewBox="0 0 40 40" aria-hidden="true">{x["pic"]}</svg></span>'
    if compact:
        return f'<a class="rc" href="/park/rules.html#r-{x["id"]}">{pic}<span>{E(x["l"])}</span></a>'
    u = PRULES['urls'][x['s']]
    return (f'<div class="rti" id="r-{x["id"]}">{pic}<div class="rtx"><b>{E(x["l"])}</b><p>{E(x["t"])}</p><div class="rmeta">'
            + ('<span class="rsign">On the entrance sign</span>' if x.get('sign') else '') + f'<a href="{u}" target="_blank" rel="noopener">{E(x["c"])}</a></div></div></div>')

def rules_html(compact=False):
    if compact:
        return '<div class="rcg">' + ''.join(tile(x, True) for x in PRULES['tiles']) + '</div>'
    out = ''
    for g, gl in PRULES['groups']:
        ts = [x for x in PRULES['tiles'] if x['g'] == g]
        out += f'<div class="rgrp"><h3>{E(gl)}</h3><div class="{"rcg" if compact else "rgrid"}">' + ''.join(tile(x, compact) for x in ts) + '</div></div>'
    return out

RULES_CSS_RAW = """.rgrp h3{{font:500 .63rem 'DM Mono',monospace;text-transform:uppercase;letter-spacing:.11em;color:#6b7280;margin:14px 0 6px}}.rgrp:first-child h3{{margin-top:0}}
.rgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:8px}}
.rti{{display:flex;gap:10px;align-items:flex-start;border:1.5px solid #e6e1d8;border-radius:10px;padding:10px;background:#fff}}
.rpic{{flex:none;width:42px;height:42px;border-radius:50%;background:#1D3425;display:flex}}.rpic svg{{width:42px;height:42px}}
.rtx b{{display:block;font-size:.95rem;color:#0d1b4b;line-height:1.2}}.rtx p{{margin:3px 0 0;font-size:.84rem;line-height:1.4;color:#333}}
.rmeta{{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:5px;font-size:.74rem}}.rmeta a{{color:#5b6675}}
.rcg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:4px 12px}}.bio a.rc,.rc{{display:flex;align-items:center;gap:7px;text-decoration:none;color:#0d1b4b;font-weight:700;font-size:.8rem;line-height:1.15;border:0;padding:2px 0;margin:0;background:none}}.rc .rpic,.rc .rpic svg{{width:30px;height:30px}}
.rgrp h3{{margin:10px 0 5px}}
.rsign{{background:#e8f0ea;color:#1D3425;border-radius:6px;padding:1px 6px;font-weight:700}}
.rmore{{display:block;font-size:.74rem;color:#6b7280;margin-top:3px}}
.rhere{{background:#1D3425;color:#fff;border-radius:8px;padding:9px 12px;margin-bottom:10px;font-size:.88rem}}.rhere b{{color:#fff}}.rhere p{{margin:3px 0;color:#fff}}
"""

RULES_CSS = RULES_CSS_RAW.replace("{{", "{").replace("}}", "}")

def here_sec(pid):
    ss = signs_for(pid)
    hrs = sorted({x['hours'] for x in ss if x.get('hours') and (x.get('what') or '').startswith('Park ')})
    ws = {x['what'] for x in ss}
    dog = ('Dogs may be off leash here before 9 a.m. and after 9 p.m. (Parks lists it as an off-leash area).' if any('Off-Leash OK' in w for w in ws) else
           'This park has a dog run; outside it, dogs must be leashed.' if any(w.startswith('Dog Run') or w.startswith('Park with Dog Run') for w in ws) else
           'No off-leash hours here: dogs must be leashed at all times.' if any('No Off' in w for w in ws) else '')
    h = (f'Open {E(hrs[0])}, as posted on the entrance sign.' if hrs else 'Open 6 a.m. to 1 a.m. unless other hours are posted at the park (the Parks rules default).')
    return f'<div class="rhere"><b>At this park</b><p>{h}</p>' + (f'<p>{dog}</p>' if dog else '') + '</div>'

def rules_sec(pid):
    body = here_sec(pid) + rules_html(compact=True) + ('<div class="chips" style="margin-top:12px"><a class="chip hot" href="/park/rules.html">Every rule, explained</a></div>'
            '<p class="subnote">From the Parks Department rules (Title 56 of the Rules of the City of New York). Tap a rule to read it.</p>')
    return sec('Park rules', body, 'rules')

def rules_page():
    title = 'NYC park rules'
    desc = 'Every rule on an NYC Parks entrance sign, plus the other common ones, in plain words with the rule it comes from.'
    h = head(title, desc, 'rules')
    h += ('  <div class="phead">\n    <div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="/parks-policy/" style="color:inherit">Parks in CB6</a></div>\n'
          f'    {banner("Park rules", hours="")}\n    <h1>{E(title)}</h1>\n    <div class="pseat">What the entrance signs say, and what else the rules say</div>\n  </div>\n')
    h += sec('Share this', '<p>Tap a rule to get a link straight to it, or share the whole page.</p><div class="chips"><button class="chip hot" id="shareAll" type="button">Share these rules</button>'
             '<button class="chip" type="button" onclick="print()">Print</button></div>')
    h += sec('The rules', rules_html())
    h += sec('Sources', f'<p class="subnote">Read {PRULES["src"]["read"]} from <a href="{PRULES["src"]["rules"]}" target="_blank" rel="noopener">NYC Parks Rules &amp; Regulations</a> '
             f'(Title 56 of the Rules of the City of New York) and <a href="{PRULES["urls"]["dogs"]}" target="_blank" rel="noopener">Dogs in NYC Parks</a>. '
             'Some parks post different hours or have their own rules; the signs at the park govern there.</p>')
    h += foot().replace('</div>\n</body>', '</div>\n<script>document.querySelectorAll(".rti").forEach(t=>{t.style.cursor="pointer";t.onclick=e=>{if(e.target.closest("a"))return;const u=location.origin+location.pathname+"#"+t.id;history.replaceState(null,"","#"+t.id);(navigator.share?navigator.share({title:t.querySelector("b").textContent+": NYC park rules",url:u}):navigator.clipboard.writeText(u).then(()=>{t.style.outline="2px solid #1D3425";setTimeout(()=>t.style.outline="",900)})).catch(()=>{})}});'
                                                  'document.getElementById("shareAll").onclick=()=>{const u=location.origin+location.pathname;(navigator.share?navigator.share({title:"NYC park rules",url:u}):navigator.clipboard.writeText(u).then(()=>alert("Link copied"))).catch(()=>{})};</script>\n</body>', 1)
    return h

def page(pid):
    ps = parts(pid); p0 = ps[0]; src = S.P.get(pid, {})
    slug = SLUG[pid]
    name = NAME.get(pid) or p0['n']
    ty = TYPE.get(p0['type'], p0['type']); nb = hood(p0['n'])
    acres = sum(p['acres'] for p in ps)
    desc = f"{name}: a {ty.lower()} in {nb + ', ' if nb else ''}Brooklyn Community Board 6. {acres:,.2f} acres. History, hours, what's there, inspections, projects and what New Yorkers for Parks has found."
    h = head(name, desc, slug)
    h += ('  <div class="phead">\n    <div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="/parks-policy/" style="color:inherit">Parks in CB6</a></div>\n'
          f'    {banner(name, pid)}\n    <h1>{E(name)}</h1>\n    <div class="pseat">{E(ty)}{" &middot; " + E(nb) if nb else ""} &middot; {acres:,.2f} acres</div>\n  </div>\n')
    if src.get('about'): h += sec('What it is', ''.join(f'<p>{E(x)}</p>' for x in src['about']))
    h += sec('Details', kv(facts(pid, ps) + hours(pid)) + chips(pid, ps, slug))
    h += mapsec(p0, name, acres, pid=pid)
    w = whats_here(pid, ps, src)
    if w: h += sec("What's here", w)
    if src.get('history'): h += sec('History', ''.join(f'<p>{E(x)}</p>' for x in src['history']) + f'<p class="subnote">From NYC Parks\' history of the park (its Historical Signs Project), in our words.</p>')
    i = inspections(ps)
    if i: h += sec('Inspections', i)
    c = capital(ps)
    if c: h += sec('Capital projects', c)
    h += rules_sec(pid)
    s = signs_sec(pid, slug)
    if s: h += sec('Signs', s)
    h += sec('New Yorkers for Parks', ny4p(pid), 'ny4p')
    h += foot(pid in S.GT).replace('<script src="/assets/profile-map.js', acts_script(pid) + '<script src="/assets/profile-map.js', 1)
    return slug, h

def mapsec(p, name, acres, sub=False, pid=None):
    pin = PINS.get(pid or p['id'])
    z = 16 if acres > 5 else 18 if acres < .3 else 17
    m = ('<details class="mapwrap" open><summary>Map of the park<span class="msub">zoning, boundary, overlaps, land use</span><span class="marr2">&#9660;</span></summary>'
         f'<div class="mapinner"><div class="mapttl">{E(p["loc"] or name)} <span>the park, its block and the zoning around it</span></div>'
         '<div class="msearch"><input type="search" placeholder="Search an address to drop a pin" autocomplete="off"><button type="button">Find</button><button type="button" class="mreset" data-map-reset>Reset</button></div>'
         f'<div class="pmap" id="map-{p["id"]}" data-profile-map data-chamber="cb" data-district="306" data-start-zoning="1" data-point-lat="{p["lat"]}" data-point-lng="{p["lon"]}" data-point-zoom="{z}" '
         + (f'data-point-icon="{pin["pin"]}" data-point-icon-w="{pin["w"]}" data-point-icon-h="{pin["h"]}" data-point-icon-px="80" data-point-icon-plain="#1D3425"></div>' if pin else
            f'data-point-label="{E(name)}" data-point-icon="/park/park-pin.svg" data-point-icon-w="200" data-point-icon-h="200"></div>')
         + '<div class="mstat" data-map-status></div><button type="button" class="mtoggle" aria-expanded="false" data-map-toggle-btn><span style="flex:1;text-align:left">Add to the map</span><span class="marr">&#9660;</span></button>'
         '<div class="mtools" data-map-toggles hidden></div><div class="mhint">Tap the map anywhere to drop a pin and open that lot.</div></div></details>')
    if pin:
        m += ('<script>document.addEventListener("profile-map-ready",function(e){if(e.target&&e.target.id==="map-' + p['id'] + '"){var mm=e.target._pmap.map;'
              'var dn=0;[600,1500,3000].forEach(function(t){setTimeout(function(){if(dn)return;try{var c0=mm.getCenter();mm.panBy([0,-70],{animate:false});var c1=mm.getCenter();if(c1&&c0&&c1.lat!==c0.lat)dn=1}catch(x){}},t)})}});</script>')
    return m if sub else f'  <div class="sec"><h2>Where it is</h2>\n    {m}\n  </div>\n'

def foot(garden=False):
    return ('  <div class="pfoot">Sources: NYC Parks\' page and history for each park (nycgovparks.org); NYC Parks Properties, Parks Inspection Program, '
            'facilities and Capital Project Tracker data and the Parks sign inventory (NYC Open Data)' + ('; GreenThumb Garden Info (NYC Open Data)' if garden else '') +
            '; New Yorkers for Parks report cards and Open Space Profile (ny4p.org).<br>\n'
            '  <a href="/parks-policy/">Parks in CB6</a> &middot; <a href="/park/cb6-small-spaces.html">Small park spaces in CB6</a> &middot; <a href="/">bkcb6.app</a></div>\n</div>\n<script src="/assets/profile-map.js?v=20261026lbl"></script>\n</body></html>\n')

def small_page():
    name = 'Small park spaces in CB6'
    desc = 'The smallest pieces of NYC Parks land in Brooklyn Community Board 6: triangles, plantings and lots next to streets and highways.'
    h = head(name, desc, SMALL_SLUG)
    h += ('  <div class="phead">\n    <div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="/parks-policy/" style="color:inherit">Parks in CB6</a></div>\n'
          f'    <h1>{E(name)}</h1>\n    <div class="pseat">{len(SMALL)} properties &middot; {sum(PK[i]["acres"] for i in SMALL):,.2f} acres together</div>\n  </div>\n')
    h += sec('What these are', '<p>The Parks Department counts every piece of land it holds as a park, including slivers left over where streets meet or highways were built. '
             'These four are in CB6. Each is a few thousand square feet or less of planting, paving or empty lot, with no playground, courts or fields: '
             'not what most people picture when they hear &ldquo;park.&rdquo; They still count toward the district\'s park acreage.</p>'
             '<p>For scale: an acre is 43,560 square feet. The smallest here, 0.03 acres, is about 1,300 square feet.</p>')
    body = ''
    for i in SMALL:
        p = PK[i]; src = S.P.get(i, {})
        nm = p['n'] if p['n'] != 'Park' else f'Unnamed ({p["loc"] or i})'
        body += (f'<div class="sm" id="{i}">{banner(p["n"] if p["n"] != "Park" else "Park", i)}<h3>{E(nm)}</h3>' + kv([('Where', E(p['loc'] or '')), ('Size', f'{p["acres"]} acres, about {round(p["acres"] * 43560, -1):,.0f} square feet'),
                 ('Type', E(TYPE.get(p['type'], p['type']))), ('Parks ID', E(i)), ('A park since', E(p['acq']) if p.get('acq') and p['acq'] > '1800' else '')]) +
                 mapsec(p, nm, p['acres'], True, pid=i) +
                 ''.join(f'<p>{E(x)}</p>' for x in src.get('about', []) + src.get('history', [])) +
                 (f'<p><b>New Yorkers for Parks:</b> listed as &ldquo;{E(S.NY4P_LIST[i])}&rdquo; among the district\'s parks in its {NY["year"]} Open Space Profile.</p>' if i in S.NY4P_LIST else '') +
                 f'<div class="chips"><a class="chip" href="/parks-policy/#park-{i}">On the map</a>' + (f'<a class="chip" href="https://www.nycgovparks.org/parks/{i}" target="_blank" rel="noopener">NYC Parks page &#8599;</a>' if i not in NO_PAGE else '') + '</div></div>')
    h += sec('The spaces', body)
    h += foot()
    return h

def redirect(to, title):
    u = '/park/' + (to.replace('#', '.html#') if '#' in to else to + '.html')
    return ('<!DOCTYPE html>\n<html lang="en"><head><meta charset="UTF-8"><title>%s | bkcb6.app</title>\n'
            '<link rel="canonical" href="https://bkcb6.app%s">\n<meta http-equiv="refresh" content="0; url=%s">\n'
            "<script>location.replace('%s');</script>\n</head><body><a href=\"%s\">%s</a></body></html>\n") % (E(title), u.split('#')[0], u, u, u, E(title))

if __name__ == '__main__':
    out = os.path.join(ROOT, 'park')
    made = {}
    for pid in SLUG:
        slug, h = page(pid)
        assert '{' not in re.sub(r'<style>.*?</style>|<script>.*?</script>', '', h, flags=re.S), slug
        open(os.path.join(out, slug + '.html'), 'w').write(h); made[pid] = slug
    open(os.path.join(out, SMALL_SLUG + '.html'), 'w').write(small_page())
    open(os.path.join(out, 'rules.html'), 'w').write(rules_page())
    for a, b in FORWARD.items():
        open(os.path.join(out, a + '.html'), 'w').write(redirect(b, 'Small park spaces in CB6' if 'small' in b else b.replace('-', ' ').title()))
    # map: Parks ID -> profile page, for the CB6 parks map
    idx = {}
    for pid, slug in made.items():
        for i in GROUPS.get(pid, [pid]): idx[i] = '/park/%s.html' % slug
    for i in SMALL: idx[i] = '/park/%s.html#%s' % (SMALL_SLUG, i)
    json.dump(idx, open(os.path.join(ROOT, 'parks-policy/profiles.json'), 'w'), indent=0)
    print(len(made), 'profiles,', len(SMALL), 'small spaces,', len(FORWARD), 'forwards')
