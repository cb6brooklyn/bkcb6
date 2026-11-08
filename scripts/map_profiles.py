#!/usr/bin/env python3
"""Every place on the CB6 maps gets a profile page, and its map pin opens it.

Reads the CB6 block-map layers (assets/blocks/cb6-layers.json). For each place layer (subway stations, Citi Bike docks,
libraries, firehouses, greenmarkets and supermarkets, culture and institutions, poll sites, LIFT housing sites, child care
and pre-K, vaccine sites, parks) each pin is matched to a profile that already exists (the apps' Directory,
app/data/civic/orgs/orgs-profiles.json, and the site's pages); a pin with no profile gets one:
  site  /<kind>/<slug>.html in the site's profile template, with the place on a map and its precinct, sector, school
        district and neighborhood when it is in CB6
  apps  a Directory profile (Schools, parks and facilities) for places in or at the edge of CB6
and the pin's link ('u') is pointed at the profile. Permits, street work, events, block parties, alternate-side
parking, liquor licenses and landmarked buildings are records, not places, and keep their own pages.
Rerunnable: its own map-* app entries and /<kind>/ pages are rewritten.
"""
import html, json, os, re, sys, difflib, math
from shapely.geometry import shape, Point
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
sys.path.insert(0, 'scripts')
import importlib.util
spec = importlib.util.spec_from_file_location('dss', 'scripts/directory_safety_schools.py'); DSS = importlib.util.module_from_spec(spec); spec.loader.exec_module(DSS)
E = html.escape
LAY = 'assets/blocks/cb6-layers.json'
PROF = 'app/data/civic/orgs/orgs-profiles.json'
L = json.load(open(LAY)); LBY = {l['id']: l for l in L['layers']}
D = json.load(open(PROF))
cb6 = DSS.cb6
GROUP = 'Schools, parks and facilities'
KINDS = {  # layer id: (dir, kind label, app topic, about line, outside link)
 'subway': ('subway', 'Subway station', 'Subway stations and Citi Bike', 'A New York City subway station.', ('MTA', 'https://new.mta.info/')),
 'citibike': ('citibike', 'Citi Bike dock', 'Subway stations and Citi Bike', 'A Citi Bike bike-share dock.', ('Citi Bike station map', 'https://citibikenyc.com/explore')),
 'library': ('library', 'Library', 'Libraries', 'A Brooklyn Public Library location.', None),
 'fdny': ('firehouse', 'FDNY firehouse', 'Firehouses', 'A New York City Fire Department firehouse.', ('FDNY', 'https://www.nyc.gov/site/fdny/index.page')),
 'food': ('food-place', 'Food access', 'Farmers markets', '', None),
 'culture': ('culture-place', 'Culture and institutions', 'Culture and institutions', '', None),
 'polls': ('poll-site', 'Poll site', 'Poll sites', 'A poll site where voters assigned to it vote in person.', ('Find your poll site', 'https://findmypollsite.vote.nyc/')),
 'lift': ('lift-site', 'LIFT housing site', 'Housing sites', 'A housing site on the City\'s LIFT list of planned homes.', None),
 'childcare': ('childcare', 'Child care and pre-K', 'Child care and pre-K', '', ('NYC child care search', 'https://www.nyc.gov/site/doh/services/child-care.page')),
 'vaccines': ('vaccine-site', 'Vaccine site', 'Hospitals and health care', 'A vaccine site on the NYC Health Map.', ('NYC Health Map', 'https://a816-health.nyc.gov/NYCHealthMap/ServiceCategory/Vaccines')),
}
NEW_TOPICS = ['Subway stations and Citi Bike', 'Firehouses', 'Farmers markets', 'Culture and institutions', 'Poll sites', 'Housing sites']

def slugify(s): return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', html.unescape(s).lower().replace("'", ''))).strip('-')[:80]
def nn(s): return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', s.lower().replace('&', 'and')).split())
def dist(a, b, c, d): return math.hypot((a - c) * 111000, (b - d) * 84000)

def site_page_for(p):
    """the site page an app profile already has, if any"""
    s = p['slug']; w = p.get('weburl') or ''
    if w.startswith('https://bkcb6.app/'): return w[len('https://bkcb6.app'):]
    for c in (s, s.replace('place-', '', 1), s.replace('health-', '', 1), p.get('official') or ''):
        if c and os.path.isfile(f'{c}/index.html'): return f'/{c}/'
    for l in p.get('links') or []:
        if l[1].startswith('https://bkcb6.app/') and l[0] in ('Profile and map', 'Full park profile', 'Profile', 'Sector page and map'): return l[1][len('https://bkcb6.app'):]
    return ''

APPLOC = [p for p in D['profiles'] if p.get('lat') and p.get('lng') and not p['slug'].startswith('map-')]
def match_app(it):
    best = None
    for p in APPLOC:
        dd = dist(it['y'], it['x'], p['lat'], p['lng'])
        if dd > 120: continue
        r = difflib.SequenceMatcher(None, nn(it['t']), nn(p['name'])).ratio()
        if r >= 0.72 and (not best or r - dd / 1000 > best[0]): best = (r - dd / 1000, p)
    return best[1] if best else None

def around(lat, lng):
    if not cb6.buffer(0.002).contains(Point(lng, lat)): return []
    sd, pct, sec = DSS.where(lat, lng)
    hood = next((n for n, g in DSS.HOODS.items() if g.buffer(0.0003).contains(Point(lng, lat))), '')
    rows = [('Neighborhood', E(hood))] if hood else []
    rows += DSS.links_row({'sd': sd, 'pct': pct, 'sec': sec})
    return rows

def page(kind, it, title, seat, rows, about, ext, path):
    lat, lng = it['y'], it['x']
    h = DSS.head(title, f'{title}: {seat}. Where it is, on a map, and what is around it.', path)
    h += ('  <div class="phead">\n    <div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="/blockbyblock" style="color:inherit">CB6 maps</a></div>\n'
          f'    <h1>{E(title)}</h1>\n    <div class="pseat">{E(seat)}</div>\n  </div>\n')
    if about: h += DSS.sec('What it is', ''.join(f'<p>{E(a)}</p>' for a in about))
    chips = '<div class="chips">' + (f'<a class="chip" href="{E(ext[1])}" target="_blank" rel="noopener">{E(ext[0])} &#8599;</a>' if ext else '') + '<a class="chip" href="/blockbyblock">The CB6 block maps</a></div>'
    h += DSS.sec('Details', DSS.kv(rows) + chips)
    h += DSS.sec('Where it is', DSS.mapblock('cb', '306', lat, lng, title, 'the place and Brooklyn Community Board 6', zoom=17, fit=False))
    ar = around(lat, lng)
    if ar: h += DSS.sec('Its precinct, sector and school district', DSS.kv(ar))
    h += DSS.FOOT.format(src=f'From the CB6 block maps ({E(LBY[kind]["label"])} layer) and the City\'s open data behind it. Precinct, sector and school district from the NYC Open Data maps.')
    return h

USED = set()
def main():
    made_app = []; pages = 0; linked = 0; n_items = 0
    for kind, (dr, klabel, topic, about1, ext) in KINDS.items():
        os.makedirs(dr, exist_ok=True)
        for it in LBY[kind]['items']:
            n_items += 1
            ap = match_app(it) if kind != 'polls' else None
            sp = site_page_for(ap) if ap else ''
            if sp:
                it['u'] = sp; linked += 1; continue
            title = it['t']; s = it.get('s', '')
            slug = slugify(title + ('' if kind not in ('citibike', 'childcare', 'vaccines', 'food') else '-' + s.split(',')[-1].split('·')[0])) if kind in ('vaccines',) else slugify(title)
            if kind == 'vaccines': slug = slugify(title + ' ' + re.sub(r'^.*·', '', s))
            if (dr, slug) in USED: slug = slugify(title + ' ' + re.sub(r'^[^,]*, ', '', s))[:80]
            k2 = 2
            while (dr, slug) in USED: slug = f'{slug}-{k2}'; k2 += 1
            USED.add((dr, slug))
            path = f'/{dr}/{slug}.html'
            rows, about = [], [about1] if about1 else []
            if kind == 'subway':
                seat = f'Subway station · {s} trains'; rows = [('Trains', E(s))]
            elif kind == 'citibike':
                seat = 'Citi Bike dock'; rows = [('Corner', E(title))]
            elif kind == 'library':
                seat = 'Brooklyn Public Library'; rows = [('Address', E(s))]
                ext2 = ('Library page', it['u']) if it.get('u', '').startswith('http') else None
            elif kind == 'fdny':
                seat = 'FDNY firehouse'; rows = [('Units', E(title)), ('Address', E(s))]
            elif kind == 'food':
                k0, rest = (s.split(', ', 1) + [''])[:2]
                seat = 'Greenmarket (farmers market)' if k0 == 'greenmarket' else 'Supermarket'
                about = ['A GrowNYC Greenmarket farmers market.'] if k0 == 'greenmarket' else ['A supermarket on the City\'s food access map.']
                rows = [('Where and when' if k0 == 'greenmarket' else 'Address', E(rest))]
                gm = next((x for x in LBY['markets']['items'] if nn(x['t']) == nn(title)), None)
                if gm: rows = [('Where and when', E(gm['s']))]
            elif kind == 'culture':
                k0, rest = (s.split(', ', 1) + [''])[:2] if ', ' in s else ('', s)
                seat = k0 or 'Culture and institutions'; rows = [('Kind', E(k0)), ('Address', E(rest))]
            elif kind == 'polls':
                a, b = (s.split(' · ') + [''])[:2]
                seat = 'Poll site'; rows = [('Address', E(a)), ('Entrance', E(b if b != a else ''))]
            elif kind == 'lift':
                parts = [x.strip() for x in s.split(',')]
                seat = 'LIFT housing site'; rows = [('Address', E(parts[0].title())), ('Agency', E(parts[1] if len(parts) > 1 else '')), ('Planned homes', E(parts[2] if len(parts) > 2 else ''))]
            elif kind == 'childcare':
                k0, rest = (s.split(', ', 1) + [''])[:2]
                seat = k0; rows = [('Kind', E(k0)), ('Address', E(rest))]
                about = [{'Day care': 'A licensed child care program.', 'Pre-K / 3-K': 'A 3-K or Pre-K for All program.', 'Preschool special ed': 'A preschool special education program.'}.get(k0, '')]
            elif kind == 'vaccines':
                v, _, a = s.partition(' · ')
                seat = 'Vaccine site'; rows = [('Vaccines', E(v)), ('Address', E(a.title() if a.isupper() else a))]
            rows = [r for r in rows if r[1]]
            e2 = ext2 if kind == 'library' else ext
            open(path[1:], 'w').write(page(kind, it, title, seat, rows, [a for a in about if a], e2, path))
            pages += 1; it['u'] = path
            # the apps: a Directory profile for places in or at the edge of CB6 that the apps don't have yet
            if not ap and cb6.buffer(0.004).contains(Point(it['x'], it['y'])) and kind != 'vaccines':
                made_app.append({'slug': f'map-{dr}-{slug}', 'type': f'map-{dr}-{slug}', 'name': title, 'seat': seat, 'desc': f'{title}. {seat}.',
                                 'lat': it['y'], 'lng': it['x'], 'addr': next((r[1] for r in rows if r[0] == 'Address'), ''), 'zip': '', 'addr_note': '', 'phone': '', 'email': '',
                                 'web': f'bkcb6.app{path}', 'weburl': f'https://bkcb6.app{path}', 'since': '', 'intro': [a for a in about if a], 'does': [],
                                 'kv': [[k, html.unescape(re.sub(r'<[^>]+>', '', v))] for k, v in rows] + [['Community board', 'Brooklyn Community Board 6'], ['Source', f'CB6 block maps, {LBY[kind]["label"]}']],
                                 'links': [['Profile and map', f'https://bkcb6.app{path}']] + ([[e2[0], e2[1]]] if e2 else []),
                                 'logo': '', 'cal': None, 'n': 0, 'going': [], 'kind': 'org', 'official': '', 'group': 'Local businesses' if seat == 'Supermarket' else GROUP, 'topic': 'Supermarkets' if seat == 'Supermarket' else topic, 'sort': 0})
    # parks pins: the park's own profile
    PKP = json.load(open('parks-policy/profiles.json')); PK = json.load(open('parks-policy/cb6.json'))['parks']
    PG = [(p['id'], shape(p['g']).buffer(0.0002)) for p in PK]
    for it in LBY['parks']['items']:
        pt = Point(it['x'], it['y'])
        hit = next((i for i, g in PG if g.contains(pt) and i in PKP), None)
        if hit: it['u'] = PKP[hit]; linked += 1
    D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith('map-')] + made_app
    used = {it['u'] for k in KINDS for it in LBY[k]['items']}
    for dr in {v[0] for v in KINDS.values()}:
        for f in os.listdir(dr):
            if f'/{dr}/{f}' not in used: os.remove(f'{dr}/{f}')
    g = next(x for x in D['groups'] if x['name'] == GROUP)
    for t in NEW_TOPICS:
        if t not in g['topics']: g['topics'].append(t)
    json.dump(D, open(PROF, 'w'), ensure_ascii=False, indent=1)
    json.dump(L, open(LAY, 'w'), ensure_ascii=False, separators=(',', ':'))
    print(n_items, 'pins;', linked, 'linked to existing profiles;', pages, 'new pages;', len(made_app), 'new app profiles')

if __name__ == '__main__':
    main()
