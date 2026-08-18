#!/usr/bin/env python3
"""
Builds a button image for each hub, for the hub-of-hubs page.

Same layout as every other button on the site: the url alone on the hub's own
colour inside a border, a window onto the hub itself, then its name. Colours are
each hub's own, sampled from its live page rather than chosen here.

Usage: python3 make_hubhub_buttons.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

SANS = 'fonts/DMSans.ttf'
SHOTS = 'hubshots'
OUT = 'hubhub'
S, BAN, RULE, LBL_TOP, BORDER = 600, 88, 4, 496, 9
WIN_TOP = BAN + RULE

WHITE = (255, 255, 255)

# key: (banner field, url type, border and label band, label type)
HUBS = [
    ('311',          'BKCB6.app/311-hub',    '311',
     (253, 233, 7),  (27, 27, 26),  (27, 27, 26),  (253, 233, 7)),
    ('parks',        'BKCB6.app/parks',      'Parks',
     (255, 255, 255), (2, 117, 57),  (2, 117, 57),  (255, 255, 255)),
    ('eduhub',       'BKCB6.app/eduhub',     'Education',
     (255, 255, 255), (4, 31, 93),   (4, 31, 93),   (255, 255, 255)),
    ('transport',    'BKCB6.app/transport',  'Transportation',
     (244, 121, 32), (13, 27, 75),  (13, 27, 75),  (255, 255, 255)),
    ('publicsafety', 'BKCB6.app/publicsafety', 'Public Safety',
     (13, 27, 75),   (255, 255, 255), (244, 121, 32), (13, 27, 75)),
    ('culture',      'BKCB6.app/culture',    'Culture',
     (244, 121, 32), (6, 2, 77),    (6, 2, 77),    (255, 255, 255)),
    ('useofland',    'BKCB6.app/useofland',  'Use of Land',
     (13, 27, 75),   (255, 255, 255), (13, 27, 75), (255, 255, 255)),
]


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


def window(key, w, h):
    p = os.path.join(SHOTS, key + '.png')
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert('RGB')
    iw, ih = im.size
    sc = w / iw
    need = int(h / sc)
    # start below the masthead so the window shows the hub's tiles, not its title
    top = min(int(ih * 0.20), max(0, ih - need))
    im = im.crop((0, top, iw, min(ih, top + need)))
    im = im.resize((w, max(1, int(im.size[1] * sc))), Image.LANCZOS)
    if im.size[1] < h:
        pad = Image.new('RGB', (w, h), WHITE)
        pad.paste(im, (0, 0))
        return pad
    return im.crop((0, 0, w, h))


def build(key, url, label, ban_bg, ban_fg, rule, lbl_fg):
    im = Image.new('RGB', (S, S), WHITE)
    d = ImageDraw.Draw(im)

    d.rectangle([0, 0, S, BAN], fill=rule)
    d.rectangle([BORDER, BORDER, S - BORDER, BAN - BORDER], fill=ban_bg)
    u = url.upper()
    f, tw, th = fit(d, u, 46, 900, S - 2 * BORDER - 26)
    d.text(((S - tw) / 2, (BAN - th) / 2 - 4), u, font=f, fill=ban_fg)

    win = window(key, S, LBL_TOP - WIN_TOP)
    if win is not None:
        im.paste(win, (0, WIN_TOP))

    d.rectangle([0, LBL_TOP, S, S], fill=rule)
    lab = label.upper()
    f2, tw2, th2 = fit(d, lab, 54, 800, S - 44)
    d.text(((S - tw2) / 2, LBL_TOP + ((S - LBL_TOP) - th2) / 2 - 6), lab, font=f2, fill=lbl_fg)

    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, 'hub-%s.png' % key)
    im.save(p, optimize=True)
    return p


if __name__ == '__main__':
    missing = [h[0] for h in HUBS if not os.path.exists(os.path.join(SHOTS, h[0] + '.png'))]
    if missing:
        raise SystemExit('missing screenshots, refusing to build: %s' % missing)
    for h in HUBS:
        print('  wrote', build(*h))
