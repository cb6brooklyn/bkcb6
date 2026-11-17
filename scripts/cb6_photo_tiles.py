#!/usr/bin/env python3
"""Photo tiles for Directory listings that show a photo of the place in place of a logo.

Each photo (Street View, or a search photo that is not a logo) gets a round badge in the corner with an
emoji for the kind of place, so the tile reads like the other icons. Real logos are left alone.
Reads data/cb6-audit/street-view.json, web-images.json and web-logos.json (search picks that are logos);
writes logos/tile-<slug>.jpg, data/cb6-audit/photo-tiles.json and sets each profile's logo."""
import json, os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

A = 'data/cb6-audit'; LOGOS = 'app/data/civic/orgs/logos'; PROF = 'app/data/civic/orgs/orgs-profiles.json'
FONT = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
EM = {'Nonprofits': '🤝', 'Restaurants, cafes and food': '🍽', 'Health and medical': '🩺', 'Services and offices': '💼',
      'Trades, workshops and industrial': '🔨', 'Stores': '🛍', 'Hair, beauty and personal care': '💇',
      'Groceries and food stores': '🛒', 'Delis and bodegas': '🥪', 'Auto and transportation': '🚗',
      'Houses of worship': '⛪', 'Smoke, vape and cannabis shops': '🚬', 'Other businesses': '🏪',
      'Hotels and tourism': '🏨', 'Gyms, yoga, Pilates and fitness': '🏋', 'Historic places': '🏛',
      'Compost and textile drop-off sites': '♻', 'Arts and culture': '🎨', 'After-school and youth programs': '🎒',
      'Community organizations': '🤝', 'Housing and community development': '🏘', 'Pharmacies': '💊',
      'Supermarkets': '🛒', 'NYCHA community centers': '🏢', 'Day camps': '⛺', 'Civic and neighborhood groups': '🤝',
      'Youth, schools and libraries': '📚', 'Human and social services': '🤝', 'Education': '🎓',
      'Hospitals and health care': '🏥', 'Fitness and recreation': '🏋', 'Senior centers and services': '🧓',
      'Community services': '🤝', 'Sports': '⚽', 'Culture and institutions': '🎭', 'Food pantries': '🥫',
      'High school equivalency programs': '🎓', 'Schools': '🏫', 'Philanthropy': '💝',
      'Legal services and justice': '⚖', 'Venues': '🎤', 'Faith organizations': '⛪', 'Health and mental health': '🩺',
      'Farmers markets': '🥕', 'Private and parochial schools': '🏫', 'Charter schools': '🏫', 'Special education schools': '🏫',
      'Public schools': '🏫', 'Preschool for students with disabilities': '🧸', 'Parks, gardens and the environment': '🌳',
      'Food and mutual aid': '🥫', 'Public safety': '🚨', 'International': '🌍', 'Jobs and workforce': '🧰',
      'Community and support': '🤝', 'Museums': '🏛'}
DEFAULT = '📍'
_f = ImageFont.truetype(FONT, 109)
_g = {}


def glyph(e, s):
    if (e, s) not in _g:
        g = Image.new('RGBA', (136, 128), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((0, 0), e, font=_f, embedded_color=True)
        bb = g.getbbox()
        g = g.crop(bb) if bb else g
        r = s / max(g.size)
        _g[(e, s)] = g.resize((max(1, round(g.width * r)), max(1, round(g.height * r))), Image.LANCZOS)
    return _g[(e, s)]


def tile(im, e):
    im = ImageEnhance.Color(im.convert('RGB').resize((256, 256), Image.LANCZOS)).enhance(1.15).convert('RGBA')
    S = 4; o = Image.new('RGBA', (256 * S, 256 * S), (0, 0, 0, 0))
    ImageDraw.Draw(o).ellipse((156 * S, 156 * S, 248 * S, 248 * S), fill='#ffffff', outline='#0d1b4b', width=5 * S)
    im.alpha_composite(o.resize((256, 256), Image.LANCZOS))
    g = glyph(e, 58)
    im.alpha_composite(g, (202 - g.width // 2, 202 - g.height // 2))
    return im.convert('RGB')


def main():
    SV = json.load(open(os.path.join(A, 'street-view.json'))); W = json.load(open(os.path.join(A, 'web-images.json')))
    WL = set(json.load(open(os.path.join(A, 'web-logos.json'))))
    D = json.load(open(PROF)); BY = {p['slug']: p for p in D['profiles']}
    src = {s: v['file'] for s, v in SV.items()}
    src.update({s: v['file'] for s, v in W.items() if s not in WL})
    out = {}; miss = []
    for s, fn in sorted(src.items()):
        p = BY.get(s); path = os.path.join(LOGOS, fn)
        if not p or not os.path.exists(path):
            miss.append(s); continue
        e = EM.get(p.get('topic'), DEFAULT)
        t = 'tile-%s.jpg' % s
        tile(Image.open(path), e).save(os.path.join(LOGOS, t), quality=88)
        p['logo'] = t; out[s] = {'file': t, 'photo': fn, 'kind': p.get('topic'), 'badge': e}
    json.dump(out, open(os.path.join(A, 'photo-tiles.json'), 'w'), indent=0, ensure_ascii=False)
    open(PROF, 'w').write(json.dumps(D, indent=1, ensure_ascii=False) + '\n')
    print(len(out), 'photo tiles;', len(WL), 'search logos left alone;', len(miss), 'missing', miss[:10])


if __name__ == '__main__':
    main()
