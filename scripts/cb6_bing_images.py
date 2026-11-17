#!/usr/bin/env python3
"""For every BKCB6 Directory listing still on a placeholder tile: the picture of the business from a Bing image search
on its name and address (its own Yelp page's main photo, or a picture from its own website), as Mike set for listings
with no logo of their own. The searches are run in a browser (Bing answers a script with unrelated pictures); the
picture chosen for each listing is in data/cb6-audit/bing-picks.json. Every picture is looked at before it goes on, and
the ones turned down are in data/cb6-audit/bing-reject.json with the reason.
  python3 scripts/cb6_bing_images.py --sheets D   contact sheets of the picks, into folder D
  python3 scripts/cb6_bing_images.py --apply      puts the picks not turned down on the profiles (data/cb6-audit/web-images.json)
The listings are data/cb6-audit/bing-todo.json: [[slug, name, address, ...], ...]."""
import json, os, re, sys, io, html, time, random, hashlib, urllib.request, urllib.parse, concurrent.futures as cf
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
LOGOS = P('app/data/civic/orgs/logos'); A = P('data/cb6-audit')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
arg = lambda k, d=None: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
TODO = json.load(open(arg('--todo', P('data/cb6-audit/bing-todo.json'))))
load = lambda f, d: json.load(open(f)) if os.path.exists(f) else d
def get(u, n=6000000, t=25, ref=None):
    h = {'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'}
    if ref: h['Referer'] = ref
    return urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=t).read(n)
def query(name, addr):
    a = re.sub(r'\s+', ' ', re.sub(r'[\"#*()]|\b(Apt|Ste|Suite|Unit|Fl|Floor|Rm|Room)\b\.?\s*\S*', '', addr or '')).strip()
    return ('%s %s Brooklyn' % (re.sub(r'[\"*]', '', name), a)).replace('  ', ' ').strip()
def search(q):
    for k in range(4):
        try:
            b = get('https://www.bing.com/images/search?' + urllib.parse.urlencode({'q': q, 'form': 'HDRSC2', 'setlang': 'en-US', 'cc': 'US', 'mkt': 'en-US'})).decode('utf-8', 'ignore')
        except Exception as e:
            time.sleep(3 + 4 * k); continue
        out = []
        for m in re.finditer(r'\bm="(\{[^"]+\})"', b):
            try: j = json.loads(html.unescape(m.group(1)))
            except Exception: continue
            if j.get('murl'): out.append([j.get('purl', ''), j['murl'], j.get('turl', ''), j.get('t', ''), j.get('desc', '')])
        if out or 'no results' in b.lower() or 'There are no results' in b: return out[:15]
        time.sleep(4 + 5 * k)
    return None
STOP = set('the and of inc llc corp co ltd pc pllc lp llp nyc ny brooklyn bklyn new york at in for a an by to on de la el'.split())
toks = lambda n: [w for w in re.findall(r'[a-z0-9]+', n.lower().replace('&', ' ').replace("'", '').replace('’', '')) if w not in STOP and len(w) > 1]
BADSITE = re.compile(r'shutterstock|alamy|istock|gettyimages|dreamstime|depositphotos|123rf|adobe\.com|freepik|pinterest|streeteasy|loopnet|zillow|redfin|trulia|realtor|apartments\.com|'
                     r'propertyshark|compass\.com|corcoran|elliman|cityrealty|renthop|zumper|hotpads|homes\.com|crexi|commercialcafe|wikipedia|wikimedia|flickr|reddit|youtube|ebay|amazon\.|'
                     r'etsy|tiktok|linkedin|twitter|x\.com|nytimes|brownstoner|patch\.com|bkmag|curbed|eater|timeout|gothamist|nypost|nydailynews|google\.|bing\.|msn\.|yahoo|mapquest|'
                     r'opencorporates|bizapedia|dnb\.com|zoominfo|manta\.com|npidb|npino|healthgrades|vitals|webmd|usnews|ratemds|bkcb6|govsalaries|causeiq|guidestar|propublica|'
                     r'facebook\.com/(photo|groups|marketplace)|blockshopper|rocketreach|buzzfile|chamberofcommerce|cylex|loc8nearme|findglocal|nextdoor', re.I)
def pick(name, addr, res):
    ts = toks(name)
    if not ts: return None
    num = re.match(r'\s*(\d+)', addr or '')
    num = num.group(1) if num else ''
    st = [w for w in toks(re.sub(r'^\s*\d+\S*', '', (addr or '').split(',')[0])) if w not in ('street', 'st', 'avenue', 'ave', 'place', 'pl')][:1]
    joined = ''.join(ts)
    best = None
    for i, (purl, murl, turl, t, desc) in enumerate(res):
        if BADSITE.search(purl) or not murl.startswith('http'): continue
        text = (t + ' ' + desc).lower(); tt = set(toks(t + ' ' + desc)); dom = re.sub(r'^www\.', '', urllib.parse.urlparse(purl).netloc.lower())
        slug = re.sub(r'[^a-z0-9]', '', urllib.parse.urlparse(purl).path.lower())
        named = all(w in tt for w in ts) or joined in re.sub(r'[^a-z0-9]', '', dom) or (len(joined) >= 6 and joined in slug)
        if not named: continue
        ataddr = bool(num) and re.search(r'(?<!\d)%s(?!\d)' % num, text) is not None and (not st or st[0] in text or re.sub(r'(st|nd|rd|th)$', '', st[0]) in text)
        own = joined in re.sub(r'[^a-z0-9]', '', dom) and len(joined) >= 5
        yelp = 'yelp.com/biz' in purl
        if not (ataddr or own or (not num and 'brooklyn' in (text + purl).lower())): continue
        score = (0 if yelp and ataddr else 1 if own else 2 if ataddr else 3, i)
        if best is None or score < best[0]: best = (score, purl, murl, turl, t)
    return best
def square(b, size=256):
    im = Image.open(io.BytesIO(b)); im.load()
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg
    im = im.convert('RGB'); w, h = im.size
    if min(w, h) < 120: raise ValueError('too small')
    s = min(w, h); im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s)).resize((size, size), Image.LANCZOS)
    o = io.BytesIO(); im.save(o, 'PNG', optimize=True); return o.getvalue()
SF = os.path.join(A, 'bing.json'); PF = os.path.join(A, 'bing-picks.json'); RF = os.path.join(A, 'bing-reject.json')
if '--search' in sys.argv:
    S = load(SF, {}); todo = [t for t in TODO if S.get(t[0]) is None]
    print('to search:', len(todo), flush=True)
    def job(t):
        time.sleep(random.random() * .6); return t[0], search(query(t[1], t[2]))
    n = 0
    with cf.ThreadPoolExecutor(int(arg('--threads', 6))) as ex:
        for s, r in ex.map(job, todo):
            S[s] = r; n += 1
            if n % 100 == 0: print(n, 'none back:', sum(1 for v in S.values() if v == []), 'failed:', sum(1 for v in S.values() if v is None), flush=True); json.dump(S, open(SF, 'w'))
    json.dump(S, open(SF, 'w'))
    print('searched:', len(S), '| nothing back:', sum(1 for v in S.values() if v == []), '| failed:', sum(1 for v in S.values() if v is None))
if '--pick' in sys.argv:
    S = load(SF, {}); K = load(PF, {})
    def job(t):
        s = t[0]
        if s in K and os.path.exists(os.path.join(LOGOS, K[s]['file'])): return s, K[s]
        b = pick(t[1], t[2], S.get(s) or [])
        if not b: return s, None
        for u in (b[2], b[3]):
            if not u: continue
            try: png = square(get(u, ref=b[1]))
            except Exception: continue
            fn = 'web-%s.png' % s
            open(os.path.join(LOGOS, fn), 'wb').write(png)
            return s, {'file': fn, 'image': b[2], 'page': b[1], 'title': b[4], 'from': 'Bing image search for "%s"' % query(t[1], t[2])}
        return s, None
    with cf.ThreadPoolExecutor(12) as ex:
        for s, r in ex.map(job, TODO):
            if r: K[s] = r
    json.dump(K, open(PF, 'w'), indent=0, ensure_ascii=False)
    print('listings:', len(TODO), '| pictures picked:', sum(1 for t in TODO if t[0] in K))
if '--sheets' in sys.argv:
    K = load(PF, {}); out = arg('--sheets'); os.makedirs(out, exist_ok=True)
    rows = [t for t in TODO if t[0] in K]; per = 30; cols = 6
    try: f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    except Exception: f = ImageFont.load_default()
    idx = []
    for k in range(0, len(rows), per):
        sh = Image.new('RGB', (cols * 220, 5 * 250), 'white'); d = ImageDraw.Draw(sh)
        for i, t in enumerate(rows[k:k + per]):
            x, y = (i % cols) * 220, (i // cols) * 250
            try: sh.paste(Image.open(os.path.join(LOGOS, K[t[0]]['file'])).convert('RGB').resize((190, 190)), (x + 15, y + 4))
            except Exception: pass
            n = k + i
            d.text((x + 6, y + 196), '%d %s' % (n, t[1][:26]), fill='black', font=f)
            d.text((x + 6, y + 212), (t[2] or '')[:20] + ' | ' + (t[4] or '')[:10], fill=(90, 90, 90), font=f)
            d.text((x + 6, y + 228), re.sub(r'^www\.', '', urllib.parse.urlparse(K[t[0]]['page']).netloc)[:28], fill=(0, 60, 160), font=f)
            idx.append([n, t[0], t[1], K[t[0]]['page'], K[t[0]]['title']])
        sh.save(os.path.join(out, 's%03d.jpg' % (k // per)), quality=80)
    json.dump(idx, open(os.path.join(out, 'index.json'), 'w'), indent=0)
    print('sheets:', (len(rows) + per - 1) // per, 'pictures:', len(rows))
if '--apply' in sys.argv:
    K = load(PF, {}); R = set(load(RF, {})); W = load(os.path.join(A, 'web-images.json'), {})
    f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8')); BY = {p['slug']: p for p in D['profiles']}
    n = 0
    for t in TODO:
        s = t[0]
        if s in R:
            fn = os.path.join(LOGOS, 'web-%s.png' % s)
            if os.path.exists(fn): os.remove(fn)
            continue
        if s not in K or s not in BY: continue
        BY[s]['logo'] = K[s]['file']; W[s] = {k: K[s][k] for k in ('file', 'image', 'page', 'from')}; n += 1
    json.dump(W, open(os.path.join(A, 'web-images.json'), 'w'), indent=0, ensure_ascii=False)
    open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
    print('pictures on profiles:', n, '| turned down:', len(R & {t[0] for t in TODO}))
