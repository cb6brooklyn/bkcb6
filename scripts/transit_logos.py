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
def _fit(d, text, maxw, size, minsize=28):
    while size > minsize and d.textbbox((0, 0), text, font=_f(size))[2] > maxw: size -= 2
    return _f(size)
def _bus_icon(d, cx, cy, w):
    """White bus front with the arrow, as on the NYC DOT bus stop sign."""
    h = w * 1.12; x0, y0 = cx - w / 2, cy - h / 2; W = 'white'; B = '#1f3f8f'
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h * .86), w * .14, fill=W)
    d.rounded_rectangle((x0 + w * .1, y0 + h * .08, x0 + w * .9, y0 + h * .17), w * .04, fill=B)
    d.rounded_rectangle((x0 + w * .08, y0 + h * .24, x0 + w * .92, y0 + h * .56), w * .06, fill=B)
    for ex in (x0 + w * .2, x0 + w * .8): d.ellipse((ex - w * .07, y0 + h * .66, ex + w * .07, y0 + h * .78), fill=B)
    for wx in (x0 + w * .1, x0 + w * .72): d.rectangle((wx, y0 + h * .86, wx + w * .18, y0 + h * .98), fill=W)
def _chair(d, cx, cy, r):
    W = 'white'; lw = max(4, int(r * .16))
    d.ellipse((cx - r * .15, cy - r * 1.15, cx + r * .15, cy - r * .85), fill=W)
    d.line((cx, cy - r * .7, cx, cy + r * .05, cx + r * .7, cy + r * .05, cx + r * 1.0, cy + r * .6), fill=W, width=lw, joint='curve')
    d.arc((cx - r * .85, cy - r * .35, cx + r * .45, cy + r * .95), 100, 330, fill=W, width=lw)
_WORD = None
def bus(stop, legs, out):
    """A bus stop's logo, laid out like the NYC DOT bus stop sign: the round blue head with the bus and the MTA Bus
    mark (in place of NO STANDING), then a blue panel per route (where it goes | route), then the white panel naming the stop.
    legs: [(route, destination)]."""
    global _WORD
    S = 1024; BLUE = '#1f3f8f'; im = Image.new('RGB', (S, S), 'white'); d = ImageDraw.Draw(im)
    if _WORD is None: _WORD = Image.open('assets/map-icons/mta-bus-wordmark.png').convert('RGB')
    legs = legs[:4]; n = len(legs)
    # head
    R = 190; cx = S // 2; cy = 24 + R
    d.ellipse((cx - R - 12, cy - R - 12, cx + R + 12, cy + R + 12), fill='#2f6b4f')
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=BLUE)
    _bus_icon(d, cx + 30, cy - 62, 150); _chair(d, cx - 110, cy - 80, 44)
    d.polygon([(cx - 60, cy + 58), (cx - 20, cy + 38), (cx - 20, cy + 51), (cx + 110, cy + 51), (cx + 110, cy + 65), (cx - 20, cy + 65), (cx - 20, cy + 78)], fill='white')
    # MTA Bus mark where NO STANDING was: a banner across the bottom of the disc
    by0 = cy + R - 78; by1 = cy + R + 52; bx0, bx1 = cx - 200, cx + 200
    d.rounded_rectangle((bx0 - 10, by0 - 10, bx1 + 10, by1 + 10), 40, fill='#2f6b4f'); d.rounded_rectangle((bx0, by0, bx1, by1), 32, fill='white')
    wh = by1 - by0 - 22; ww = int(_WORD.width * wh / _WORD.height); im.paste(_WORD.resize((ww, wh), Image.LANCZOS), (cx - ww // 2, by0 + 11))
    # pole
    top = by1 + 30; d.rectangle((cx - 22, by1 + 10, cx + 22, S), fill='#2f6b4f')
    # route panels
    PH = {1: 130, 2: 112, 3: 92, 4: 78}[max(n, 1)]; gap = 10; L0, L1, R0, R1 = 70, cx - 28, cx + 28, S - 70
    y = top
    for r, dest in legs:
        d.rectangle((L0, y, L1, y + PH), fill=BLUE); d.rectangle((R0, y, R1, y + PH), fill=BLUE)
        f = _fit(d, dest, L1 - L0 - 36, int(PH * .42)); b = d.textbbox((0, 0), dest, font=f)
        d.text((L0 + 18 - b[0], y + (PH - (b[3] - b[1])) / 2 - b[1]), dest, font=f, fill='white')
        f = _fit(d, r, R1 - R0 - 36, int(PH * .72)); b = d.textbbox((0, 0), r, font=f)
        d.text((R0 + 18 - b[0], y + (PH - (b[3] - b[1])) / 2 - b[1]), r, font=f, fill='white')
        y += PH + gap
    # the stop
    lines = [l.strip() for l in (stop.split(' & ', 1)[0] + ' &|' + stop.split(' & ', 1)[1] if ' & ' in stop else stop).split('|')]
    H = S - 24 - y
    if H > 60:
        d.rectangle((L0, y, L1, S - 24), fill='white', outline='#9aa0a6', width=4)
        fs = min(int(H / len(lines) * .62), 74); f = _f(fs)
        fs = min(_fit(d, l, L1 - L0 - 36, fs).size for l in lines); f = _f(fs)
        for k, l in enumerate(lines):
            b = d.textbbox((0, 0), l, font=f)
            d.text((L0 + 18 - b[0], y + (H - len(lines) * fs * 1.15) / 2 + k * fs * 1.15 - b[1] + 4), l, font=f, fill='#111')
    im.resize((512, 512), Image.LANCZOS).save(out, optimize=True)

_CB = None
WORDS = {'St': 'Street', 'Ave': 'Avenue', 'Av': 'Avenue', 'Pl': 'Place', 'Blvd': 'Boulevard', 'Pkwy': 'Parkway', 'Rd': 'Road', 'Sq': 'Square', 'Dr': 'Drive'}
def citibike(name, hood, out):
    """A Citi Bike dock's logo, laid out like the Citi Bike station sign: the dark panel with the corner on one row and the
    neighborhood on the next, then the blue Citi Bike band."""
    global _CB
    if _CB is None: _CB = Image.open('assets/map-icons/citibike-wordmark-white.png').convert('RGBA')
    import re
    name = re.sub(r'\b(St|Ave|Av|Pl|Blvd|Pkwy|Rd|Sq|Dr)\b\.?', lambda m: WORDS[m.group(1)], name)
    S = 1024; im = Image.new('RGB', (S, S), '#b8bec2'); d = ImageDraw.Draw(im)
    d.rectangle((40, 40, S - 40, S - 40), fill='#5d6468')
    x0, x1 = 90, S - 90; rows = [(name, 230), (hood, 230)]; y = 140
    for txt, h in rows:
        d.rectangle((x0, y, x1, y + h), fill='#2b2f31')
        if txt:
            f = _fit(d, txt, x1 - x0 - 70, 96); b = d.textbbox((0, 0), txt, font=f)
            if f.size < 84 and ' & ' in txt:
                a, c = txt.split(' & ', 1); txt = a + ' &\n' + c; f = _fit(d, max(a + ' &', c, key=len), x1 - x0 - 70, 80)
                b = d.multiline_textbbox((0, 0), txt, font=f, spacing=8)
                d.multiline_text((x0 + 36 - b[0], y + (h - (b[3] - b[1])) / 2 - b[1]), txt, font=f, fill='#f2f2f2', spacing=8)
            else:
                d.text((x0 + 36 - b[0], y + (h - (b[3] - b[1])) / 2 - b[1]), txt, font=f, fill='#f2f2f2')
        y += h + 14
    # the blue band, darker to lighter as on the sign
    bh = S - 140 - y
    band = Image.new('RGB', (x1 - x0, bh)); bd = ImageDraw.Draw(band)
    for i in range(x1 - x0):
        t = i / (x1 - x0); c = tuple(int(a + (b - a) * t) for a, b in ((0x1b, 0x3f), (0x3c, 0xa9), (0xc8, 0xe6)))
        bd.line((i, 0, i, bh), fill=c)
    im.paste(band, (x0, y))
    ww = int((x1 - x0) * 0.62); wh = int(_CB.height * ww / _CB.width)
    im.paste(_CB.resize((ww, wh), Image.LANCZOS), (x0 + 36, y + (bh - wh) // 2), _CB.resize((ww, wh), Image.LANCZOS))
    ax = x1 - 90; ay = y + bh // 2
    d.polygon([(ax - 30, ay - 22), (ax + 10, ay - 22), (ax + 10, ay - 40), (ax + 46, ay), (ax + 10, ay + 40), (ax + 10, ay + 22), (ax - 30, ay + 22)], fill='white')
    im.resize((512, 512), Image.LANCZOS).save(out, optimize=True)
