#!/usr/bin/env python3
"""data/officials-wide.json: the officials every community board shares by borough or city or state (Borough President,
District Attorney, the citywide and statewide offices, the US senators), from app/data/civic/officials.json, in the
order the community board pages list them after the district's own members. Usage: python3 scripts/officials_wide.py"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
O = {o['slug']: o for o in json.load(open('app/data/civic/officials.json'))}
row = lambda o: [o['slug'], o['name'], (o.get('seat') or '').split(' · ')[0]]
out = {'bp': {}, 'da': {}}
for o in O.values():
    if o['type'] in ('bp', 'da'): out[o['type']][o.get('boro') or ''] = row(o)
for k, sl in (('city', ['comptroller', 'publicadvocate', 'mayor']), ('state', ['attorneygeneral', 'statecomptroller', 'governor', 'lieutenantgovernor']),
              ('us', ['ussenschumer', 'ussengillibrand'])):
    out[k] = [row(O[s]) for s in sl if s in O]
out['names'] = {o['slug']: o['name'] for o in O.values() if o['type'] == 'congress'}   # House members' names, for tiles that carry only the district
json.dump(out, open('data/officials-wide.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print(sorted(out['bp']), len(out['city']), len(out['state']), len(out['us']))
