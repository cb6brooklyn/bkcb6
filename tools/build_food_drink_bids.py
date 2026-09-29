"""Cut the Brooklyn food-drink district files down to each CB6 BID boundary.

Writes data/food-drink/bid-<slug>.json with the boundary and every place inside it,
across every community district the BID touches. Each place gets:
  nb  neighborhood, from data/city-neighborhoods.geojson
  blk block, "Street, Cross A to Cross B", from the DCP street centerline
      (NYC Open Data inkn-q76z), matched to the business's own street when
      its address names one, otherwise the nearest street in the BID.
"""
import json, glob, re, urllib.request, urllib.parse, math
from shapely.geometry import shape, Point, LineString, mapping
from shapely.strtree import STRtree

SLUGS = ['park-slope-5th-avenue', 'north-flatbush', 'atlantic-avenue']
bids = {f['properties']['slug']: f for f in json.load(open('data/bids.geojson'))['features']}
files = sorted(glob.glob('data/food-drink/cb*.json')) + ['data/food-drink/navyyard.json']
src = {fn: json.load(open(fn))['items'] for fn in files}

NB = [(f['properties']['nb'], shape(f['geometry']).buffer(0))
      for f in json.load(open('data/city-neighborhoods.geojson'))['features']
      if f['properties'].get('boro') == 'Brooklyn']

def nb_of(pt):
    for n, g in NB:
        if g.contains(pt): return n
    best = min(NB, key=lambda x: x[1].distance(pt))
    return best[0]

ABBR = {'AVENUE': 'AVE', 'AVE': 'AVE', 'AV': 'AVE', 'STREET': 'ST', 'ST': 'ST', 'PLACE': 'PL', 'PL': 'PL',
        'ROAD': 'RD', 'BOULEVARD': 'BLVD', 'BLVD': 'BLVD', 'PLAZA': 'PLZ', 'LANE': 'LN', 'TERRACE': 'TER'}
ORD = {'FIRST': '1', 'SECOND': '2', 'THIRD': '3', 'FOURTH': '4', 'FIFTH': '5', 'SIXTH': '6', 'SEVENTH': '7', 'EIGHTH': '8', 'NINTH': '9'}

def norm(s):
    s = (s or '').upper().replace('.', ' ')
    s = re.sub(r'\b(\d+)(ST|ND|RD|TH)\b', r'\1', s)
    w = [ORD.get(x, ABBR.get(x, x)) for x in s.split()]
    return ' '.join(w)

def addr_street(a):
    m = re.match(r'^\s*[\d\-A-Z]*\d[\dA-Z\-]*\s+(.+)$', (a or '').upper())
    return norm(m.group(1)) if m else ''

FULL = {'AVE': 'Avenue', 'AV': 'Avenue', 'ST': 'Street', 'PL': 'Place', 'RD': 'Road', 'BLVD': 'Boulevard',
        'PLZ': 'Plaza', 'LN': 'Lane', 'TER': 'Terrace', 'CT': 'Court', 'DR': 'Drive', 'PKWY': 'Parkway',
        'E': 'East', 'W': 'West', 'N': 'North', 'S': 'South'}
def ordinal(n):
    n = int(n)
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
def title(s):
    w = s.upper().split()
    out = []
    for i, x in enumerate(w):
        if x.isdigit(): out.append(ordinal(x))
        elif x in FULL and i > 0: out.append(FULL[x])
        elif x == 'ST' and i == 0: out.append('St.')
        else: out.append(x.capitalize())
    return ' '.join(out)

def centerline(bbox):
    w, s, e, n = bbox
    where = f"within_box(the_geom,{n},{w},{s},{e})"
    url = 'https://data.cityofnewyork.us/resource/inkn-q76z.json?' + urllib.parse.urlencode(
        {'$where': where, '$limit': 50000,
         '$select': 'the_geom,full_street_name,stname_label,rw_type,segment_type,physicalid'})
    rows = json.load(urllib.request.urlopen(url, timeout=120))
    segs = []
    for r in rows:
        g = r.get('the_geom')
        name = r.get('stname_label') or r.get('full_street_name')
        if not g or not name: continue
        if str(r.get('rw_type')) != '1': continue
        lines = g['coordinates'] if g['type'] == 'MultiLineString' else [g['coordinates']]
        for c in lines:
            if len(c) > 1: segs.append((name, LineString(c)))
    return segs

def key(c): return (round(c[0], 5), round(c[1], 5))

def build_blocks(segs):
    """For every segment, find the cross streets bounding the run of same-street
    segments it sits in. Returns list of (name, geom, cross_a, cross_b)."""
    at = {}
    for i, (n, g) in enumerate(segs):
        for c in (g.coords[0], g.coords[-1]):
            at.setdefault(key(c), []).append(i)
    def cross_at(k, name):
        return sorted({segs[j][0] for j in at.get(k, []) if norm(segs[j][0]) != norm(name)})
    def walk(i, end):
        name = segs[i][0]; seen = {i}; cur = i; k = key(segs[i][1].coords[end])
        for _ in range(60):
            cs = cross_at(k, name)
            if cs: return cs
            nxt = [j for j in at.get(k, []) if j not in seen and norm(segs[j][0]) == norm(name)]
            if not nxt: return []
            cur = nxt[0]; seen.add(cur)
            g = segs[cur][1]
            k = key(g.coords[-1]) if key(g.coords[0]) == k else key(g.coords[0])
        return []
    out = []
    for i, (n, g) in enumerate(segs):
        out.append((n, g, walk(i, 0), walk(i, -1)))
    return out

def label(n, a, b):
    A = title(a[0]) if a else None; B = title(b[0]) if b else None
    if A and B and A != B:
        # order cross streets consistently so both halves of a block read the same
        A, B = sorted([A, B], key=lambda s: [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', s)])
        return f"{title(n)}, {A} to {B}"
    if A or B: return f"{title(n)} at {A or B}"
    return title(n)

for s in SLUGS:
    f = bids[s]; poly = shape(f['geometry']).buffer(0)
    out, seen = [], set()
    for fn, items in src.items():
        for p in items:
            if p.get('lat') and p.get('lng') and poly.contains(Point(p['lng'], p['lat'])):
                k = (p.get('name'), p.get('address'), p.get('t'))
                if k in seen: continue
                seen.add(k); out.append(dict(p))
    w, so, e, n = poly.bounds
    pad = 0.004
    segs = centerline((w - pad, so - pad, e + pad, n + pad))
    blocks = build_blocks(segs)
    near = poly.buffer(0.0003)
    blocks = [b for b in blocks if b[1].intersects(near)]
    tree = STRtree([b[1] for b in blocks])
    # main street = the street with the most length inside the BID; blocks ordered along it
    ln = {}
    for b in blocks: ln[norm(b[0])] = ln.get(norm(b[0]), 0) + b[1].intersection(near).length
    main = max(ln, key=ln.get)
    mains = [b[1] for b in blocks if norm(b[0]) == main]
    xs = [c for g in mains for c in g.coords]
    lat0 = sum(c[1] for c in xs) / len(xs); kx = math.cos(math.radians(lat0))
    mx = sum(c[0] for c in xs) / len(xs); my = lat0
    sxx = sum(((c[0]-mx)*kx)**2 for c in xs); syy = sum((c[1]-my)**2 for c in xs); sxy = sum((c[0]-mx)*kx*(c[1]-my) for c in xs)
    ang = 0.5 * math.atan2(2*sxy, sxx - syy); ux, uy = math.cos(ang), math.sin(ang)
    if uy < 0: ux, uy = -ux, -uy          # north first
    def along(pt): return (pt.x - mx) * kx * ux + (pt.y - my) * uy
    for p in out:
        pt = Point(p['lng'], p['lat'])
        p['nb'] = nb_of(pt)
        st = addr_street(p.get('address'))
        cand = [blocks[i] for i in tree.query(pt.buffer(0.0025))]
        same = [b for b in cand if st and norm(b[0]) == st]
        pool = same or cand or blocks
        b = min(pool, key=lambda b: b[1].distance(pt))
        p['blk'] = label(b[0], b[2], b[3])
        p['bo'] = round(-along(b[1].interpolate(0.5, normalized=True)) * 1e5) + (0 if norm(b[0]) == main else 10**7)
    doc = {'slug': s, 'name': f['properties']['name'], 'cds': f['properties']['cds'],
           'geometry': mapping(shape(f['geometry'])), 'items': out}
    json.dump(doc, open(f'data/food-drink/bid-{s}.json', 'w'), separators=(',', ':'))
    nbs = {}
    for p in out: nbs.setdefault(p['nb'], set()).add(p['blk'])
    print(s, len(out), 'places;', {k: len(v) for k, v in nbs.items()})
