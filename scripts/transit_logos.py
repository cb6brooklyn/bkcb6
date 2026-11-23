"""Logos for transit places: a subway station's route bullets in the MTA colors, a bus stop's route badges."""
from PIL import Image, ImageDraw, ImageFont
F = 'assets/fonts/DMSans-Bold.ttf'
SUB = {'1': '#EE352E', '2': '#EE352E', '3': '#EE352E', '4': '#00933C', '5': '#00933C', '6': '#00933C', '7': '#B933AD',
       'A': '#0039A6', 'C': '#0039A6', 'E': '#0039A6', 'B': '#FF6319', 'D': '#FF6319', 'F': '#FF6319', 'M': '#FF6319',
       'G': '#6CBE45', 'J': '#996633', 'Z': '#996633', 'L': '#A7A9AC', 'N': '#FCCC0A', 'Q': '#FCCC0A', 'R': '#FCCC0A', 'W': '#FCCC0A', 'S': '#808183'}
DARKTEXT = set('NQRW')
def _f(s): return ImageFont.truetype(F, s)
def subway(lines, out):
    S = 1024; im = Image.new('RGB', (S, S), 'white'); d = ImageDraw.Draw(im)
    lines = [l for l in lines if l in SUB] or ['S']
    n = len(lines); per = min(4, n); rows = (n + per - 1) // per
    D = min(300, int((S - 120) / per) - 30); gap = 30
    y0 = (S - (rows * D + (rows - 1) * gap)) // 2
    for r in range(rows):
        row = lines[r * per:(r + 1) * per]; w = len(row) * D + (len(row) - 1) * gap; x = (S - w) // 2; y = y0 + r * (D + gap)
        for l in row:
            d.ellipse((x, y, x + D, y + D), fill=SUB[l]); f = _f(int(D * 0.68)); b = d.textbbox((0, 0), l, font=f)
            d.text((x + (D - (b[2] - b[0])) / 2 - b[0], y + (D - (b[3] - b[1])) / 2 - b[1]), l, font=f, fill='#000' if l in DARKTEXT else '#fff'); x += D + gap
    im.resize((256, 256), Image.LANCZOS).save(out, optimize=True)
def bus(routes, out):
    S = 1024; BLUE = '#0039A6'; im = Image.new('RGB', (S, S), 'white'); d = ImageDraw.Draw(im)
    d.rounded_rectangle((60, 60, S - 60, S - 60), 70, fill=BLUE)
    f = _f(110); b = d.textbbox((0, 0), 'BUS STOP', font=f); d.text(((S - (b[2] - b[0])) / 2 - b[0], 130 - b[1]), 'BUS STOP', font=f, fill='white')
    d.line((140, 290, S - 140, 290), fill='white', width=8)
    routes = routes[:4]; n = len(routes); fs = 230 if n == 1 else 190 if n == 2 else 140
    f = _f(fs); hs = [d.textbbox((0, 0), r, font=f) for r in routes]; H = sum(b[3] - b[1] for b in hs) + 50 * (n - 1)
    y = 330 + (S - 120 - 330 - H) / 2
    for r, b in zip(routes, hs):
        d.text(((S - (b[2] - b[0])) / 2 - b[0], y - b[1]), r, font=f, fill='white'); y += b[3] - b[1] + 50
    im.resize((256, 256), Image.LANCZOS).save(out, optimize=True)
