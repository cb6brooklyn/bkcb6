#!/usr/bin/env python3
"""Every bus stop in CB6 as a place on the CB6 block maps (a 'bus' layer in assets/blocks/cb6-layers.json), so
map_profiles.py gives each a profile page (/bus-stop/<slug>.html) and a Directory listing under BKCB6 transit.

Source: data/cb6-bus-stops.json, made from the MTA's static GTFS feeds (NYCT Brooklyn gtfs_b and MTA Bus gtfs_busco,
rrgtfsfeeds.s3.amazonaws.com): the stops inside the CB6 boundary, the routes that stop there and where they go.
Run before map_profiles.py; rerunnable."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
LAY = 'assets/blocks/cb6-layers.json'
ABBR = {'AV': 'Av', 'ST': 'St', 'PL': 'Pl', 'RD': 'Rd', 'BLVD': 'Blvd', 'PKWY': 'Pkwy', 'EXPWY': 'Expwy', 'DR': 'Dr', 'SQ': 'Sq', 'PLZ': 'Plaza'}
def nice(s):
    out = []
    for w in re.split(r'(\W+)', s):
        if not w or not w[0].isalnum(): out.append(w); continue
        out.append(ABBR.get(w, w if any(c.isdigit() for c in w) else w.capitalize()))
    return ''.join(out)
def stop_name(s): return ' & '.join(nice(x.strip()) for x in s.split('/'))
def dest(h): return nice(re.split(r'\s+via\s+', h, flags=re.I)[0].replace('LIMITED ', 'Limited to ').strip())
def main():
    S = json.load(open('data/cb6-bus-stops.json')); L = json.load(open(LAY))
    items = []; cnt = {}
    for s in S: cnt[stop_name(s['name'])] = cnt.get(stop_name(s['name']), 0) + 1
    for s in sorted(S, key=lambda s: s['name']):
        parts = ['%s to %s' % (r, ' / '.join(dest(h) for h in hs)) for r, hs in s['routes'].items()]
        items.append({'x': s['lng'], 'y': s['lat'], 't': stop_name(s['name']) + (' (to %s)' % dest(next(iter(s['routes'].values()))[0]) if cnt[stop_name(s['name'])] > 1 else ''), 's': '; '.join(parts), 'r': list(s['routes']), 'id': s['id']})
    lay = {'id': 'bus', 'label': 'Bus stops', 'kind': 'pt', 'n': len(items), 'items': items, 'note': 'MTA bus stops (static GTFS)'}
    L['layers'] = [l for l in L['layers'] if l['id'] != 'bus']
    i = next(k for k, l in enumerate(L['layers']) if l['id'] == 'subway') + 1
    L['layers'].insert(i, lay)
    # subway stations in or on the edge of CB6 that the layer was missing (MTA gtfs_subway stops.txt)
    sub = next(l for l in L['layers'] if l['id'] == 'subway')
    for x, y, t, r in [(-73.972367, 40.67705, '7 Av', 'B Q'), (-73.971046, 40.675235, 'Grand Army Plaza Station', '2 3')]:
        if not any(abs(i['x'] - x) < 1e-4 and abs(i['y'] - y) < 1e-4 for i in sub['items']):
            sub['items'].append({'x': x, 'y': y, 't': t, 's': r})
    FIX = {'Atlantic Av-Barclays Ctr': '2 3 4 5 B D N Q R', 'Borough Hall': '2 3 4 5'}
    for i in sub['items']:
        if i['t'] in FIX: i['s'] = FIX[i['t']]
    sub['n'] = len(sub['items'])
    json.dump(L, open(LAY, 'w'), ensure_ascii=False, separators=(',', ':'))
    print(len(items), 'bus stops')
if __name__ == '__main__': main()
