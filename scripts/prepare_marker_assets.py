from pathlib import Path
from PIL import Image

ROOT = Path('/home/ubuntu/work/bkcb6_repo_1776697502')
UPLOAD = Path('/home/ubuntu/upload')
OUT = ROOT / 'assets' / 'map-icons'
OUT.mkdir(parents=True, exist_ok=True)

SOURCES = {
    'parks': UPLOAD / 'images.png',
    'schools': UPLOAD / 'download.jpg',
    'childcare': UPLOAD / 'download(1).png',
    'libraries': UPLOAD / 'BPL+Cover.webp',
}

TARGET_SIZE = (44, 44)
CANVAS = (56, 56)

for key, src in SOURCES.items():
    img = Image.open(src).convert('RGBA')
    img.thumbnail(TARGET_SIZE, Image.LANCZOS)

    canvas = Image.new('RGBA', CANVAS, (255, 255, 255, 0))
    x = (CANVAS[0] - img.width) // 2
    y = (CANVAS[1] - img.height) // 2
    canvas.alpha_composite(img, (x, y))

    out_path = OUT / f'{key}.png'
    canvas.save(out_path)
    print(f'saved {out_path}')
