#!/usr/bin/env python3
"""Every block of every street in the city with the election district on each side of it, for the
"pick your block" finder on bkcb6.app/edresults/.

Source: NYC Street Centerline (CSCL), NYC Open Data inkn-q76z, streets only (rw_type 1). A block is the run of
centerline between two intersections. Each side of each block is placed in an election district by points
12 meters off the centerline at a quarter, half and three quarters of each segment, inside electionexplainer/map/eds.geojson (BOE 2026 map). Election
district lines usually run down the middle of a street, so the two sides of a block can be in different EDs.

Run: python3 scripts/build_ed_streets.py CL1.geojson CL2.geojson ...
  (download: https://data.cityofnewyork.us/resource/inkn-q76z.geojson?$where=rw_type='1'&$limit=50000&$offset=0, then 50000)
Writes data/edstreets/<1-5>.json, one file per borough.
"""
import json, math, os, re, sys
from collections import defaultdict
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TYPES = {'ST': 'Street', 'AVE': 'Avenue', 'PL': 'Place', 'RD': 'Road', 'CT': 'Court', 'LN': 'Lane', 'DR': 'Drive', 'BCH': 'Beach',
         'BLVD': 'Boulevard', 'TER': 'Terrace', 'CIR': 'Circle', 'PKWY': 'Parkway', 'SQ': 'Square', 'PLZ': 'Plaza', 'CRES': 'Crescent',
         'ALY': 'Alley', 'EXPY': 'Expressway', 'BRG': 'Bridge', 'HWY': 'Highway', 'TPKE': 'Turnpike', 'EXT': 'Extension', 'GDNS': 'Gardens',
         'HTS': 'Heights', 'PT': 'Point', 'XING': 'Crossing', 'WAY': 'Way', 'LOOP': 'Loop', 'WALK': 'Walk', 'ROW': 'Row', 'PATH': 'Path', 'SLIP': 'Slip'}
DIRS = {'E': 'East', 'W': 'West', 'N': 'North', 'S': 'South'}

def ordinal(n):
    n = int(n); s = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'); return '%d%s' % (n, s)

def pretty(label):
    t = label.split()
    out = []
    for i, w in enumerate(t):
        nxt = t[i + 1] if i + 1 < len(t) else None
        if i == 0 and w in DIRS and len(t) > 1: out.append(DIRS[w])
        elif w == 'ST' and i == 0 and len(t) > 1: out.append('St')
        elif w in TYPES and (i > 0 or len(t) > 1): out.append(TYPES[w])
        elif re.fullmatch(r'\d+', w) and nxt in TYPES: out.append(ordinal(w))
        elif re.fullmatch(r'\d+', w): out.append(w)
        elif w in ('JFK', 'LGA', 'FDR', 'MLK', 'BQE'): out.append(w)
        elif w == 'MC': out.append('Mc')
        else: out.append(w.capitalize() if len(w) > 1 else w)
    return ' '.join(out)

def hnkey(h):
    m = re.match(r'^(\d+)(?:-(\d+))?', h or '')
    return (int(m.group(1)), int(m.group(2) or 0)) if m else None

def main():
    feats = []
    for f in sys.argv[1:]: feats += json.load(open(f))['features']
    eds = json.load(open(os.path.join(ROOT, 'electionexplainer/map/eds.geojson')))['features']
    ekeys = [f['properties']['id'] for f in eds]
    epolys = [shape(f['geometry']).buffer(0) for f in eds]
    tree = STRtree(epolys)

    def ed_at(x, y):
        p = Point(x, y)
        for j in tree.query(p):
            if epolys[int(j)].contains(p): return ekeys[int(j)]
        return None

    R = lambda c: (round(c[0], 6), round(c[1], 6))
    segs = []
    for f in feats:
        p = f['properties']
        if not f.get('geometry') or p.get('status') not in ('2', None) or not p.get('stname_label'): continue
        lines = f['geometry']['coordinates'] if f['geometry']['type'] == 'MultiLineString' else [f['geometry']['coordinates']]
        pts = [c for ln in lines for c in ln]
        if len(pts) < 2: continue
        segs.append({'b': p['boroughcode'], 'n': p['stname_label'], 'pts': pts, 'a': R(pts[0]), 'z': R(pts[-1]),
                     'l': (p.get('l_low_hn'), p.get('l_high_hn')), 'r': (p.get('r_low_hn'), p.get('r_high_hn'))})
    print(len(segs), 'street segments', file=sys.stderr)

    names_at = defaultdict(set)
    for s in segs:
        names_at[(s['b'], s['a'])].add(s['n']); names_at[(s['b'], s['z'])].add(s['n'])

    def sides(s):
        """EDs on the left and right of the segment (12 m off the centerline at 1/4, 1/2 and 3/4 of its length),
        the left normal at the middle, and the middle point."""
        pts = s['pts']; k = math.cos(math.radians(pts[0][1]))
        L = [0.0]
        for i in range(1, len(pts)):
            L.append(L[-1] + math.hypot((pts[i][0] - pts[i - 1][0]) * k, pts[i][1] - pts[i - 1][1]))
        def at(frac):
            pos = L[-1] * frac; i = 1
            while i < len(pts) - 1 and L[i] < pos: i += 1
            a, b = pts[i - 1], pts[i]; seg = (L[i] - L[i - 1]) or 1e-12; t = (pos - L[i - 1]) / seg
            mx, my = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            dx, dy = (b[0] - a[0]) * k, b[1] - a[1]; d = math.hypot(dx, dy) or 1e-12
            return mx, my, -dy / d, dx / d
        off = 12 / 111320; le, re_ = [], []
        for frac in (0.25, 0.5, 0.75):
            mx, my, nx, ny = at(frac)
            for lst, sg in ((le, 1), (re_, -1)):
                e = ed_at(mx + sg * nx * off / k, my + sg * ny * off)
                if e and e not in lst: lst.append(e)
        mx, my, nx, ny = at(0.5)
        return le, re_, (nx, ny), (mx, my)

    out = {}
    bystreet = defaultdict(list)
    for i, s in enumerate(segs): bystreet[(s['b'], s['n'])].append(i)
    for (boro, name), idx in bystreet.items():
        adj = defaultdict(list)
        for i in idx: adj[segs[i]['a']].append(i); adj[segs[i]['z']].append(i)
        def stop(node): return len(names_at[(boro, node)]) > 1 or len(adj[node]) != 2
        used = set(); blocks = []
        starts = [n for n in adj if stop(n)] + list(adj)
        for n0 in starts:
            for i0 in adj[n0]:
                if i0 in used: continue
                chain = []; node = n0; i = i0
                while True:
                    used.add(i); s = segs[i]; fwd = s['a'] == node
                    chain.append((i, fwd)); node = s['z'] if fwd else s['a']
                    if stop(node) or node == n0: break
                    nxt = [j for j in adj[node] if j not in used]
                    if not nxt: break
                    i = nxt[0]
                blocks.append((n0, node, chain))
        rows = []
        for n0, n1, chain in blocks:
            sd = {'L': [], 'R': []}; hn = {'L': [], 'R': []}; nvec = None; mids = []
            for i, fwd in chain:
                s = segs[i]; le, re_, nv, mid = sides(s); mids.append(mid)
                if not fwd: le, re_, nv = re_, le, (-nv[0], -nv[1])
                lh, rh = (s['l'], s['r']) if fwd else (s['r'], s['l'])
                if nvec is None: nvec = nv
                for side, es, h in (('L', le, lh), ('R', re_, rh)):
                    for e in es:
                        if e not in sd[side]: sd[side].append(e)
                    for x in h:
                        if hnkey(x): hn[side].append(x)
            def xlabel(node):
                o = sorted(pretty(x) for x in names_at[(boro, node)] if x != name)
                return ' & '.join(o) if o else 'Dead end'
            def comp(v):
                if abs(v[0]) >= abs(v[1]): return 'East side' if v[0] > 0 else 'West side'
                return 'North side' if v[1] > 0 else 'South side'
            sl = []
            for side, v in (('L', nvec), ('R', (-nvec[0], -nvec[1]))):
                h = sorted(hn[side], key=hnkey)
                rng = ('%s to %s' % (h[0], h[-1]) if h[0] != h[-1] else h[0]) if h else ''
                par = ''
                if h:
                    odd = {hnkey(x)[1 if hnkey(x)[1] else 0] % 2 for x in h}
                    par = 'odd' if odd == {1} else 'even' if odd == {0} else ''
                sl.append([comp(v), (par + ' numbers ' + rng).strip() if rng else '', sd[side]])
            if not sl[0][2] and not sl[1][2]: continue
            m = mids[len(mids) // 2]
            rows.append([xlabel(n0), xlabel(n1), round(m[1], 5), round(m[0], 5), sl])
        if rows:
            out.setdefault(boro, {})[pretty(name)] = out.get(boro, {}).get(pretty(name), []) + rows
    os.makedirs(os.path.join(ROOT, 'data/edstreets'), exist_ok=True)
    for boro, st in out.items():
        names = sorted(st)
        data = {'src': 'NYC Street Centerline (CSCL), NYC Open Data inkn-q76z; election districts from the NYC Board of Elections 2026 map',
                'streets': names, 'blocks': [st[n] for n in names]}
        json.dump(data, open(os.path.join(ROOT, 'data/edstreets/%s.json' % boro), 'w'), separators=(',', ':'))
        print(boro, len(names), 'streets', sum(len(v) for v in st.values()), 'blocks', file=sys.stderr)

if __name__ == '__main__':
    main()
