#!/usr/bin/env python3
"""Build /agencies/nys (directory) and /agencies/nys/<slug>/ (profiles) for the 98 entries on
https://www.ny.gov/agencies, with 700x700 tiles from the state's own agency cards.
Inputs: /tmp/nys-agencies-raw.json (name, category, ny.gov page, card image, description as
published on ny.gov), /tmp/urls.json (agency's own site), /tmp/urlcheck.json (live check)."""
import json, re, os, html
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAVY = (13, 27, 75); ORANGE = (244, 121, 32); LINE = (229, 226, 219)
raw = json.load(open('/tmp/nys-agencies-raw.json'))
urls = json.load(open('/tmp/urls.json')); chk = json.load(open('/tmp/urlcheck.json'))
E = html.escape
def slugify(n): return re.sub(r'[^a-z0-9]+', '-', n.lower().replace("'", '')).strip('-')
CATS = ['Administration', 'Business', 'Education', 'Health and Human Services', 'Local and Regional Authorities',
        'Public Safety', 'Recreation and Environment', 'Statewide Elected Officials', 'Transportation and Utilities']
BLURB = {'Administration': 'The offices that run the state government itself.', 'Business': 'Licensing, regulation, labor, tax and economic development.',
 'Education': 'Schools, universities and student aid.', 'Health and Human Services': 'Health, housing, children, aging and disability services.',
 'Local and Regional Authorities': 'Authorities and bodies with a local or regional footprint.', 'Public Safety': 'Police, corrections, emergency services and oversight.',
 'Recreation and Environment': 'Parks, the environment, arts and regional land use.', 'Statewide Elected Officials': 'The Governor, Comptroller, Attorney General and the Legislature.',
 'Transportation and Utilities': 'Roads, transit, bridges, energy and utilities.'}
STATE_PROFILE = {'Office of the Governor': '/governor', 'New York State Senate': '/electeds', 'New York Assembly': '/electeds'}
for k, v in list(STATE_PROFILE.items()):
    if not os.path.isdir(os.path.join(ROOT, v.lstrip('/'))): del STATE_PROFILE[k]
ag = []
for r in sorted(raw, key=lambda x: x['name'].lower()):
    s = slugify(r['name']); site = urls[r['name']]
    code = chk[r['name']].split(' ')[0]
    live_host = code != '000'                     # 403/503 here are the state's bot challenge, the host answers
    subpath = bool(re.sub(r'^https?://[^/]+/?', '', site))
    if not live_host: site = r['ny']              # fall back to the ny.gov page, which redirects to the agency
    elif subpath: site = re.match(r'https?://[^/]+/', site).group(0)   # page inside a parent site; link the parent root
    cats = [c.strip() for c in r['cat'].split(',')]
    ag.append({'slug': s, 'name': r['name'], 'cats': cats, 'cat': cats[0], 'ny': r['ny'], 'site': site,
               'desc': re.sub(r'\s*[\u2014\u2013]\s*', ', ', r['desc']), 'site_link': STATE_PROFILE.get(r['name'], '')})
json.dump({'source': 'https://www.ny.gov/agencies', 'count': len(ag), 'agencies': ag}, open(os.path.join(ROOT, 'data/agencies-nys.json'), 'w'), indent=0, ensure_ascii=False)

ICON = os.path.join(ROOT, 'site-icons/agencies/nys'); os.makedirs(ICON, exist_ok=True)
W = 700
for a in ag:
    lg = Image.open(os.path.join(ROOT, 'assets/agency-logos/nys', a['slug'] + '.png')).convert('RGBA')
    im = Image.new('RGB', (W, W), (255, 255, 255)); d = ImageDraw.Draw(im)
    if abs(lg.width - lg.height) < 4:            # the state's square card: fill the tile
        lg = lg.resize((W, W - 28), Image.LANCZOS); im.paste(lg, (0, 0), lg)
    else:
        pad = 70; sc = min((W - 2 * pad) / lg.width, (W - 28 - 2 * pad) / lg.height)
        lg = lg.resize((int(lg.width * sc), int(lg.height * sc)), Image.LANCZOS); im.paste(lg, ((W - lg.width) // 2, (W - 28 - lg.height) // 2), lg)
        d.rectangle([0, 0, W - 1, W - 1], outline=LINE, width=2)
    d.rectangle([0, W - 28, W, W], fill=ORANGE)
    im.convert('P', palette=Image.ADAPTIVE, colors=128).save(os.path.join(ICON, a['slug'] + '.png'), optimize=True)

DIR = open(os.path.join(ROOT, 'electeds/index.html')).read()
DIR_CSS = DIR[DIR.find('<style>'):DIR.rfind('</style>') + 8]; DIR_JS = DIR[DIR.rfind('<script>'):DIR.rfind('</script>') + 9]
PROF = open(os.path.join(ROOT, 'mayor/index.html')).read()
PROF_CSS = ''.join('<style>' + x + '</style>' for x in re.findall(r'<style>(.*?)</style>', PROF, re.S))
CF = '<!-- Cloudflare Web Analytics --><script type=\'module\' src=\'https://static.cloudflareinsights.com/beacon.min.js\' data-cf-beacon=\'{"token": "b6e9b47ba0cf416388d72db8edaf4198"}\'></script><!-- End Cloudflare Web Analytics -->'
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700;900&display=swap" rel="stylesheet">')
def head(title, desc, canon, og):
    return (f'<!DOCTYPE html>\n<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{E(title)} &mdash; bkcb6.app</title>\n<meta name="description" content="{E(desc)}">\n<link rel="canonical" href="https://bkcb6.app{canon}">\n'
            f'<meta property="og:site_name" content="Brooklyn Community Board 6"><meta property="og:type" content="website">\n'
            f'<meta property="og:title" content="{E(title)}"><meta property="og:url" content="https://bkcb6.app{canon}">\n<meta property="og:description" content="{E(desc)}">\n'
            f'<meta property="og:image" content="https://bkcb6.app{og}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://bkcb6.app{og}">\n' + FONTS + '\n')
n = len(ag); secs = []
for c in CATS:
    rows = [a for a in ag if a['cat'] == c]
    if not rows: continue
    li = ''.join(f'<li class="row"><a class="rowlink" href="/agencies/nys/{a["slug"]}/"><span class="ico"><img src="/site-icons/agencies/nys/{a["slug"]}.png" alt="" loading="lazy" width="700" height="700"></span>'
                 f'<span class="txt"><span class="nm">{E(a["name"])}</span><span class="kd">{E(a["desc"][:110] + ("…" if len(a["desc"]) > 110 else ""))}</span><span class="ad">{E(", ".join(a["cats"]))}</span></span></a></li>' for a in rows)
    secs.append(f'<section class="dsub" id="{slugify(c)}"><button type="button" class="shead" aria-expanded="false"><span class="sname">{E(c)}</span><span class="scount">{len(rows)}</span><span class="sarr">&#9660;</span></button>'
                f'<div class="sbody" hidden><p class="blurb">{E(BLURB[c])}</p><input class="ssearch" type="search" placeholder="Search this list" autocomplete="off"><ul class="rows">{li}</ul><div class="snone" hidden>Nothing here matches.</div></div></section>')
page = (head('New York State Agency Directory', f'All {n} agencies, authorities, boards and offices listed on ny.gov, what each does and where to reach it.', '/agencies/nys', '/og-agencies-nys.jpg')
    + DIR_CSS + '\n' + CF + '\n</head><body>\n<div class="wrap">\n<header>\n  <div class="crumb"><a href="/">CB6 &amp; Beyond</a> &middot; <a href="/government/">Government</a> &middot; <a href="/agencies/">NYC Agencies</a></div>\n'
    '  <h1>New York State Agency <span>Directory</span></h1>\n' + f'  <div class="sub">{n} agencies, authorities, boards and offices, as listed by ny.gov</div>\n</header>\n'
    '<div class="intro"><p>Search an agency or what it does and every match opens at once. Or open a section, sorted the way ny.gov sorts them. Every entry has its own page. City agencies are in the <a href="/agencies/">NYC Agency Directory</a>.</p></div>\n'
    '<div class="tools"><input id="q" type="search" placeholder="Search a state agency" autocomplete="off"></div>\n<div class="none" id="none" hidden>Nothing matches that.</div>\n'
    f'<section class="lvl" id="state"><div class="lhead"><span class="lname">State of New York</span><span class="lcount">{n}</span></div>{"".join(secs)}</section>\n'
    '<div class="foot">\n  Names, groupings, descriptions and tiles are the state&rsquo;s own, from ny.gov/agencies, read the day this page was built. Each agency&rsquo;s site link was checked live.<br>\n'
    '  <a href="/agencies/">NYC Agency Directory</a> &middot; <a href="/electeds">Who Represents You</a> &middot; <a href="/govhub.html">City government org chart</a>\n</div>\n</div>\n' + DIR_JS + '\n</body></html>\n')
os.makedirs(os.path.join(ROOT, 'agencies/nys'), exist_ok=True)
open(os.path.join(ROOT, 'agencies/nys/index.html'), 'w').write(page)
for a in ag:
    canon = f'/agencies/nys/{a["slug"]}/'
    btns = (f'<a class="btn hot" href="{a["site_link"]}">Officeholder profile on bkcb6.app</a>' if a['site_link'] else '')
    btns += f'<a class="btn{"" if a["site_link"] else " hot"}" href="{E(a["site"])}" target="_blank" rel="noopener">Official site &#8599;</a>'
    if a['site'] != a['ny']: btns += f'<a class="btn" href="{E(a["ny"])}" target="_blank" rel="noopener">On ny.gov &#8599;</a>'
    btns += '<a class="btn" href="/agencies/nys/">State agency directory</a><a class="btn" href="/agencies/">NYC agency directory</a>'
    what = f'<div class="sec"><h2>What it does</h2><div class="wide"><p>{E(a["desc"])}</p><p class="secnote">In the state&rsquo;s own words, from ny.gov.</p></div></div>' if a['desc'] else ''
    desc = (a['desc'][:150] + ('…' if len(a['desc']) > 150 else '')) if a['desc'] else f'{a["name"]}, a New York State agency: what it does and where to reach it.'
    open(os.path.join(ROOT, 'agencies/nys', a['slug'], 'index.html') if os.makedirs(os.path.join(ROOT, 'agencies/nys', a['slug']), exist_ok=True) is None else '', 'w').write(
        head(a['name'], desc, canon, f'/site-icons/agencies/nys/{a["slug"]}.png') + PROF_CSS + '\n' + CF + '\n</head><body>\n<div class="pwrap">\n  <div class="phead">\n'
        f'    <span class="pmark"><img src="/site-icons/agencies/nys/{a["slug"]}.png" alt="{E(a["name"])}"></span>\n    <span>\n'
        '      <div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="/agencies/nys/" style="color:inherit">State agencies</a></div>\n'
        f'      <h1>{E(a["name"])}</h1>\n      <div class="pseat">New York State &middot; {E(", ".join(a["cats"]))}</div>\n    </span>\n  </div>\n'
        f'<div class="sec"><h2>In brief</h2><div class="bio"><p><b>{E(a["name"])}</b> is a New York State agency, listed by ny.gov under <b>{E(" and ".join(a["cats"]))}</b>.</p></div></div>'
        + what + f'<div class="sec"><h2>Go on</h2><div class="btns">{btns}</div></div>\n'
        '  <div class="pfoot">Name, grouping, description and tile from ny.gov/agencies. The agency&rsquo;s own site is the final word.<br>\n'
        '  <a href="/agencies/nys/">New York State Agency Directory</a> &middot; <a href="/agencies/">NYC Agency Directory</a> &middot; <a href="/electeds">Who Represents You</a></div>\n</div>\n</body></html>\n')
print('state agencies', n, 'subpath-or-fallback sites', sum(1 for a in ag if a['site'] != urls[a['name']]))
