#!/usr/bin/env python3
"""
build-event-share-pages.py

Generates one share page per hardcoded calendar event that has a flyer, at
/e/<slug>.html. Each page carries that event's own flyer as its og:image, so a
link pasted into iMessage, Slack, WhatsApp, or Facebook previews the actual
event instead of the site-wide default card. The page forwards to the calendar
deep link via JS; crawlers do not run JS, so they read the OG tags as served.

The slug must stay byte-identical to evSlug() in calendar.html:
    dateKey + '-' + slugify(label)

Usage:  python3 build-event-share-pages.py
Re-run after adding or renaming events, then commit the /e/ directory.
"""

import html
import json
import os
import re
import subprocess
import sys
from datetime import date

REPO = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(REPO, "e")
CALENDAR = os.path.join(REPO, "calendar.html")
SITE = "https://bkcb6.app"

DOW_LONG = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday"]
MONTH_LONG = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]


def slugify(s):
    """Mirror of slugify() in calendar.html."""
    s = (s or "").lower()
    s = re.sub(r"[\u2018\u2019']", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s[:80]


def ev_slug(date_key, label):
    return date_key + "-" + slugify(label)


def extract_events():
    """Evaluate the EVENTS object literal out of calendar.html using node."""
    src = open(CALENDAR, encoding="utf-8").read()
    start = src.index("const EVENTS = {")
    end = src.index("\n};", start) + 3
    block = src[start:end]
    script = block + "\nprocess.stdout.write(JSON.stringify(EVENTS));"
    tmp = os.path.join(REPO, ".events-extract.tmp.js")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(script)
    try:
        res = subprocess.run(["node", tmp], capture_output=True, text=True)
        if res.returncode != 0:
            sys.exit("Could not evaluate EVENTS from calendar.html:\n" + res.stderr)
        return json.loads(res.stdout)
    finally:
        os.remove(tmp)


def image_size(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def describe(date_key, ev):
    """Preview text built only from fields the event actually has."""
    y, m, d = (int(x) for x in date_key.split("-"))
    dow = DOW_LONG[date(y, m, d).weekday()]
    bits = ["%s, %s %d, %d" % (dow, MONTH_LONG[m - 1], d, y)]
    if ev.get("time"):
        bits.append(ev["time"])
    if ev.get("location"):
        bits.append(ev["location"])
    line = " \u00b7 ".join(bits)
    desc = (ev.get("desc") or "").strip()
    if desc:
        line = line + " \u2014 " + desc
    if len(line) > 280:
        cut = line[:279]
        space = cut.rfind(" ")
        if space > 200:
            cut = cut[:space]
        line = cut.rstrip(" ,.;:\u2014-") + "\u2026"
    return line


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} &mdash; CB6 Calendar</title>
<meta property="og:type" content="article">
<meta property="og:site_name" content="Brooklyn Community Board 6">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{img}">
<meta property="og:image:type" content="{imgtype}">{imgdims}
<meta property="og:image:alt" content="Flyer for {title}">
<meta property="og:url" content="{page_url}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{img}">
<link rel="canonical" href="{cal_url}">
<style>
  body{{margin:0;background:#132D65;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;padding:24px;box-sizing:border-box;font-family:'DM Sans',system-ui,sans-serif;gap:18px}}
  img{{max-width:min(420px,100%);height:auto;border-radius:10px;box-shadow:0 6px 30px rgba(0,0,0,.4)}}
  h1{{font-size:1.1rem;font-weight:700;text-align:center;margin:0;max-width:520px;line-height:1.35}}
  p{{margin:0;font-size:.85rem;color:rgba(255,255,255,.7);text-align:center;max-width:520px}}
  a{{display:block;background:#FD890E;color:#fff;font-weight:700;font-size:1.05rem;padding:16px 32px;border-radius:10px;text-decoration:none;text-align:center}}
</style>
</head>
<body>
<img src="{img}" alt="Flyer for {title}">
<h1>{title}</h1>
<p>{meta}</p>
<a href="{cal_url}">View on the CB6 Calendar &rarr;</a>
<script>
// Humans go straight through to the calendar listing. Crawlers do not run JS,
// so link previews still read the og: tags above.
location.replace({cal_json});
</script>
</body>
</html>
"""


def main():
    events = extract_events()
    os.makedirs(OUT_DIR, exist_ok=True)

    written, skipped_no_flyer, missing_files = 0, 0, []
    seen_slugs = {}

    for date_key in sorted(events):
        for ev in events[date_key]:
            label = ev.get("label")
            flyer = ev.get("flyer")
            if not label:
                continue
            if not flyer:
                skipped_no_flyer += 1
                continue

            slug = ev_slug(date_key, label)
            if slug in seen_slugs:
                continue  # same event listed twice on one day
            seen_slugs[slug] = True

            fname = flyer.rsplit("/", 1)[-1]
            local = os.path.join(REPO, fname)
            if not os.path.exists(local):
                missing_files.append(fname)
                continue

            size = image_size(local)
            dims = ""
            if size:
                dims = ('\n<meta property="og:image:width" content="%d">'
                        '\n<meta property="og:image:height" content="%d">'
                        % (size[0], size[1]))
            imgtype = "image/png" if fname.lower().endswith(".png") else "image/jpeg"

            cal_url = "%s/calendar.html?event=%s" % (SITE, slug)
            page = PAGE.format(
                title=html.escape(label, quote=True),
                desc=html.escape(describe(date_key, ev), quote=True),
                meta=html.escape(describe(date_key, ev), quote=True),
                img="%s/%s" % (SITE, fname),
                imgtype=imgtype,
                imgdims=dims,
                page_url="%s/e/%s.html" % (SITE, slug),
                cal_url=html.escape(cal_url, quote=True),
                cal_json=json.dumps(cal_url),
            )
            with open(os.path.join(OUT_DIR, slug + ".html"), "w",
                      encoding="utf-8") as fh:
                fh.write(page)
            written += 1

    print("share pages written: %d" % written)
    print("events without a flyer (no page generated): %d" % skipped_no_flyer)
    if missing_files:
        print("FLYER FILES REFERENCED BUT NOT IN REPO: %s"
              % ", ".join(sorted(set(missing_files))))


if __name__ == "__main__":
    main()
