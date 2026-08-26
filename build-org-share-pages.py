#!/usr/bin/env python3
"""
build-org-share-pages.py

Generates one share page per organization in the calendar's org filter, at
/o/<type>.html. Each page carries an org-specific og:title and og:description
so a link pasted into iMessage, Slack, or Facebook says which organization's
events it opens, instead of previewing as a generic site card.

The page forwards to calendar.html?org=<type>, which is the existing org filter
deep link. Crawlers do not run JS, so they read the OG tags as served.

Org logos in the repo are mostly 40-200px, too small to upscale into a 1200x630
preview without looking broken, so every org page uses the standard CB6 card as
its image and carries the org name in the title and description instead.

Usage:  python3 build-org-share-pages.py
Re-run after adding or renaming a dropdown option, then commit the /o/ directory.
"""

import html
import os
import re
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(REPO, "o")
CALENDAR = os.path.join(REPO, "calendar.html")
SITE = "https://bkcb6.app"
CARD = "og-image.png"

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} &mdash; CB6 Calendar</title>
<meta property="og:type" content="website">
<meta property="og:site_name" content="Brooklyn Community Board 6">
<meta property="og:title" content="{name} — CB6 Calendar">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{img}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="{iw}">
<meta property="og:image:height" content="{ih}">
<meta property="og:url" content="{page_url}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{name} — CB6 Calendar">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{img}">
<link rel="canonical" href="{cal_url}">
<style>
  body{{margin:0;background:#132D65;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;padding:24px;box-sizing:border-box;font-family:'DM Sans',system-ui,sans-serif;gap:18px}}
  h1{{font-size:1.25rem;font-weight:700;text-align:center;margin:0;max-width:520px;line-height:1.35}}
  p{{margin:0;font-size:.85rem;color:rgba(255,255,255,.7);text-align:center;max-width:520px}}
  a{{display:block;background:#FD890E;color:#fff;font-weight:700;font-size:1.05rem;padding:16px 32px;border-radius:10px;text-decoration:none;text-align:center}}
</style>
</head>
<body>
<h1>{name}</h1>
<p>{desc}</p>
<a href="{cal_url}">View these events on the CB6 Calendar &rarr;</a>
<script>
// Humans go straight through to the filtered calendar. Crawlers do not run JS,
// so link previews still read the og: tags above.
location.replace({cal_json});
</script>
</body>
</html>
"""


def card_size():
    try:
        from PIL import Image
        with Image.open(os.path.join(REPO, CARD)) as im:
            return im.size
    except Exception:
        sys.exit("Could not read %s" % CARD)


def dropdown_options():
    """Pull (value, display name) out of the org filter select in calendar.html."""
    src = open(CALENDAR, encoding="utf-8").read()
    start = src.index('<select class="list-filter" id="list-org-filter"')
    end = src.index("</select>", start)
    block = src[start:end]
    opts = re.findall(r'<option value="([^"]*)">([^<]+)</option>', block)
    return [(v, html.unescape(n).strip()) for v, n in opts if v]


def main():
    import json
    opts = dropdown_options()
    if not opts:
        sys.exit("No org options found in calendar.html")
    iw, ih = card_size()
    os.makedirs(OUT_DIR, exist_ok=True)

    for value, name in opts:
        cal_url = "%s/calendar.html?org=%s" % (SITE, value)
        desc = ("Upcoming %s events on the Brooklyn Community Board 6 "
                "community calendar." % name)
        page = PAGE.format(
            name=html.escape(name, quote=True),
            desc=html.escape(desc, quote=True),
            img="%s/%s" % (SITE, CARD),
            iw=iw, ih=ih,
            page_url="%s/o/%s.html" % (SITE, value),
            cal_url=html.escape(cal_url, quote=True),
            cal_json=json.dumps(cal_url),
        )
        with open(os.path.join(OUT_DIR, value + ".html"), "w",
                  encoding="utf-8") as fh:
            fh.write(page)

    print("org share pages written: %d" % len(opts))


if __name__ == "__main__":
    main()
