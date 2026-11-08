#!/usr/bin/env python3
"""data/official-offices.json: every elected official's district office (app/data/civic/officials.json, office a1/a2)
placed on the map with NYC Planning Labs GeoSearch (PAD), for the office pin on each official's profile map
(assets/profile-map.js). Where PAD has no such house number, the pin goes between the nearest numbers PAD has
(PLACE below). The pin shows the official's logo (the same one the profiles directory uses)."""
import json, os, re, sys, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from directory_grid import OWN_LOGO
PLACE = {'cmjustinsanchez': (40.816665, -73.928627), 'cmbanks': (40.655012, -73.873252)}   # 416 Walton Ave; 1199 Elton St

def main():
    out = {}
    for o in json.load(open(os.path.join(ROOT, 'app/data/civic/officials.json'))):
        of = o.get('office') or {}
        a1 = of.get('a1', '').strip(); a2 = re.sub(r'\s*·.*', '', of.get('a2', '')).strip()
        if not a1: print('no office:', o['slug']); continue
        if o['slug'] in PLACE: lat, lng = PLACE[o['slug']]
        else:
            f = json.load(urllib.request.urlopen('https://geosearch.planninglabs.nyc/v2/search?size=1&text=' + urllib.parse.quote(a1 + ', ' + a2), timeout=20))['features']
            if not f: print('not found:', o['slug'], a1, a2); continue
            lng, lat = f[0]['geometry']['coordinates']
        out[o['slug']] = {'lat': round(lat, 6), 'lng': round(lng, 6), 'a1': a1, 'a2': a2, 'icon': OWN_LOGO.get(o['slug']) or o.get('icon', ''), 'name': o['name']}
    json.dump(out, open(os.path.join(ROOT, 'data/official-offices.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    print(len(out), 'offices')

if __name__ == '__main__':
    main()
