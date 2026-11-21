#!/usr/bin/env python3
"""Real logos for Directory listings that showed a Street View or search photo.

Source images (each one checked by eye against the listing name) come from the business's own website,
or else from a Bing image search; data/cb6-audit/real-logos.json records where each came from.
Every listing in photo-tiles.json with no real logo gets a plain kind icon instead of a street photo.
Writes logos/logo-<slug>.png or logos/kind-<slug>.png and sets each profile's logo."""
import json, os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from cb6_photo_tiles import EM, DEFAULT, glyph

A = 'data/cb6-audit'; LOGOS = 'app/data/civic/orgs/logos'; PROF = 'app/data/civic/orgs/orgs-profiles.json'
SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/real-logo-src'


def square(im):
    im = im.convert('RGBA')
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg.convert('RGB')
    w, h = im.size; c = im.getpixel((2, 2))
    diff = Image.new('L', im.size, 0); px = im.load(); dp = diff.load()
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            if abs(p[0]-c[0]) + abs(p[1]-c[1]) + abs(p[2]-c[2]) > 40: dp[x, y] = 255
    bb = diff.getbbox()
    if bb: im = im.crop(bb)
    side = int(max(im.size) * 1.12) + 2
    out = Image.new('RGB', (side, side), c); out.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
    out = out.resize((256, 256), Image.LANCZOS)
    return out.quantize(colors=128, method=Image.Quantize.MEDIANCUT)


def kind(e):
    S = 4; im = Image.new('RGBA', (256 * S, 256 * S), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, 256 * S - 1, 256 * S - 1), 40 * S, fill='#eef1f8')
    im = im.resize((256, 256), Image.LANCZOS)
    g = glyph(e, 120); im.alpha_composite(g, (128 - g.width // 2, 128 - g.height // 2))
    bg = Image.new('RGB', im.size, '#ffffff'); bg.paste(im, mask=im.split()[3]); return bg


def main():
    PT = json.load(open(os.path.join(A, 'photo-tiles.json'))); RL = json.load(open(os.path.join(A, 'real-logos.json')))
    D = json.load(open(PROF)); BY = {p['slug']: p for p in D['profiles']}
    n_logo = n_kind = 0; res = {}
    for s, v in sorted(PT.items()):
        p = BY.get(s)
        if not p: continue
        for f in (v.get('file'), v.get('photo')):
            if f and os.path.exists(os.path.join(LOGOS, f)): os.remove(os.path.join(LOGOS, f))
        if s in RL:
            fn = 'logo-%s.png' % s
            square(Image.open(os.path.join(SRC, s + '.png'))).save(os.path.join(LOGOS, fn), optimize=True)
            n_logo += 1; res[s] = {'file': fn, **RL[s]}
        else:
            fn = 'kind-%s.png' % s
            kind(EM.get(p.get('topic'), DEFAULT)).quantize(colors=96).save(os.path.join(LOGOS, fn), optimize=True)
            n_kind += 1; res[s] = {'file': fn, 'via': 'kind icon', 'kind': p.get('topic')}
        p['logo'] = fn
    json.dump(res, open(os.path.join(A, 'listing-images.json'), 'w'), indent=0, ensure_ascii=False)
    open(PROF, 'w').write(json.dumps(D, indent=1, ensure_ascii=False) + '\n')
    print(n_logo, 'real logos;', n_kind, 'kind icons')


if __name__ == '__main__':
    main()
