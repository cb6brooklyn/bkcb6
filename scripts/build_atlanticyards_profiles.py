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
<link rel="stylesheet" href="/atlanticyards/profile.css?v=2">
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
<script src="/atlanticyards/profile.js?v=2"></script>
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


# ---- zoning and land use, from PLUTO, like the address card ----
PL = {(int(r['block']), int(r['lot'])): r for r in json.load(open(os.path.join(ROOT, 'atlanticyards/pluto.json')))}
LU = {'1':'One and two family buildings','2':'Multi-family walk-up buildings','3':'Multi-family elevator buildings','4':'Mixed residential and commercial buildings','5':'Commercial and office buildings','6':'Industrial and manufacturing','7':'Transportation and utility','8':'Public facilities and institutions','9':'Open space and outdoor recreation','10':'Parking facilities','11':'Vacant land'}
ZK = {'R':'residence district','C':'commercial district','M':'manufacturing district'}
ZD = {'M1-1':'light manufacturing district','C6-2':'general central commercial district','C4-4A':'general commercial district','R7A':'residence district','R6B':'residence district'}
SP = {'DB':'Special Downtown Brooklyn District'}
CM = {'35':('Crystal Hudson','/cmhudson/'),'39':('Shahana Hanif','/cmhanif/')}
FIRE = {'L':'Ladder','E':'Engine'}
def num(v):
    try: return float(v)
    except: return 0.0
def zoning_rows(keys, built_gsf=None, gsf_src=None, plain=False):
    rs = [PL[k] for k in keys if k in PL]
    zs = []
    for r in rs:
        for f in ('zonedist1','zonedist2','zonedist3','zonedist4'):
            z = r.get(f)
            if z and z not in zs: zs.append(z)
    ov = []
    for r in rs:
        for f in ('overlay1','overlay2'):
            o = r.get(f)
            if o and o not in ov: ov.append(o)
    sp = sorted({SP.get(r.get(f), r.get(f)) for r in rs for f in ('spdist1','spdist2','spdist3') if r.get(f)})
    lu = []
    for r in rs:
        l = LU.get(str(int(r['landuse']))) if r.get('landuse') else None
        if l and l not in lu: lu.append(l)
    lot = sum(num(r.get('lotarea')) for r in rs)
    bld = sum(num(r.get('bldgarea')) for r in rs)
    split = any(r.get('splitzone') in (True, 'true', 'True') for r in rs)
    rows = []
    if zs:
        rows.append(('Zoning', '; '.join(f'{z}, a {ZD.get(z, ZK.get(z[0], "district"))}' for z in zs) + (' (the lot is split between districts)' if split and len(zs) > 1 else '')))
    if ov: rows.append(('Commercial overlay', ', '.join(ov)))
    if sp: rows.append(('Special district', ', '.join(sp)))
    if zs:
        r0 = [r for r in rs if r.get('zonedist1')][0]
        rf, cf, ff = num(r0.get('residfar')), num(r0.get('commfar')), num(r0.get('facilfar'))
        rows.append(('What city zoning allows', (f'Housing up to {rf:g} times the lot area' if rf else 'No housing as of right') + (f'; commercial up to {cf:g}' if cf else '; no commercial') + (f'; community facilities up to {ff:g}' if ff else '')))
    if lu: rows.append(('Land use', '; '.join(lu)))
    if lot: rows.append(('Lot area', f'{fmt(round(lot))} square feet'))
    if bld:
        rows.append(('Building area', f'{fmt(round(bld))} square feet'))
        rows.append(('Built', f'{bld/lot:.1f} times the lot area'))
    yb = sorted({r['yearbuilt'] for r in rs if r.get('yearbuilt') and r['yearbuilt'] != '0'})
    if yb and bld: rows.append(('Year built, tax records', ', '.join(yb)))
    us = sum(num(r.get('unitsres')) for r in rs); ut = sum(num(r.get('unitstotal')) for r in rs)
    if us: rows.append(('Units', f'{fmt(round(us))} residential, {fmt(round(ut))} in all'))
    # Atlantic Yards: what the state plan allows over city zoning
    if zs:
        r0 = [r for r in rs if r.get('zonedist1')][0]
        rf = num(r0.get('residfar'))
        g = built_gsf or bld
        if g and lot and not plain:
            far = g / lot
            src = f' (<a href="{gsf_src}" target="_blank" rel="noopener">proposed size</a>)' if gsf_src else ''
            txt = f'{"Proposed" if built_gsf else "Built"} at {far:.1f} times the lot area{src}, ' + (f'{far/rf:.1f} times the housing city zoning would allow here' if rf else 'on land where city zoning allows no housing') + f'. The state&rsquo;s <a href="{MOU}" target="_blank" rel="noopener">Atlantic Yards project plan overrides city zoning</a>.'
        else:
            txt = f'The state&rsquo;s <a href="{MOU}" target="_blank" rel="noopener">Atlantic Yards project plan overrides city zoning</a> on this site.'
        rows.append(('Atlantic Yards', txt))
    # districts
    c = rs[0].get('council'); 
    if c:
        nm = CM.get(c)
        rows.append(('City Council', f'District {c}' + (f', <a href="{nm[1]}">{nm[0]}</a>' if nm else '')))
    if rs[0].get('policeprct'): rows.append(('Police precinct', f'<a href="/precinct/{rs[0]["policeprct"]}/">{rs[0]["policeprct"]}th Precinct</a>'))
    if rs[0].get('schooldist'): rows.append(('School district', f'<a href="/eduhub-csd-{rs[0]["schooldist"]}.html">District {rs[0]["schooldist"]}</a>'))
    fc = rs[0].get('firecomp')
    if fc: rows.append(('Fire company', f'{FIRE.get(fc[0], "")} {fc[1:]}'.strip()))
    if rs[0].get('zipcode'): rows.append(('ZIP code', rs[0]['zipcode']))
    return rows
def ztable(rows):
    return '<section class="sec"><h2>Zoning and land use</h2></section><div class="ftab"><table>' + ''.join(f'<tr><td>{a}</td><td>{b}</td></tr>' for a, b in rows) + '</table></div>'
LOTS = {'B2':[(1118,2)],'B3':[(1118,7501)],'B4':[(1118,7502)],'B15':[(1128,7505)],'B11':[(1129,7501)],'B14':[(1129,7502)],'B12 and B13':[(1129,7503)],
        'Arena':[(1118,1)],'B1':[(1118,1)],'Site 5':[(927,1),(927,16)],
        'B5':[(1120,1),(1120,19),(1120,35)],'B6':[(1120,1),(1120,19),(1120,35)],'B7':[(1120,1),(1120,19),(1120,35)],
        'B8':[(1121,1),(1121,42),(1121,47)],'B9':[(1121,1),(1121,42),(1121,47)],'B10':[(1121,1),(1121,42),(1121,47)]}
BLOCK = {1118:'the arena block, bounded by Flatbush Avenue, Atlantic Avenue, 6th Avenue and Dean Street',1128:'the block between Pacific Street and Dean Street from 6th Avenue to Carlton Avenue',1129:'the block between Pacific Street and Dean Street from Carlton Avenue to Vanderbilt Avenue'}
DIR = []

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
    blk = LOTS[pid][0][0]
    descp = f'<p>{esc(title)} is parcel {esc(pid)} of Atlantic Yards, on {BLOCK[blk]}, in {esc(p["cd"])}: a {p["fl"]}-floor building of {fmt(p["u"])} ' + ('condominiums, none of them income-restricted' if not p['a'] else f'apartments, {fmt(p["a"])} of them affordable') + f', completed in {p["yr"]}.</p>'
    body = '<section class="sec"><h2>The building</h2></section><div class="pts">' + descp + (x['extra'] or '') + (f'<p>{esc(p["note"])}</p>' if p.get('note') and pid not in ('B2',) else '') + f'</div><div class="ftab"><table>{facts}</table></div>'
    body += ztable(zoning_rows(LOTS[pid]))
    if inc:
        body += f'<section class="sec"><h2>Who the affordable apartments are for</h2><div class="lede">By household income, as counted in <a href="{HPD}" target="_blank" rel="noopener">HPD&rsquo;s production data</a>.{(" " + x["hpdnote"]) if x["hpdnote"] else ""}</div></section><div class="bars">{inc}</div>'
        body += f'<section class="sec"><h2>Their sizes</h2></section><div class="bars">{br}</div>'
    DIR.append(dict(id=pid, slug=x['slug'], t=title, k='built', st='Built '+p['yr'], cd=p['cd'], d=descp, z=zoning_rows(LOTS[pid])))
    desc = f'{title}, parcel {pid} of Atlantic Yards: {fmt(p["u"])} apartments, {fmt(p["a"])} affordable, {p["fl"]} floors, completed {p["yr"]}, in {p["cd"]}.'
    sub = f'Parcel {esc(pid)} &middot; {esc(p["cd"])} &middot; built'
    made.append((x['slug'], page(x['slug'], title, sub, kpis, body, 'built', pid, desc)))

# Barclays Center
arena = [f['properties'] for f in D['lots']['features'] if f['properties']['kind'] == 'arena'][0]
body = f'''<section class="sec"><h2>The arena</h2></section><div class="pts">
<p>Barclays Center opened on <a href="https://en.wikipedia.org/wiki/Pacific_Park,_Brooklyn" target="_blank" rel="noopener">September 21, 2012</a> with 18,000 seats, the home of the Brooklyn Nets, at Flatbush Avenue and Atlantic Avenue over the Atlantic Av-Barclays Ctr subway station and across Atlantic Avenue from the Long Island Rail Road&rsquo;s Atlantic Terminal. Ground was broken on March 11, 2010. Joseph Tsai completed his purchase of the Nets and the arena in September 2019.</p>
<p>The arena&rsquo;s tax lot is assigned to BKCB2, but 37.5% of it lies inside the BKCB6 line, the most of any part of the project. The plaza at its western tip is B1, approved for a tower that the July 2026 proposal does not include.</p></div>
<div class="ftab"><table><tr><td>Address</td><td>620 Atlantic Avenue</td></tr><tr><td>Community board</td><td>BKCB2, with 37.5% of the lot in BKCB6</td></tr><tr><td>Tax lot</td><td>Brooklyn block 1118, lot 1</td></tr><tr><td>Owner of record</td><td>Arena Nominee Sub B</td></tr></table></div>''' + ztable(zoning_rows(LOTS['Arena'], plain=True))
DIR.append(dict(id='Arena', slug='barclays-center', t='Barclays Center', k='arena', st='Opened 2012', cd='BKCB2 and BKCB6', d='<p>The 18,000-seat arena at Flatbush Avenue and Atlantic Avenue, opened September 21, 2012, over the Atlantic Av-Barclays Ctr subway station. 37.5% of its lot lies inside BKCB6.</p>', z=zoning_rows(LOTS['Arena'], plain=True)))
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
    S5 = (1450000, 'https://citylimits.org/in-atlantic-yards-reboot-new-developers-seek-more-subsidies-2382-more-apartments-but-only-366-more-affordable-ones/') if pid == 'Site 5' else (None, None)
    zr = zoning_rows(LOTS[pid], *S5, plain=(pid == 'B1'))
    if pid in ('B5','B6','B7'): zr.insert(0, ('Lots', 'All of Block 1120, the railyard between 6th Avenue and Carlton Avenue, shared by B5, B6 and B7'))
    if pid in ('B8','B9','B10'): zr.insert(0, ('Lots', 'All of Block 1121, the railyard between Carlton Avenue and Vanderbilt Avenue, shared by B8, B9 and B10'))
    if pid == 'B1': zr = [r for r in zr if r[0] not in ('Building area','Built','Year built, tax records','Units','Land use','Lot area')]
    if pid == 'B1': zr.insert(0, ('Lot', 'The western tip of the arena lot, Brooklyn block 1118, lot 1'))
    body += ztable(zr)
    DIR.append(dict(id=pid, slug=x['slug'], t=pid, k='p2', st='Phase II, unbuilt', cd='BKCB2', d=x['extra'], z=zr, h=(str(t['h'])+' ft') if t.get('u') else ('open space' if pid=='B8' else 'plaza')))
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

# ---- the directory ----
import re
def noa(h): return re.sub(r'</?a\b[^>]*>', '', h)
def dcard(e):
    z = {k: noa(v) for k, v in e['z']}
    chips = ''.join(f'<span><b>{k}</b> {z[k]}</span>' for k in ('Zoning','Special district','Land use','What city zoning allows','Atlantic Yards') if k in z)
    return f'<a class="dc {e["k"]}" href="/atlanticyards/{e["slug"]}/" data-app="1"><div class="dh"><span class="dt">{esc(e["t"])}</span><span class="ds">{esc(e["st"])} &middot; {esc(e["cd"])}{(" &middot; " + esc(e["h"])) if e.get("h") else ""}</span></div><div class="dd">{noa(e["d"])}</div><div class="dz">{chips}</div><div class="dg">Open the profile &rarr;</div></a>'
groups = [('Built', [e for e in DIR if e['k'] in ('built', 'arena')]), ('Phase II, unbuilt', [e for e in DIR if e['k'] == 'p2'])]
cards = ''.join(f'<section class="sec"><h2>{g}</h2><div class="lede">{len(es)} {"buildings" if g=="Built" else "sites"}</div></section><div class="dgrid">' + ''.join(dcard(e) for e in es) + '</div>' for g, es in groups)
dirhtml = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Atlantic Yards directory &mdash; bkcb6.app</title>
<meta name="description" content="Every building and site of Atlantic Yards: what it is, its zoning and land use, and what the state&rsquo;s project plan allows there, each with its own profile.">
<link rel="canonical" href="https://bkcb6.app/atlanticyards/directory/">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/atlanticyards/profile.css?v=2">
</head>
<body><script src="/assets/site-bar.js?v=1" defer></script><a id="asb" href="https://apps.apple.com/us/app/bkcb6/id6813967208" target="_blank" rel="noopener" style="display:block;background:#0d1b4b;text-align:center;padding:8px 0;line-height:0;text-decoration:none"><img src="/appstore-badge.png" alt="Download BKCB6 on the App Store" width="121" height="40" style="height:40px;width:auto;border:0;display:inline-block"></a><script>(function(){{try{{var a=document.getElementById("asb"),q=/[?&]app=1\\b/.test(location.search);if(q)sessionStorage.setItem("bkapp","1");if(location.protocol==="bkcb:"||q||sessionStorage.getItem("bkapp")==="1"||/^bkcb:/.test(document.referrer)){{a.style.display="none"}}}}catch(e){{}}}})();</script>
<div class="wrap">
<div class="top-bar"><div class="top-txt"><h1>Atlantic Yards directory</h1><p>Every building and site, its zoning and land use</p></div><a class="back-link" href="/atlanticyards/">&larr; Atlantic Yards</a></div>
{cards}
<div class="src"><b>Sources</b><a href="{PLUTO}" target="_blank" rel="noopener">NYC DCP, PLUTO 26v2</a> (zoning, land use, lot and building area); <a href="{HPD}" target="_blank" rel="noopener">NYC HPD, Affordable Housing Production by Building</a>; <a href="{MOU}" target="_blank" rel="noopener">Atlantic Yards Phase II Memorandum of Understanding, July 28, 2026</a>; <a href="{FLY}" target="_blank" rel="noopener">Empire State Development, Phase II, September 1, 2026</a></div>
</div>
<script>(function(){{try{{if(/[?&]app=1\\b/.test(location.search)||sessionStorage.getItem('bkapp')==='1')document.querySelectorAll('a[data-app]').forEach(function(a){{a.href+='?app=1'}})}}catch(e){{}}}})();</script>
</body>
</html>
'''
os.makedirs(os.path.join(ROOT, 'atlanticyards/directory'), exist_ok=True)
open(os.path.join(ROOT, 'atlanticyards/directory/index.html'), 'w').write(dirhtml)
print('directory', len(DIR))
# the same cards for the project page map
json.dump([{'id': e['id'], 'slug': e['slug'], 't': e['t'], 'k': e['k'], 'st': e['st'], 'cd': e['cd'], 'h': e.get('h', ''), 'd': e['d'], 'z': e['z']} for e in DIR],
          open(os.path.join(ROOT, 'atlanticyards/directory.json'), 'w'), separators=(',', ':'))
