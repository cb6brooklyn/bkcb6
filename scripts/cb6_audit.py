#!/usr/bin/env python3
"""BKCB6 Directory audit: every record of the official registers that falls inside Community District 306, checked
against the Directory. data/cb6-audit/{restaurants,dcwp,agmarkets,sla}.json (pulled Nov 16, 2026):
  restaurants  DOHMH restaurant inspections (43nn-pn8j), community board 306, one row per restaurant (CAMIS), with cuisine
  dcwp         DCWP active business licenses (w7w3-xahh), community board 306
  agmarkets    NYS Ag & Markets retail food stores (9a8c-vfzj), inside the district boundary
  sla          NYS Liquor Authority active licenses (9s3h-dpkz), inside the district boundary
match(rows) -> (matched {register id: profile slug}, missing rows). Prints the coverage; writes data/cb6-audit/missing.json."""
import json, os, re, math, difflib, collections, importlib.util as iu
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
sp = iu.spec_from_file_location('dd', P('scripts/directory_dedupe.py')); dd = iu.module_from_spec(sp); sp.loader.exec_module(dd)
A = lambda f: json.load(open(P('data/cb6-audit', f), encoding='utf-8'))
def rows():
    out = []
    for r in A('restaurants.json'):
        out.append({'src': 'restaurants', 'id': 'camis-' + r['camis'], 'name': r.get('dba', ''), 'alt': '', 'addr': '%s %s' % (r.get('building', ''), r.get('street', '')),
                    'zip': r.get('zipcode', ''), 'lat': float(r['latitude']) if r.get('latitude') and float(r['latitude']) else None, 'lng': float(r['longitude']) if r.get('longitude') and float(r['longitude']) else None,
                    'phone': r.get('phone', ''), 'cuisine': r.get('cuisine_description', ''), 'last': r.get('last', '')})
    for r in A('dcwp.json'):
        out.append({'src': 'dcwp', 'id': 'dcwp-' + r['license_nbr'], 'name': r.get('dba_trade_name') or r.get('business_name', ''), 'alt': r.get('business_name', ''),
                    'addr': '%s %s' % (r.get('address_building', ''), r.get('address_street_name', '')), 'zip': r.get('address_zip', ''),
                    'lat': float(r['latitude']) if r.get('latitude') else None, 'lng': float(r['longitude']) if r.get('longitude') else None, 'phone': r.get('contact_phone', ''),
                    'cat': r.get('business_category', ''), 'premises': r.get('license_type') == 'Premises'})
    for r in A('agmarkets.json'):
        c = r['georeference']['coordinates']
        out.append({'src': 'agmarkets', 'id': 'ag-' + r['license_number'], 'name': r.get('dba_name') or r.get('entity_name', ''), 'alt': r.get('entity_name', ''),
                    'addr': '%s %s' % (r.get('street_number', ''), r.get('street_name', '')), 'zip': r.get('zip_code', ''), 'lat': c[1], 'lng': c[0], 'sqft': r.get('square_footage', ''), 'estab': r.get('estab_type', '')})
    for r in A('sla.json'):
        c = r['georeference']['coordinates']
        out.append({'src': 'sla', 'id': 'sla-' + r['licensepermitid'], 'name': r.get('dba') or r.get('legalname', ''), 'alt': r.get('legalname', ''), 'addr': r.get('actualaddressofpremises', ''),
                    'zip': r.get('zipcode', ''), 'lat': c[1], 'lng': c[0], 'cat': r.get('description', ''), 'expires': r.get('expirationdate', '')})
    return out
def nn(s): return re.sub(r'[^a-z0-9]', '', re.sub(r'\b(the|inc|llc|corp|ltd|co)\b', '', (s or '').lower().replace('&', 'and')))
def sim(a, b):
    a, b = nn(a), nn(b)
    if not a or not b: return 0
    if a == b: return 1
    if len(a) >= 5 and len(b) >= 5 and (a in b or b in a): return .9
    return difflib.SequenceMatcher(None, a, b).ratio()
def match(R, profiles):
    byk = collections.defaultdict(list); grid = collections.defaultdict(list)
    for p in profiles:
        k = dd._ak(p)
        if k: byk[k].append(p)
        if p.get('lat') and p.get('lng'): grid[(round(p['lat'] * 500), round(p['lng'] * 500))].append(p)
    got, miss = {}, []
    for r in R:
        k = dd._ak({'addr': r['addr']}); best = (0, None)
        cands = list(byk.get(k, [])) if k else []
        near = []
        if r.get('lat'):
            gx, gy = round(r['lat'] * 500), round(r['lng'] * 500)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for p in grid.get((gx + dx, gy + dy), []):
                        d = math.hypot((p['lat'] - r['lat']) * 111000, (p['lng'] - r['lng']) * 84000)
                        if d <= 60: near.append(p)
        for p in cands:
            s = max(sim(r['name'], p['name']), sim(r['alt'], p['name']), .86 if (dd._words(r['name']) and dd._words(p['name']) and (dd._words(r['name']) <= dd._words(p['name']) or dd._words(p['name']) <= dd._words(r['name']))) else 0)
            if s > best[0]: best = (s, p)
        if best[0] < .62:
            for p in near:
                s = max(sim(r['name'], p['name']), sim(r['alt'], p['name']))
                if s >= .8 and s > best[0]: best = (s, p)
        if best[1] is not None and best[0] >= .62: got[r['id']] = best[1]['slug']
        else: miss.append(r)
    return got, miss
if __name__ == '__main__':
    D = json.load(open(P('app/data/civic/orgs/orgs-profiles.json'), encoding='utf-8'))['profiles']
    R = rows(); got, miss = match(R, D)
    c = collections.Counter(r['src'] for r in R); m = collections.Counter(r['src'] for r in miss)
    for s in c: print('%-12s in BKCB6: %4d | in the Directory: %4d | missing: %4d' % (s, c[s], c[s] - m[s], m[s]))
    json.dump(miss, open(P('data/cb6-audit/missing.json'), 'w'), indent=0)
    json.dump(got, open(P('data/cb6-audit/matched.json'), 'w'), indent=0)
