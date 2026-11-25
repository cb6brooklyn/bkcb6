#!/usr/bin/env python3
"""One tile per place in the Directory. Profiles that are the same place under the same name, from different sources
(a DOHMH child care permit and a DOE Pre-K site at one address, a school's Pre-K listing, the same center's two permits,
a map pin and a profile), are folded into one: the Directory shows the fullest profile, in every category any of
them was in. Same name means the same letters and digits, ignoring case, punctuation, "the", "inc", "llc";
same place means the same house number and street, or, where a profile has no street address, within 400 meters. Also the same agency listed by both the city and the state.
Also the pairs in data/directory-same-place.json: one place listed under two names (e.g. "Katsuei" and "Sushi Katsuei Inc" at
210 7th Avenue, "Lundy's" and "Lundy Bros." at 44 Beard Street), checked by hand, Nov 16, 2026.
canon(profiles) -> {slug: canonical slug}. Run as a script, it first takes the listings in data/directory-removed.json (closed,
not in the district: checked one by one) out of orgs-profiles.json and deletes their /biz/ pages, then writes
data/directory-duplicates.json (the groups)."""
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
# a synagogue and the child care center it runs are two listings
NOT_SAME = [{'biz-ae227f8f89', 'place-congregation-beth-elohim-ecc'}]
def same(a, b):
    if {a.get('slug'), b.get('slug')} in NOT_SAME: return False
    ka, kb = _ak(a), _ak(b); d = _d(a, b)
    if a.get('worship') and b.get('worship') and d is not None and d <= 150: return True   # a church listed by its corner or its rectory's address
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
SAME_F = os.path.join(ROOT, 'data/directory-same-place.json')
SAME = json.load(open(SAME_F)) if os.path.exists(SAME_F) else []
REMOVED_F = os.path.join(ROOT, 'data/directory-removed.json')
REMOVED = json.load(open(REMOVED_F, encoding='utf-8')) if os.path.exists(REMOVED_F) else {}
def same_groups(profiles):
    """the hand-checked pairs, joined into groups (a place listed three ways is one group)"""
    S = {p['slug']: p for p in profiles}; up = {}
    def f(x):
        while up.get(x, x) != x: x = up[x]
        return x
    for a, b in SAME:
        if a in S and b in S: up[f(a)] = f(b)
    g = collections.defaultdict(list)
    for s in {x for pr in SAME for x in pr if x in S}: g[f(s)].append(S[s])
    return [v for v in g.values() if len(v) > 1]
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
    # the hand-checked pairs: each group (with whatever its members were already folded with) shows its fullest profile
    S = {p['slug']: p for p in profiles}
    for cl in same_groups(profiles):
        top = {m.get(p['slug'], p['slug']) for p in cl}
        members = {s for s in top} | {k for k, v in m.items() if v in top} | {p['slug'] for p in cl}
        # a map listing of a public place (a firehouse, a school) shows over the same place's business-directory entry
        best = min((S[s] for s in members if s in S), key=lambda p: (p['slug'].startswith('biz-') and p.get('group') == 'Local businesses', _rank(p)))['slug']
        for s in members:
            if s != best: m[s] = best
        m.pop(best, None)
    for k in list(m):   # a folded profile points at the one that is shown
        seen = {k}
        while m[k] in m and m[k] not in seen: seen.add(m[k]); m[k] = m[m[k]]
    for pr in NOT_SAME:
        for x in pr:
            if m.get(x) in pr: m.pop(x)
    return m
if __name__ == '__main__':
    pf = os.path.join(ROOT, 'app/data/civic/orgs/orgs-profiles.json'); DD = json.load(open(pf, encoding='utf-8'))
    gone = [p for p in DD['profiles'] if p['slug'] in REMOVED]
    if gone:
        for p in gone:
            for _, u in p.get('links') or []:
                if u.startswith('https://bkcb6.app/biz/') and os.path.exists(os.path.join(ROOT, u[len('https://bkcb6.app/'):])): os.remove(os.path.join(ROOT, u[len('https://bkcb6.app/'):]))
        DD['profiles'] = [p for p in DD['profiles'] if p['slug'] not in REMOVED]
        open(pf, 'w', encoding='utf-8').write(json.dumps(DD, ensure_ascii=False, indent=1) + '\n')
        rp = os.path.join(ROOT, 'data/cb6-audit/reg-pages.json')
        if os.path.exists(rp):
            RP = json.load(open(rp)); json.dump({k: v for k, v in RP.items() if k not in REMOVED}, open(rp, 'w'), indent=0)
    print('removed', len(gone), [p['name'] for p in gone])
    D = DD['profiles']
    G = groups(D); _m = {p['slug']: 1 for cl in G for p in cl if p is not min(cl, key=_rank)}; G += store_groups(D, _m); G += same_groups(D)
    rows = [{'shown': min(cl, key=_rank)['slug'], 'folded': sorted(p['slug'] for p in cl if p is not min(cl, key=_rank)), 'name': cl[0]['name']} for cl in G]
    json.dump(rows, open(os.path.join(ROOT, 'data/directory-duplicates.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('groups', len(G), '| tiles folded', len(canon(D)))
