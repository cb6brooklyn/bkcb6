#!/usr/bin/env python3
"""The apps' profiles of Brooklyn's 23 police precincts and 12 community school districts, on the same screen as an
elected official's profile (its outline on the map, the community boards and officials it overlaps, the office).

Writes app/data/civic/area-profiles.json (one record per area, the officials.json shape plus "rings", the outline,
"chip", the pill under the name, and "color") and app/data/civic/officials/<slug>.png (the logo). The apps open them
from any link to the site's profile page through the "areas" table that scripts/one_profile.py writes into
civic/profile-index.json.

Sources: data/gov-profiles.json (the site's profiles, from scripts/district_profiles.py and the hand-written 76th and
78th), data/districts/precinct-<n>.geojson and school-<n>.geojson (the outlines), bk_eds.geojson (Brooklyn's election
districts), data/districts/{council,senate,congress}-<n>.geojson, cd-boundaries-simple.geojson, officials.json.
Rerunnable."""
import json, os, re
from PIL import Image
from shapely.geometry import shape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
J = lambda p: json.load(open(p, encoding='utf-8'))


def ordinal(n):
    return '%d%s' % (n, 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'))


def plain(s): return re.sub(r'<[^>]+>', '', s).replace('&middot;', '·').replace('&amp;', '&').replace('&rsquo;', '’')


def gj(p):
    g = J(p)['features'][0]['geometry']
    if g['type'] == 'MultiPolygon':  # some files carry slivers of under four points
        g = {'type': 'MultiPolygon', 'coordinates': [[r for r in poly if len(r) >= 4] for poly in g['coordinates'] if len(poly[0]) >= 4]}
    s = shape(g)
    return s if s.is_valid else s.buffer(0)


officials = J('app/data/civic/officials.json')
by_seat = {(o['type'], o['district']): o for o in officials if o.get('district') not in (None, '')}
label = {}
for o in officials:
    for d in o.get('dists', []): label.setdefault(d['slug'], (d['label'], d['name']))
gov = {r['slug']: r for r in J('data/gov-profiles.json')}

cds = [(int(f['properties']['cd']) - 300, shape(f['geometry'])) for f in J('cd-boundaries-simple.geojson')['features'] if f['properties']['cd'].startswith('3') and int(f['properties']['cd']) % 100 <= 18]
eds = []
for f in J('bk_eds.geojson')['features']:
    g = shape(f['geometry'])
    eds.append((g.representative_point(), int(f['properties']['ad'])))
chambers = {}
for ch, rng in (('council', range(1, 52)), ('senate', range(1, 64)), ('congress', range(1, 27))):
    for n in rng:
        p = 'data/districts/%s-%d.geojson' % (ch, n)
        if os.path.exists(p): chambers[(ch, n)] = gj(p)
for n in range(1, 66):
    p = 'data/districts/assembly-%d.geojson' % n
    if os.path.exists(p): chambers[('assembly', n)] = gj(p)


def pct(x): return '%d%%' % round(x * 100)


def build(kind, n, slug):
    g = gj('data/districts/%s-%d.geojson' % (kind, n))
    noun = 'precinct' if kind == 'precinct' else 'school district'
    inside = [(pt, ad) for pt, ad in eds if g.contains(pt)]
    # community boards: election districts inside, and area both ways
    cbs, cdrows = [], []
    for cd, s in cds:
        a = g.intersection(s).area
        if a / g.area < 0.005: continue
        e = sum(1 for pt, _ in inside if s.contains(pt))
        cbs.append({'label': 'Brooklyn CB%d' % cd, 'cd': str(300 + cd), 'eds': e})
        cdrows.append({'n': 'Brooklyn CB %d' % cd, 'l': 'cb-bk-%d.html' % cd, 'w': 100.0, 'a': '%s of the %s' % (pct(a / g.area), noun), 'b': '%s of it' % pct(a / s.area), '_s': a})
    cbs.sort(key=lambda b: -b['eds']); cdrows.sort(key=lambda r: -r['_s'])
    # officials whose districts it overlaps, by election districts inside both
    dists, groups = [], []
    for ch, title in (('council', 'City Council districts'), ('assembly', 'State Assembly districts'), ('senate', 'State Senate districts'), ('congress', 'Congressional districts')):
        rows = []
        for (c, d), s in chambers.items():
            if c != ch: continue
            a = g.intersection(s).area
            if a / g.area < 0.005: continue
            e = sum(1 for pt, ad in inside if (ad == d if ch == 'assembly' else s.contains(pt)))
            o = by_seat.get((ch, d))
            if o:
                lb, nm = label.get(o['slug'], ('', o['name']))
                dists.append({'label': lb, 'slug': o['slug'], 'name': nm, 'eds': e, '_s': a})
            rows.append({'n': label.get(o['slug'], ('%s %d' % (title, d), ''))[0] if o else '%s %d' % (title, d), 'l': o['slug'] if o else None, 'w': 100.0,
                         'a': '%s of the %s' % (pct(a / g.area), noun), 'b': '%s of it' % pct(a / s.area), '_s': a})
        rows.sort(key=lambda r: -r['_s'])
        if rows: groups.append({'t': title, 'rows': rows})
    dists.sort(key=lambda d: (['council', 'assembly', 'senate', 'congress'].index(by_seat_type(d['slug'])), -d['eds'], -d['_s']))
    for x in dists + cdrows + [r for gp in groups for r in gp['rows']]: x.pop('_s', None)
    return g, cbs, cdrows, dists, groups


def by_seat_type(slug):
    return next(o['type'] for o in officials if o['slug'] == slug)


def rings(g):
    polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
    return [[[round(x, 5), round(y, 5)] for x, y in p.exterior.coords] for p in polys]


out = []
layers = {l['k']: l for l in J('bkcompplan/layers.json')}
for kind, key in (('precinct', 'precinct'), ('school', 'school')):
    for f in layers[key]['f']:
        n = f['n']
        slug = '%s-precinct' % ordinal(n) if kind == 'precinct' else 'school-district-%d' % n
        r = gov[slug]
        g, cbs, cdrows, dists, groups = build(kind, n, slug)
        noun = 'precinct' if kind == 'precinct' else 'school district'
        boards = ', '.join('Brooklyn %d' % (int(b['cd']) - 300) for b in sorted(cbs, key=lambda b: int(b['cd'])))
        bio = [plain(p) for p in r['intro']]
        bio.append('The %s overlaps community board%s %s.' % (noun, '' if len(cbs) == 1 else 's', re.sub(r', ([^,]*)$', r' and \1', boards)))
        about = [plain(p) for p in r['does']]
        site = r.get('weburl', '')
        a2 = 'Brooklyn, NY %s · %s' % (r['zip'], 'Station house' if kind == 'precinct' else 'District office' + (', ' + r['addr_note'] if r.get('addr_note') else ''))
        out.append({
            'slug': slug, 'name': r['name'], 'seat': plain(r['seat']), 'type': kind, 'chamber': kind, 'district': n, 'boro': 'Brooklyn',
            'chip': 'NYPD' if kind == 'precinct' else 'NYC Public Schools', 'color': '#1b4c7e' if kind == 'precinct' else '#4242d7',
            'shape': '%s-%d' % (kind, n), 'rings': rings(g),
            'dists': dists, 'cbs': cbs, 'bio': bio, 'about': about,
            'overlaps': [{'t': 'Community districts', 'rows': cdrows}] + groups,
            'committees': [], 'bills': [],
            'office': {'a1': r['addr'], 'a2': a2, 'phone': r.get('tel', ''), 'site': site},
            'page': '/%s/' % slug,
        })
        src = 'elected/precinct/%d.png' % n if kind == 'precinct' else 'elected/school/%d.png' % n
        im = Image.open(src).convert('RGBA'); im.thumbnail((400, 400), Image.LANCZOS)
        im.save('app/data/civic/officials/%s.png' % slug, optimize=True)

json.dump(out, open('app/data/civic/area-profiles.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(out), 'area profiles')
