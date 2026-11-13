#!/usr/bin/env python3
"""A simple profile for every State Senator and Assembly Member whose district is outside the city.

The city's members already have full profiles (/amsimon/, /sengounardes/). Everyone else in the Legislature gets
/<slug>/ with the district map (assets/state-district-map.js), the counties the district takes in, and the events
on the calendar that name them. The State Senate and Assembly pages list every member, linked to their profile.

Reads data/state-legislators.json (from the Senate's member directory and nyassembly.gov/mem) and the district
shapes in data/districts/senate-N.geojson and assembly-N.geojson (Census 2024 state legislative districts for the
ones outside the city). Writes the profiles, adds the members lists, and adds each profile to the profile index the
apps read. Idempotent.
"""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda p: json.load(open(os.path.join(ROOT, p), encoding='utf-8'))
E = html.escape
rows = J('data/state-legislators.json')
EV_JS = open(os.path.join(ROOT, 'scripts/oneprofile/ev_script.js'), encoding='utf-8').read()
EV_CSS = open(os.path.join(ROOT, 'scripts/oneprofile/ev.css'), encoding='utf-8').read()
LOGO = {'senate': '/assets/agency-logos/nys/new-york-state-senate.png', 'assembly': '/assets/agency-logos/nys/new-york-assembly.png'}
TITLE = {'senate': 'State Senator', 'assembly': 'Assembly Member'}
SEAT = {'senate': 'State Senate District', 'assembly': 'State Assembly District'}
BODY = {'senate': ('The New York State Senate', '/agencies/nys/new-york-state-senate/', 'https://www.nysenate.gov/senators-committees'),
        'assembly': ('The New York State Assembly', '/agencies/nys/new-york-assembly/', 'https://nyassembly.gov/mem/')}
ASB = ('<script src="/assets/site-bar.js?v=1" defer></script><a id="asb" href="https://apps.apple.com/us/app/bkcb6/id6813967208" target="_blank" rel="noopener" '
       'style="display:block;background:#0d1b4b;text-align:center;padding:8px 0;line-height:0;text-decoration:none"><img src="/appstore-badge.png" '
       'alt="Download BKCB6 on the App Store" width="121" height="40" style="height:40px;width:auto;border:0;display:inline-block"></a><script>(function(){try{var '
       'a=document.getElementById("asb"),q=/[?&]app=1\\b/.test(location.search);if(q)sessionStorage.setItem("bkapp","1");if(location.protocol==="bkcb:"||q||'
       'sessionStorage.getItem("bkapp")==="1"||/^bkcb:/.test(document.referrer)){a.style.display="none"}}catch(e){}})();</script>')


def andlist(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1]


def counties(r):
    full, part = r.get('counties_all', []), r.get('counties_part', [])
    bits = []
    if full: bits.append('all of ' + andlist(full) + (' County' if len(full) == 1 else ' counties'))
    if part: bits.append(('part of ' if len(part) == 1 else 'parts of ') + andlist(part) + (' County' if len(part) == 1 else ' counties'))
    return ' and '.join(bits)


def events(r):
    # the calendar's events that name this member, in the title or the description
    js = EV_JS.replace('__ORG__', json.dumps(r['slug'])).replace('__HREF__', json.dumps('/calendar.html')) \
        .replace('__NAME__', json.dumps('The CB6 calendar')).replace('__LOGO__', json.dumps(LOGO[r['chamber']]))
    js = js.replace('ALSO=[]', 'ALSO=' + json.dumps([r['name'].replace('Dr. ', '')]), 1)
    js = js.replace("return String(ev.label).toLowerCase()", "return (String(ev.label)+' '+String(ev.desc||'')).toLowerCase()", 1)
    return ('<!--oneprofile-->\n<style>' + EV_CSS + '</style>\n<div class="sec evsec"><h2>Coming up with ' + E(r['name']) + '</h2><div id="orgEvents"><div class="evcard">'
            '<div class="evline">Loading from the CB6 calendar…</div></div></div><div id="orgMore"></div></div>\n' + js + '\n<!--/oneprofile-->')


def page(r):
    ch, n, slug, name = r['chamber'], r['district'], r['slug'], r['name']
    title, seat = TITLE[ch], '%s %d' % (SEAT[ch], n)
    body_name, body_page, body_dir = BODY[ch]
    desc = '%s %s represents %s, which takes in %s.' % (title, name, seat, counties(r))
    site = r.get('site') or body_dir
    site_lbl = 'Official page' if r.get('site') else body_name.replace('The ', '') + ' members'
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta name="apple-itunes-app" content="app-id=6813967208"><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} {E(name)} &mdash; {seat} &mdash; bkcb6.app</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="https://bkcb6.app/{slug}">
<meta property="og:site_name" content="Brooklyn Community Board 6"><meta property="og:type" content="profile">
<meta property="og:title" content="{E(title)} {E(name)} &middot; {seat}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="https://bkcb6.app/{slug}">
<meta property="og:image" content="https://bkcb6.app{LOGO[ch]}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://cdn.apple-mapkit.com/mk/5.x.x/mapkit.js"></script><script src="/assets/mapkit-leaflet.js"></script>
<link rel="stylesheet" href="/assets/state-profile.css?v=20261112">
</head>
<body>{ASB}
<div class="pwrap">
<div class="phead"><span class="pmark"><img src="{LOGO[ch]}" alt="{E(body_name)}"></span><span>
<div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="{body_page}" style="color:inherit">{E(body_name)}</a></div>
<h1>{E(name)}</h1><div class="pseat">{E(title)} &middot; {seat}</div></span></div>
<div class="sec"><h2>In brief</h2><div class="bio"><p><b>{E(title)} {E(name)}</b> represents <b>{seat}</b>, which takes in {E(counties(r))}.</p>
<p>Members of the State {'Senate' if ch == 'senate' else 'Assembly'} serve two year terms.</p></div></div>
<div class="sec"><h2>The district</h2><div class="mapttl">NYS {'Senate' if ch == 'senate' else 'Assembly'} District {n} <span>{E(title)} {E(name.split()[-1] if not name.endswith(('Jr.', 'III')) else name)}</span></div>
<div class="msearch" data-state-search><input type="search" placeholder="Search an address to drop a pin" autocomplete="off"><button type="button">Find</button><button type="button" class="mreset" data-state-reset>Reset</button></div>
<div class="pmap" id="map" data-state-map data-chamber="{ch}" data-district="{n}"></div><div class="mstat" data-state-status></div>
<div class="mhint">Tap the map anywhere to drop a pin and see whether it is in the district.</div></div>
{events(r)}
<div class="sec"><h2>Go on</h2><div class="btns"><a class="btn hot" href="{E(site)}" target="_blank" rel="noopener">{site_lbl} &#8599;</a><a class="btn" href="{body_page}">{E(body_name)} &rarr;</a><a class="btn" href="/govhub.html">The Government Hub &rarr;</a></div></div>
<div class="pfoot">District boundary from the Census Bureau's 2024 state legislative districts. Member from {'the Senate member directory' if ch == 'senate' else 'nyassembly.gov'}.<br>
<a href="/govhub.html">The Government Hub</a> &middot; <a href="{body_page}">{E(body_name)}</a></div>
</div>
<script src="/assets/state-district-map.js?v=20261112"></script>
</body></html>
'''


def redirect(slug, title):
    return (f'<!DOCTYPE html>\n<html lang="en"><head><meta name="apple-itunes-app" content="app-id=6813967208"><meta charset="UTF-8">\n'
            f'<link rel="canonical" href="https://bkcb6.app/{slug}">\n<meta http-equiv="refresh" content="0; url=/{slug}/">\n'
            f'<title>{E(title)} &mdash; bkcb6.app</title>\n<script>location.replace(\'/{slug}/\');</script>\n</head><body></body></html>\n')


made = 0
for r in rows:
    if r.get('vacant') or r.get('existing'): continue
    os.makedirs(os.path.join(ROOT, r['slug']), exist_ok=True)
    open(os.path.join(ROOT, r['slug'], 'index.html'), 'w', encoding='utf-8').write(page(r))
    open(os.path.join(ROOT, r['slug'] + '.html'), 'w', encoding='utf-8').write(redirect(r['slug'], '%s %s' % (TITLE[r['chamber']], r['name'])))
    made += 1

# every member, by district, on the Senate's and the Assembly's own pages
for ch in ('senate', 'assembly'):
    p = os.path.join(ROOT, BODY[ch][1].strip('/'), 'index.html')
    s = open(p, encoding='utf-8').read()
    s = re.sub(r'<!--members-->.*?<!--/members-->', '', s, flags=re.S)
    li = []
    for r in sorted([x for x in rows if x['chamber'] == ch], key=lambda x: x['district']):
        if r.get('vacant'):
            li.append('<li><span class="mn">%d</span> Vacant</li>' % r['district'])
        else:
            li.append('<li><span class="mn">%d</span> <a href="/%s/">%s</a></li>' % (r['district'], r['slug'], E(r['name'])))
    who = 'senators' if ch == 'senate' else 'members'
    sec = ('<!--members--><style>.mlist{list-style:none;columns:2;column-gap:18px;margin-top:6px}.mlist li{font-size:.86rem;line-height:1.5;padding:3px 0;break-inside:avoid}'
           '.mlist .mn{display:inline-block;min-width:2.2em;font-family:"DM Mono",monospace;font-size:.72rem;color:#6b6760}.mlist a{color:#0d1b4b;font-weight:700;text-decoration:none}'
           '@media(max-width:560px){.mlist{columns:1}}</style><details class="sec"><summary><h2 style="display:inline">All %d %s, by district</h2></summary>'
           '<ul class="mlist">%s</ul></details><!--/members-->') % (len(li), who, ''.join(li))
    i = s.find('<div class="sec"><h2>Go on</h2>')
    if i < 0: i = s.rfind('</body>')
    s = s[:i] + sec + s[i:]
    open(p, 'w', encoding='utf-8').write(s)

# the apps open each new profile the way they open the precinct and school district pages
for p in ('data/profile-index.json', 'app/data/civic/profile-index.json'):
    idx = J(p)
    for r in rows:
        if r.get('vacant') or r.get('existing'): continue
        idx['pages']['/%s/' % r['slug']] = 'web:%s/index.html?app=1' % r['slug']
        if r.get('site'):
            idx['urls'].setdefault(re.sub(r'^https?://(www2?\.)?', '', r['site']).rstrip('/').lower(), '/%s/' % r['slug'])
    json.dump(idx, open(os.path.join(ROOT, p), 'w'), ensure_ascii=False, indent=0, sort_keys=True)
print('profiles:', made)
