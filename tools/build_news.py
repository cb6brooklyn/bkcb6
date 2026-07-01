#!/usr/bin/env python3
"""
build_news.py  --  CB6 newsletter -> Google News-eligible web archive

Reads issues.json and writes, into ./news/ :
  - one article page per issue  (news/<slug>.html)
  - an archive index            (news/index.html)
  - a Google news sitemap       (news/news-sitemap.xml)  [articles < 48h]
  - a standard sitemap          (news/sitemap.xml)       [all articles]

Add new issues by appending an object to issues.json, then re-run:
  python3 build_news.py
Then deploy and bump sw.js cache version.
"""

import json
import html
import datetime
import pathlib

# ---- config -------------------------------------------------------------
SITE = "https://bkcb6.app"
BASE = "/news"                      # URL path where the archive lives
AUTHOR = "Mike Racioppo"
PUBLICATION = "Brooklyn Community Board 6"
TZ = "-04:00"                       # America/New_York, EDT
OUT = pathlib.Path(__file__).parent.parent / "news"   # repo-root/news
NEWS_WINDOW_HOURS = 48             # Google News sitemap only wants recent items
# ------------------------------------------------------------------------

OUT.mkdir(exist_ok=True)
issues = json.loads((pathlib.Path(__file__).parent / "issues.json").read_text())
# issues.json lives next to this script, in tools/
# newest first
issues.sort(key=lambda x: x["date"], reverse=True)


def iso(datestr, time="09:00:00"):
    return f"{datestr}T{time}{TZ}"


def render_body(blocks):
    out = []
    for b in blocks:
        if b["type"] == "p":
            out.append(f"      <p>{b['html']}</p>")
        elif b["type"] == "h2":
            out.append(f"      <h2>{html.escape(b['text'])}</h2>")
    return "\n".join(out)


def article_page(issue, prev_issue, next_issue):
    url = f"{SITE}{BASE}/{issue['slug']}.html"
    pub_iso = iso(issue["date"])
    title = html.escape(issue["title"])
    dek = html.escape(issue["dek"])

    # split "Wednesday, July 1, 2026" -> dow / month-day / year for masthead
    _d = datetime.date.fromisoformat(issue["date"])
    dow = _d.strftime("%A")
    md = _d.strftime("%B ") + str(_d.day)   # no leading zero on day
    yr = str(_d.year)

    ld = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": issue["title"],
        "description": issue["dek"],
        "datePublished": pub_iso,
        "dateModified": pub_iso,
        "author": {"@type": "Person", "name": AUTHOR,
                   "url": f"{SITE}/"},
        "publisher": {
            "@type": "Organization",
            "name": PUBLICATION,
            "logo": {"@type": "ImageObject",
                     "url": f"{SITE}/cb6-logo-square.png"},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "isPartOf": {"@type": "Newsletter",
                     "name": "Brooklyn Community Board 6 Newsletter"},
    }
    ld_json = json.dumps(ld, indent=2, ensure_ascii=False)

    nav = []
    if next_issue:  # chronologically newer
        nav.append(f'<a class="pn newer" href="{next_issue["slug"]}.html">'
                   f'&larr; Newer<span>{html.escape(next_issue["title"])}</span></a>')
    else:
        nav.append('<span></span>')
    if prev_issue:  # chronologically older
        nav.append(f'<a class="pn older" href="{prev_issue["slug"]}.html">'
                   f'Older &rarr;<span>{html.escape(prev_issue["title"])}</span></a>')
    else:
        nav.append('<span></span>')
    nav_html = "\n      ".join(nav)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &middot; CB6 Newsletter</title>
<meta name="description" content="{dek}">
<link rel="canonical" href="{url}">
<meta name="author" content="{html.escape(AUTHOR)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{html.escape(PUBLICATION)}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{dek}">
<meta property="og:url" content="{url}">
<meta property="article:published_time" content="{pub_iso}">
<meta property="article:author" content="{html.escape(AUTHOR)}">
<meta name="twitter:card" content="summary">
<script type="application/ld+json">
{ld_json}
</script>
<style>
  :root{{
    --navy:#06024D; --orange:#FD890E; --white:#FDFDFD;
    --ink:#1a1a2e; --paper:#ffffff; --rule:#e4e2ee;
    --muted:#5c5a72; --link:#1a3fb8;
    --measure:38rem;
  }}
  *{{box-sizing:border-box}}
  html{{-webkit-text-size-adjust:100%}}
  body{{
    margin:0; background:var(--paper); color:var(--ink);
    font-family:Georgia,"Iowan Old Style","Times New Roman",serif;
    line-height:1.62; font-size:19px;
  }}
  a{{color:var(--link)}}

  /* ── CB6 masthead ── */
  .masthead{{
    background:var(--navy); padding:22px 20px;
  }}
  .masthead-inner{{
    max-width:var(--measure); margin:0 auto;
    display:flex; align-items:center; gap:20px;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
  }}
  .cb6-mark{{
    flex:0 0 auto; border:3px solid var(--orange); border-radius:6px;
    padding:8px 14px 10px; text-align:center; line-height:1;
  }}
  .cb6-mark .big{{
    font-size:2.5rem; font-weight:900; color:var(--white);
    letter-spacing:-.02em; display:block;
  }}
  .cb6-mark .sub{{
    font-size:.5rem; font-weight:800; color:var(--orange);
    letter-spacing:.08em; margin-top:5px; display:block; line-height:1.25;
  }}
  .mast-date{{
    flex:1 1 auto; min-width:0; color:var(--white);
    font-weight:800; letter-spacing:-.01em; line-height:1.02;
  }}
  .mast-date .dow{{font-size:2.2rem; display:block}}
  .mast-date .md{{font-size:2.2rem}}
  .mast-date .yr{{font-size:2.2rem; color:var(--orange)}}

  .wrap{{max-width:var(--measure); margin:0 auto; padding:0 22px 96px}}

  .backbar{{
    max-width:var(--measure); margin:0 auto; padding:11px 22px;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
    font-size:12px; letter-spacing:.1em; text-transform:uppercase;
    font-weight:700; border-bottom:1px solid var(--rule);
    display:flex; justify-content:space-between; align-items:center;
  }}
  .backbar span{{color:var(--muted)}}
  .backbar a{{color:var(--navy); text-decoration:none}}

  article{{margin-top:30px}}
  .eyebrow{{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
    font-size:12px; letter-spacing:.12em; text-transform:uppercase;
    color:var(--orange); font-weight:800; margin:0 0 10px;
  }}
  h1{{
    font-size:2.15rem; line-height:1.12; margin:0 0 14px;
    font-weight:800; letter-spacing:-.01em; color:var(--navy);
  }}
  .dek{{
    font-size:1.12rem; color:var(--muted); font-style:italic;
    margin:0 0 22px; line-height:1.5;
  }}
  .byline{{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
    font-size:13px; color:var(--muted); border-top:2px solid var(--navy);
    border-bottom:1px solid var(--rule); padding:11px 0; margin:0 0 30px;
    display:flex; flex-wrap:wrap; gap:6px 16px;
  }}
  .byline strong{{color:var(--ink); font-weight:700}}
  article p{{margin:0 0 20px}}
  article h2{{
    font-size:1.3rem; margin:34px 0 12px; line-height:1.2; color:var(--navy);
  }}
  .signoff{{
    margin-top:34px; padding-top:20px; border-top:1px solid var(--rule);
    font-size:.95rem; color:var(--muted);
  }}
  .signoff .name{{color:var(--navy); font-weight:700; font-style:normal}}
  .source-note{{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
    font-size:12.5px; color:var(--muted); margin-top:26px;
    background:#f4f4fb; border:1px solid var(--rule);
    border-left:4px solid var(--orange); border-radius:6px;
    padding:12px 14px;
  }}
  nav.prevnext{{
    display:flex; justify-content:space-between; gap:14px; margin-top:44px;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
  }}
  nav.prevnext a{{
    text-decoration:none; color:var(--navy); font-size:13px; font-weight:700;
    max-width:47%;
  }}
  nav.prevnext a.older{{text-align:right; margin-left:auto}}
  nav.prevnext a span{{
    display:block; color:var(--muted); font-weight:400; font-size:14px;
    margin-top:3px; font-family:Georgia,serif;
  }}
  footer.site{{
    margin-top:56px; padding:24px 22px; background:var(--navy); color:var(--white);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
    font-size:12.5px; line-height:1.7; text-align:center;
  }}
  footer.site a{{color:var(--orange); text-decoration:none}}
  @media (max-width:480px){{
    body{{font-size:18px}} h1{{font-size:1.8rem}}
    .cb6-mark .big{{font-size:2rem}}
    .mast-date .dow, .mast-date .md, .mast-date .yr{{font-size:1.7rem}}
  }}
  @media (prefers-reduced-motion:no-preference){{
    article{{animation:fade .5s ease both}}
    @keyframes fade{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
  }}
</style>
</head>
<body>
  <div class="masthead">
    <div class="masthead-inner">
      <div class="cb6-mark">
        <span class="big">CB6</span>
        <span class="sub">BROOKLYN<br>COMMUNITY BOARD 6</span>
      </div>
      <div class="mast-date">
        <span class="dow">{dow}</span>
        <span class="md">{md} </span><span class="yr">{yr}</span>
      </div>
    </div>
  </div>
  <div class="backbar">
    <span>The CB6 Newsletter</span>
    <a href="index.html">All issues &rarr;</a>
  </div>

<div class="wrap">
  <article>
    <p class="eyebrow">District Manager\u2019s Notes</p>
    <h1>{title}</h1>
    <p class="dek">{dek}</p>
    <div class="byline">
      <span>By <strong>{html.escape(AUTHOR)}</strong>, District Manager</span>
      <span><time datetime="{pub_iso}">{issue['date_display']}</time></span>
    </div>

{render_body(issue['body'])}

    <div class="signoff">
      Best,<br>
      <span class="name">Mike Racioppo</span>, District Manager<br>
      Brooklyn Community Board 6 &middot; 250 Baltic Street, Brooklyn, NY 11201<br>
      <a href="mailto:Mike@bkcb6.org">Mike@bkcb6.org</a>
    </div>

    <p class="source-note">This is the web archive of a newsletter originally
    sent by email to Brooklyn Community Board 6 subscribers on
    {issue['date_display']}. The email edition may contain additional event
    listings and links.</p>
  </article>

  <nav class="prevnext">
      {nav_html}
  </nav>
</div>

<footer class="site">
    Brooklyn Community Board 6 &middot; 250 Baltic Street &middot; Brooklyn, NY 11201<br>
    <a href="{SITE}/">bkcb6.app</a> &middot;
    <a href="index.html">Newsletter archive</a> &middot;
    <a href="mailto:Mike@bkcb6.org">Contact</a>
</footer>
</body>
</html>
"""


def index_page(issues):
    rows = []
    for it in issues:
        rows.append(f"""      <li class="entry">
        <time datetime="{iso(it['date'])}">{it['date_display']}</time>
        <a href="{it['slug']}.html"><h2>{html.escape(it['title'])}</h2></a>
        <p>{html.escape(it['dek'])}</p>
      </li>""")
    rows_html = "\n".join(rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Newsletter Archive &middot; Brooklyn Community Board 6</title>
<meta name="description" content="Web archive of the Brooklyn Community Board 6 newsletter \u2014 District Manager Mike Racioppo\u2019s notes on elections, land use, heat, transit, and local government.">
<link rel="canonical" href="{SITE}{BASE}/">
<style>
  :root{{--navy:#06024D;--orange:#FD890E;--white:#FDFDFD;
    --ink:#1a1a2e;--paper:#ffffff;--rule:#e4e2ee;--muted:#5c5a72}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--paper);color:var(--ink);
    font-family:Georgia,"Iowan Old Style",serif;line-height:1.6}}
  .masthead{{background:var(--navy);padding:26px 20px}}
  .masthead-inner{{max-width:44rem;margin:0 auto;display:flex;align-items:center;gap:20px;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}}
  .cb6-mark{{flex:0 0 auto;border:3px solid var(--orange);border-radius:6px;
    padding:8px 14px 10px;text-align:center;line-height:1}}
  .cb6-mark .big{{font-size:2.5rem;font-weight:900;color:var(--white);
    letter-spacing:-.02em;display:block}}
  .cb6-mark .sub{{font-size:.5rem;font-weight:800;color:var(--orange);
    letter-spacing:.08em;margin-top:5px;display:block;line-height:1.25}}
  .mast-title{{flex:1 1 auto;color:var(--white)}}
  .mast-title .t{{font-size:2rem;font-weight:900;line-height:1.05;letter-spacing:-.01em}}
  .mast-title .t .accent{{color:var(--orange)}}
  .wrap{{max-width:44rem;margin:0 auto;padding:0 22px 90px}}
  .sub{{max-width:44rem;margin:0 auto;padding:16px 22px 0;color:var(--muted);
    font-style:italic}}
  ul{{list-style:none;padding:0;margin:20px 0 0}}
  .entry{{padding:22px 0;border-bottom:1px solid var(--rule)}}
  .entry time{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
    font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--orange);
    font-weight:800}}
  .entry a{{text-decoration:none;color:var(--ink)}}
  .entry h2{{font-size:1.4rem;margin:6px 0 8px;line-height:1.18;color:var(--navy)}}
  .entry a:hover h2{{color:var(--orange)}}
  .entry p{{margin:0;color:var(--muted);font-size:1.02rem}}
  footer.site{{margin-top:40px;padding:24px 22px;background:var(--navy);color:var(--white);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
    font-size:12.5px;text-align:center}}
  footer.site a{{color:var(--orange);text-decoration:none}}
  @media (max-width:480px){{
    .cb6-mark .big{{font-size:2rem}} .mast-title .t{{font-size:1.55rem}}
  }}
</style>
</head>
<body>
  <div class="masthead">
    <div class="masthead-inner">
      <div class="cb6-mark">
        <span class="big">CB6</span>
        <span class="sub">BROOKLYN<br>COMMUNITY BOARD 6</span>
      </div>
      <div class="mast-title">
        <div class="t">Newsletter <span class="accent">Archive</span></div>
      </div>
    </div>
  </div>
  <p class="sub">District Manager\u2019s notes on elections, land use, heat, transit, and local government.</p>
<div class="wrap">
  <ul>
{rows_html}
  </ul>
</div>
<footer class="site">
    Brooklyn Community Board 6 &middot; 250 Baltic Street &middot; Brooklyn, NY 11201<br>
    <a href="{SITE}/">bkcb6.app</a>
</footer>
</body>
</html>
"""


def news_sitemap(issues):
    now = datetime.datetime.now(datetime.timezone.utc)
    items = []
    for it in issues:
        pub = datetime.datetime.fromisoformat(iso(it["date"]))
        age_h = (now - pub).total_seconds() / 3600
        if age_h > NEWS_WINDOW_HOURS:
            continue
        url = f"{SITE}{BASE}/{it['slug']}.html"
        items.append(f"""  <url>
    <loc>{url}</loc>
    <news:news>
      <news:publication>
        <news:name>{PUBLICATION}</news:name>
        <news:language>en</news:language>
      </news:publication>
      <news:publication_date>{iso(it['date'])}</news:publication_date>
      <news:title>{html.escape(it['title'])}</news:title>
    </news:news>
  </url>""")
    body = "\n".join(items)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
{body}
</urlset>
"""


def full_sitemap(issues):
    items = [f"""  <url>
    <loc>{SITE}{BASE}/</loc>
  </url>"""]
    for it in issues:
        items.append(f"""  <url>
    <loc>{SITE}{BASE}/{it['slug']}.html</loc>
    <lastmod>{it['date']}</lastmod>
  </url>""")
    body = "\n".join(items)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{body}
</urlset>
"""


# ---- write everything ---------------------------------------------------
for i, issue in enumerate(issues):
    newer = issues[i - 1] if i > 0 else None          # chronologically newer
    older = issues[i + 1] if i + 1 < len(issues) else None
    (OUT / f"{issue['slug']}.html").write_text(
        article_page(issue, older, newer), encoding="utf-8")

(OUT / "index.html").write_text(index_page(issues), encoding="utf-8")
(OUT / "news-sitemap.xml").write_text(news_sitemap(issues), encoding="utf-8")
(OUT / "sitemap.xml").write_text(full_sitemap(issues), encoding="utf-8")

print(f"Built {len(issues)} article pages + index + 2 sitemaps into {OUT}/")
in_window = sum(
    1 for it in issues
    if (datetime.datetime.now(datetime.timezone.utc)
        - datetime.datetime.fromisoformat(iso(it['date']))).total_seconds()/3600
    <= NEWS_WINDOW_HOURS)
print(f"news-sitemap.xml currently lists {in_window} article(s) (< {NEWS_WINDOW_HOURS}h old)")
