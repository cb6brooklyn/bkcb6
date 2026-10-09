"""The BID profile pages in the apps' Organizations tab: each BID's logo, a map of the district (the BID in orange, Community
Board 6's line in navy, the directory's businesses as dots) as the page's first card, and the directory of every business
inside the district from the CB6 business directory (civic/business/business-cb6.json) in the page's details. The proposed
Gowanus BID covers the Gowanus rezoning area.
Writes civic/orgs/logos/*.png, civic/orgs/going/bid-*.png and the profiles in civic/orgs/orgs-profiles.json."""
import json, os
from PIL import Image
from shapely.geometry import shape, Point, LineString, box
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from math import cos, radians

C = 'app/data/civic'
P = f'{C}/orgs/orgs-profiles.json'
font_manager.fontManager.addfont('assets/fonts/DMSans-Bold.ttf')
plt.rcParams['font.family'] = 'DM Sans'
NAVY, ORANGE, INK = '#06024d', '#f47920', '#14141c'

# logos
LOGOS = {'atlanticavebid.png': 'site-icons/bid-atlantic-avenue.png', 'northflatbushbid.png': 'site-icons/bid-north-flatbush.png',
         'gowanusbid.png': 'gowanus-bid.png'}
for out, src in LOGOS.items():
    im = Image.open(src).convert('RGBA'); im.thumbnail((400, 400)); im.save(f'{C}/orgs/logos/{out}', optimize=True)

bids = {f['properties']['name']: shape(f['geometry']) for f in json.load(open(f'{C}/bids.geojson'))['features']}
cb6 = shape(json.load(open('data/cb6_boundary.geojson'))['features'][0]['geometry'])
base = json.load(open(f'{C}/basemap/cb6-basemap.json'))
rows = json.load(open(f'{C}/business/business-cb6.json'))['rows']  # name, category, kind, address, nb, lat, lng, ...
SHORT = {'Bar or restaurant (liquor license)': 'Bar or restaurant', 'Restaurants and cafes': 'Restaurant or cafe',
         'Health and medical': 'Health', 'Offices and professional': 'Office', 'Home, goods and general retail': 'Retail',
         'Hair, beauty and personal care': 'Hair and beauty', 'Groceries and food shops': 'Food shop', 'Food stores': 'Food store',
         'Fitness and recreation': 'Fitness', 'Trades and workshops': 'Trades', 'Clothing, shoes and jewelry': 'Clothing',
         'Auto and transportation': 'Auto', 'Food stores with beer or liquor license': 'Food store', 'Other businesses': 'Other',
         'Grocery beer license': 'Grocery', 'Wholesale or temporary liquor license': 'Liquor license', 'Liquor or wine store': 'Wine and liquor',
         'Bars and nightlife': 'Bar', 'Warehouses, logistics and industrial': 'Industrial', 'Hotels and tourism': 'Hotel',
         'Hardware stores': 'Hardware', 'Brewery, distillery, winery': 'Brewery', 'Government offices': 'Government', 'Services': 'Services'}

def inside(g):
    gb = g.buffer(0.00018)  # about 20 m, for addresses placed at the curb
    return [r for r in rows if gb.contains(Point(r[6], r[5]))]

def draw(name, area, pts, out, pad=0.0028):
    x0, y0, x1, y1 = area.bounds
    k = cos(radians((y0 + y1) / 2))
    x0, x1, y0, y1 = x0 - pad / k, x1 + pad / k, y0 - pad, y1 + pad
    w, h = (x1 - x0) * k, (y1 - y0)
    if w / h < 1.25: cx = (x0 + x1) / 2; half = 1.25 * h / k / 2; x0, x1 = cx - half, cx + half; w = (x1 - x0) * k
    if w / h > 1.8: cy = (y0 + y1) / 2; half = w / 1.8 / 2; y0, y1 = cy - half, cy + half; h = y1 - y0
    fig = plt.figure(figsize=(12, 12 * h / w), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect(1 / k); ax.axis('off')
    fig.patch.set_facecolor('#cfdde6')
    for poly in base['land']:
        ax.fill([p[0] for p in poly], [p[1] for p in poly], color='#f4f2ec', lw=0, zorder=1)
    view = box(x0, y0, x1, y1)
    for s in base['streets']:
        l = s['l']
        if not LineString(l).intersects(view): continue
        ax.plot([p[0] for p in l], [p[1] for p in l], color='#ffffff', lw={1: 5.5, 2: 4, 3: 2.6}.get(s.get('c', 3), 2.2), solid_capstyle='round', zorder=2)
        ax.plot([p[0] for p in l], [p[1] for p in l], color='#dcd8cf', lw=0.6, zorder=2.1)
    for g in (area.geoms if hasattr(area, 'geoms') else [area]):
        xs, ys = g.exterior.xy
        if name: ax.fill(xs, ys, color=ORANGE, alpha=0.28, lw=0, zorder=3)
        ax.plot(xs, ys, color=ORANGE, lw=2.4 if name else 0, zorder=4)
    for g in (cb6.geoms if hasattr(cb6, 'geoms') else [cb6]):
        xs, ys = g.exterior.xy; ax.plot(xs, ys, color=NAVY, lw=2.2, ls=(0, (6, 3)), zorder=5)
    if pts: ax.scatter([r[6] for r in pts], [r[5] for r in pts], s=16, color=NAVY, edgecolor='white', linewidth=0.6, zorder=6)
    used = []
    for lb in base['labels']:
        x, y = lb['p']
        if not (x0 < x < x1 and y0 < y < y1) or lb.get('c', 3) > 3: continue
        if any(abs(x - u[0]) * k < 0.0016 and abs(y - u[1]) < 0.0016 for u in used): continue
        used.append((x, y))
        ax.text(x, y, lb['n'], rotation=lb.get('a', 0), rotation_mode='anchor', ha='center', va='center', fontsize=10, color='#55575f', zorder=7,
                bbox=dict(facecolor='#ffffff', alpha=0.75, lw=0, pad=0.6))
    fig.savefig(out, dpi=100); plt.close(fig)
    im = Image.open(out).convert('RGB'); im.save(out, optimize=True)

def directory(pts):
    pts = sorted(pts, key=lambda r: (SHORT.get(r[1], r[1] or 'Other'), r[0].lower()))
    return [[SHORT.get(r[1], r[1] or 'Other'), f'{r[0]} · {r[3]}' if r[3] else r[0]] for r in pts]

PAGES = {'park-slope-fifth-avenue-bid': 'Park Slope 5th Avenue', 'atlantic-avenue-bid': 'Atlantic Avenue', 'north-flatbush-bid': 'North Flatbush'}
LOGO = {'atlantic-avenue-bid': 'atlanticavebid.png', 'north-flatbush-bid': 'northflatbushbid.png', 'gowanus-bid-formation-effort': 'gowanusbid.png'}
d = json.load(open(P))
for p in d['profiles']:
    s = p['slug']
    if s in LOGO: p['logo'] = LOGO[s]
    if s in PAGES:
        g = bids[PAGES[s]]; pts = inside(g); img = f'bid-{s}.png'
        draw(True, g, pts, f'{C}/orgs/going/{img}')
        p['going'] = [{'img': img, 'kicker': 'The district', 'title': f"{p['name']}: where it is",
                       'text': f"Orange: the BID. Dashed navy line: Community Board 6. Dots: the {len(pts)} businesses in the CB6 business directory inside the BID, listed under Details.",
                       'until': '', 'btns': []}]
        p['kv'] = [['Community board', 'Brooklyn Community Board 6'], ['Businesses', f'{len(pts)} in the CB6 business directory inside the BID, below']] + directory(pts)
    if s == 'gowanus-bid-formation-effort':
        # the proposed BID covers the Gowanus rezoning area (data/gowanus_rezoning_boundary.geojson)
        g = shape(json.load(open('data/gowanus_rezoning_boundary.geojson'))['features'][0]['geometry']); pts = inside(g)
        img = f'bid-{s}.png'
        draw(True, g, pts, f'{C}/orgs/going/{img}', pad=0.0015)
        p['going'] = [{'img': img, 'kicker': 'The district', 'title': 'The proposed Gowanus BID: where it is',
                       'text': f"Orange: the proposed BID, the same as the Gowanus rezoning area. Dashed navy line: Community Board 6. Dots: the {len(pts)} businesses in the CB6 business directory inside it, listed under Details.",
                       'until': '', 'btns': []}]
        p['kv'] = [['Community board', 'Brooklyn Community Board 6'], ['Businesses', f'{len(pts)} in the CB6 business directory inside the proposed BID, below']] + directory(pts)
    if s in PAGES or s == 'gowanus-bid-formation-effort':
        print(s, p['logo'], len(p['kv']) - 2, 'businesses')
json.dump(d, open(P, 'w'), ensure_ascii=False, indent=1)
