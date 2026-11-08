#!/usr/bin/env python3
"""Directory profiles for CB6's NYPD precincts and sectors, school districts and schools, on the site and in the apps.

Boundaries: data/districts/{precinct,sector,school}-<id>.geojson (NYC Open Data Police Precincts, NYPD Sectors,
School Districts, downloaded 2026-11-08). CB6 is served by the 76th and 78th Precincts (the 72nd touches 0.4% of it),
sectors 76A-D and 78A-D, and School Districts 13 and 15 (17 touches 0.4%).

Site:
  /nypd-sector/<id>.html             a page per sector: its map, what's in it, its precinct
  /76th-precinct/, /78th-precinct/   a "Sectors" block (and current commanding officer and community council)
  /school-district-13/, -15/         a "Schools in CB6" block
  /school/<slug>.html                each CB6 school: a map block (school district boundary, the school pinned) and its
                                     district, precinct and sector; schools without a page get one
Apps (app/data/civic/orgs/orgs-profiles.json): a profile per sector and per school district; precincts and schools
linked to them; the business-directory duplicate of the 78th Precinct removed.
Blocks on existing pages sit between <!--cb6dir--> markers, so a rerun replaces them.
"""
import difflib, glob, html, json, os, re
from shapely.geometry import shape, Point

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
E = html.escape
PROF = 'app/data/civic/orgs/orgs-profiles.json'
D = json.load(open(PROF))
BY = {p['slug']: p for p in D['profiles']}
cb6 = shape(json.load(open('data/cb6_boundary.geojson'))['features'][0]['geometry'])
HOODS = {n: shape({'type': 'Polygon', 'coordinates': v}) for n, v in json.load(open('app/data/civic/hoods-cb6.json')).items()}
geo = lambda k: shape(json.load(open(f'data/districts/{k}.geojson'))['features'][0]['geometry']).buffer(0)
SECTORS = ['76A', '76B', '76C', '76D', '78A', '78B', '78C', '78D']
SECT = {s: geo('sector-' + s) for s in SECTORS}
SECT_MI = {s: json.load(open(f'data/districts/sector-{s}.geojson'))['features'][0]['properties']['sq_miles'] for s in SECTORS}
PCT = {'76': geo('precinct-76'), '78': geo('precinct-78')}
SD = {'13': geo('school-13'), '15': geo('school-15')}
ORD = {'76': '76th', '78': '78th'}

# Read from nyc.gov/site/nypd/bureaus/patrol/precincts/<n>th-precinct.page on 2026-11-08
NYPD = {
 '76': dict(co='Deputy Inspector Tai Yuen Lee', addr='191 Union Street, Brooklyn, NY 11231', phone='(718) 834-3211', ca='(718) 834-3207',
            council='President Jerry Armer. Meetings typically the first Wednesday of each month at 7:00 PM.',
            area='Carroll Gardens, Red Hook, Cobble Hill, parts of Gowanus, and the Columbia Street Waterfront District'),
 '78': dict(co='Deputy Inspector Billy J. Morales', addr='65 6th Avenue, Brooklyn, NY 11217', phone='(718) 636-6411', ca='(718) 636-6410',
            council='President Erika Clark. Meetings typically the last Tuesday of each month at 6:30 PM at 65 6th Avenue.',
            area='Park Slope, and Prospect Park'),
}
QTEAM = ('NYPD\'s Quality of Life Teams (Q-Teams) handle non-emergency quality-of-life complaints. To report one, call 311 or use the 311 app; '
         'to reach a Q-Team member, call or visit the precinct.')

def where(lat, lng):
    pt = Point(lng, lat)
    sd = next((k for k, g in SD.items() if g.buffer(0.0002).contains(pt)), '')
    pct = next((k for k, g in PCT.items() if g.buffer(0.0002).contains(pt)), '')
    sec = next((k for k, g in SECT.items() if g.buffer(0.0002).contains(pt)), '')
    return sd, pct, sec

def hoods_of(g):
    out = []
    for n, h in HOODS.items():
        a = g.intersection(h).area
        if a / g.area > 0.08: out.append((a, n))
    return [n for a, n in sorted(out, reverse=True)]

# ---------- page shell (the site's place-profile template) ----------
def head(title, desc, path, maps=True):
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta name="apple-itunes-app" content="app-id=6813967208"><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} &mdash; bkcb6.app</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="https://bkcb6.app{path}">
<meta property="og:site_name" content="Brooklyn Community Board 6"><meta property="og:type" content="website">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="https://bkcb6.app{path}"><meta property="og:image" content="https://bkcb6.app/og-image.png">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://bkcb6.app/og-image.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/place-profile.css?v=2">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://cdn.apple-mapkit.com/mk/5.x.x/mapkit.js"></script><script src="/assets/mapkit-leaflet.js"></script>
</head><body><script src="/assets/site-bar.js?v=1" defer></script><a id="asb" href="https://apps.apple.com/us/app/bkcb6/id6813967208" target="_blank" rel="noopener" style="display:block;background:#0d1b4b;text-align:center;padding:8px 0;line-height:0;text-decoration:none"><img src="/appstore-badge.png" alt="Download BKCB6 on the App Store" width="121" height="40" style="height:40px;width:auto;border:0;display:inline-block"></a><script>(function(){{try{{var a=document.getElementById("asb"),q=/[?&]app=1\\b/.test(location.search);if(q)sessionStorage.setItem("bkapp","1");if(location.protocol==="bkcb:"||q||sessionStorage.getItem("bkapp")==="1"||/^bkcb:/.test(document.referrer)){{a.style.display="none"}}}}catch(e){{}}}})();</script>
<div class="pwrap">
'''

def sec(t, body, id_=''):
    return f'  <div class="sec"{" id=" + chr(34) + id_ + chr(34) if id_ else ""}><h2>{t}</h2><div class="bio">{body}</div></div>\n'

def kv(rows):
    return '<ul class="kv">' + ''.join(f'<li><span class="k">{E(k)}</span><span class="v">{v}</span></li>' for k, v in rows if v) + '</ul>'

def mapblock(chamber, district, lat, lng, title, sub, icon='', zoom=16, fit=True, iw=200, ih=200):
    pt = (f'data-point-lat="{lat}" data-point-lng="{lng}" data-point-zoom="{zoom}" ' if lat else '') + (f'data-point-icon="{icon}" data-point-icon-w="{iw}" data-point-icon-h="{ih}" ' if icon else '')
    return ('<details class="mapwrap" open><summary>Map<span class="msub">boundary, overlaps, zoning, land use</span><span class="marr2">&#9660;</span></summary>'
            f'<div class="mapinner"><div class="mapttl">{E(title)} <span>{E(sub)}</span></div>'
            '<div class="msearch"><input type="search" placeholder="Search an address to drop a pin" autocomplete="off"><button type="button">Find</button><button type="button" class="mreset" data-map-reset>Reset</button></div>'
            f'<div class="pmap" data-profile-map data-chamber="{chamber}" data-district="{district}" {"data-fit-own=" + chr(34) + "1" + chr(34) + " " if fit else ""}{pt}></div>'
            '<div class="mstat" data-map-status></div><button type="button" class="mtoggle" aria-expanded="false" data-map-toggle-btn><span style="flex:1;text-align:left">Add to the map</span><span class="marr">&#9660;</span></button>'
            '<div class="mtools" data-map-toggles hidden></div><div class="mhint">Tap the map anywhere to drop a pin and open that lot.</div></div></details>')

FOOT = '''  <div class="pfoot">{src}<br>
  <a href="/publicsafety/">Public safety</a> &middot; <a href="/eduhub">Schools</a> &middot; <a href="/citywide-search.html">Search any address</a> &middot; <a href="/">bkcb6.app</a></div>
</div>
<script src="/assets/profile-map.js?v=20261108y"></script>
</body></html>
'''

# ---------- what's where ----------
SCHOOLS = [p for p in D['profiles'] if p.get('topic') == 'Schools']
PARKS = json.load(open('parks-policy/profiles.json'))
PK = {p['id']: p for p in json.load(open('parks-policy/cb6.json'))['parks']}

def school_page_index():
    pages = []
    for f in glob.glob('school/*.html'):
        s = open(f).read()
        h1 = re.search(r'<h1>([^<]*)', s); a = re.search(r'Address</span><span class="v">([^<]*)', s)
        dbn = re.search(r'DBN</span><span class="v">([^<]*)', s); cb = re.search(r'Community board</span><span class="v">([^<]*)', s)
        pages.append(dict(f=f, n=html.unescape(h1.group(1)) if h1 else '', a=a.group(1) if a else '', dbn=dbn.group(1) if dbn else '', cb=cb.group(1) if cb else ''))
    return pages

def na(s):
    s = re.sub(r'[^a-z0-9 ]', '', s.lower().split(',')[0].replace('street', 'st').replace('avenue', 'ave').replace('place', 'pl')).strip()
    return re.sub(r'(\d)(st|nd|rd|th)\b', r'\1', s)
def nn(s): return ' '.join(re.sub(r'\b0+(\d)', r'\1', re.sub(r'[^a-z0-9 ]', ' ', s.lower())).split())
def sim(a, b): return difflib.SequenceMatcher(None, nn(a), nn(b)).ratio()

def match_schools():
    pages = school_page_index(); out = {}
    for p in SCHOOLS:
        cand = [x for x in pages if x['a'] and na(x['a']) == na(p.get('addr') or '-')] or [x for x in pages if x['cb'] == 'Brooklyn Community Board 6']
        best = max(cand, key=lambda x: sim(x['n'], p['name'])) if cand else None
        out[p['slug']] = best if best and sim(best['n'], p['name']) >= 0.9 else None
    return out, pages

def slugify(s): return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s.lower())).strip('-')

def main():
    match, pages = match_schools()
    info = {}  # school slug -> dict(page, sd, pct, sec)
    for p in SCHOOLS:
        sd, pct, sc = where(p['lat'], p['lng'])
        pg = match[p['slug']]
        info[p['slug']] = dict(p=p, page='/' + pg['f'] if pg else f'/school/{slugify(p["name"])}.html', exists=bool(pg), sd=sd, pct=pct, sec=sc, dbn=pg['dbn'] if pg else '')
    # ---- school pages ----
    for s, x in info.items():
        p = x['p']
        block = school_block(x)
        if x['exists']: inject(x['page'][1:], block, maps=True)
        else: write_school_page(x, block)
    # ---- sector pages ----
    os.makedirs('nypd-sector', exist_ok=True)
    for s in SECTORS: open(f'nypd-sector/{s.lower()}.html', 'w').write(sector_page(s, info))
    # ---- precinct and district blocks ----
    for n in ('76', '78'): inject(f'{ORD[n]}-precinct/index.html', precinct_block(n, info), maps=False)
    for n in ('13', '15'): inject(f'school-district-{n}/index.html', district_block(n, info), maps=False)
    # ---- apps ----
    app(info)
    print(len(info), 'schools;', sum(not x['exists'] for x in info.values()), 'new school pages;', len(SECTORS), 'sectors')

def links_row(x):
    rows = []
    if x['sd']: rows.append(('School district', f'<a href="/school-district-{x["sd"]}/">District {x["sd"]}</a>' + (' &middot; <a href="/cec-district-15/">CEC 15</a>' if x['sd'] == '15' else '')))
    if x['pct']: rows.append(('Police precinct', f'<a href="/{ORD[x["pct"]]}-precinct/">{ORD[x["pct"]]} Precinct</a>'))
    if x['sec']: rows.append(('NYPD sector', f'<a href="/nypd-sector/{x["sec"].lower()}.html">Sector {x["sec"]}</a>'))
    return rows

def school_block(x):
    p = x['p']
    icon = f'/app/data/civic/orgs/logos/{p["logo"]}' if p.get('logo') and os.path.exists(f'app/data/civic/orgs/logos/{p["logo"]}') else ''
    m = mapblock('school', x['sd'] or '15', p['lat'], p['lng'], p.get('addr') or p['name'], f'the school and School District {x["sd"]}' if x['sd'] else 'the school', icon=icon, zoom=17, fit=False)
    return sec('Where it is', m) + sec('Its district, precinct and sector', kv(links_row(x)))

def inject(path, block, maps):
    s = open(path).read()
    s = re.sub(r'<!--cb6dir-->.*?<!--/cb6dir-->\n?', '', s, flags=re.S)
    block = '<!--cb6dir-->\n' + block + '<!--/cb6dir-->\n'
    i = s.find('  <div class="pfoot">')
    if i < 0: i = s.find('<div class="pfoot">')
    s = s[:i] + block + s[i:]
    if maps and 'mapkit-leaflet.js' not in s:
        s = s.replace('</head>', '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>\n<script src="https://cdn.apple-mapkit.com/mk/5.x.x/mapkit.js"></script><script src="/assets/mapkit-leaflet.js"></script>\n</head>', 1)
    if maps and 'profile-map.js' not in s:
        s = s.replace('</body>', '<script src="/assets/profile-map.js?v=20261108y"></script>\n</body>', 1)
    open(path, 'w').write(s)

def write_school_page(x, block):
    p = x['p']; title = p['name']
    rows = [(k, E(v)) for k, v in p['kv'] if k not in ('Source', 'Community board', 'Neighborhood')]
    rows = [('Address', E((p.get('addr') or '') + ', Brooklyn'))] + rows + [('Neighborhood', E(next((v for k, v in p['kv'] if k == 'Neighborhood'), ''))),
            ('Community board', '<a href="/cb-bk-6.html">Brooklyn Community Board 6</a>')]
    web = f'<div class="chips"><a class="chip" href="{E(p["weburl"])}" target="_blank" rel="noopener">School website &#8599;</a></div>' if p.get('weburl') else ''
    h = head(title, f'{title}, {p["seat"]}. Where it is, its school district, police precinct and sector.', x['page'])
    h += ('  <div class="phead">\n    <div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="/eduhub" style="color:inherit">Schools</a></div>\n'
          f'    <h1>{E(title)}</h1>\n    <div class="pseat">{E(p["seat"])}</div>\n  </div>\n')
    h += sec('Details', kv(rows) + web) + '<!--cb6dir-->\n' + block + '<!--/cb6dir-->\n'
    h += FOOT.format(src='From the NYC Facilities Database (Department of City Planning). District, precinct and sector from the NYC Open Data School Districts, Police Precincts and NYPD Sectors maps.')
    open(x['page'][1:], 'w').write(h)

def sector_page(s, info):
    n = s[:2]; g = SECT[s]; pr = NYPD[n]
    inside = g.intersection(cb6).area / g.area
    hs = hoods_of(g)
    parks = sorted({(PK[i]['n'] if i not in ('B223A', 'B223B', 'B118A', 'B118B') else {'B223': 'DiMattina Playground', 'B118': "St. Mary's Park"}[i[:4]], PARKS[i])
                    for i, pk in PK.items() if i in PARKS and g.buffer(0.0002).contains(Point(pk['lon'], pk['lat']))})
    schools = sorted((x['p']['name'], x['page']) for x in info.values() if x['sec'] == s)
    pct_app = BY.get(f'{ORD[n]}-precinct', {})
    title = f'Sector {s}'
    desc = f'NYPD Sector {s} of the {ORD[n]} Precinct, in Brooklyn Community Board 6: its map, neighborhoods, parks and schools, and how to reach the precinct.'
    h = head(title, desc, f'/nypd-sector/{s.lower()}.html')
    h += ('  <div class="phead">\n    <div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="/publicsafety/" style="color:inherit">Public safety</a> &middot; '
          f'<a href="/{ORD[n]}-precinct/" style="color:inherit">{ORD[n]} Precinct</a></div>\n'
          f'    <div class="olog" style="margin-top:8px"><img src="/app/data/civic/orgs/logos/pct{n}.png" alt="" style="border-radius:9px"><div class="otx"><h1 style="margin-top:0">{title}</h1>'
          f'<div class="pseat">NYPD {ORD[n]} Precinct &middot; {E(", ".join(hs[:3]))}</div></div></div>\n  </div>\n')
    h += sec('What it is', f'<p>The NYPD divides each precinct into sectors for patrol. Sector {s} is one of the {ORD[n]} Precinct\'s four sectors '
             f'({", ".join(x for x in SECTORS if x[:2] == n)}). It covers {SECT_MI[s]} square miles' + (f', {round(inside * 100)}% of it in CB6' if inside < 0.97 else ', all in CB6') + '.</p>')
    h += sec('Where it is', mapblock('sector', s, pct_app.get('lat'), pct_app.get('lng'), f'Sector {s}', f'its boundary, with the {ORD[n]} Precinct station house', icon=f'/app/data/civic/orgs/logos/pct{n}.png', zoom=15))
    h += sec('Details', kv([('Precinct', f'<a href="/{ORD[n]}-precinct/">{ORD[n]} Precinct</a>, {E(pr["addr"])}'), ('Area', f'{SECT_MI[s]} square miles'),
                            ('Neighborhoods', E(', '.join(hs))), ('Precinct phone', E(pr['phone'])), ('Community Affairs', E(pr['ca'])),
                            ('Commanding officer', E(pr['co'])), ('Community council', E(pr['council'])), ('Emergencies', '911'), ('Quality of life', E(QTEAM))]))
    if parks: h += sec('Parks in this sector', '<div class="chips">' + ''.join(f'<a class="chip" href="{u}">{E(nm)}</a>' for nm, u in parks) + '</div>')
    if schools: h += sec('Schools in this sector', '<div class="chips">' + ''.join(f'<a class="chip" href="{u}">{E(nm)}</a>' for nm, u in schools) + '</div>')
    h += sec('The other sectors', '<div class="chips">' + ''.join(f'<a class="chip{" hot" if x == s else ""}" href="/nypd-sector/{x.lower()}.html">Sector {x}</a>' for x in SECTORS) + '</div>')
    h += FOOT.format(src='Sector boundaries and areas from NYC Open Data, NYPD Sectors. Precinct contacts, commanding officer and community council from the NYPD precinct page, read November 8, 2026.')
    return h

def precinct_block(n, info):
    pr = NYPD[n]
    rows = [('Commanding officer', E(pr['co'])), ('Community council', E(pr['council'])), ('Quality of life', E(QTEAM))]
    secs = ''.join(f'<a class="chip" href="/nypd-sector/{s.lower()}.html">Sector {s}: {E(", ".join(hoods_of(SECT[s])[:2]))}</a>' for s in SECTORS if s[:2] == n)
    return sec('Sectors', f'<p>The {ORD[n]} Precinct is divided into four patrol sectors. Each has its own page with its map, parks and schools.</p><div class="chips">{secs}</div>') + sec('Leadership and community council', kv(rows) + '<p class="subnote">From the NYPD precinct page, read November 8, 2026.</p>')

def district_block(n, info):
    sch = sorted((x['p']['name'], x['page']) for x in info.values() if x['sd'] == n)
    return sec(f'Schools in CB6 in District {n}', f'<p>{len(sch)} schools in Brooklyn Community Board 6 are inside School District {n}\'s boundary.</p><div class="chips">'
               + ''.join(f'<a class="chip" href="{u}">{E(nm)}</a>' for nm, u in sch) + '</div>')

# ---------- apps ----------
def app(info):
    prof = D['profiles']
    # the business directory's copy of the 78th Precinct duplicates the precinct's own profile
    prof[:] = [p for p in prof if p['slug'] != 'biz-80580acec2']
    base = BY['nypd']
    for s in SECTORS:
        n = s[:2]; g = SECT[s]; pr = NYPD[n]; pct = BY[f'{ORD[n]}-precinct']
        slug = f'nypd-sector-{s.lower()}'
        c = g.representative_point()
        q = {k: base.get(k) for k in base}
        q.update(slug=slug, type=slug, name=f'Sector {s}', seat=f'NYPD {ORD[n]} Precinct · ' + ', '.join(hoods_of(g)[:3]),
                 desc=f'NYPD Sector {s}, {ORD[n]} Precinct.', lat=c.y, lng=c.x, addr=pr['addr'].split(',')[0], zip=pr['addr'][-5:], addr_note='',
                 phone=pr['phone'], email='', web=f'bkcb6.app/nypd-sector/{s.lower()}.html', weburl=f'https://bkcb6.app/nypd-sector/{s.lower()}.html', since='',
                 intro=[f'The NYPD divides each precinct into sectors for patrol. Sector {s} is one of the {ORD[n]} Precinct\'s four sectors. It covers {SECT_MI[s]} square miles.'],
                 does=[QTEAM],
                 kv=[['Precinct', f'{ORD[n]} Precinct'], ['Neighborhoods', ', '.join(hoods_of(g))], ['Area', f'{SECT_MI[s]} square miles'],
                     ['Community Affairs', pr['ca']], ['Commanding officer', pr['co']], ['Community council', pr['council']],
                     ['Schools in the sector', ', '.join(sorted(x['p']['name'] for x in info.values() if x['sec'] == s))],
                     ['Community board', 'Brooklyn Community Board 6'], ['Source', 'NYC Open Data NYPD Sectors; NYPD precinct page']],
                 links=[['Sector page and map', f'https://bkcb6.app/nypd-sector/{s.lower()}.html'], [f'{ORD[n]} Precinct', f'https://bkcb6.app/{ORD[n]}-precinct/']],
                 logo=pct['logo'], cal=None, n=0, going=[], kind='org', official='', group='Government agencies', topic='', sort=pct.get('sort', 0) + 0.1,
                 kvdest={f'{ORD[n]} Precinct': f'org:{ORD[n]}-precinct'})
        q['kv'] = [r for r in q['kv'] if r[1]]
        prof[:] = [p for p in prof if p['slug'] != slug]; prof.append(q)
    for n in ('76', '78'):
        p = BY[f'{ORD[n]}-precinct']; pr = NYPD[n]
        p['kv'] = [r for r in p['kv'] if r[0] not in ('Commanding Officer', 'Commanding officer', 'Community council', 'Sectors')]
        p['kv'][:0] = [['Commanding officer', pr['co']], ['Community council', pr['council']],
                       ['Sectors', ', '.join(f'Sector {s}' for s in SECTORS if s[:2] == n)]]
        p.setdefault('kvdest', {}).update({f'Sector {s}': f'org:nypd-sector-{s.lower()}' for s in SECTORS if s[:2] == n})
        if not any(l[1].startswith('https://bkcb6.app/') for l in p.get('links') or []):
            p['links'] = (p.get('links') or []) + [['Precinct page and map', f'https://bkcb6.app/{ORD[n]}-precinct/']]
    sch = BY['nyc-public-schools-cb6']
    for n in ('13', '15'):
        slug = f'school-district-{n}'
        q = {k: sch.get(k) for k in sch}
        c = SD[n].intersection(cb6).representative_point()
        names = sorted(x['p']['name'] for x in info.values() if x['sd'] == n)
        q.update(slug=slug, type=slug, name=f'Community School District {n}', seat='NYC Public Schools · ' + ('serves most of CB6' if n == '15' else 'serves the northeast corner of CB6'),
                 desc=f'Community School District {n}.', lat=c.y, lng=c.x, web=f'bkcb6.app/school-district-{n}/', weburl=f'https://bkcb6.app/school-district-{n}/',
                 intro=[f'Community School District {n} is one of the 32 community school districts of NYC Public Schools, for the public elementary and middle schools in its area. '
                        f'{len(names)} schools in CB6 are inside its boundary.'],
                 does=[], kv=[['Schools in CB6', ', '.join(names)], ['Community board', 'Brooklyn Community Board 6'], ['Source', 'NYC Open Data School Districts; NYC Facilities Database']],
                 links=[['District page and map', f'https://bkcb6.app/school-district-{n}/']], cal=None, n=0, going=[], kind='org', official='', group='Government agencies', topic='',
                 kvdest={'CEC District 15': 'org:cec-district-15'} if n == '15' else {})
        if n == '15': q['kv'].insert(0, ['Community Education Council', 'CEC District 15'])
        prof[:] = [p for p in prof if p['slug'] != slug]; prof.append(q)
    for s, x in info.items():
        p = x['p']
        p['kv'] = [r for r in p['kv'] if r[0] not in ('Police precinct', 'NYPD sector')]
        p['kv'] = [r if r[0] != 'School district' else ['School district', f'District {x["sd"]}' if x['sd'] else r[1]] for r in p['kv']]
        if x['sd'] and not any(r[0] == 'School district' for r in p['kv']): p['kv'].append(['School district', f'District {x["sd"]}'])
        if x['pct']: p['kv'].append(['Police precinct', f'{ORD[x["pct"]]} Precinct'])
        if x['sec']: p['kv'].append(['NYPD sector', f'Sector {x["sec"]}'])
        kd = p.get('kvdest') or {}
        if x['sd']: kd[f'District {x["sd"]}'] = f'org:school-district-{x["sd"]}'
        if x['pct']: kd[f'{ORD[x["pct"]]} Precinct'] = f'org:{ORD[x["pct"]]}-precinct'
        if x['sec']: kd[f'Sector {x["sec"]}'] = f'org:nypd-sector-{x["sec"].lower()}'
        p['kvdest'] = kd
        p['links'] = [l for l in (p.get('links') or []) if l[0] != 'Profile and map'] + [['Profile and map', 'https://bkcb6.app' + x['page']]]
    json.dump(D, open(PROF, 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
