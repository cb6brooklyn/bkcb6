"""CB6 trees map data: street trees (NYC Parks Forestry Tree Points, hn5i-inap), tree canopy 2010 and 2017
(NYC Tree Canopy Change 2010-2017, by9k-vhck, the LiDAR-based data New Yorkers for Parks uses), block pruning cycles
(from treepruning/pruning.json). Writes trees/data.json and canopy tiles trees/canopy/{z}/{x}/{y}.png.
Usage: python3 build.py <work dir with tp.json and canopy_cb6area.pkl>"""
import sys, json, pickle, math, os, collections as C, datetime, numpy as np, shapely
from shapely.geometry import shape, mapping
from pyproj import Transformer
from PIL import Image, ImageDraw
W = sys.argv[1]; R = '/root/bkcb6'
F = Transformer.from_crs(4326, 2263, always_xy=True); Bk = Transformer.from_crs(2263, 4326, always_xy=True)
to2263 = lambda g: shapely.transform(g, lambda xy: np.column_stack(F.transform(xy[:, 0], xy[:, 1])))
to4326 = lambda g: shapely.transform(g, lambda xy: np.column_stack(Bk.transform(xy[:, 0], xy[:, 1])))
gj = json.load(open(R + '/cb6_boundary.geojson')); cb4 = shape(gj['features'][0]['geometry'] if 'features' in gj else gj['geometry']); cb = to2263(cb4)
# ---- canopy fragments inside CB6
geom, fields = pickle.load(open(W + '/canopy_cb6area.pkl', 'rb'))
G = shapely.from_wkb(geom); cls = np.array(fields[0])
idx = shapely.STRtree(G).query(cb, predicate='intersects'); inter = shapely.intersection(G[idx], cb); ccl = cls[idx]
keep = ~shapely.is_empty(inter); inter = inter[keep]; ccl = ccl[keep]
area = shapely.area(inter); A = cb.area
tot = {k: float(area[ccl == k].sum() / A * 100) for k in ['No Change', 'Gain', 'Loss']}
# ---- blocks and their share of canopy (each 10-foot cell goes to its nearest block, so blocks include their half of the streets)
B = json.load(open(R + '/sanitation-policy/cb6-blocks.geojson'))['features']
BP = np.array([to2263(shape(f['geometry'])) for f in B])
x0, y0, x1, y1 = cb.bounds; s = 10
X, Y = np.meshgrid(np.arange(x0, x1, s) + s / 2, np.arange(y0, y1, s) + s / 2); X = X.ravel(); Y = Y.ravel()
m = shapely.contains_xy(cb, X, Y); X = X[m]; Y = Y[m]; P = shapely.points(X, Y)
nr = shapely.STRtree(BP).query_nearest(P, all_matches=False); nb = np.full(len(P), -1); nb[nr[0]] = nr[1]
hit = shapely.STRtree(inter).query(P, predicate='within'); cc = np.full(len(P), '', dtype=object); cc[hit[0]] = ccl[hit[1]]
# ---- street trees
T = json.load(open(W + '/tp.json'))
COND = ['Excellent', 'Good', 'Fair', 'Poor', 'Critical', 'Dead', 'Unknown']
trees = []
for r in T:
    if r.get('tpstructure') != 'Full' or not r.get('location'): continue
    lon, lat = r['location']['coordinates']
    if not shapely.contains_xy(cb4, lon, lat): continue
    sp = (r.get('genusspecies') or 'Unknown').split(' - ')
    trees.append(dict(lat=lat, lon=lon, dbh=int(float(r.get('dbh') or 0)), cond=r.get('tpcondition') or 'Unknown', sp=sp[-1].strip() if len(sp) > 1 else sp[0], lat_name=sp[0].strip(),
                      yr=(r.get('planteddate') or '')[:4]))
SP = [k for k, _ in C.Counter(t['sp'] for t in trees).most_common()]
tx, ty = F.transform([t['lon'] for t in trees], [t['lat'] for t in trees])
tn = shapely.STRtree(BP).query_nearest(shapely.points(tx, ty), all_matches=False); tb = np.full(len(trees), -1); tb[tn[0]] = tn[1]
blocks = []
for i, f in enumerate(B):
    mm = nb == i; n = int(mm.sum())
    if not n: continue
    k = cc[mm]; nc = int((k == 'No Change').sum()); g = int((k == 'Gain').sum()); l = int((k == 'Loss').sum())
    bt = [trees[j] for j in np.where(tb == i)[0]]
    p = f['properties']
    blocks.append(dict(id=p['b'], names=p.get('names'), c=p['c'], g=f['geometry'], c17=round(100 * (nc + g) / n, 1), c10=round(100 * (nc + l) / n, 1),
                       gain=round(100 * g / n, 1), loss=round(100 * l / n, 1), acres=round(n * s * s / 43560, 2), trees=len(bt),
                       dead=sum(t['cond'] == 'Dead' for t in bt), dbh=round(sum(t['dbh'] for t in bt) / len(bt), 1) if bt else None))
# ---- pruning cycle
PR = json.load(open(R + '/treepruning/pruning.json'))
segs = [dict(ln=sg['ln'], n=sg['n'], hn=sg['hn'], last=sg['last']) for sg in PR['segments']]
out = dict(built=str(datetime.date.today()), prunBuilt=PR['built'], cond=COND, sp=SP,
    trees=[[round(t['lat'], 6), round(t['lon'], 6), t['dbh'], COND.index(t['cond']) if t['cond'] in COND else 6, SP.index(t['sp']), t['yr']] for t in trees],
    canopy=dict(c17=round(tot['No Change'] + tot['Gain'], 1), c10=round(tot['No Change'] + tot['Loss'], 1), gain=round(tot['Gain'], 1), loss=round(tot['Loss'], 1),
                acres17=round((area[ccl == 'No Change'].sum() + area[ccl == 'Gain'].sum()) / 43560, 1), acres=round(A / 43560, 1)),
    blocks=blocks, segs=segs)
os.makedirs(R + '/trees', exist_ok=True)
json.dump(out, open(R + '/trees/data.json', 'w'), separators=(',', ':'))
print('trees', len(trees), 'blocks', len(blocks), 'canopy', out['canopy'], os.path.getsize(R + '/trees/data.json') // 1024, 'KB')
# ---- canopy tiles
inter4 = to4326(inter)
COL = {'No Change': (46, 125, 50, 200), 'Gain': (124, 179, 66, 215), 'Loss': (229, 57, 53, 215)}
def lonlat2px(lon, lat, z):
    n = 256 * 2 ** z; x = (lon + 180) / 360 * n; y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n; return x, y
lo0, la0, lo1, la1 = cb4.bounds; cnt = 0
tree4 = shapely.STRtree(inter4)
for z in range(13, 19):
    X0, Y1 = lonlat2px(lo0, la0, z); X1, Y0 = lonlat2px(lo1, la1, z)
    simp = shapely.simplify(inter4, 0.000002 * 2 ** (18 - z))
    for tx_ in range(int(X0 // 256), int(X1 // 256) + 1):
        for ty_ in range(int(Y0 // 256), int(Y1 // 256) + 1):
            # tile bounds in lon/lat
            n = 2 ** z; tlo0 = tx_ / n * 360 - 180; tlo1 = (tx_ + 1) / n * 360 - 180
            tla0 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (ty_ + 1) / n)))); tla1 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * ty_ / n))))
            q = tree4.query(shapely.box(tlo0, tla0, tlo1, tla1))
            if not len(q): continue
            im = Image.new('RGBA', (512, 512), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            for kk in ['No Change', 'Gain', 'Loss']:
                for j in q[ccl[q] == kk]:
                    gg = simp[j]
                    for poly in getattr(gg, 'geoms', [gg]):
                        if poly.is_empty or poly.geom_type != 'Polygon': continue
                        pts = [((lonlat2px(a, b, z)[0] - tx_ * 256) * 2, (lonlat2px(a, b, z)[1] - ty_ * 256) * 2) for a, b in poly.exterior.coords]
                        if len(pts) > 2: d.polygon(pts, fill=COL[kk])
                        for h in poly.interiors:
                            hp = [((lonlat2px(a, b, z)[0] - tx_ * 256) * 2, (lonlat2px(a, b, z)[1] - ty_ * 256) * 2) for a, b in h.coords]
                            if len(hp) > 2: d.polygon(hp, fill=(0, 0, 0, 0))
            p = f'{R}/trees/canopy/{z}/{tx_}'; os.makedirs(p, exist_ok=True); im.save(f'{p}/{ty_}.png', optimize=True); cnt += 1
    print('z', z, cnt)
