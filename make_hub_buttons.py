#!/usr/bin/env python3
"""
Builds a button image for every destination in the Parks Hub and Education Hub.

Nothing here is typed by hand. The labels and links come from jobs.json, which
was read out of the rendered hubs, and each window is a screenshot of the page
that button actually opens.

Layout:
  y 0-88     banner: the hub's CB6 mark small in the top-left, then the url
  y 88-92    rule in the hub's accent colour
  y 92-496   a large window into the destination page
  y 496-600  the button's own name, on the hub's colour

Usage: python3 make_hub_buttons.py
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

SANS = 'fonts/DMSans.ttf'
SHOTS = 'pageshots2'
OUT = 'hubbuttons'
S, BAN, RULE, LBL_TOP = 600, 88, 4, 496
WIN_TOP = BAN + RULE

# Anchored shots are already scrolled into place; plain ones are not.
TOP_FRAC = {'edu': 0.10, 'parks': 0.34}

HUBS = {
    'parks': {
        'src': 'parks-brand.png',
        'url': 'BKCB6.app/parks',
        'field': (251, 251, 251),
        'ban_bg': (2, 117, 58),      # hub green, sampled from the supplied mark
        'ban_fg': (255, 255, 255),
        'accent': (255, 255, 255),
        'lbl_bg': (2, 117, 58),
        'lbl_fg': (255, 255, 255),
    },
    'edu': {
        'src': 'edu-brand.png',
        'url': 'BKCB6.app/eduhub',
        'field': (254, 254, 254),
        'ban_bg': (4, 31, 93),       # hub navy
        'ban_fg': (255, 255, 255),
        'accent': (243, 146, 32),
        'lbl_bg': (4, 31, 93),
        'lbl_fg': (255, 255, 255),
    },
}


def font(size, weight=800):
    f = ImageFont.truetype(SANS, size)
    try:
        f.set_variation_by_axes([40, weight])
    except Exception:
        pass
    return f


def fit(d, text, size, weight, max_w, floor=13):
    while size > floor:
        f = font(size, weight)
        l, t, r, b = d.textbbox((0, 0), text, font=f)
        if r - l <= max_w:
            return f, r - l, b - t
        size -= 2
    f = font(floor, weight)
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    return f, r - l, b - t


def window(key, hub, w, h):
    p = os.path.join(SHOTS, key + '.png')
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert('RGB')
    iw, ih = im.size
    # Fit the full page width. Centre-cropping lopped the left edge off
    # text-heavy pages and made them unreadable.
    sc = w / iw
    need = int(h / sc)
    top = min(int(ih * TOP_FRAC.get(hub, 0.34)), max(0, ih - need))
    im = im.crop((0, top, iw, min(ih, top + need)))
    im = im.resize((w, max(1, int(im.size[1] * sc))), Image.LANCZOS)
    if im.size[1] < h:
        pad = Image.new('RGB', (w, h), (255, 255, 255))
        pad.paste(im, (0, 0))
        return pad
    return im.crop((0, 0, w, h))


def build(job):
    hub = job['hub']
    cfg = HUBS[hub]
    label = job['label'].upper()

    im = Image.new('RGB', (S, S), cfg['field'])
    d = ImageDraw.Draw(im)

    # Banner: the url alone on the hub's colour inside a border, matching the
    # supplied template. No mark competing with the words.
    BORDER = 9
    d.rectangle([0, 0, S, BAN], fill=cfg['lbl_bg'])
    d.rectangle([BORDER, BORDER, S - BORDER, BAN - BORDER], fill=cfg['ban_bg'])
    url = cfg['url'].upper()
    f, tw, th = fit(d, url, 46, 900, S - 2 * BORDER - 26)
    d.text(((S - tw) / 2, (BAN - th) / 2 - 4), url, font=f, fill=cfg['ban_fg'])

    win = window(job['key'], hub, S, LBL_TOP - WIN_TOP)
    if win is not None:
        im.paste(win, (0, WIN_TOP))

    d.rectangle([0, LBL_TOP, S, S], fill=cfg['lbl_bg'])
    f2, tw2, th2 = fit(d, label, 54, 800, S - 44)
    d.text(((S - tw2) / 2, LBL_TOP + ((S - LBL_TOP) - th2) / 2 - 6), label,
           font=f2, fill=cfg['lbl_fg'])

    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, job['key'] + '.png')
    im.save(p, optimize=True)
    return p


if __name__ == '__main__':
    jobs = json.load(open('jobs.json'))
    missing = [j['key'] for j in jobs if not os.path.exists(os.path.join(SHOTS, j['key'] + '.png'))]
    if missing:
        raise SystemExit('missing screenshots, refusing to build: %s' % missing)
    for j in jobs:
        build(j)
    print('built %d buttons' % len(jobs))
