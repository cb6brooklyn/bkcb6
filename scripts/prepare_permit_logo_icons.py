#!/usr/bin/env python3
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
UPLOAD = Path('/home/ubuntu/upload')
OUTDIR = ROOT / 'assets' / 'permit-icons'
OUTDIR.mkdir(parents=True, exist_ok=True)

SPECS = [
    ('Logosforpermitmap-DOBlogo.png', 'dob-logo.png'),
    ('Logosforpermitmap-Dotlogo.png', 'dot-logo.png'),
    ('Logosforpermitmap-Filmlogo.png', 'film-logo.png'),
]

for src_name, out_name in SPECS:
    src = UPLOAD / src_name
    out = OUTDIR / out_name
    with Image.open(src) as im:
        converted = im.convert('RGBA')
        converted.save(out, format='PNG', optimize=True)
        print(f'{src} -> {out}')
