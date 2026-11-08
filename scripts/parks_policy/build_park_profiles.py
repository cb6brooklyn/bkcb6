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
</style>
</head><body><script src="/assets/site-bar.js?v=1" defer></script><a id="asb" href="https://apps.apple.com/us/app/bkcb6/id6813967208" target="_blank" rel="noopener" style="display:block;background:#0d1b4b;text-align:center;padding:8px 0;line-height:0;text-decoration:none"><img src="/appstore-badge.png" alt="Download BKCB6 on the App Store" width="121" height="40" style="height:40px;width:auto;border:0;display:inline-block"></a><script>(function(){{try{{var a=document.getElementById("asb"),q=/[?&]app=1\\b/.test(location.search);if(q)sessionStorage.setItem("bkapp","1");if(location.protocol==="bkcb:"||q||sessionStorage.getItem("bkapp")==="1"||/^bkcb:/.test(document.referrer)){{a.style.display="none"}}}}catch(e){{}}}})();</script>
<div class="pwrap">
'''

LEAF = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'parks_logo_leaf100.txt')).read().strip()  # NYC Parks leaf, traced from a Parks sign
LOGO = f'<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="47.1" fill="none" stroke="#fff" stroke-width="5.8"/><path fill="#fff" d="{LEAF}"/></svg>'
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

def rules_sec(pid):
    ws = [x['what'] for x in signs_for(pid) if (x.get('what') or '').startswith('Park ')]
    if not ws: return ''
    R = PRULES['rules']; leash = any('No Off' in w for w in ws); offok = any('Off-Leash OK' in w for w in ws)
    b = ('<div class="prl"><b>WELCOME</b><p>' + E(' '.join(R['welcome'])) + '</p><b>RULES PROHIBIT:</b><ul>' + ''.join(f'<li>{E(x)}</li>' for x in R['prohibit']) + '</ul>'
         + ('<b>DOGS</b><ul>' + ''.join(f'<li>{E(x)}</li>' for x in R['dogs']) + '</ul>' if leash and not offok else '')
         + f'<p><b style="display:inline">{E(R["q"])}</b></p><div class="prp">' + ''.join(f'<svg viewBox="0 0 40 40" role="img" aria-label="{E(t)}"><title>{E(t)}</title>{PRULES["picto"][k]}</svg>' for k, t in R['picto']) + '</div></div>')
    note = ('These are the rules printed on NYC Parks\' park entrance signs (from the City Hall Park sign). The Parks sign inventory lists this park\'s entrance signs as: '
            + E('; '.join(sorted(set(w.lower() for w in ws)))) + '. The exact wording on them is not in the City\'s data and may differ.')
    return sec('Rules posted at the entrance', b + f'<p class="subnote">{note}</p>')

def page(pid):
    ps = parts(pid); p0 = ps[0]; src = S.P.get(pid, {})
    slug = SLUG[pid]
    name = NAME.get(pid) or p0['n']
    ty = TYPE.get(p0['type'], p0['type']); nb = hood(p0['n'])
    acres = sum(p['acres'] for p in ps)
    desc = f"{name}: a {ty.lower()} in {nb + ', ' if nb else ''}Brooklyn Community Board 6. {acres:,.2f} acres. History, hours, what's there, inspections, projects and what New Yorkers for Parks has found."
    h = head(name, desc, slug)
    h += ('  <div class="phead">\n    <div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="/parks-policy/" style="color:inherit">Parks in CB6</a></div>\n'
          f'    {sign(name)}\n    <h1>{E(name)}</h1>\n    <div class="pseat">{E(ty)}{" &middot; " + E(nb) if nb else ""} &middot; {acres:,.2f} acres</div>\n  </div>\n')
    if src.get('about'): h += sec('What it is', ''.join(f'<p>{E(x)}</p>' for x in src['about']))
    h += sec('Details', kv(facts(pid, ps) + hours(pid)) + chips(pid, ps, slug))
    h += mapsec(p0, name, acres)
    w = whats_here(pid, ps, src)
    if w: h += sec("What's here", w)
    if src.get('history'): h += sec('History', ''.join(f'<p>{E(x)}</p>' for x in src['history']) + f'<p class="subnote">From NYC Parks\' history of the park (its Historical Signs Project), in our words.</p>')
    i = inspections(ps)
    if i: h += sec('Inspections', i)
    c = capital(ps)
    if c: h += sec('Capital projects', c)
    r = rules_sec(pid)
    if r: h += r
    s = signs_sec(pid, slug)
    if s: h += sec('Signs', s)
    h += sec('New Yorkers for Parks', ny4p(pid), 'ny4p')
    h += foot(pid in S.GT)
    return slug, h

def mapsec(p, name, acres, sub=False):
    z = 16 if acres > 5 else 18 if acres < .3 else 17
    m = ('<details class="mapwrap" open><summary>Map of the park<span class="msub">zoning, boundary, overlaps, land use</span><span class="marr2">&#9660;</span></summary>'
         f'<div class="mapinner"><div class="mapttl">{E(p["loc"] or name)} <span>the park, its block and the zoning around it</span></div>'
         '<div class="msearch"><input type="search" placeholder="Search an address to drop a pin" autocomplete="off"><button type="button">Find</button><button type="button" class="mreset" data-map-reset>Reset</button></div>'
         f'<div class="pmap" id="map-{p["id"]}" data-profile-map data-chamber="cb" data-district="306" data-start-zoning="1" data-point-lat="{p["lat"]}" data-point-lng="{p["lon"]}" data-point-zoom="{z}" '
         f'data-point-label="{E(name)}" data-point-icon="/park/park-pin.svg" data-point-icon-w="200" data-point-icon-h="200"></div>'
         '<div class="mstat" data-map-status></div><button type="button" class="mtoggle" aria-expanded="false" data-map-toggle-btn><span style="flex:1;text-align:left">Add to the map</span><span class="marr">&#9660;</span></button>'
         '<div class="mtools" data-map-toggles hidden></div><div class="mhint">Tap the map anywhere to drop a pin and open that lot.</div></div></details>')
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
        body += (f'<div class="sm" id="{i}"><h3>{E(nm)}</h3>' + kv([('Where', E(p['loc'] or '')), ('Size', f'{p["acres"]} acres, about {round(p["acres"] * 43560, -1):,.0f} square feet'),
                 ('Type', E(TYPE.get(p['type'], p['type']))), ('Parks ID', E(i)), ('A park since', E(p['acq']) if p.get('acq') and p['acq'] > '1800' else '')]) +
                 mapsec(p, nm, p['acres'], True) +
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
    for a, b in FORWARD.items():
        open(os.path.join(out, a + '.html'), 'w').write(redirect(b, 'Small park spaces in CB6' if 'small' in b else b.replace('-', ' ').title()))
    # map: Parks ID -> profile page, for the CB6 parks map
    idx = {}
    for pid, slug in made.items():
        for i in GROUPS.get(pid, [pid]): idx[i] = '/park/%s.html' % slug
    for i in SMALL: idx[i] = '/park/%s.html#%s' % (SMALL_SLUG, i)
    json.dump(idx, open(os.path.join(ROOT, 'parks-policy/profiles.json'), 'w'), indent=0)
    print(len(made), 'profiles,', len(SMALL), 'small spaces,', len(FORWARD), 'forwards')
