"""Per community district: every district that overlapped it since 1898 and every contest on any ballot cast in it.
Writes data/cbhistory/<c>.json for the 59 community districts. Read by throughtime/index.html?cb=<c>.
- congress: pre-2001 congressional districts (UCLA lines in data/districthistory/congress-history.json) overlapping today's
  district, by share of its land area: [[from congress, to congress, [[district, share], ...]], ...]
- cpd1968: 1968 Community Planning Districts overlapping it, by share of area.
- ballots: {election id: [contest index, ...]} for every election in data/ballots/index.json; for 2026-11-03 the
  cd/sd/ad lists and the borough key. Election-district ballots use the BOE ED-to-community-district files
  (data/edhistory/geo/ed2cd*.json); Assembly-level ballots use data/districthistory/overlap.json; 1898-1999 ballots
  take every statewide and citywide contest, the borough's contests and the congressional districts that overlapped."""
import json, os, collections
from shapely.geometry import shape
from shapely.strtree import STRtree
MIN = 0.005
cds = [f for f in json.load(open('data/cd-boundaries-lite.geojson'))['features'] if int(f['properties']['c'][1:]) <= 18]
CDG = {f['properties']['c']: shape(f['geometry']).buffer(0) for f in cds}
ov = json.load(open('data/districthistory/overlap.json'))
OVG = {}
for o in ov['offices']:
    for r in o['rows']:
        OVG[r['geo']] = r['cbs']
def shares(feats, key):
    gs = [shape(f['geometry']).buffer(0) for f in feats]
    tr = STRtree(gs)
    out = {}
    for c, g in CDG.items():
        a = g.area
        res = []
        for i in tr.query(g):
            s = gs[i].intersection(g).area / a
            if s >= MIN:
                res.append([feats[i]['properties'][key], round(s, 4)])
        out[c] = sorted(res, key=lambda x: -x[1])
    return out
ch = json.load(open('data/districthistory/congress-history.json'))
CONG = {c: [] for c in CDG}
for m in ch['maps']:
    s = shares(m['features'], 'd')
    for c in CDG:
        CONG[c].append([m['from'], m['to'], s[c]])
cpd = shares(json.load(open('data/cd1968.geojson'))['features'], 'c')
cpd = {c: [x for x in v if x[0][0] == c[0]] for c, v in cpd.items()}
idx = json.load(open('data/ballots/index.json'))
BAL = {c: {} for c in CDG}
E2C = {}
for e in idx:
    if e['k'] == 'g26':
        B = json.load(open('data/ballots/e/2026-11-03-general.json'))
        bn = {'1': 'MANHATTAN', '2': 'BRONX', '3': 'BROOKLYN', '4': 'QUEENS', '5': 'STATEN ISLAND'}
        for c in CDG:
            def ds(prefix):
                for o in ov['offices']:
                    if o['key'] == prefix:
                        return [d for d, s, p in o['rows'][-1]['cbs'].get(c, [])]
            BAL[c][e['id']] = {'cd': ds('congress'), 'sd': ds('senate'), 'ad': ds('assembly'), 'sc': bn[c[0]]}
        continue
    if e['k'] == 'm':
        B = json.load(open('data/ballots/e/%s.json' % e['id']))
        per = collections.defaultdict(set)
        if B.get('level') == 'ad':
            cbs = OVG.get(B['geo'])
            if cbs is None:
                print('no overlap for', B['geo']); continue
            for c in CDG:
                for d, s, p in cbs.get(c, []):
                    per[c].update(B['keys'].get('A%d' % int(d), []))
        else:
            rel = B['geo'].replace('geo/ed', '').replace('.topo.json', '')
            if rel not in E2C:
                E2C[rel] = json.load(open('data/edhistory/geo/ed2cd%s.json' % rel))
            m = E2C[rel]
            for k, ids in B['keys'].items():
                c = m.get(k)
                if c in CDG:
                    per[c].update(ids)
        for c in CDG:
            BAL[c][e['id']] = sorted(per[c])
        continue
    B = json.load(open('data/ballots/hist/%s.json' % e['id']))
    cong = None
    y = int(e['date'][:4]); d = e['date']
    # Congress number for the date (same rule as the page)
    if d < '1933-03-04':
        n = (y - 1789) // 2 + 1
        if (y - 1789) % 2 == 0 and d < '%d-03-04' % y: n -= 1
    elif d < '1935-01-03':
        n = 73
    else:
        n = (y - 1935) // 2 + 74
        if (y - 1935) % 2 == 0 and d < '%d-01-03' % y: n -= 1
    for c in CDG:
        dists = set()
        for f, t, s in CONG[c]:
            if f <= n <= t:
                dists = {x[0] for x in s}
        ids = []
        for i, k in enumerate(B['contests']):
            sc = k.get('scope')
            if sc in ('state', 'city') or (sc == 'boro' and str(k.get('boro')) == c[0]) or (sc == 'congress' and (k.get('district') == 0 or k.get('district') in dists)):
                ids.append(i)
        BAL[c][e['id']] = ids
os.makedirs('data/cbhistory', exist_ok=True)
for c in CDG:
    json.dump({'c': c, 'congress': CONG[c], 'cpd1968': cpd[c], 'ballots': BAL[c]}, open('data/cbhistory/%s.json' % c, 'w'), separators=(',', ':'))
print(len(CDG), 'districts;', 'CB6 1968:', cpd['306'], 'CB6 ballots with contests:', sum(1 for v in BAL['306'].values() if v))
