#!/usr/bin/env python3
"""
Generates the 311 hub tiles in the same visual language as the existing
/tiles/*.png: 600x600, navy field, a simple geometric mark, a bold title,
a mono subtitle, and an orange bar along the bottom.

Colours sampled directly from tiles/eduhub-citywide.png rather than guessed.
"""
from PIL import Image, ImageDraw, ImageFont
import os

NAVY   = (13, 27, 75)
ORANGE = (244, 121, 32)
WHITE  = (255, 255, 255)
LILAC  = (150, 163, 205)
S      = 600
BAR    = 14

SANS = 'fonts/DMSans.ttf'
MONO = 'fonts/DMMono.ttf'


def font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight:
        try:
            f.set_variation_by_axes([9, weight])
        except Exception:
            pass
    return f


def centre(d, text, f, y, fill):
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    d.text(((S - (r - l)) / 2 - l, y), text, font=f, fill=fill)
    return b - t


def base():
    im = Image.new('RGB', (S, S), NAVY)
    d = ImageDraw.Draw(im)
    d.rectangle([0, S - BAR, S, S], fill=ORANGE)
    return im, d


def rounded(d, box, fill, r=12):
    d.rounded_rectangle(box, radius=r, fill=fill)


# ---- marks -------------------------------------------------------------

def mark_grid(d, hot=(1, 1)):
    """3x3 of squares, one picked out in orange."""
    size, gap, x0, y0 = 62, 22, 195, 140
    for r in range(3):
        for c in range(3):
            x = x0 + c * (size + gap)
            y = y0 + r * (size + gap)
            if (r, c) == hot:
                col = ORANGE
            elif (r + c) % 2:
                col = LILAC
            else:
                col = WHITE
            rounded(d, [x, y, x + size, y + size], col, 10)


def mark_pin(d):
    """A map pin over a baseline."""
    cx, cy, r = 300, 205, 58
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ORANGE)
    d.polygon([(cx - 34, cy + 38), (cx + 34, cy + 38), (cx, cy + 112)], fill=ORANGE)
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=NAVY)
    d.rounded_rectangle([170, 330, 430, 344], radius=7, fill=LILAC)


def mark_bars(d):
    """Ascending bars, tallest in orange."""
    x, w, gap, base_y = 176, 46, 18, 330
    for i, h in enumerate([70, 112, 156, 196]):
        col = ORANGE if i == 3 else (WHITE if i % 2 == 0 else LILAC)
        rounded(d, [x, base_y - h, x + w, base_y], col, 8)
        x += w + gap


def mark_dots(d):
    """Scatter of complaint dots."""
    pts = [(215, 150, WHITE), (300, 132, LILAC), (378, 168, WHITE),
           (196, 232, LILAC), (300, 214, ORANGE), (392, 240, LILAC),
           (232, 308, WHITE), (312, 300, LILAC), (386, 322, WHITE)]
    for cx, cy, col in pts:
        r = 30 if col is ORANGE else 23
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)


def mark_boro(d):
    """Five blocks, one highlighted, for the five boroughs."""
    coords = [(196, 150, 96, 76), (306, 150, 98, 76),
              (196, 240, 96, 76), (306, 240, 98, 76),
              (250, 330, 100, 76)]
    for i, (x, y, w, h) in enumerate(coords):
        col = ORANGE if i == 2 else (WHITE if i % 2 == 0 else LILAC)
        rounded(d, [x, y, x + w, y + h], col, 10)


def mark_ring(d):
    """Doughnut, matching the dashboard's own chart."""
    cx, cy, R, r = 300, 235, 105, 62
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=LILAC)
    d.pieslice([cx - R, cy - R, cx + R, cy + R], -90, 40, fill=ORANGE)
    d.pieslice([cx - R, cy - R, cx + R, cy + R], 40, 135, fill=WHITE)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=NAVY)


def mark_stadium(d):
    """An oval bowl."""
    d.ellipse([160, 168, 440, 320], fill=WHITE)
    d.ellipse([206, 196, 394, 292], fill=NAVY)
    d.ellipse([236, 214, 364, 274], fill=ORANGE)
    rounded(d, [170, 336, 430, 350], LILAC, 7)


MARKS = {'grid': mark_grid, 'pin': mark_pin, 'bars': mark_bars,
         'dots': mark_dots, 'boro': mark_boro, 'ring': mark_ring,
         'stadium': mark_stadium}


def tile(path, mark, title, subtitle):
    im, d = base()
    MARKS[mark](d)
    size = 62 if len(title) <= 12 else (52 if len(title) <= 17 else 44)
    ft = font(SANS, size, 800)
    fs = font(MONO, 26)
    centre(d, title, ft, 400, WHITE)
    centre(d, subtitle.upper(), fs, 480, LILAC)
    im.save(path, optimize=True)
    print('  wrote', path, os.path.getsize(path), 'bytes')


TILES = [
    ('jia-hub.png',      'boro',    'Joint Areas',  'twelve of them'),
    ('jia-parks.png',    'grid',    'The Parks',    'seven big ones'),
    ('jia-airports.png', 'bars',    'Airports',     'jfk and lga'),
    ('jia-borders.png',  'ring',    'Who Borders',  'shared review'),
    ('jia-find.png',     'pin',     'Check One',    'address card'),
]

if __name__ == '__main__':
    os.makedirs('out_tiles', exist_ok=True)
    for name, mark, title, sub in TILES:
        tile(os.path.join('out_tiles', name), mark, title, sub)
