#!/usr/bin/env python3
"""Puts the logos and photos gathered for the BID businesses (data/bid-audit/shots/: <slug>.png logo screenshots from
the business's own website, <slug>.og share images from its site, <slug>.photo photos of the business found on the web;
results.json says where each came from) onto their Directory profiles: squared to 256 pixels and saved as
app/data/civic/orgs/logos/shot-<slug>.png. A logo screenshot keeps the page's own background around it; a photo is
cropped to its center. Rerunnable; run before app_directory_tiles.py and bid_maps.py."""
import json, os, sys
from PIL import Image, ImageChops, ImageStat
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
S = 'data/bid-audit/shots'
R = json.load(open(os.path.join(S, 'results.json')))
D = json.load(open('app/data/civic/orgs/orgs-profiles.json', encoding='utf-8'))
BY = {p['slug']: p for p in D['profiles']}
for p in D['profiles']:   # this script's own images are placed again each run
    if (p.get('logo') or '').startswith('shot-'): p['logo'] = ''
def corner_bg(im):
    w, h = im.size
    px = [im.getpixel((x, y)) for x, y in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2))]
    return max(set(px), key=px.count)
def logo_sq(im):
    im = im.convert('RGB'); bg = corner_bg(im)
    bb = ImageChops.difference(im, Image.new('RGB', im.size, bg)).point(lambda v: 255 if v > 24 else 0).getbbox()
    if not bb: return None
    im = im.crop(bb); w, h = im.size
    if max(w, h) < 40 or min(w, h) < 12: return None
    s = int(max(w, h) * 1.14); c = Image.new('RGB', (s, s), bg); c.paste(im, ((s - w) // 2, (s - h) // 2))
    return c.resize((256, 256), Image.LANCZOS)
def photo_sq(im):
    im = im.convert('RGB'); w, h = im.size
    if min(w, h) < 120: return None
    s = min(w, h); x, y = (w - s) // 2, (h - s) // 2
    return im.crop((x, y, x + s, y + s)).resize((256, 256), Image.LANCZOS)
n = {'logo': 0, 'photo': 0, 'unusable': 0}
for slug, r in R.items():
    if slug not in BY or r.get('kind') not in ('logo', 'photo', 'webphoto'): continue
    src = os.path.join(S, slug + {'logo': '.png', 'photo': '.og', 'webphoto': '.photo'}[r['kind']])
    if not os.path.exists(src): continue
    try: im = Image.open(src)
    except Exception: n['unusable'] += 1; continue
    out = logo_sq(im) if r['kind'] == 'logo' else photo_sq(im)
    if out is None or max(ImageStat.Stat(out).stddev) < 6: n['unusable'] += 1; r['used'] = False; continue
    fn = 'shot-%s.png' % slug
    out.save(os.path.join('app/data/civic/orgs/logos', fn), optimize=True)
    BY[slug]['logo'] = fn; r['used'] = True
    n['logo' if r['kind'] == 'logo' else 'photo'] += 1
json.dump(R, open(os.path.join(S, 'results.json'), 'w'), indent=0)
open('app/data/civic/orgs/orgs-profiles.json', 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print(n)
