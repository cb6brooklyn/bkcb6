#!/usr/bin/env python3
"""One tile per place in the Directory. Profiles that are the same place under the same name, from different sources
(a DOHMH child care permit and a DOE Pre-K site at one address, a school's Pre-K listing, the same center's two permits,
a map pin and a profile), are folded into one: the Directory shows the fullest profile, in every category any of
them was in. Same name means the same letters and digits, ignoring case, punctuation, "the", "inc", "llc";
same place means the same house number and street, or, where a profile has no street address, within 400 meters. Also the same agency listed by both the city and the state.
canon(profiles) -> {slug: canonical slug}. Run as a script, it writes data/directory-duplicates.json (the groups)."""
import json, math, os, re, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAME_AGENCY = [('mta', 'nys-metropolitan-transportation-authority'), ('cuny', 'nys-city-university-of-new-york'), ('311', 'nys-nyc-311')]
def _nm(s): return re.sub(r'[^a-z0-9]', '', re.sub(r'\b(the|inc|llc|corp)\b', '', (s or '').lower().replace('&', 'and')))
def _d(a, b):
    if not (a.get('lat') and b.get('lat') and a.get('lng') and b.get('lng')): return None
    return math.hypot((a['lat'] - b['lat']) * 111000, (a['lng'] - b['lng']) * 84000)
ORDER = [('sch-', 1), ('lib-', 2), ('hosp-', 2), ('health-', 2), ('place-', 3), ('rx-', 4), ('mkt-', 4), ('cbo-', 5), ('cc-', 6), ('pk-', 7), ('swdpre-', 8), ('biz-', 9), ('liquor-', 9), ('map-', 10)]
def _rank(p):
    if p.get('kind') in ('official', 'agency') or p.get('group') in ('Community boards', 'Government agencies'): r = 0
    else: r = next((v for k, v in ORDER if p['slug'].startswith(k)), 3)
    return (r, 0 if p.get('logo') else 1, -len(' '.join(p.get('intro') or [])), p['slug'])
SUF = {'first': '1', 'second': '2', 'third': '3', 'fourth': '4', 'fifth': '5', 'sixth': '6', 'seventh': '7', 'eighth': '8', 'ninth': '9', 'tenth': '10',
       'eleventh': '11', 'twelfth': '12', 'east': 'e', 'west': 'w', 'north': 'n', 'south': 's', 'street': 'st', 'st': 'st', 'avenue': 'av', 'ave': 'av', 'av': 'av', 'boulevard': 'blvd', 'blvd': 'blvd', 'road': 'rd', 'rd': 'rd',
       'place': 'pl', 'pl': 'pl', 'parkway': 'pkwy', 'pkwy': 'pkwy', 'drive': 'dr', 'dr': 'dr', 'lane': 'ln', 'court': 'ct', 'highway': 'hwy', 'hwy': 'hwy'}
def _ak(p):
    """(house number, street) from the profile's address, or None"""
    a = (p.get('addr') or '').lower().split(',')[0]
    m = re.match(r'\s*(\d+)(?:-\d+\w*|\s+\d+/\d+)?\s+(.+)', a)
    if not m: return None
    w = [x for x in re.sub(r'[^a-z0-9 ]', ' ', m.group(2)).split() if x]
    w = [re.sub(r'^(\d+)(st|nd|rd|th)$', r'\1', x) for x in w]
    w = [SUF.get(x, x) for x in w if x not in ('fl', 'floor', 'suite', 'ste', 'apt', 'unit')]
    w = w[:4]
    if not w: return None
    return (m.group(1), ' '.join(w[:2]))
def same(a, b):
    ka, kb = _ak(a), _ak(b); d = _d(a, b)
    if ka and kb: return ka == kb
    return d is not None and d <= 400
def groups(profiles):
    by = collections.defaultdict(list)
    for p in profiles: by[_nm(p['name'])].append(p)
    out = []
    for k, v in by.items():
        if len(v) < 2 or not k: continue
        used = set()
        for i, a in enumerate(v):
            if i in used: continue
            cl = [a]
            for j in range(i + 1, len(v)):
                if j not in used and any(same(x, v[j]) for x in cl): cl.append(v[j]); used.add(j)
            if len(cl) > 1: out.append(cl)
    S = {p['slug']: p for p in profiles}
    for a, b in SAME_AGENCY:
        if a in S and b in S: out.append([S[a], S[b]])
    return out

# stores: the same storefront under a second name (a liquor license, a pharmacy license or a map pin for the same shop),
# e.g. "Royal Deli" and "Royal Supermarket" at 1419 8th Avenue. Same house number and street, and one name's words
# (leaving out words like deli, grocery, supermarket, pharmacy) are all in the other's.
GENERIC = set('and the of inc llc corp co deli grocery groceries supermarket supermarkets pharmacy drugs drug restaurant ristorante store food foods mart mini convenience brooklyn nyc ny new york'.split())
def _words(n):
    n = re.sub(r',.*', '', (n or '').lower()).replace("'", '').replace('&', ' and ')
    return {w for w in re.sub(r'[^a-z0-9 ]', ' ', n).split() if w not in GENERIC}
def _store(p): return p['slug'].startswith(('biz-', 'rx-', 'mkt-', 'liquor-', 'health-', 'map-food', 'map-biz', 'place-')) and p.get('group') in ('Local businesses', 'Food', 'Health', 'Schools, parks and facilities', 'Culture')
def store_groups(profiles, folded):
    by = collections.defaultdict(list)
    for p in profiles:
        if p['slug'] in folded or not _store(p): continue
        k = _ak(p)
        if k: by[k].append(p)
    out = []
    for k, v in by.items():
        if len(v) < 2: continue
        used = set()
        for i, a in enumerate(v):
            if i in used: continue
            cl = [a]
            for j in range(i + 1, len(v)):
                if j in used: continue
                b = v[j]; d = _d(a, b); wa, wb = _words(a['name']), _words(b['name'])
                if wa and wb and (wa <= wb or wb <= wa) and (d is None or d <= 60): cl.append(b); used.add(j)
            if len(cl) > 1: out.append(cl)
    return out
def canon(profiles):
    m = {}
    for cl in groups(profiles):
        best = min(cl, key=_rank)
        for p in cl:
            if p is not best: m[p['slug']] = best['slug']
    for cl in store_groups(profiles, m):
        best = min(cl, key=_rank)
        for p in cl:
            if p is not best: m[p['slug']] = best['slug']
    for k in list(m):   # a folded profile points at the one that is shown
        seen = {k}
        while m[k] in m and m[k] not in seen: seen.add(m[k]); m[k] = m[m[k]]
    return m
if __name__ == '__main__':
    D = json.load(open(os.path.join(ROOT, 'app/data/civic/orgs/orgs-profiles.json'), encoding='utf-8'))['profiles']
    G = groups(D); _m = {p['slug']: 1 for cl in G for p in cl if p is not min(cl, key=_rank)}; G += store_groups(D, _m)
    rows = [{'shown': min(cl, key=_rank)['slug'], 'folded': sorted(p['slug'] for p in cl if p is not min(cl, key=_rank)), 'name': cl[0]['name']} for cl in G]
    json.dump(rows, open(os.path.join(ROOT, 'data/directory-duplicates.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('groups', len(G), '| tiles folded', sum(len(r['folded']) for r in rows))
