#!/usr/bin/env python3
"""Build /agencies (directory), /agencies/<slug>/ (profiles), site-icons/agencies/*.png (700x700 tiles)
and data/agencies.json from the official nyc.gov agency directory feed.

Source: https://www.nyc.gov/bin/nyc/agencydirectory.json (the feed behind
https://www.nyc.gov/main/your-government/agency-directory). Only records with
listed_in_nyc_gov_agency == true are used, which is exactly what nyc.gov lists.
Descriptions come from the site's own govhub copy where the agency is already
described there, otherwise from the agency's own site meta description. Nothing is invented.
"""
import json, re, os, html, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/agencydirectory.json'
META = sys.argv[2] if len(sys.argv) > 2 else '/home/claude/agency-meta.json'
PILLS = sys.argv[3] if len(sys.argv) > 3 else '/home/claude/govhub-pills.json'

NAVY = (13, 27, 75); ORANGE = (244, 121, 32); OFF = (248, 247, 244); LINE = (229, 226, 219); MUTED = (107, 103, 96)
SANS = os.path.join(ROOT, 'assets/fonts/DMSans-Bold.ttf')
MONO = os.path.join(ROOT, 'assets/fonts/DMMono-Medium.ttf')

raw = json.load(open(SRC))
meta = json.load(open(META)) if os.path.exists(META) else {}
pills = json.load(open(PILLS)) if os.path.exists(PILLS) else []

L = [r for r in raw if r.get('listed_in_nyc_gov_agency') in (1, True, '1')]

TYPE_ORDER = [
    ('Mayoral Agency', 'Mayoral agencies', 'The line agencies. Each is run by a commissioner or director the Mayor appoints.'),
    ('Mayoral Office', 'Mayoral offices', 'Offices inside City Hall and the deputy mayors who oversee the agencies.'),
    ('Elected Office', 'Elected offices', 'Offices New Yorkers vote for directly.'),
    ('Advisory or Regulatory Organization', 'Boards and commissions', 'Advisory, regulatory and oversight bodies.'),
    ('Division', 'Divisions', 'Units that sit inside a larger agency or office.'),
    ('Public Benefit or Development Organization', 'Public benefit corporations', 'City-created corporations and authorities.'),
    ('Pension Fund', 'Pension funds', 'The retirement systems for city workers.'),
    ('Nonprofit Organization', 'Affiliated nonprofits', 'Independent nonprofits that work with or for the city.'),
    ('State Government Agency', 'State agencies listed by the city', 'State entities the city directory includes.'),
]
TYPE_LABEL = {t: lab for t, lab, _ in TYPE_ORDER}
SINGULAR = {'Mayoral Agency': 'Mayoral agency', 'Mayoral Office': 'Mayoral office', 'Elected Office': 'Elected office',
            'Advisory or Regulatory Organization': 'Board or commission', 'Division': 'Division',
            'Public Benefit or Development Organization': 'Public benefit corporation', 'Pension Fund': 'Pension fund',
            'Nonprofit Organization': 'Affiliated nonprofit', 'State Government Agency': 'State agency listed by the city'}

# ---- existing site links for elected offices (keep people on bkcb6.app) ----
ELECTED_LINK = {
    'Office of the Mayor': '/mayor',
    'Office of the New York City Comptroller': '/comptroller',
    'Office of the Public Advocate': '/publicadvocate',
    'Office of the Borough President of Brooklyn': '/bpbrooklyn',
    'Office of the Borough President of The Bronx': '/bpbronx',
    'Office of the Borough President of Manhattan': '/bpmanhattan',
    'Office of the Borough President of Queens': '/bpqueens',
    'Office of the Borough President of Staten Island': '/bpstatenisland',
    'Manhattan District Attorney\'s Office': '/dabragg',
    'Bronx District Attorney\'s Office': '/daclark',
    'Brooklyn District Attorney\'s Office': '/dagonzalez',
    'Queens District Attorney\'s Office': '/dakatz',
    'Staten Island District Attorney\'s Office': '/damcmahon',
    'New York City Council': '/electeds',
    'Community Boards': '/electeds',
}
for k, v in list(ELECTED_LINK.items()):
    p = os.path.join(ROOT, v.lstrip('/'))
    if not (os.path.isdir(p) or os.path.exists(p + '.html') or os.path.exists(p + '/index.html')):
        del ELECTED_LINK[k]

# ---- match govhub descriptions ----
def norm(s):
    s = s.lower().replace('&', 'and').replace('’', "'")
    s = re.sub(r"\bdept\b", 'department', s)
    s = re.sub(r"mayor's office (of|for|to)\b", '', s)
    s = re.sub(r"^(office (of|for|to)|department (of|for)|new york city|nyc)\s+", '', s).strip()
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()

pill_by_acr, pill_by_name = {}, {}
for p in pills:
    lab = p['label']
    if '—' in lab:
        acr, nm = [x.strip() for x in lab.split('—', 1)]
        pill_by_acr.setdefault(acr.upper(), p)
        pill_by_name.setdefault(norm(nm), p)
    else:
        pill_by_name.setdefault(norm(lab), p)
STATE_PILL_ACR = {'DOT', 'DOH', 'DOS', 'DOL'}  # ambiguous acronyms that are state entries in govhub

MANUAL_PILL = {'MWBE': 'M/WBE Office', 'CCHR': 'CHR', 'OPGV': 'Office of Gun Violence Prevention'}
# site meta descriptions that are boilerplate or slogans rather than a description of the office
BAD_META = {'NYC_GOID_%s' % x for x in ()}
def bad_meta(d):
    return bool(re.search(r'page excerpt|board of trustees meeting|official guide to|brave justice|^new york city police pension fund$', d, re.I))

def find_desc(r):
    acr = (r.get('acronym') or '').upper()
    name = r['name']
    p = None
    if acr in MANUAL_PILL:
        p = pill_by_acr.get(MANUAL_PILL[acr]) or pill_by_name.get(norm(MANUAL_PILL[acr]))
    if not p and acr and acr in pill_by_acr and not (acr in STATE_PILL_ACR and 'state' in pill_by_acr[acr]['desc'].lower()):
        p = pill_by_acr[acr]
    if not p:
        p = pill_by_name.get(norm(name))
    if not p:
        for alt in aslist(r.get('alternate_or_former_names')):
            p = pill_by_name.get(norm(alt))
            if p: break
    if p:
        d = re.sub(r'\s*[\u2014\u2013]\s*', ', ', p['desc'])
        # keep govhub copy, but the profile is citywide: keep CB6 context sentences as written
        return d, 'bkcb6.app'
    m = meta.get(r['record_id']) or {}
    d = (m.get('desc') or m.get('og') or '').strip()
    if d and len(d) > 30 and not re.match(r'^(nyc\.gov|home|welcome)\b', d, re.I) and not bad_meta(d):
        return d, 'official site'
    return '', ''

def aslist(v):
    if not v: return []
    if isinstance(v, list): return [str(x) for x in v if x]
    return [x.strip() for x in re.split(r'\s*[;|]\s*', str(v)) if x.strip()]

# ---- slugs ----
def slugify(s):
    s = s.lower().replace("'", '').replace('’', '').replace('+', ' plus ')
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s

used = {}
agencies = []
for r in sorted(L, key=lambda x: x['name_alphabetized'].lower()):
    acr = (r.get('acronym') or '').strip()
    slug = slugify(acr) if acr and len(acr) <= 12 else slugify(r['name'])
    if slug in used or len(slug) < 2:
        slug = slugify(r['name'])
    base = slug; n = 2
    while slug in used:
        slug = f'{base}-{n}'; n += 1
    used[slug] = True
    url = (r.get('url') or {}).get('url', '') or ''
    contact = (r.get('principal_officer_contact') or {}).get('url', '') or ''
    desc, dsrc = find_desc(r)
    agencies.append({
        'id': r['record_id'], 'slug': slug, 'name': r['name'], 'sort': r['name_alphabetized'],
        'acronym': acr, 'type': r['organization_type'],
        'officer': r.get('principal_officer_full_name', '') or '', 'title': r.get('principal_officer_title', '') or '',
        'reports_to': r.get('reports_to', '') or '', 'url': url, 'contact': contact,
        'alt_names': aslist(r.get('alternate_or_former_names')), 'alt_acronyms': aslist(r.get('alternate_or_former_acronyms')),
        'desc': desc, 'desc_src': dsrc, 'site_link': ELECTED_LINK.get(r['name'], ''),
    })

name_to_slug = {a['name']: a['slug'] for a in agencies}
os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
json.dump({'source': 'https://www.nyc.gov/bin/nyc/agencydirectory.json', 'count': len(agencies), 'agencies': agencies},
          open(os.path.join(ROOT, 'data/agencies.json'), 'w'), indent=0, ensure_ascii=False)

# ---- tiles 700x700 ----
ICON_DIR = os.path.join(ROOT, 'site-icons/agencies'); os.makedirs(ICON_DIR, exist_ok=True)
W = 700

def wrap(d, text, font, maxw):
    words = text.split(); lines = []; cur = ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def fit(d, text, path, maxw, maxh, start, minsz, maxlines):
    for sz in range(start, minsz - 1, -2):
        f = ImageFont.truetype(path, sz)
        lines = wrap(d, text, f, maxw)
        lh = int(sz * 1.08)
        if len(lines) <= maxlines and len(lines) * lh <= maxh and all(d.textlength(l, font=f) <= maxw for l in lines):
            return f, lines, lh
    f = ImageFont.truetype(path, minsz); return f, wrap(d, text, f, maxw)[:maxlines], int(minsz * 1.08)

def tile(a):
    im = Image.new('RGB', (W, W), (255, 255, 255)); d = ImageDraw.Draw(im)
    top = 118
    d.rectangle([0, 0, W, top], fill=NAVY)
    eb = ImageFont.truetype(MONO, 22)
    d.text((44, 34), 'NYC.GOV', font=eb, fill=ORANGE)
    d.text((44, 68), TYPE_LABEL[a['type']].upper(), font=eb, fill=(255, 255, 255))
    d.rectangle([0, W - 28, W, W], fill=ORANGE)
    d.rectangle([0, 0, W - 1, W - 1], outline=LINE, width=2)
    body_top = top + 40; body_h = W - 28 - body_top - 40
    big = a['acronym'] if a['acronym'] and len(a['acronym']) <= 8 else ''
    if big:
        f, lines, lh = fit(d, big, SANS, W - 88, 190, 190, 60, 1)
        y = body_top + 12
        for l in lines:
            d.text((44, y), l, font=f, fill=NAVY); y += lh
        f2, lines2, lh2 = fit(d, a['name'], SANS, W - 88, body_h - (y - body_top) - 30, 44, 26, 4)
        y += 24
        for l in lines2:
            d.text((44, y), l, font=f2, fill=MUTED); y += lh2
    else:
        f, lines, lh = fit(d, a['name'], SANS, W - 88, body_h - 40, 78, 34, 5)
        y = body_top + 16
        for l in lines:
            d.text((44, y), l, font=f, fill=NAVY); y += lh
    # accent rule
    d.rectangle([44, W - 72, 44 + 160, W - 64], fill=ORANGE)
    im = im.convert('P', palette=Image.ADAPTIVE, colors=64)
    im.save(os.path.join(ICON_DIR, a['slug'] + '.png'), optimize=True)

for a in agencies: tile(a)

# ---- shared CSS (same as /electeds and the office profiles) ----
DIR_CSS = open(os.path.join(ROOT, 'electeds/index.html')).read()
DIR_CSS = DIR_CSS[DIR_CSS.find('<style>'):DIR_CSS.rfind('</style>') + 8]
PROF = open(os.path.join(ROOT, 'mayor/index.html')).read()
PROF_CSS = ''.join('<style>' + x + '</style>' for x in re.findall(r'<style>(.*?)</style>', PROF, re.S))
CF = '<!-- Cloudflare Web Analytics --><script type=\'module\' src=\'https://static.cloudflareinsights.com/beacon.min.js\' data-cf-beacon=\'{"token": "b6e9b47ba0cf416388d72db8edaf4198"}\'></script><!-- End Cloudflare Web Analytics -->'
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700;900&display=swap" rel="stylesheet">')
E = html.escape

def head(title, desc, canon, og):
    return (f'<!DOCTYPE html>\n<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{E(title)} &mdash; bkcb6.app</title>\n<meta name="description" content="{E(desc)}">\n'
            f'<link rel="canonical" href="https://bkcb6.app{canon}">\n'
            f'<meta property="og:site_name" content="Brooklyn Community Board 6"><meta property="og:type" content="website">\n'
            f'<meta property="og:title" content="{E(title)}"><meta property="og:url" content="https://bkcb6.app{canon}">\n'
            f'<meta property="og:description" content="{E(desc)}">\n'
            f'<meta property="og:image" content="https://bkcb6.app{og}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="https://bkcb6.app{og}">\n'
            + FONTS + '\n')

# ---- directory ----
by = {}
for a in agencies: by.setdefault(a['type'], []).append(a)
secs = []
for t, lab, blurb in TYPE_ORDER:
    rows = by.get(t, [])
    if not rows: continue
    li = ''
    for a in rows:
        kd = E(a['officer'] + (', ' + a['title'] if a['title'] else '')) if a['officer'] else E(a['title'] or TYPE_LABEL[t])
        ad = E(a['acronym']) if a['acronym'] else E(a['reports_to'])
        li += (f'<li class="row"><a class="rowlink" href="/agencies/{a["slug"]}/"><span class="ico"><img src="/site-icons/agencies/{a["slug"]}.png" alt="" loading="lazy" width="700" height="700"></span>'
               f'<span class="txt"><span class="nm">{E(a["name"])}</span><span class="kd">{kd}</span><span class="ad">{ad}</span></span></a></li>')
    sid = slugify(lab)
    secs.append(f'<section class="dsub" id="{sid}"><button type="button" class="shead" aria-expanded="false"><span class="sname">{E(lab)}</span><span class="scount">{len(rows)}</span><span class="sarr">&#9660;</span></button>'
                f'<div class="sbody" hidden><p class="blurb">{E(blurb)}</p><input class="ssearch" type="search" placeholder="Search this list" autocomplete="off"><ul class="rows">{li}</ul><div class="snone" hidden>Nothing here matches.</div></div></section>')

DIR_JS = PROF_JS = None
DIR_JS = open(os.path.join(ROOT, 'electeds/index.html')).read()
DIR_JS = DIR_JS[DIR_JS.rfind('<script>'):DIR_JS.rfind('</script>') + 9]

n = len(agencies)
directory = (head('NYC Agency Directory', f'Every one of the {n} agencies, offices, boards and commissions in the nyc.gov agency directory, who runs each one and where it sits in city government.', '/agencies', '/og-agencies.jpg')
    + DIR_CSS + '\n' + CF + '\n</head><body>\n<div class="wrap">\n<header>\n'
    '  <div class="crumb"><a href="/">CB6 &amp; Beyond</a> &middot; <a href="/government/">Government</a></div>\n'
    '  <h1>NYC Agency <span>Directory</span></h1>\n'
    f'  <div class="sub">{n} agencies, offices, boards and commissions, as listed by nyc.gov</div>\n</header>\n'
    '<div class="intro"><p>Search an agency, an acronym, a commissioner or a deputy mayor and every match opens at once. Or open a section to read the full list. Every entry has its own page.</p></div>\n'
    '<div class="tools"><input id="q" type="search" placeholder="Search an agency, acronym or name" autocomplete="off"></div>\n'
    '<div class="none" id="none" hidden>Nothing matches that.</div>\n'
    f'<section class="lvl" id="city"><div class="lhead"><span class="lname">City of New York</span><span class="lcount">{n}</span></div>{"".join(secs)}</section>\n'
    '<div class="foot">\n  Names, titles, reporting lines and links from the official nyc.gov agency directory feed, read the day this page was built. What each agency does is written here on bkcb6.app or taken from the agency&rsquo;s own site.<br>\n'
    '  <a href="/electeds">Who Represents You</a> &middot; <a href="/govhub.html">City government org chart</a> &middot; <a href="/directory">The Address Directory</a>\n</div>\n</div>\n'
    + DIR_JS + '\n</body></html>\n')
os.makedirs(os.path.join(ROOT, 'agencies'), exist_ok=True)
open(os.path.join(ROOT, 'agencies/index.html'), 'w').write(directory)

# ---- profiles ----
def profile(a):
    t = TYPE_LABEL[a['type']]
    canon = f'/agencies/{a["slug"]}/'
    lead = ''
    if a['officer']:
        lead = f'<p>Led by <b>{E(a["officer"])}</b>' + (f', {E(a["title"])}' if a['title'] else '') + '.</p>'
    elif a['title']:
        lead = f'<p>Led by a {E(a["title"])}; the seat is not filled in the current city directory.</p>'
    rep = ''
    if a['reports_to']:
        rs = name_to_slug.get(a['reports_to'])
        rep = f'<p>Reports to <b>' + (f'<a href="/agencies/{rs}/">{E(a["reports_to"])}</a>' if rs else E(a['reports_to'])) + '</b>.</p>'
    acr = f' It goes by <b>{E(a["acronym"])}</b>.' if a['acronym'] else ''
    alt = ''
    alts = a['alt_names'] + a['alt_acronyms']
    if alts:
        alt = f'<p>Also known as, or formerly, {E(", ".join(alts))}.</p>'
    what = ''
    if a['desc']:
        src = 'As described on bkcb6.app.' if a['desc_src'] == 'bkcb6.app' else 'In the agency&rsquo;s own words, from its website.'
        what = f'<div class="sec"><h2>What it does</h2><div class="wide"><p>{E(a["desc"])}</p><p class="secnote">{src}</p></div></div>'
    # children: entries that report to this one
    kids = [b for b in agencies if b['reports_to'] == a['name']]
    kidhtml = ''
    if kids:
        kidhtml = '<div class="sec"><h2>Reports to this office</h2><ul class="cmt">' + ''.join(
            f'<li><span class="cn"><a href="/agencies/{b["slug"]}/" style="color:var(--navy);text-decoration:none">{E(b["name"])}</a></span></li>' for b in kids) + '</ul></div>'
    btns = ''
    if a['site_link']:
        btns += f'<a class="btn hot" href="{a["site_link"]}">Officeholder profile on bkcb6.app</a>'
    if a['url']:
        btns += f'<a class="btn{"" if a["site_link"] else " hot"}" href="{E(a["url"])}" target="_blank" rel="noopener">Official site &#8599;</a>'
    if a['contact'] and a['contact'] != a['url']:
        btns += f'<a class="btn" href="{E(a["contact"])}" target="_blank" rel="noopener">Contact &#8599;</a>'
    btns += '<a class="btn" href="/agencies/">Agency directory</a><a class="btn" href="/govhub.html">The Government Hub</a>'
    desc = (a['desc'][:150] + ('…' if len(a['desc']) > 150 else '')) if a['desc'] else f'{a["name"]}: who runs it, where it sits in city government, and how to reach it.'
    return (head(a['name'], desc, canon, f'/site-icons/agencies/{a["slug"]}.png')
        + PROF_CSS + '\n' + CF + '\n</head><body>\n<div class="pwrap">\n  <div class="phead">\n'
        f'    <span class="pmark"><img src="/site-icons/agencies/{a["slug"]}.png" alt="{E(a["name"])}"></span>\n    <span>\n'
        '      <div class="pcrumb"><a href="/" style="color:inherit">bkcb6.app</a> &middot; <a href="/agencies/" style="color:inherit">Agencies</a></div>\n'
        f'      <h1>{E(a["name"])}</h1>\n      <div class="pseat">{E(SINGULAR[a["type"]])}' + (f' &middot; {E(a["acronym"])}' if a['acronym'] else '') + '</div>\n    </span>\n  </div>\n'
        f'<div class="sec"><h2>In brief</h2><div class="bio"><p><b>{E(a["name"])}</b> is listed by nyc.gov under <b>{E(t.lower())}</b>.{acr}</p>{lead}{rep}{alt}</div></div>'
        + what + kidhtml +
        f'<div class="sec"><h2>Go on</h2><div class="btns">{btns}</div></div>\n'
        '  <div class="pfoot">Name, leadership, reporting line and links from the official nyc.gov agency directory feed. Agency leadership changes; the official site is the final word.<br>\n'
        '  <a href="/agencies/">NYC Agency Directory</a> &middot; <a href="/electeds">Who Represents You</a> &middot; <a href="/govhub.html">The Government Hub</a></div>\n</div>\n</body></html>\n')

for a in agencies:
    p = os.path.join(ROOT, 'agencies', a['slug']); os.makedirs(p, exist_ok=True)
    open(os.path.join(p, 'index.html'), 'w').write(profile(a))

print('agencies', n, 'with desc', sum(1 for a in agencies if a['desc']), '(govhub', sum(1 for a in agencies if a['desc_src'] == 'bkcb6.app'), ')')
