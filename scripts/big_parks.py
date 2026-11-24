#!/usr/bin/env python3
"""Prospect Park, Brooklyn Bridge Park and Governors Island belong in the BKCB6 Directory, with everything in them: the
places the Prospect Park Alliance runs get a profile and a page each (/prospect-park/<slug>.html) and the Prospect Park
Alliance's logo (the Zoo its own), and data/cb6-audit/big-parks.json lists every listing that goes under the BKCB6 heading
"Prospect Park, Brooklyn Bridge Park and Governors Island" (read by app_directory_tiles.py). Rerunnable; run before the
Directory rebuild."""
import json, os, re, sys, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT); sys.path.insert(0, 'scripts')
spec = importlib.util.spec_from_file_location('bsp', 'scripts/biz_site_profiles.py'); bsp = importlib.util.module_from_spec(spec); spec.loader.exec_module(bsp)
PPA = [  # name, address, lat, lng, what it is
    ('Prospect Park Zoo', '450 Flatbush Avenue', 40.66525, -73.96523, 'The zoo in Prospect Park, run by the Wildlife Conservation Society.'),
    ('Audubon Center at the Boathouse', 'Prospect Park, by the Lullwater (Lincoln Road and Ocean Avenue entrance)', 40.66028, -73.96370, 'The Prospect Park Alliance nature center in the Boathouse.'),
    ('LeFrak Center at Lakeside', '171 East Drive, Prospect Park', 40.65456, -73.96585, 'Ice skating in winter and roller skating and water play in summer, run by the Prospect Park Alliance.'),
    ('Prospect Park Carousel', 'Prospect Park, near the Flatbush Avenue and Empire Boulevard entrance', 40.66445, -73.96442, 'The 1912 carousel in Prospect Park, run by the Prospect Park Alliance.'),
    ('Picnic House', 'Prospect Park, off Prospect Park West at 3rd Street', 40.66810, -73.97270, 'An event space in Prospect Park, run by the Prospect Park Alliance.'),
    ('Litchfield Villa', '95 Prospect Park West', 40.66641, -73.97621, 'The Prospect Park Alliance and NYC Parks Brooklyn offices.'),
    ('Prospect Park Tennis Center', '50 Parkside Avenue', 40.65189, -73.96984, 'Tennis courts in Prospect Park.'),
    ('Long Meadow', 'Prospect Park', 40.66560, -73.97060, 'The largest meadow in Prospect Park.'),
    ('Prospect Park Dog Beach', 'Prospect Park, below the Long Meadow', 40.66220, -73.97110, 'The dog pool in Prospect Park.'),
]
INCLUDE = ['Prospect Park', 'Prospect Park: courts and fields', 'Prospect Park Alliance', 'Lefferts Historic House', 'Parade Ground',
           'BRIC Celebrate Brooklyn at the Prospect Park Bandshell', 'Grand Army Plaza', 'Bird Collective',
           'Brooklyn Bridge Park', 'Brooklyn Bridge Park: courts and fields', 'Brooklyn Bridge Park: Main Street Dog Run', 'Pier 6 Dog Run',
           'Brooklyn Bridge Park: Pier 2 Play Turf', 'Brooklyn Bridge Park: Cobble Hill Dog Park', 'Brooklyn Bridge Park Boathouse',
           'Governors Island', 'Urban Assembly New York Harbor School', 'Institute for Public Architecture', 'Porch Stomp', 'Wytchonymous Arts']
def main():
    f = 'app/data/civic/orgs/orgs-profiles.json'; raw = open(f, encoding='utf-8').read(); D = json.loads(raw)
    D['profiles'] = [p for p in D['profiles'] if not p['slug'].startswith('ppa-')]
    os.makedirs('prospect-park', exist_ok=True)
    RL = json.load(open('data/cb6-audit/real-logos.json')); src = '/home/claude/work/real-logo-src'
    for name, addr, lat, lng, what in PPA:
        s = bsp.slugify(name); slug = 'ppa-' + s; path = f'/prospect-park/{s}.html'
        p = {'slug': slug, 'type': slug, 'name': name, 'seat': 'Prospect Park', 'desc': f'{name}. {what}', 'lat': lat, 'lng': lng, 'addr': addr, 'zip': '',
             'addr_note': '', 'phone': '', 'email': '', 'web': '', 'weburl': '', 'since': '', 'intro': [what], 'does': [],
             'kv': [['Park', 'Prospect Park'], ['Run by', 'Wildlife Conservation Society' if 'Zoo' in name else 'Prospect Park Alliance'], ['Source', 'bkcb6.app']],
             'links': [['Profile and map', 'https://bkcb6.app' + path]], 'logo': '', 'cal': None, 'n': 0, 'going': [], 'kind': 'org', 'official': '',
             'group': 'Schools, parks and facilities', 'topic': 'Parks, playgrounds and gardens', 'sort': 0}
        D['profiles'].append(p)
        open(path[1:], 'w').write(bsp.page(p, None, path))
    open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    json.dump({'heading': 'Prospect Park, Brooklyn Bridge Park and Governors Island', 'names': INCLUDE + [x[0] for x in PPA]}, open('data/cb6-audit/big-parks.json', 'w'), indent=1)
    print(len(PPA), 'Prospect Park places;', len(INCLUDE) + len(PPA), 'listings under the heading')
if __name__ == '__main__': main()
