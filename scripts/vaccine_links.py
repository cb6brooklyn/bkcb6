"""Links each NYC Health Map vaccine site (data/vaccine-sites.json) to the bkcb6.app profile of the same place, where there is one
(data/health-locations.json, from scripts/health_profiles.py): the site gets the profile's path (u) and logo (i), and the profile
gets the vaccines the city lists there. Used by scripts/health_profiles.py and tools/build_vaccine_sites.py."""
import json, math, re

STOP = {'pharmacy', 'inc', 'the', 'of', 'brooklyn', 'center', 'health', 'medical', 'llc', 'corp', 'drugs', 'and', 'nyc', 'ny', 'care', 'store', 'dba'}

def _tok(s):
    return set(re.sub(r'[^a-z0-9 ]', ' ', (s or '').lower().replace('/', ' ')).split()) - STOP

def _dist(a, b, c, d):
    return math.hypot((a - c) * 111000, (b - d) * 84000)

def match(site, locations):
    """The profile for this vaccine site: the nearest one within 120 m that shares a word of its name (or sits within 15 m)."""
    near = []
    for r in locations:
        dd = _dist(r['lat'], r['lng'], site['lat'], site['lng'])
        if dd < 120 and (_tok(r['name']) & _tok(site['name']) or dd < 15 and (not _tok(r['name']) or not _tok(site['name']))):
            near.append((dd, r))
    return min(near, key=lambda x: x[0])[1] if near else None

def link(sites, locations):
    """Sets u and i on every site that has a profile; returns {slug: [vaccines]}."""
    out = {}
    for s in sites:
        s.pop('u', None); s.pop('i', None)
        r = match(s, locations)
        if not r: continue
        s['u'] = f"/{r['slug']}/"
        if r.get('logo'): s['i'] = '/' + r['logo']
        v = out.setdefault(r['slug'], [])
        for x in s.get('vaccines') or []:
            if x not in v: v.append(x)
    return out

def link_file(vpath='data/vaccine-sites.json', lpath='data/health-locations.json'):
    doc = json.load(open(vpath))
    res = link(doc['sites'], json.load(open(lpath)))
    json.dump(doc, open(vpath, 'w'), separators=(',', ':'))
    return res
