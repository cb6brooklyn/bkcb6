#!/usr/bin/env python3
"""
Generate one page per civic entity under /gov/, plus a directory at /gov/index.html.

Every community board, City Council body, borough president and city agency in
data/civic-calendar/ gets its own URL, so a person can be sent straight to that
one calendar instead of the whole citywide pile:

    https://bkcb6.app/gov/bkcb14.html
    https://bkcb6.app/gov/council-committee-on-land-use.html
    https://bkcb6.app/gov/bp-queens.html

Each page carries its own og: tags and forwards to
calendar.html?civic=<source>&entity=<slug>, which turns on the right calendar
and focuses it on that entity. Crawlers do not run JS, so previews still read
the og: tags as served.

Slugs must stay identical to entitySlug() in calendar.html.

Usage:  python3 build-entity-pages.py
Re-run after the civic-calendar Action adds a new body or agency.
"""

import html
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(REPO, "data", "civic-calendar")
OUT_DIR = os.path.join(REPO, "gov")
SITE = "https://bkcb6.app"
CARD = "og-image.png"


def slug(text):
    text = re.sub(r"[\u2018\u2019']", "", str(text or "").lower())
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:60]


def load(name):
    path = os.path.join(DATA, name + ".json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def collect():
    """(slug, display name, source key, group, upcoming count) per entity."""
    out = {}

    boards = load("brooklyn-cbs")
    if boards:
        for b in boards.get("boards", {}).values():
            key = "bkcb%d" % b["cb"]
            out[key] = {
                "name": "Brooklyn Community Board %d" % b["cb"],
                "source": "bkcbs",
                "group": "Brooklyn Community Boards",
                "count": len(b.get("events") or []),
                "site": b.get("site"),
            }

    council = load("council")
    if council:
        for day in council.get("events", {}).values():
            for e in day:
                key = "council-" + slug(e["label"])
                row = out.setdefault(key, {
                    "name": "NYC Council \u2014 " + e["label"],
                    "source": "council",
                    "group": "NYC Council",
                    "count": 0,
                    "site": "https://council.nyc.gov/",
                })
                row["count"] += 1

    bp = load("bp")
    if bp:
        for b in bp.get("boroughs", {}).values():
            key = "bp-" + slug(b["borough"])
            out[key] = {
                "name": "%s Borough President" % b["borough"],
                "source": "bp",
                "group": "Borough Presidents",
                "count": len(b.get("events") or []),
                "site": b.get("site"),
            }

    hearings = load("hearings")
    if hearings:
        for day in hearings.get("events", {}).values():
            for e in day:
                if (e.get("kind") or "hearing") != "hearing":
                    continue
                key = "agency-" + slug(e["agency"])
                row = out.setdefault(key, {
                    "name": e["agency"],
                    "source": "hearing",
                    "group": "City Agencies",
                    "count": 0,
                    "site": "https://www.nyc.gov/",
                })
                row["count"] += 1

    return dict(sorted(out.items()))


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name} &mdash; CB6 Calendar</title>
<meta property="og:type" content="website">
<meta property="og:site_name" content="Brooklyn Community Board 6">
<meta property="og:title" content="{name} \u2014 CB6 Calendar">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{img}">
<meta property="og:image:type" content="image/png">
<meta property="og:url" content="{page_url}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{name} \u2014 CB6 Calendar">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{img}">
<link rel="canonical" href="{cal_url}">
<style>
  body{{margin:0;background:#132D65;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;padding:24px;box-sizing:border-box;font-family:'DM Sans',system-ui,sans-serif;gap:16px}}
  h1{{font-size:1.2rem;font-weight:700;text-align:center;margin:0;max-width:520px;line-height:1.35}}
  p{{margin:0;font-size:.85rem;color:rgba(255,255,255,.7);text-align:center;max-width:520px}}
  a.go{{display:block;background:#FD890E;color:#fff;font-weight:700;font-size:1.05rem;padding:16px 32px;border-radius:10px;text-decoration:none;text-align:center}}
  a.alt{{color:rgba(255,255,255,.7);font-size:.8rem}}
</style>
</head>
<body>
<h1>{name}</h1>
<p>{desc}</p>
<a class="go" href="{cal_url}">Open this calendar &rarr;</a>
<a class="alt" href="/gov/">All government calendars</a>
<script>
location.replace({cal_json});
</script>
</body>
</html>
"""

INDEX_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Government calendars &mdash; CB6</title>
<meta property="og:title" content="Government calendars \u2014 CB6">
<meta property="og:description" content="Every community board, City Council committee, borough president and city agency with a calendar on bkcb6.app.">
<meta property="og:image" content="{img}">
<meta property="og:url" content="{site}/gov/">
<meta name="twitter:card" content="summary_large_image">
<style>
  :root{{--navy:#132D65;--orange:#FD890E;--muted:#5c6579;--border:#dfe4ee}}
  body{{margin:0;background:#f6f7fb;color:var(--navy);font-family:'DM Sans',system-ui,sans-serif;padding:24px 16px 60px}}
  .wrap{{max-width:840px;margin:0 auto}}
  h1{{font-size:1.5rem;margin:0 0 6px}}
  .sub{{color:var(--muted);font-size:.9rem;margin:0 0 24px}}
  h2{{font-size:.72rem;font-family:'DM Mono',monospace;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:26px 0 10px}}
  ul{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:8px}}
  a.card{{display:flex;align-items:center;justify-content:space-between;gap:10px;background:#fff;border:1.5px solid var(--border);border-radius:9px;padding:11px 13px;text-decoration:none;color:var(--navy);font-weight:600;font-size:.87rem}}
  a.card:hover{{border-color:var(--navy)}}
  .n{{font-family:'DM Mono',monospace;font-size:.72rem;color:var(--muted);font-weight:500;white-space:nowrap}}
  .back{{display:inline-block;margin-top:30px;color:var(--muted);font-size:.85rem}}
</style>
</head>
<body>
<div class="wrap">
<h1>Government calendars</h1>
<p class="sub">Each one opens on its own, so you see only that body&rsquo;s meetings.</p>
"""

GROUP_ORDER = ["Brooklyn Community Boards", "NYC Council",
               "Borough Presidents", "City Agencies"]


def main():
    entities = collect()
    if not entities:
        sys.exit("no civic-calendar data found; run the Action first")
    os.makedirs(OUT_DIR, exist_ok=True)

    for key, row in entities.items():
        cal_url = "%s/calendar.html?civic=%s&entity=%s" % (SITE, row["source"], key)
        count = row["count"]
        desc = ("%s upcoming meeting%s on the Brooklyn Community Board 6 "
                "community calendar." % (count, "" if count == 1 else "s")
                if count else
                "Meetings for %s on the Brooklyn Community Board 6 community "
                "calendar." % row["name"])
        with open(os.path.join(OUT_DIR, key + ".html"), "w", encoding="utf-8") as fh:
            fh.write(PAGE.format(
                name=html.escape(row["name"], quote=True),
                desc=html.escape(desc, quote=True),
                img="%s/%s" % (SITE, CARD),
                page_url="%s/gov/%s.html" % (SITE, key),
                cal_url=html.escape(cal_url, quote=True),
                cal_json=json.dumps(cal_url),
            ))

    groups = {}
    for key, row in entities.items():
        groups.setdefault(row["group"], []).append((key, row))
    for rows in groups.values():
        rows.sort(key=lambda kv: (-kv[1]["count"], kv[1]["name"]))

    parts = [INDEX_HEAD.format(img="%s/%s" % (SITE, CARD), site=SITE)]
    for group in GROUP_ORDER + [g for g in groups if g not in GROUP_ORDER]:
        rows = groups.get(group)
        if not rows:
            continue
        parts.append("<h2>%s</h2>\n<ul>\n" % html.escape(group))
        for key, row in rows:
            parts.append(
                '<li><a class="card" href="/gov/%s.html"><span>%s</span>'
                '<span class="n">%d</span></a></li>\n'
                % (key, html.escape(row["name"]), row["count"]))
        parts.append("</ul>\n")
    parts.append('<a class="back" href="/calendar.html">&larr; Full calendar</a>\n'
                 "</div>\n</body>\n</html>\n")
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write("".join(parts))

    print("entity pages written: %d" % len(entities))
    for group in GROUP_ORDER:
        if group in groups:
            print("  %-28s %d" % (group, len(groups[group])))
    print("directory: /gov/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
