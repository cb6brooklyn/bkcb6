"""The BMT site outline from the tax lots: Block 281 Lot 1 (Piers 7 to 10, 70 Columbia Street) and Block 515 Lot 61
(Piers 11 and 12 and the Atlantic Basin, 118 Conover Street), both Port Authority lots in the CB6 lots file, with the
slips between the piers closed, as the Vision Plan draws the site. Writes a [lat, lon] ring for projects.json and a plot."""
import json, gzip, sys, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon, shape
from shapely.ops import unary_union
R = '/home/claude/bkcb6'
d = json.load(gzip.open(R + '/app/data/civic/lots/306.json.gz'))
idx = {r[0]: i for i, r in enumerate(d['lots'])}
LOTS = ['3002810001', '3005150061']
K = math.cos(math.radians(40.687))
def proj(ring): return [(x * K, y) for x, y in ring]
def unproj(ring): return [(x / K, y) for x, y in ring]
polys = []
for b in LOTS:
    for ring in d['geo'][idx[b]]:
        p = Polygon(proj(ring))
        if p.is_valid and p.area > 0: polys.append(p)
u = unary_union(polys)
# close the slips between the pier fingers (about 90 m), then take the outline back
m = 90 / 111320.0
c = u.buffer(m, join_style=2).buffer(-m, join_style=2)
if isinstance(c, MultiPolygon):
    # the two lots meet at the mouth of the basin by Hamilton Avenue: join them across the gap
    from shapely.ops import nearest_points
    from shapely.geometry import LineString
    parts = sorted(c.geoms, key=lambda g: -g.area)
    print('parts', len(parts), 'gap m', round(parts[0].distance(parts[1]) * 111320, 1))
    a, b2 = nearest_points(parts[0], parts[1])
    c = unary_union([c, LineString([a, b2]).buffer(30 / 111320.0, cap_style=3, join_style=2)])
    if isinstance(c, MultiPolygon): c = max(c.geoms, key=lambda g: g.area)
c = Polygon(c.exterior).simplify(4 / 111320.0)
ring = unproj(list(c.exterior.coords))
site = [[round(y, 5), round(x, 5)] for x, y in ring]
json.dump(site, open(sys.argv[1], 'w'))
print(len(site), 'points; area acres', round(c.area * 111320 * 111320 / 4046.86, 1))
fig, ax = plt.subplots(figsize=(9, 9))
b = json.load(open(R + '/data/cb6_boundary.geojson'))
for f in b['features'] if 'features' in b else [b]:
    g = shape(f['geometry'])
    for p in (g.geoms if hasattr(g, 'geoms') else [g]):
        x, y = p.exterior.xy; ax.plot(x, y, color='navy', lw=1)
for r, g in zip(d['lots'], d['geo']):
    lat, lon = r[-2], r[-1]
    if not (40.678 < lat < 40.695 and -74.02 < lon < -73.998): continue
    for rg in g:
        try: p = Polygon(rg)
        except Exception: continue
        x, y = p.exterior.xy; ax.fill(x, y, color='#ddd', alpha=0.5, lw=0.3, ec='#888')
xs = [p[1] for p in site]; ys = [p[0] for p in site]
ax.fill(xs, ys, color='orange', alpha=0.35, ec='darkorange', lw=2)
ax.set_xlim(-74.02, -73.998); ax.set_ylim(40.678, 40.695); ax.set_aspect(1 / K)
fig.savefig(sys.argv[2], dpi=100, bbox_inches='tight')
