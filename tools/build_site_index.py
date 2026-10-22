#!/usr/bin/env python3
"""Site search index and section rules for bkcb6.app.

Writes data/site-index.json: every page of the site (title, one line, section), minus the 82,000 block cards
(found by address search), the /bk/ mirror and the app folder, and keeps the section rules in assets/site-bar.js
in step with this file (the bar names the page's section from the same rules, without fetching the index).

Run from the repo root: python3 tools/build_site_index.py
"""
import os, re, json, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Sections, in the order they are offered: name, hub page. First matching rule wins.
SECTIONS = [
    ('Apps',            '/apps/',             r'^(apps/|appstore|privacy-)'),
    ('Calendar & News', '/calendar.html',     r'^(calendar|e/|news|today/|flyer-|civic-calendar|press/)'),
    ('Elections',       '/elections.html',    r'(election|ballot|vote|voting|poll|primary|november2026|throughtime|comptroller-results|ad52-results|edhistory|cbhistory|results|registration|enrollment|ed-map|turnout)'),
    ('CB6',             '/',                  r'^(index\.html$|minutes|board|committees|budget|survey|districtneeds|district-needs|jobs|250baltic|about|help|faq|contact|members|civic-handbook|handbook|hubs|250-baltic|cb6-faq|resolutions|letters|cb6-logo|cb6-map|cb6_|cb6-isometric|homemap|planning-map-cb6|welcome|crossword|puzzle|game|jeopardy|quiz|civics|glossary|recommended|reading|cb6-electeds|cb6-)'),
    ('Housing',         '/rent.html',         r'(^rent|rents|housing|allhousing|lessexpensive|nycha|lotter|^cd/|affordab)'),
    ('Government',      '/government/',       r'^(who|am[a-z]|sen[a-z]|cm[a-z]|council|senate|assembly|congress|cb-|cbmap|cb6-legislative|district-map|mydistricts|gov/|government|govhub|agencies|agency|charter|orgchart|org-chart|comptroller|mayor|bp|borough|directory\.html|jointinterest|beyondcb6|citywide|nyc-|state|federal|cuny-trustees|publicadvocate|public-advocate|electeds|brooklyn|bronx|manhattan|queens|staten|bayridge|hanif|gounardes|simon|reynoso|lander|mamdani|hochul|velazquez|goldman|schumer|gillibrand|dinapoli|levine|williams|adams|governors)'),
    ('Land Use',        '/useofland/',        r'(landuse|land-use|zoning|zoned|lots|useofland|builtmap|built|gowanus|bmt|lpc|landmark|preservation|rezon|ulurp|compplan|fhgs|permit|ownership|buildings|building-|^p/|27-buildings|226-kane|557-6|kane-street|historic|density|fair-housing|marine-terminal|pluto|lot-)'),
    ('Transportation',  '/transport',         r'(transport|truck|speed|bqe|bike|subway|bus-|buses|parking|visionzero|vision-zero|bergndean|bergen|ferry|citibike|citi-bike|streets|crash|sammy|mta|transit|dot-)'),
    ('Parks',           '/parks/',            r'(^park/|^parks|treepruning|tree|playground|community-garden|^garden|greenway|openstreets|open-streets|pops|waterfront|esplanade|dog-run|pool)'),
    ('Schools',         '/eduhub',            r'(^school|eduhub|schooldistrict|college|cuny|childcare|child-care|prek|pre-k|3k|education|universit)'),
    ('Services',        '/311-hub',           r'(^311|sanitation|dsny|mailbox|postal|usps|trash|recycl|compost|services|dob|hpd|dep-|water|noise|weather|flood|heat|alert|emergency|evacuation|hurricane|cooling|cooldown|complaint|health)'),
    ('Safety',          '/publicsafety/',     r'(safety|precinct|sector/|crime|nypd|fdny|arrest|shooting|violation|camera|ticket)'),
    ('Culture',         '/culture/',          r'(culture|museum|cinema|theatre|theater|library|librar|stadium|^c/|place|galler|venue|film|^art|music|bookstore|openstudios|studios)'),
    ('Directory',       '/o/',                r'(^org|^o/|orgs|business|^biz|liquor|food-drink|food-stores|hardware|bids?\b|restaurant|shop|coop|bid-|nonprofit|community-groups|sale-listings|listings)'),
    ('More',            '/hubs.html',         r'.'),
]

# generated place families and a few exact pages: decided before the section rules
PREFIX_RULES = [
    ('Schools',   r'^(school-|college-|eduhub)'),
    ('Culture',   r'^(library-|museum-|cinema-|theatre-|theater-|place-|art-|gallery-|venue-)'),
    ('Directory', r'^(org-|biz-)'),
    ('Land Use',  r'^(building-|reviewing\.html|lamp\.html)'),
    ('CB6',       r'^(search/|hubs\.html)'),
    ('Parks',     r'^(park-|garden-|playground-)'),
    ('Transportation', r'^(bqe|transport|truck)'),
]

# second pass for pages whose path says nothing: title and description decide
TEXT_RULES = [
    ('Schools',    r'(school|preschool|playschool|academy|\bps \d|\bms \d|\bps k|day care|daycare|montessori|\bprep\b|kids|learning center|education council|camp )'),
    ('Government', r'(districts & research|census atlas|neighborhoods|representative|senator|attorney general|governor|district attorney|council member|councilmember|assembly|state senate|city council|comptroller|public advocate|borough president|mayor|elected official)'),
    ('Elections',  r'(election|ballot|voting)'),
    ('CB6',        r'(cb6 (full board|business|committee|calendar)|draft agenda|robert|community board 6|district manager|resources & maps|privacy policy|support)'),
    ('Housing',    r'(housing|tenant|rent)'),
    ('Land Use',   r'(zoning|land use|liquor|ulurp|architecture)'),
    ('Parks',      r'(garden|park alliance|playground|parks activities|old stone house)'),
    ('Culture',    r'(arts?\b|cinema|music|performance|theater|theatre|gallery|studio|dance|brewery|bookstore|books|cafe|coffee|lobster|restaurant)'),
    ('Services',   r'(311|trash|collection|sanitation|supermarket|greenmarket|farmers market)'),
    ('Safety',     r'(crime|arrests|justice center|firefighters)'),
    ('Directory',  r'(brooklyn\.|organization|business|collective|association|initiative|civic council|dsa|soccer|salon|certified|portside|resilient|union hall)'),
]

SKIP_DIRS = {'.git', 'node_modules', 'block', 'bk', 'app', 'bkcball18', 'cb6app10226', 'minutes-docs', 'press'}
SKIP_FILES = re.compile(r'(^404\.html$|\.bak$|^og-|^test|^tmp|^strip|^banner-|^embed)', re.I)
# families of generated pages: indexed with the title only, no description, to keep the index small
LIGHT_DIRS = {'school', 'park', 'news', 'minutes', 'c', 'org', 'o', 'sector', 'precinct', 'college', 'p', 'e', 'gov', 'agencies'}

TITLE_RE = re.compile(r'<title[^>]*>(.*?)</title>', re.I | re.S)
DESC_RE = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', re.I)
OG_DESC_RE = re.compile(r'<meta\s+property="og:description"\s+content="([^"]*)"', re.I)
H1_RE = re.compile(r'<h1[^>]*>(.*?)</h1>', re.I | re.S)
TAGS = re.compile(r'<[^>]+>')
SUFFIX = re.compile(r'\s*(\||&mdash;|—|–|-|·|&middot;)\s*(bkcb6\.app|BKCB6|Brooklyn CB6|CB6 Calendar|Brooklyn Community Board 6.*|CB6)\s*$', re.I)


def clean(s):
    s = html.unescape(TAGS.sub(' ', s or ''))
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def section_of(path, title='', desc=''):
    p = path.lower()
    for name, rule in PREFIX_RULES:
        if re.search(rule, p):
            return name
    for name, hub, rule in SECTIONS:
        if re.search(rule, p):
            if name != 'More':
                return name
            break
    t = (title + ' ' + desc).lower()
    for name, rule in TEXT_RULES:
        if re.search(rule, t):
            return name
    return 'More'


def page_url(rel):
    if rel.endswith('/index.html'):
        return '/' + rel[:-len('index.html')]
    return '/' + rel


def main():
    names = [s[0] for s in SECTIONS]
    pages = []
    for dp, dn, fn in os.walk(ROOT):
        rel_dir = os.path.relpath(dp, ROOT)
        top = rel_dir.split(os.sep)[0] if rel_dir != '.' else ''
        dn[:] = [d for d in dn if d not in SKIP_DIRS and not (rel_dir == '.' and d in SKIP_DIRS)]
        if top in SKIP_DIRS:
            continue
        for f in fn:
            if not f.endswith('.html') or SKIP_FILES.search(f):
                continue
            rel = os.path.normpath(os.path.join(rel_dir, f)) if rel_dir != '.' else f
            try:
                with open(os.path.join(dp, f), 'rb') as fh:
                    b = fh.read(60000).decode('utf-8', 'ignore')
            except OSError:
                continue
            if '<body' not in b.lower() or 'http-equiv="refresh"' in b:
                continue
            m = TITLE_RE.search(b)
            title = clean(m.group(1)) if m else ''
            if not title:
                m = H1_RE.search(b)
                title = clean(m.group(1)) if m else ''
            if not title:
                continue
            title = SUFFIX.sub('', title).strip()
            title = re.sub(r'^[\U0001F300-\U0001FAFF☀-➿️\s]+', '', title)
            desc = ''
            if top not in LIGHT_DIRS:
                m = DESC_RE.search(b) or OG_DESC_RE.search(b)
                desc = clean(m.group(1)) if m else ''
                if len(desc) > 140:
                    desc = desc[:137].rsplit(' ', 1)[0] + '…'
            sec = section_of(rel, title, desc)
            pages.append([page_url(rel), title, names.index(sec), desc])
    pages.sort(key=lambda p: (p[2], p[0].count('/'), p[1].lower()))
    out = {'sections': [[s[0], s[1]] for s in SECTIONS], 'pages': pages}
    os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
    with open(os.path.join(ROOT, 'data', 'site-index.json'), 'w') as fh:
        json.dump(out, fh, ensure_ascii=False, separators=(',', ':'))
    # keep the bar's rules in step
    bar = os.path.join(ROOT, 'assets', 'site-bar.js')
    if os.path.exists(bar):
        js = open(bar).read()
        js2 = js
        for tag, var, val in (('sections', 'SECTIONS', [[s[0], s[1], s[2]] for s in SECTIONS]),
                              ('prefix', 'PREFIX_RULES', [[r[0], r[1]] for r in PREFIX_RULES]),
                              ('text', 'TEXT_RULES', [[r[0], r[1]] for r in TEXT_RULES])):
            rules = 'var ' + var + '=' + json.dumps(val, ensure_ascii=False) + ';'
            js2 = re.sub(r'/\*' + tag + r'\*/.*?/\*/' + tag + r'\*/', lambda m: '/*' + tag + '*/' + rules + '/*/' + tag + '*/', js2, flags=re.S)
        if js2 != js:
            open(bar, 'w').write(js2)
    from collections import Counter
    c = Counter(names[p[2]] for p in pages)
    print(len(pages), 'pages;', os.path.getsize(os.path.join(ROOT, 'data', 'site-index.json')) // 1024, 'KB')
    for k, v in c.most_common():
        print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
