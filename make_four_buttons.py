#!/usr/bin/env python3
"""
Builds a button image for every destination in the 311, Transportation,
Public Safety and Culture hubs.

Labels and links come from jobs4.json, which was read out of the rendered hubs.
Each window is a screenshot of the page that button actually opens. Colours are
the CB6 house palette those four pages already use, read from their own CSS.

Layout matches the parks and education buttons:
  y 0-88    banner: hub mark top-left, then the url
  y 88-92   orange rule
  y 92-496  the page window
  y 496-600 the button's name
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

SANS = 'fonts/DMSans.ttf'
SHOTS = 'pageshots4'
OUT = 'fourbuttons'
S, BAN, RULE, LBL_TOP = 600, 88, 4, 496
WIN_TOP = BAN + RULE

NAVY = (13, 27, 75)
ORANGE = (244, 121, 32)
FIELD = (251, 251, 251)

# The 311 hub uses the yellow-and-black mark, so its banner and label band
# follow it rather than the house navy.
BAND = {
    # bg = banner field, fg = url type, rule = border and label band
    '311':          {'bg': (253, 240, 5),  'fg': (0, 0, 0),       'rule': (0, 0, 0)},
    'transport':    {'bg': (244, 121, 32), 'fg': (13, 27, 75),    'rule': (13, 27, 75)},
    'publicsafety': {'bg': (13, 27, 75),   'fg': (255, 255, 255), 'rule': (244, 121, 32),
                     'lbl_bg': (13, 27, 75), 'lbl_fg': (255, 255, 255)},
    'culture':      {'bg': (244, 121, 32), 'fg': (6, 2, 77),      'rule': (6, 2, 77)},
}

HUBS = {
    '311':          {'mark': 'marks/logo-311.png',          'url': 'BKCB6.app/311-hub'},
    'transport':    {'mark': 'marks/logo-transport.png',    'url': 'BKCB6.app/transport'},
    'publicsafety': {'mark': 'marks/logo-publicsafety.png', 'url': 'BKCB6.app/publicsafety'},
    'culture':      {'mark': 'marks/logo-culture.png',      'url': 'BKCB6.app/culture'},
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


TOP_FRAC = {'transport': 0.02, '311': 0.16, 'publicsafety': 0.16, 'culture': 0.06}


def window(key, hub, w, h):
    p = os.path.join(SHOTS, key + '.png')
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert('RGB')
    iw, ih = im.size
    # Fit the full page width; never centre-crop, which lops the left edge off
    # text-heavy pages.
    sc = w / iw
    need = int(h / sc)
    # Transport map pages differ in their active layer chips at the very top;
    # the map itself looks the same at citywide zoom. Start from the top there.
    frac = TOP_FRAC.get(hub, 0.16)
    top = min(int(ih * frac), max(0, ih - need))
    im = im.crop((0, top, iw, min(ih, top + need)))
    im = im.resize((w, max(1, int(im.size[1] * sc))), Image.LANCZOS)
    if im.size[1] < h:
        pad = Image.new('RGB', (w, h), (255, 255, 255))
        pad.paste(im, (0, 0))
        return pad
    return im.crop((0, 0, w, h))


def build(job):
    cfg = HUBS[job['hub']]
    im = Image.new('RGB', (S, S), FIELD)
    d = ImageDraw.Draw(im)

    band = BAND.get(job['hub'], {'bg': NAVY, 'fg': (255, 255, 255), 'rule': ORANGE})
    # The banner is the url on its own, on the hub's colour inside a border,
    # matching the supplied template. No mark competing with the words.
    BORDER = 9
    d.rectangle([0, 0, S, BAN], fill=band['rule'])
    d.rectangle([BORDER, BORDER, S - BORDER, BAN - BORDER], fill=band['bg'])
    url = cfg['url'].upper()
    f, tw, th = fit(d, url, 46, 900, S - 2 * BORDER - 26)
    d.text(((S - tw) / 2, (BAN - th) / 2 - 4), url, font=f, fill=band['fg'])

    win = window(job['key'], job['hub'], S, LBL_TOP - WIN_TOP)
    if win is not None:
        im.paste(win, (0, WIN_TOP))

    lab_bg = band.get('lbl_bg', band['rule'])
    lab_fg = band.get('lbl_fg', band['bg'])
    d.rectangle([0, LBL_TOP, S, S], fill=lab_bg)
    label = job['label'].upper()
    f2, tw2, th2 = fit(d, label, 54, 800, S - 44)
    d.text(((S - tw2) / 2, LBL_TOP + ((S - LBL_TOP) - th2) / 2 - 6), label,
           font=f2, fill=lab_fg)

    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, job['key'] + '.png')
    im.save(p, optimize=True)
    return p


if __name__ == '__main__':
    jobs = json.load(open('jobs4.json'))
    missing = [j['key'] for j in jobs
               if not os.path.exists(os.path.join(SHOTS, j['key'] + '.png'))]
    if missing:
        raise SystemExit('missing screenshots, refusing to build: %s' % missing)
    for j in jobs:
        build(j)
    print('built %d buttons' % len(jobs))
