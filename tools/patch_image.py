"""Patch lead image: 'Mike Racioppo' + date on navy, beside the issue's first newsletter image.
usage: python3 tools/patch_image.py <source_image> "October 29, 2026" <out.png>"""
import sys
from PIL import Image, ImageDraw, ImageFont

NAVY = (15, 36, 80)
ORANGE = (247, 148, 29)
WHITE = (255, 255, 255)
F = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"


def make(src, date, out, W=1200, H=800):
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 8], fill=ORANGE)
    d.rectangle([0, H - 8, W, H], fill=ORANGE)
    pic = Image.open(src).convert("RGB")
    side = H - 16
    r = side / pic.height
    pic = pic.resize((max(1, int(pic.width * r)), side), Image.LANCZOS)
    if pic.width > W - 400:
        x0 = (pic.width - (W - 400)) // 2
        pic = pic.crop((x0, 0, x0 + W - 400, side))
    im.paste(pic, (W - pic.width, 8))
    left = W - pic.width
    pad = 48
    maxw = left - 2 * pad
    size = 96
    while True:
        f = ImageFont.truetype(F, size)
        if max(d.textlength("Mike", font=f), d.textlength("Racioppo", font=f)) <= maxw or size < 30:
            break
        size -= 2
    fd = ImageFont.truetype(F, max(24, size // 3))
    y = H // 2 - int(size * 1.25)
    d.text((pad, y), "Mike", font=f, fill=ORANGE)
    d.text((pad, y + int(size * 1.1)), "Racioppo", font=f, fill=WHITE)
    d.text((pad, y + int(size * 2.4)), date.upper(), font=fd, fill=ORANGE)
    im.save(out, optimize=True)


if __name__ == "__main__":
    make(sys.argv[1], sys.argv[2], sys.argv[3])
