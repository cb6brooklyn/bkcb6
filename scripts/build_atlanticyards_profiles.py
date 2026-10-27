#!/usr/bin/env python3
"""Atlantic Yards profile pages: one page per built building, Barclays Center
and every Phase II site, at /atlanticyards/<slug>/. Facts come from
atlanticyards/data.json (lots, Phase II program) plus the tables below
(HPD Affordable Housing Production by Building, PLUTO, the July 28, 2026
Phase II MOU). Rerun after changing data.json or this file."""
import json, os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, 'atlanticyards/data.json')))

HPD = 'https://data.cityofnewyork.us/Housing-Development/Affordable-Housing-Production-by-Building/hg8x-zxpr'
PLUTO = 'https://data.cityofnewyork.us/City-Government/Primary-Land-Use-Tax-Lot-Output-PLUTO-/64uk-42ks'
MOU = '/atlanticyards/phase2-mou-2026-07-28.pdf'
FLY = '/atlanticyards/phase2-flyer-2026-09-01.pdf'
ESD = 'https://esd.ny.gov/atlantic-yards-community-development-corporation-1'

# built buildings: HPD counts (income bands, sizes), PLUTO lot facts
BUILT = {
 'B2': dict(slug='461-dean-street', bbl='3011180002', owner='USPA 461 Dean, LLC',
   inc=[('Low income', 37), ('Moderate income', 73)], br=[('Studios', 45), ('1 bedroom', 50), ('2 bedrooms', 15)],
   hpdnote='181 apartments here are affordable; HPD&rsquo;s production data counts 110 of them, the ones under its own program.',
   extra='<p>The first apartment building of the project. Ground was broken on December 18, 2012, and it opened in November 2016 as a modular tower; the <a href="https://www.6sqft.com/lottery-launches-for-181-affordable-units-in-pacific-parks-modular-tower/" target="_blank" rel="noopener">housing lottery for its 181 affordable apartments</a> opened in May 2016, announced at the <a href="/minutes/2016-05-11-full-board.html">CB6 full board meeting of May 11, 2016</a>.</p>'),
 'B3': dict(slug='38-sixth-avenue', bbl='3011187501', owner='Atlantic Yards B2 Owner, LLC',
   inc=[('Very low income', 14), ('Low income', 77), ('Moderate income', 14), ('Middle income', 198)],
   br=[('Studios', 66), ('1 bedroom', 131), ('2 bedrooms', 90), ('3 bedrooms', 16)], hpdnote='', extra=''),
 'B4': dict(slug='18-sixth-avenue', bbl='3011187502', owner='18 Sixth Avenue Owner LLC',
   inc=[('Middle income', 258)], br=[('Studios', 79), ('1 bedroom', 134), ('2 bedrooms', 45)], hpdnote='', extra=''),
 'B15': dict(slug='662-pacific-street', bbl='3011287505', owner='662 Pacific Owner LLC',
   inc=[('Middle income', 94)], br=[('Studios', 24), ('1 bedroom', 48), ('2 bedrooms', 22)], hpdnote='', extra=''),
 'B11': dict(slug='550-vanderbilt-avenue', bbl='3011297501', owner='', inc=[], br=[], hpdnote='', extra=''),
 'B14': dict(slug='535-carlton-avenue', bbl='3011297502', owner='Pacific Park 535 Carlton, LLC',
   inc=[('Very low income', 15), ('Low income', 75), ('Moderate income', 26), ('Middle income', 181), ('Other', 1)],
   br=[('Studios', 66), ('1 bedroom', 129), ('2 bedrooms', 88), ('3 bedrooms', 14), ('Size not reported', 1)], hpdnote='', extra=''),
 'B12 and B13': dict(slug='595-615-dean-street', bbl='3011297503', owner='595 Dean LLC',
   inc=[('Middle income', 240)], br=[('Studios', 99), ('1 bedroom', 93), ('2 bedrooms', 48)],
   hpdnote='', extra='<p>Two towers on one tax lot. City records count the two together, so they share one profile.</p>'),
}
# Phase II: approved heights from the MOU where it gives them; AMI bands from the MOU housing table
P2 = {
 'Site 5': dict(slug='site-5', block='Site 5', approved='Approved at 250 feet and 439,050 square feet',
   bands=[(52, '40%'), (155, '60%'), (52, '80%'), (0, '100%'), (0, '120%')], due='Site 5 and the Block 1120 buildings are due by December 31, 2037.',
   extra='<p>Across Flatbush Avenue at 4th Avenue, the former P.C. Richard and Modell&rsquo;s site, on solid ground, so it can be built without a deck over the tracks. The proposal allows a hotel of up to about 92,000 square feet and about 73,000 square feet of retail here. The <a href="%s" target="_blank" rel="noopener">income-restricted apartments at Site 5 must open before its condominiums or a hotel</a>, and work on the Block 1120 deck must start before the condominiums or hotel open.</p>' % MOU),
 'B5': dict(slug='b5', block='Block 1120', approved='', bands=[(18, '40%'), (46, '60%'), (55, '80%'), (46, '100%'), (18, '120%')],
   due='The Block 1120 deck is due by December 31, 2032, and its buildings by December 31, 2037.',
   extra='<p>On the deck over the railyard between 6th Avenue and Carlton Avenue, at its western end. It cannot open before B6, and it cannot change hands until work on the deck starts. The <a href="%s" target="_blank" rel="noopener">proposal puts community space in B5</a>.</p>' % FLY),
 'B6': dict(slug='b6', block='Block 1120', approved='Approved at 219 feet', bands=[(74, '40%'), (98, '60%'), (74, '80%'), (0, '100%'), (0, '120%')],
   due='Block 1120 buildings are due by December 31, 2037.',
   extra='<p>Partly on land below Atlantic Avenue, so it can go first along with Site 5, before the deck. It would hold the <a href="%s" target="_blank" rel="noopener">intergenerational community center</a>, about 14,000 square feet. It must open before B5 and B7.</p>' % FLY),
 'B7': dict(slug='b7', block='Block 1120', approved='Approved at 460 feet', bands=[(13, '40%'), (35, '60%'), (35, '80%'), (35, '100%'), (57, '120%')],
   due='The Block 1120 deck is due by December 31, 2032, and its buildings by December 31, 2037.',
   extra='<p>On the deck over the railyard at its eastern end, by Carlton Avenue. The tallest building proposed on the railyard. It cannot open before B6, and it cannot change hands until work on the deck starts.</p>'),
 'B8': dict(slug='b8', block='Block 1121', approved='Approved as a tower', bands=[], due='The B8 open space must be finished before B9 opens.',
   extra='<p>The western end of the railyard block between Carlton Avenue and Vanderbilt Avenue. The <a href="%s" target="_blank" rel="noopener">July 2026 proposal</a> makes it open space instead of a building, part of more than five acres of new open space in Phase II. Work on the Block 1121 deck has to include the money for this open space before B9 or B10 can change hands.</p>' % MOU),
 'B9': dict(slug='b9', block='Block 1121', approved='', bands=[(12, '40%'), (31, '60%'), (31, '80%'), (31, '100%'), (51, '120%')],
   due='Block 1121 is due by December 31, 2040 with a funding agreement for its deck, and by December 31, 2042 without one.',
   extra='<p>On the deck over the railyard between Carlton Avenue and Vanderbilt Avenue. It cannot open until the B8 open space is finished, and no Block 1121 building can be leased for construction until Site 5 and every Block 1120 building has started.</p>'),
 'B10': dict(slug='b10', block='Block 1121', approved='', bands=[(23, '40%'), (56, '60%'), (68, '80%'), (56, '100%'), (23, '120%')],
   due='Block 1121 is due by December 31, 2040 with a funding agreement for its deck, and by December 31, 2042 without one.',
   extra='<p>The eastern end of the railyard, at Vanderbilt Avenue. The <a href="%s" target="_blank" rel="noopener">proposal puts community space in B10</a>. No Block 1121 building can be leased for construction until Site 5 and every Block 1120 building has started.</p>' % FLY),
 'B1': dict(slug='b1', block='Arena plaza', approved='Approved at 620 feet and 1,106,009 square feet, for commercial, office and hotel use', bands=[], due='',
   extra='<p>The plaza in front of Barclays Center at Flatbush Avenue and Atlantic Avenue, over the subway entrance. The approved plan has the project&rsquo;s tallest tower here. The <a href="%s" target="_blank" rel="noopener">July 2026 housing program</a> has no building on B1, and the new development team took over its development rights in October 2025.</p>' % MOU),
}

def esc(s): return html.escape(str(s), quote=True)
def fmt(n): return f'{n:,}'

def page(slug, title, sub, kpis, body, kind, target, desc):
    k = ''.join(f'<div class="kp"><div class="v">{v}</div><div class="k">{t}</div></div>' for v, t in kpis)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}, Atlantic Yards &mdash; bkcb6.app</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="https://bkcb6.app/atlanticyards/{slug}/">
<meta property="og:title" content="{esc(title)}, Atlantic Yards"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="https://bkcb6.app/atlanticyards/{slug}/">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<link rel="stylesheet" href="/atlanticyards/profile.css?v=1">
</head>
<body><script src="/assets/site-bar.js?v=1" defer></script><a id="asb" href="https://apps.apple.com/us/app/bkcb6/id6813967208" target="_blank" rel="noopener" style="display:block;background:#0d1b4b;text-align:center;padding:8px 0;line-height:0;text-decoration:none"><img src="/appstore-badge.png" alt="Download BKCB6 on the App Store" width="121" height="40" style="height:40px;width:auto;border:0;display:inline-block"></a><script>(function(){{try{{var a=document.getElementById("asb"),q=/[?&]app=1\\b/.test(location.search);if(q)sessionStorage.setItem("bkapp","1");if(location.protocol==="bkcb:"||q||sessionStorage.getItem("bkapp")==="1"||/^bkcb:/.test(document.referrer)){{a.style.display="none"}}}}catch(e){{}}}})();</script>
<div class="wrap">
<div class="top-bar"><div class="top-txt"><h1>{esc(title)}</h1><p>{sub}</p></div><a class="back-link" href="/atlanticyards/">&larr; Atlantic Yards</a></div>
<div class="finder"><div class="hm-card">
  <div class="key" id="key"></div>
  <div id="map" data-kind="{kind}" data-target="{esc(target)}"></div>
  <div class="hm-foot"><div class="pills">
    <button class="pill on" type="button" data-l="lirr" style="--c:#111"><i></i>LIRR</button>
    <button class="pill on" type="button" data-l="subway" style="--c:#EE352E"><i></i>Subway</button>
    <button class="pill" type="button" data-l="bus" style="--c:#0039a6"><i></i>Bus routes</button>
  </div></div>
</div></div>
<div class="kpis">{k}</div>
{body}
<div class="others"><div class="lbl">EVERY BUILDING AND SITE</div><div id="others" data-self="{slug}"></div></div>
<div class="src"><b>Sources</b>
<a href="{ESD}" target="_blank" rel="noopener">Empire State Development, Atlantic Yards Community Development Corporation</a><br>
<a href="{MOU}" target="_blank" rel="noopener">Atlantic Yards Phase II Memorandum of Understanding, July 28, 2026</a><br>
<a href="{FLY}" target="_blank" rel="noopener">Empire State Development, Atlantic Yards Redevelopment: Phase II, revised September 1, 2026</a><br>
<a href="{HPD}" target="_blank" rel="noopener">NYC HPD, Affordable Housing Production by Building</a><br>
<a href="{PLUTO}" target="_blank" rel="noopener">NYC DCP, PLUTO and MapPLUTO 26v2</a>
</div>
</div>
<script src="/atlanticyards/profile.js?v=1"></script>
</body>
</html>
'''

def bars(rows, total, unit='apartments'):
    if not rows: return ''
    mx = max(n for _, n in rows) or 1
    out = ''
    for lab, n in rows:
        out += f'<div class="br"><span class="bl">{lab}</span><span class="bt"><i style="width:{n*100/mx:.1f}%"></i></span><span class="bn">{fmt(n)}</span></div>'
    return out

made = []
lots = {f['properties'].get('id'): f['properties'] for f in D['lots']['features'] if f['properties']['kind'] == 'built'}
for pid, x in BUILT.items():
    p = lots[pid]
    title = p['addr']
    share = round(p['a'] * 100 / p['u'])
    kpis = [(fmt(p['u']), 'apartments'),
            ((fmt(p['a']) if p['a'] else 'none'), f'affordable, {share}% of the building' if p['a'] else 'affordable; all condominiums'),
            (str(p['fl']), 'floors'), (p['yr'], 'completed')]
    rows = [('Parcel', esc(pid)), ('Community board', esc(p['cd'])), ('Tax lot', f'Brooklyn block {x["bbl"][1:6].lstrip("0")}, lot {x["bbl"][6:].lstrip("0")}')]
    if x['owner']: rows.append(('Owner of record', esc(x['owner'])))
    facts = ''.join(f'<tr><td>{a}</td><td>{b}</td></tr>' for a, b in rows)
    inc = bars(x['inc'], p['a'])
    br = bars(x['br'], p['a'])
    body = '<section class="sec"><h2>The building</h2></section><div class="pts">' + (x['extra'] or '') + (f'<p>{esc(p["note"])}</p>' if p.get('note') and pid not in ('B2',) else '') + f'</div><div class="ftab"><table>{facts}</table></div>'
    if inc:
        body += f'<section class="sec"><h2>Who the affordable apartments are for</h2><div class="lede">By household income, as counted in <a href="{HPD}" target="_blank" rel="noopener">HPD&rsquo;s production data</a>.{(" " + x["hpdnote"]) if x["hpdnote"] else ""}</div></section><div class="bars">{inc}</div>'
        body += f'<section class="sec"><h2>Their sizes</h2></section><div class="bars">{br}</div>'
    desc = f'{title}, parcel {pid} of Atlantic Yards: {fmt(p["u"])} apartments, {fmt(p["a"])} affordable, {p["fl"]} floors, completed {p["yr"]}, in {p["cd"]}.'
    sub = f'Parcel {esc(pid)} &middot; {esc(p["cd"])} &middot; built'
    made.append((x['slug'], page(x['slug'], title, sub, kpis, body, 'built', pid, desc)))

# Barclays Center
arena = [f['properties'] for f in D['lots']['features'] if f['properties']['kind'] == 'arena'][0]
body = f'''<section class="sec"><h2>The arena</h2></section><div class="pts">
<p>Barclays Center opened on <a href="https://en.wikipedia.org/wiki/Pacific_Park,_Brooklyn" target="_blank" rel="noopener">September 21, 2012</a> with 18,000 seats, the home of the Brooklyn Nets, at Flatbush Avenue and Atlantic Avenue over the Atlantic Av-Barclays Ctr subway station and across Atlantic Avenue from the Long Island Rail Road&rsquo;s Atlantic Terminal. Ground was broken on March 11, 2010. Joseph Tsai completed his purchase of the Nets and the arena in September 2019.</p>
<p>The arena&rsquo;s tax lot is assigned to BKCB2, but 37.5% of it lies inside the BKCB6 line, the most of any part of the project. The plaza at its western tip is B1, approved for a tower that the July 2026 proposal does not include.</p></div>
<div class="ftab"><table><tr><td>Address</td><td>620 Atlantic Avenue</td></tr><tr><td>Community board</td><td>BKCB2, with 37.5% of the lot in BKCB6</td></tr><tr><td>Tax lot</td><td>Brooklyn block 1118, lot 1</td></tr><tr><td>Owner of record</td><td>Arena Nominee Sub B</td></tr></table></div>'''
made.append(('barclays-center', page('barclays-center', 'Barclays Center', 'The arena &middot; BKCB2 and BKCB6 &middot; built', [('18,000', 'seats'), ('2012', 'opened September 21'), ('37.5%', 'of the lot inside BKCB6')], body, 'arena', 'Arena', 'Barclays Center at Atlantic Yards: 18,000 seats, opened September 21, 2012, at Flatbush and Atlantic Avenues, partly in BKCB6.')))

# Phase II
p2 = {t['id']: t for t in D['phase2']}
for pid, x in P2.items():
    t = p2[pid]
    if t.get('u'):
        rent = t['u'] - t['c']
        kpis = [(f'{t["h"]} ft', 'proposed height'), (fmt(t['u']), 'apartments proposed'),
                (fmt(t['a']), f'income-restricted, {round(t["a"]*1000/rent)/10:g}% of the rentals'), ((fmt(t['c']) if t['c'] else 'none'), 'condominiums')]
        tbl = ''.join(f'<div class="br"><span class="bl">{b} of area median income</span><span class="bt"><i style="width:{n*100/max(m for m,_ in x["bands"]):.1f}%"></i></span><span class="bn">{fmt(n)}</span></div>' for n, b in x['bands'])
        body = f'''<section class="sec"><h2>What is proposed</h2></section><div class="pts">{x['extra']}<p>{fmt(rent)} rentals, {fmt(t['a'])} of them income-restricted at an average of {t['avg']} of area median income, and {fmt(t['c']) if t['c'] else 'no'} condominiums, from the <a href="{MOU}" target="_blank" rel="noopener">example housing program in the July 2026 memorandum</a>. {x['approved'] + '; proposed at ' + str(t['h']) + ' feet.' if x['approved'] else ''} {x['due']}</p></div>
<section class="sec"><h2>Income-restricted apartments, by rent level</h2></section><div class="bars">{tbl}</div>'''
        sub = f'{esc(x["block"])} &middot; BKCB2 &middot; Phase II, unbuilt'
        desc = f'{pid} at Atlantic Yards, proposed: {t["h"]} feet, {fmt(t["u"])} apartments, {fmt(t["a"])} income-restricted. Phase II, unbuilt, in BKCB2.'
    else:
        kpis = [(('Open space' if pid == 'B8' else 'Plaza'), 'in the July 2026 proposal'), ('none', 'apartments proposed')]
        body = f'<section class="sec"><h2>What is proposed</h2></section><div class="pts">{x["extra"]}<p>{x["approved"]}.{(" " + x["due"]) if x["due"] else ""}</p></div>'
        sub = f'{esc(x["block"])} &middot; BKCB2 &middot; Phase II, unbuilt'
        desc = f'{pid} at Atlantic Yards: {"open space instead of a tower" if pid == "B8" else "the arena plaza, no building proposed"} in the July 2026 proposal. In BKCB2.'
    made.append((x['slug'], page(x['slug'], pid, sub, kpis, body, 'p2', pid, desc)))

for slug, h in made:
    os.makedirs(os.path.join(ROOT, 'atlanticyards', slug), exist_ok=True)
    open(os.path.join(ROOT, 'atlanticyards', slug, 'index.html'), 'w').write(h)
# index of profiles for the project page and each profile's list
idx = []
for pid, x in BUILT.items(): idx.append({'id': pid, 'slug': x['slug'], 't': lots[pid]['addr'], 'k': 'built'})
idx.append({'id': 'Arena', 'slug': 'barclays-center', 't': 'Barclays Center', 'k': 'arena'})
for pid, x in P2.items(): idx.append({'id': pid, 'slug': x['slug'], 't': pid, 'k': 'p2'})
json.dump(idx, open(os.path.join(ROOT, 'atlanticyards/profiles.json'), 'w'), separators=(',', ':'))
print(len(made), 'profiles')
