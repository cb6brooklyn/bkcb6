#!/usr/bin/env python3
"""Share images (og:image, 1200 x 630) for every elected official's page: the official's own logo, bkcb6.app,
"Designed by Mike Racioppo" and the Download on the App Store badge. Writes og/officials/<slug>.jpg and points each
page's og:image and twitter:image at it. Pages with a share image of their own in KEEP are left alone.
Usage: python3 scripts/official_og.py"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from directory_grid import OWN_LOGO
KEEP = {'amcarroll'}
NAVY, ORANGE, WHITE = (13, 27, 75), (244, 121, 32), (255, 255, 255)
F = lambda w, s: ImageFont.truetype({'bold': 'assets/fonts/DMSans-Bold.ttf', 'mono': 'assets/fonts/DMMono-Medium.ttf'}[w], s)
badge = Image.open('appstore-badge.png').convert('RGBA')
os.makedirs('og/officials', exist_ok=True)
n = 0
for o in json.load(open('app/data/civic/officials.json')):
    slug = o['slug']; page = slug + '/index.html'
    if slug in KEEP or not os.path.exists(page): continue
    logo = OWN_LOGO.get(slug) or o.get('icon') or ''
    if not logo or not os.path.exists(logo.lstrip('/')): print('no logo', slug); continue
    im = Image.new('RGB', (1200, 630), NAVY); d = ImageDraw.Draw(im)
    d.rectangle([0, 618, 1200, 630], fill=ORANGE)
    # the logo on a white card
    card = 470; cx, cy = 70, (630 - card) // 2
    d.rounded_rectangle([cx, cy, cx + card, cy + card], radius=36, fill=WHITE)
    lg = Image.open(logo.lstrip('/')).convert('RGBA'); pad = 34
    lg.thumbnail((card - 2 * pad, card - 2 * pad), Image.LANCZOS)
    im.paste(lg, (cx + (card - lg.width) // 2, cy + (card - lg.height) // 2), lg)
    # the words and the badge
    x = cx + card + 64
    d.text((x, 170), 'bkcb6.app', font=F('bold', 92), fill=WHITE)
    d.text((x + 4, 290), 'Designed by Mike Racioppo', font=F('mono', 30), fill=(203, 213, 225))
    b = badge.copy(); bw = 330; b = b.resize((bw, round(badge.height * bw / badge.width)), Image.LANCZOS)
    im.paste(b, (x, 370), b)
    out = 'og/officials/%s.jpg' % slug
    im.save(out, quality=90)
    s = open(page, encoding='utf-8').read()
    url = 'https://bkcb6.app/' + out
    s2 = re.sub(r'(<meta property="og:image" content=")[^"]*(")', r'\g<1>' + url + r'\g<2>', s)
    s2 = re.sub(r'(<meta name="twitter:image" content=")[^"]*(")', r'\g<1>' + url + r'\g<2>', s2)
    if s2 != s: open(page, 'w', encoding='utf-8').write(s2)
    n += 1
print(n, 'share images')
