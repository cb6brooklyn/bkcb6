#!/usr/bin/env python3
"""Each school's own facts from the web, for its profile (scripts/school_directory.py reads the result).

1. NYC Public Schools' page for the school (schools.nyc.gov/schools/<location code>) for every public and charter
   school with a code (the DBN on its page, or the 2019-20 School Locations file, wg9x-4ke6, for charters): the
   school's website, address, phone, school leader, grades, accessibility and its DBN.
2. A school with no NYC Public Schools page (private and parochial schools, newer charters, high school equivalency
   programs): its website from a web search on its name and address, kept only when the site's own title or
   description names the school.
3. The school's website: its logo (the image its header calls a logo, else its app icon, else the largest icon it
   offers) and its own description of itself (the page's description, else its og:description).
Writes data/schools-web/web.json ({slug: {...}}) and the logos to assets/school-logos/web/<slug>.png.
Rerunnable; a school already in web.json is skipped unless --refresh. Usage: python3 scripts/school_web.py [--refresh]
"""
import concurrent.futures as cf, html, io, json, math, os, re, sys, threading, time, urllib.parse
import requests
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
OUT = P('data/schools-web/web.json'); LOGO = P('assets/school-logos/web')
os.makedirs(LOGO, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
      'Accept-Language': 'en-US,en;q=0.9'}
R = json.load(open(P('data/schools-web/roster.json')))
W = json.load(open(OUT)) if os.path.exists(OUT) else {}
LOCK = threading.Lock()
T = lambda s: html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s or ''))).strip()

def get(u, **k):
    for i in range(2):
        try:
            r = requests.get(u, headers=UA, timeout=20, allow_redirects=True, **k)
            return r
        except Exception:
            time.sleep(1.5)
    return None

# charters: their location codes from the 2019-20 School Locations file
def nk(s):
    s = html.unescape(s or '').lower().replace('&', ' and ')
    s = re.sub(r'\b(the|school|of|for|and|inc|academy|high|elementary|charter|cs|chs)\b', ' ', s)
    return re.sub(r'[^a-z0-9]', '', s)
LOC = []
lf = P('data/schools-web/locations-2019-20.json')
if os.path.exists(lf):
    for r in json.load(open(lf)):
        if re.match(r'^-?[\d.]+$', r.get('latitude') or '') and re.match(r'^-?[\d.]+$', r.get('longitude') or ''): LOC.append((nk(r['location_name']), float(r['latitude']), float(r['longitude']), r['system_code']))
def code_for(s):
    if s['dbn'] and re.match(r'^\d\d[KMXQR]\d{3}$', s['dbn']): return s['dbn']
    if s['topic'] != 'Charter schools': return ''
    k = nk(s['name']); best = None
    for kk, a, b, c in LOC:
        d = math.hypot((a - s['lat']) * 111000, (b - s['lng']) * 84000)
        if d < 400 and (kk == k or (len(k) > 6 and (k in kk or kk in k))):
            if not best or d < best[0]: best = (d, c)
    return best[1] if best else ''

def doe(code):
    r = get('https://www.schools.nyc.gov/schools/' + code[2:])
    if not r or r.status_code != 200: return {}
    s = r.text
    h1 = T((re.search(r'<h1 class="title">(.*?)</h1>', s, re.S) or [None, ''])[1])
    if not h1: return {}
    o = {'doe_url': 'https://www.schools.nyc.gov/schools/' + code[2:], 'doe_name': h1}
    m = re.search(r'<span class="visually-hidden">Location:</span>\s*<a[^>]*>(.*?)</a>', s, re.S); o['address'] = T(m.group(1)) if m else ''
    m = re.search(r'<span class="visually-hidden">Phone:</span>\s*<span>(.*?)</span>', s, re.S); o['phone'] = T(m.group(1)) if m else ''
    m = re.search(r'<a href="([^"]+)" class="more">School Website</a>', s); o['website'] = html.unescape(m.group(1)).strip() if m else ''
    for k in ('Accessibility', 'Grades'):
        m = re.search(r'<strong>%s:</strong>\s*(.*?)</span>' % k, s, re.S); o[k.lower()] = T(m.group(1)) if m else ''
    m = re.search(r'<dt>School Leader</dt>\s*<dd>(.*?)</dd>', s, re.S); o['leader'] = T(m.group(1)) if m else ''
    m = re.search(r'<dt>District Borough Number</dt>\s*<dd>(.*?)</dd>', s, re.S); o['dbn'] = T(m.group(1)) if m else code
    m = re.search(r'<dt>Space</dt>\s*<dd>(.*?)</dd>', s, re.S); o['space'] = T(m.group(1)) if m else ''
    return o

BAD = ('wikipedia.', 'niche.com', 'greatschools', 'privateschoolreview', 'yelp.', 'facebook.', 'instagram.', 'linkedin.', 'mapquest.',
       'schooldigger', 'publicschoolreview', 'usnews.', 'insideschools', 'schools.nyc.gov', 'nysed.gov', 'nyc.gov', 'bing.com', 'microsoft.',
       'zillow.', 'streeteasy', 'trulia', 'opengovny', 'allbiz', 'bizapedia', 'yellowpages', 'manta.', 'chamberofcommerce', 'indeed.',
       'glassdoor', 'twitter.', 'x.com', 'youtube.', 'tiktok.', 'macaroni', 'winnie.com', 'care.com', 'trueschools', 'whatschool',
       'plainschools', 'k12guides', 'boardingschoolreview', 'privateschoolsguide', 'nces.ed.gov', 'ed.gov', 'google.', 'apple.com',
       'nytimes', 'patch.com', 'dnainfo', 'chalkbeat', 'amazon.', 'eventbrite', 'waze', 'nextdoor', 'reddit.', 'pinterest', 'msn.com',
       'ratemyteachers', 'cylex', 'spoke.com', 'dandb', 'opencorporates', 'causeiq', 'guidestar', 'propublica', 'charitynavigator',
       'nyc.charter', 'nycharters.org', 'newyorkcharters', 'schoolmint', 'myschools.nyc', 'uft.org', 'osba', 'loopnet', 'propertyshark')
SCHOOLWORD = re.compile(r'school|academy|yeshiva|yeshivah|montessori|education|learning|students|preschool|institute|collegiate|cheder|mesivta|talmud|torah|bais|beth|beis|day care|daycare|charter|lyceum|seminary|kindergarten|elementary|high school|program', re.I)
def search_site(s):
    """Its website from a web search: the first result whose own title or description names the school and reads as a school's."""
    q = '%s %s NY school' % (s['name'], s['boro'] or 'New York')
    r = get('https://www.bing.com/search', params={'q': q, 'format': 'rss', 'setlang': 'en-US', 'cc': 'US', 'mkt': 'en-US'})
    if not r or r.status_code != 200: return '', q
    urls, seen = [], set()
    for u in re.findall(r'<link>(https?://[^<]+)</link>', r.text)[1:]:
        u = html.unescape(u); host = re.match(r'^https?://([^/]+)', u).group(1).lower()
        if any(b in u.lower() for b in BAD) or host in seen: continue
        seen.add(host); urls.append(u)
    words = [w for w in re.findall(r'[a-z]{4,}', html.unescape(s['name']).lower()) if w not in ('school', 'schools', 'academy', 'high', 'elementary', 'middle',
             'charter', 'center', 'learning', 'program', 'site', 'annex', 'brooklyn', 'queens', 'bronx', 'manhattan', 'staten', 'island', 'york', 'with', 'from', 'the')]
    need = len(words) if len(words) <= 2 else math.ceil(len(words) * 0.6)
    for u in urls[:6]:
        home = re.match(r'^(https?://[^/]+)', u).group(1) + '/'
        p = get(home)
        if not p or p.status_code != 200 or 'html' not in p.headers.get('content-type', ''): continue
        t = (T((re.search(r'<title[^>]*>(.*?)</title>', p.text, re.S | re.I) or [None, ''])[1]) + ' ' + meta(p.text, 'description') + ' ' + meta(p.text, 'og:site_name') + ' ' + meta(p.text, 'og:title')).lower()
        if words and sum(1 for w in words if w in t) >= need and SCHOOLWORD.search(t):
            return p.url, q
    return '', q

def meta(s, name):
    for pat in (r'<meta[^>]+(?:name|property)=["\']%s["\'][^>]*content=["\']([^"\']*)["\']' % re.escape(name),
                r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*(?:name|property)=["\']%s["\']' % re.escape(name)):
        m = re.search(pat, s, re.I | re.S)
        if m: return T(m.group(1))
    return ''
GENERIC = re.compile(r'^(home|welcome|homepage|index|default|untitled|just another wordpress site|site description)\.?$|lorem ipsum|wix\.com|squarespace|^this is the', re.I)
OTHER = re.compile(r'\b(nyu|suny|cuny|columbia|cornell|fordham|pace university|new school|college board|ib world|international baccalaureate|google|microsoft|apple|amazon|blackbaud|finalsite|schoolmessenger|parentsquare|nysed|nycdoe)\b', re.I)
def logo_candidates(base, s, name=''):
    c = []
    skip = re.compile(r'nyc-logo|nyc_logo|nycdoe|doe_logo|college_logos|colleges?/|partners?/|sponsors?/|partner|sponsor|nycps|doe-logo|nyc-?public-?schools|facebook|twitter|instagram|youtube|linkedin|google|apple|accredit|footer|badge|award|niche', re.I)
    for m in re.finditer(r'<img\b[^>]*>', s, re.I):
        tag = m.group(0)
        src = (re.search(r'\b(?:data-src|src)=["\']([^"\']+)["\']', tag) or [None, ''])[1]
        if not src or src.startswith('data:'): continue
        before = s[max(0, m.start() - 300):m.start()]
        if (re.search(r'logo|brand|crest|seal|emblem', tag, re.I) or re.search(r'class=["\'][^"\']*(logo|brand)[^"\']*["\'][^<]*(<a[^>]*>\s*)?$', before, re.I)) and not skip.search(tag):
            o = OTHER.search(tag)
            if o and o.group(1).lower() not in name.lower(): continue
            words = [w for w in re.findall(r'[a-z]{4,}', name.lower()) if w not in ('school', 'academy', 'high', 'the', 'elementary', 'middle')]
            c.append(('img', urllib.parse.urljoin(base, html.unescape(src)), any(w in tag.lower() for w in words) or 'logo' in tag.lower()))
        if len(c) >= 4: break
    c = [(k, u) for k, u, _ in sorted(c, key=lambda x: not x[2])]
    m = re.search(r'class=["\'][^"\']*(logo|brand)[^"\']*["\'][^>]*>\s*(?:<a[^>]*>\s*)?(<svg\b.*?</svg>)', s, re.I | re.S)
    if m and len(m.group(2)) > 200: c.append(('svg', m.group(2)))
    og = meta(s, 'og:image')
    if og and re.search(r'logo|crest|seal', og, re.I): c.append(('og', urllib.parse.urljoin(base, og)))
    for rel in ('apple-touch-icon', 'apple-touch-icon-precomposed'):
        for m in re.finditer(r'<link[^>]+rel=["\'][^"\']*%s[^"\']*["\'][^>]*>' % rel, s, re.I):
            h = (re.search(r'href=["\']([^"\']+)', m.group(0)) or [None, ''])[1]
            if h: c.append(('touch', urllib.parse.urljoin(base, html.unescape(h))))
    icons = []
    for m in re.finditer(r'<link[^>]+rel=["\'][^"\']*icon[^"\']*["\'][^>]*>', s, re.I):
        h = (re.search(r'href=["\']([^"\']+)', m.group(0)) or [None, ''])[1]; sz = (re.search(r'sizes=["\'](\d+)', m.group(0)) or [None, '0'])[1]
        if h: icons.append((int(sz), urllib.parse.urljoin(base, html.unescape(h))))
    for sz, u in sorted(icons, reverse=True): c.append(('icon', u))
    c.append(('icon', urllib.parse.urljoin(base, '/favicon.ico')))
    return c
BADLOGO = re.compile(r'edlio|powered|sefaria|poweredby|schoolwires|blackboard|finalsite-logo|apptegy|thrillshare|schoolinsites|nyc-?doe|doe-?logo|nycdoe|department-?of-?education|nycps|nyc_public|google|wix-logo|squarespace-logo', re.I)
def fetch_logo(slug, cands):
    for kind, u in cands:
        if kind != 'svg' and BADLOGO.search(u): continue
        if kind != 'svg' and re.search(r'gstatic\.com|googleusercontent\.com/.*sites|wix\.com/favicon|squarespace\.com/universal|wordpress\.com/i/|s\.w\.org|edlio|finalsite.*default', u, re.I): continue
        if kind == 'svg':
            try:
                import cairosvg
                im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=u.encode(), output_width=600))).convert('RGBA')
                bb = im.getchannel('A').getbbox()
                if bb and (bb[2] - bb[0]) > 40:
                    im.crop(bb).save(os.path.join(LOGO, slug + '.png'), optimize=True); return 'inline svg', kind
            except Exception:
                pass
            continue
        r = get(u)
        if not r or r.status_code != 200 or len(r.content) < 300: continue
        ct = r.headers.get('content-type', '')
        try:
            if 'svg' in ct or u.lower().split('?')[0].endswith('.svg'):
                import cairosvg
                im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=r.content, output_width=600))).convert('RGBA')
            else:
                im = Image.open(io.BytesIO(r.content)); im.load(); im = im.convert('RGBA')
        except Exception:
            continue
        if im.width < (64 if kind == 'icon' else 48) or im.height < 32: continue
        if kind == 'img' and (im.width / im.height > 7 or im.height / im.width > 3): continue
        bb = im.getchannel('A').getbbox()
        if not bb: continue
        im = im.crop(bb)
        sm = im.copy(); sm.thumbnail((64, 64))
        alpha = sm.getchannel('A'); opaque = sum(1 for a in alpha.getdata() if a > 200) / (sm.width * sm.height)
        if kind in ('img', 'og') and opaque > 0.97 and len(set(sm.convert('RGB').getdata())) > 1800: continue   # a photograph, not a logo
        px = [p for p in sm.getdata() if p[3] > 120]
        if px and sum(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in px) / len(px) > 225:
            # a white logo made for a dark header: keep it on the school site's own dark ground, our navy
            pad = max(8, im.width // 12); bgim = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (13, 27, 75, 255))
            bgim.alpha_composite(im, (pad, pad)); im = bgim
        if max(im.size) > 300: im.thumbnail((300, 300), Image.LANCZOS)
        im.quantize(colors=128, method=Image.Quantize.FASTOCTREE).save(os.path.join(LOGO, slug + '.png'), optimize=True)
        return u, kind
    return '', ''

def first_para(s, name):
    for m in re.finditer(r'<p\b[^>]*>(.*?)</p>', s, re.S | re.I):
        t = T(m.group(1))
        if 90 <= len(t) <= 900 and good(t, '') and not re.search(r'cookie|javascript|browser|copyright|all rights reserved|privacy|©|subscribe|newsletter|login|password', t, re.I) and (SCHOOLWORD.search(t) or any(w in t.lower() for w in re.findall(r'[a-z]{5,}', name.lower()))):
            return t
    return ''
def good(d, title):
    d = re.sub(r'^(https?://\S+\s*)+', '', d or '').strip()
    words = d.split()
    if not words or d.count(',') / len(words) > 0.2 or not re.search(r"\b(is|are|was|serves?|serving|provides?|offers?|educates?|educating|mission|we|our|founded|dedicated|committed)\b", d, re.I) or re.match(r'^(read|click|welcome to our website|check out|join us|learn more)\b', d, re.I):
        return ''
    return d if d and len(d) >= 60 and not GENERIC.search(d) and d.lower().strip(' .') not in title.lower() and not re.match(r'^(home|welcome)\b.{0,40}$', d, re.I) else ''
def site(url, name=''):
    r = get(url)
    if not r or r.status_code != 200 or 'html' not in r.headers.get('content-type', 'html'): return {}
    s = r.text
    title = T((re.search(r'<title[^>]*>(.*?)</title>', s, re.S | re.I) or [None, ''])[1])[:200]
    d = good(meta(s, 'description'), title) or good(meta(s, 'og:description'), title)
    src = 'homepage description' if d else ''
    if not d:
        about = next((urllib.parse.urljoin(r.url, html.unescape(h)) for h in re.findall(r'<a[^>]+href=["\']([^"\'#]+)["\']', s, re.I)
                      if re.search(r'about|mission|who-we-are|our-school|overview', h, re.I) and not re.search(r'facebook|twitter|instagram|mailto', h, re.I)), '')
        if about:
            a = get(about)
            if a and a.status_code == 200 and 'html' in a.headers.get('content-type', 'html'):
                at = T((re.search(r'<title[^>]*>(.*?)</title>', a.text, re.S | re.I) or [None, ''])[1])
                d = good(meta(a.text, 'description'), at) or first_para(a.text, name); src = ('about page: ' + a.url) if d else ''
    if not d:
        d = first_para(s, name); src = 'homepage' if d else ''
    if len(d) > 700: d = d[:700].rsplit('. ', 1)[0] + '.'
    return {'final': r.url, 'desc': d, 'desc_src': src, 'title': title, 'cands': logo_candidates(r.url, s, name)}

def one(s):
    o = {'name': s['name']}
    code = code_for(s)
    if code: o.update(doe(code))
    web = o.get('website') or ''
    if web and not web.startswith('http'): web = 'https://' + web
    if not web:
        web, q = search_site(s); o['found_by_search'] = bool(web)
    o['website'] = web
    if web:
        x = site(web, s['name'])
        if x:
            o['website_final'] = x['final']; o['desc'] = x['desc']; o['desc_src'] = x['desc_src']; o['site_title'] = x['title']
            u, kind = fetch_logo(s['slug'], x['cands'])
            o['logo_src'] = u; o['logo_kind'] = kind
    o['logo'] = os.path.exists(os.path.join(LOGO, s['slug'] + '.png'))
    o['checked'] = time.strftime('%Y-%m-%d')
    return s['slug'], o

def here(s, text):
    street = re.sub(r'^\d+\S*\s+', '', (s.get('addr') or '').lower()).split(' ')[0] if s.get('addr') else ''
    return bool((s.get('zip') and s['zip'] in text) or re.search(r'new york|\bnyc\b|\bny\s+1\d{4}|%s' % re.escape((s.get('boro') or 'brooklyn').lower()), text, re.I) or (len(street) > 4 and street in text.lower()))
def recheck(s):
    """A site found by search must be in New York; a logo that is a platform's or the DOE's is read again."""
    o = W.get(s['slug']) or {}
    if not o.get('website'): return s['slug'], o
    if o.get('found_by_search'):
        p = get(o['website'])
        if not p or not here(s, p.text):
            for k in ('website', 'website_final', 'desc', 'desc_src', 'site_title', 'logo_src', 'logo_kind'): o.pop(k, None)
            o['found_by_search'] = False
            f = os.path.join(LOGO, s['slug'] + '.png')
            if os.path.exists(f): os.remove(f)
            o['logo'] = False
            return s['slug'], o
    if o.get('logo_src') and BADLOGO.search(o['logo_src']) or o.get('logo_src') and re.search(r'gstatic', o['logo_src']):
        f = os.path.join(LOGO, s['slug'] + '.png')
        if os.path.exists(f): os.remove(f)
        x = site(o.get('website_final') or o['website'], s['name'])
        u, kind = fetch_logo(s['slug'], x.get('cands', [])) if x else ('', '')
        o['logo_src'] = u; o['logo_kind'] = kind; o['logo'] = os.path.exists(f)
    return s['slug'], o

if __name__ == '__main__' and '--dedupe' in sys.argv:
    # one picture on the sites of three or more schools that share no name is the site builder's, not the schools': dropped
    import hashlib, collections
    H = collections.defaultdict(list)
    for k in W:
        f = os.path.join(LOGO, k + '.png')
        if os.path.exists(f): H[hashlib.md5(open(f, 'rb').read()).hexdigest()].append(k)
    STOPW = {'school', 'schools', 'academy', 'high', 'charter', 'public', 'middle', 'elementary', 'the', 'for', 'and', 'of', 'annex', 'brooklyn', 'bronx', 'queens', 'manhattan', 'staten', 'island', 'new', 'york', 'community', 'center', 'learning', 'intermediate', 'junior'}
    gone = 0
    for md, ks in H.items():
        if len(ks) < 3: continue
        sets = [set(re.findall(r'[a-z]{4,}', W[k]['name'].lower())) - STOPW for k in ks]
        if set.intersection(*sets): continue
        for k in ks:
            os.remove(os.path.join(LOGO, k + '.png')); W[k]['logo'] = False; W[k]['logo_dropped'] = 'shared with %d unrelated schools' % len(ks); gone += 1
    json.dump(W, open(OUT, 'w'), ensure_ascii=False, indent=0)
    print('shared pictures dropped:', gone); sys.exit()
if __name__ == '__main__' and '--overrides' in sys.argv:
    # websites found by hand (a web search, checked), for schools no other pass found: data/schools-web/overrides.json
    OV = json.load(open(P('data/schools-web/overrides.json')))
    RS = {s['slug']: s for s in R}
    for slug, url in OV.items():
        if slug not in RS: print('no such school:', slug); continue
        o = W.get(slug) or {'name': RS[slug]['name']}
        o['website'] = url; o['found_by_hand'] = True
        x = site(url, RS[slug]['name'])
        if x:
            o['website_final'] = x['final']; o['desc'] = x['desc']; o['desc_src'] = x['desc_src']; o['site_title'] = x['title']
            u, kind = fetch_logo(slug, x['cands']); o['logo_src'] = u; o['logo_kind'] = kind
        o['logo'] = os.path.exists(os.path.join(LOGO, slug + '.png')); o['checked'] = time.strftime('%Y-%m-%d')
        W[slug] = o; print(slug, bool(o.get('desc')), o['logo'])
    json.dump(W, open(OUT, 'w'), ensure_ascii=False, indent=0)
    sys.exit()
if __name__ == '__main__' and '--recheck' in sys.argv:
    with cf.ThreadPoolExecutor(32) as ex:
        for slug, o in ex.map(recheck, R): W[slug] = o
    json.dump(W, open(OUT, 'w'), ensure_ascii=False, indent=0)
    v = list(W.values())
    print('rechecked | website:', sum(1 for x in v if x.get('website')), '| description:', sum(1 for x in v if x.get('desc')), '| logo:', sum(1 for x in v if x.get('logo')))
    sys.exit()
if __name__ == '__main__':
    todo = [s for s in R if '--refresh' in sys.argv or s['slug'] not in W]
    print('to do:', len(todo), flush=True)
    n = 0
    with cf.ThreadPoolExecutor(32) as ex:
        for slug, o in ex.map(one, todo):
            with LOCK:
                W[slug] = o; n += 1
                if n % 50 == 0:
                    json.dump(W, open(OUT, 'w'), ensure_ascii=False, indent=0); print(n, flush=True)
    json.dump(W, open(OUT, 'w'), ensure_ascii=False, indent=0)
    v = list(W.values())
    print('done:', len(v), '| DOE page:', sum(1 for x in v if x.get('doe_url')), '| website:', sum(1 for x in v if x.get('website')),
          '| by search:', sum(1 for x in v if x.get('found_by_search')), '| description:', sum(1 for x in v if x.get('desc')), '| logo:', sum(1 for x in v if x.get('logo')))
