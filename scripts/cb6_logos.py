#!/usr/bin/env python3
"""Logos for every business and place in Community District 6 (BKCB6) that has none, for its Directory profile, tile and
the BKCB6 Directory map. The same steps as bid_logos.py (which does the three BIDs), over the whole district.

For each business profile inside a BID with no logo:
  1. the same brand already has a logo in the Directory (another branch, another listing): that logo
  2. a chain or brand in BRANDS (its own site), or the business's own website: the logo from the site itself, in this
     order: the apple-touch-icon, an <img> or <svg> marked as the logo, the site's icon at 128 pixels or more
Images are squared on white at 256 pixels and saved to app/data/civic/orgs/logos/cb6logo-<hash>.png.
Writes data/cb6-audit/logos.json (profile slug: logo file and where it came from). Rerunnable; run before
app_directory_tiles.py and bid_maps.py."""
import json, os, re, sys, io, hashlib, urllib.request, urllib.parse, collections, concurrent.futures as cf
from shapely.geometry import shape, Point
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
os.chdir(ROOT)
LOGOS = 'app/data/civic/orgs/logos'
SLUGS = ['park-slope-5th-avenue', 'north-flatbush', 'atlantic-avenue']
BIDS = [shape(json.load(open(P('data/cb6-audit/cd306.geojson'))))]
GROUPS = ('Local businesses', 'Health', 'Food', 'Child care', 'Schools, parks and facilities', 'Community groups')
# chains and brands with storefronts in these BIDs: name pattern -> their site
BRANDS = [(r'chipotle', 'chipotle.com'), (r'dunkin', 'dunkindonuts.com'), (r'starbucks', 'starbucks.com'), (r'\bcvs\b', 'cvs.com'), (r'walgreens', 'walgreens.com'),
          (r'duane reade', 'walgreens.com'), (r'rite ?aid', 'riteaid.com'), (r'\bchase\b|jpmorgan', 'chase.com'), (r'\btd bank\b', 'td.com'), (r'bank of america', 'bankofamerica.com'),
          (r'citibank|\bciti\b', 'citi.com'), (r'citizens bank', 'citizensbank.com'), (r'santander', 'santanderbank.com'), (r'capital one', 'capitalone.com'), (r'apple bank', 'applebank.com'),
          (r'wells fargo', 'wellsfargo.com'), (r'm ?& ?t bank', 'mtb.com'), (r't-?mobile', 't-mobile.com'), (r'verizon', 'verizon.com'), (r'\bat ?& ?t\b', 'att.com'),
          (r'boost mobile', 'boostmobile.com'), (r'cricket', 'cricketwireless.com'), (r'\bgnc\b', 'gnc.com'), (r'vitamin shoppe', 'vitaminshoppe.com'), (r'ups store', 'theupsstore.com'),
          (r'fedex', 'fedex.com'), (r'planet fitness', 'planetfitness.com'), (r'crunch', 'crunch.com'), (r'blink fitness', 'blinkfitness.com'), (r'orangetheory', 'orangetheory.com'),
          (r'club pilates', 'clubpilates.com'), (r'\bslt\b', 'sltnyc.com'), (r"barry'?s", 'barrys.com'), (r'solidcore', 'solidcore.co'), (r'sweetgreen', 'sweetgreen.com'),
          (r'shake shack', 'shakeshack.com'), (r'popeyes', 'popeyes.com'), (r"mcdonald'?s", 'mcdonalds.com'), (r'burger king', 'bk.com'), (r"wendy'?s", 'wendys.com'), (r'^subway\b', 'subway.com'),
          (r"domino'?s", 'dominos.com'), (r"papa john'?s", 'papajohns.com'), (r'pizza hut', 'pizzahut.com'), (r'five guys', 'fiveguys.com'), (r'\bcava\b', 'cava.com'), (r'just salad', 'justsalad.com'),
          (r'joe ?& ?the juice', 'joejuice.com'), (r'le pain quotidien', 'lepainquotidien.com'), (r'panera', 'panerabread.com'), (r'blank street', 'blankstreet.com'), (r'\btarget\b', 'target.com'),
          (r"trader joe'?s", 'traderjoes.com'), (r'whole foods', 'wholefoodsmarket.com'), (r'petco', 'petco.com'), (r'petsmart', 'petsmart.com'), (r'banfield', 'banfield.com'), (r'sephora', 'sephora.com'),
          (r'\bulta\b', 'ulta.com'), (r'lululemon', 'lululemon.com'), (r'\bnike\b', 'nike.com'), (r'foot locker', 'footlocker.com'), (r'dr\.? martens', 'drmartens.com'), (r'aesop', 'aesop.com'),
          (r'warby parker', 'warbyparker.com'), (r'lenscrafters', 'lenscrafters.com'), (r'visionworks', 'visionworks.com'), (r'quest diagnostics', 'questdiagnostics.com'), (r'labcorp', 'labcorp.com'),
          (r'citymd', 'citymd.com'), (r'northwell', 'northwell.edu'), (r'nyu langone', 'nyulangone.org'), (r'mount sinai', 'mountsinai.org'), (r'montefiore', 'montefiore.org'), (r'one medical', 'onemedical.com'),
          (r'tribeca pediatrics', 'tribecapediatrics.com'), (r'drybar', 'drybar.com'), (r'european wax', 'waxcenter.com'), (r'massage envy', 'massageenvy.com'), (r'hand ?& ?stone', 'handandstone.com'),
          (r'supercuts', 'supercuts.com'), (r'great clips', 'greatclips.com'), (r'mathnasium', 'mathnasium.com'), (r'kumon', 'kumon.com'), (r'code ninjas', 'codeninjas.com'),
          (r'learning experience', 'thelearningexperience.com'), (r'goddard school', 'goddardschool.com'), (r'kindercare', 'kindercare.com'), (r'bright horizons', 'brighthorizons.com'),
          (r'liberty tax', 'libertytax.com'), (r'jackson hewitt', 'jacksonhewitt.com'), (r'h ?& ?r block', 'hrblock.com'), (r'state farm', 'statefarm.com'), (r'allstate', 'allstate.com'),
          (r'geico', 'geico.com'), (r'corcoran', 'corcoran.com'), (r'\bcompass\b', 'compass.com'), (r'douglas elliman', 'elliman.com'), (r'brown harris stevens', 'bhsusa.com'),
          (r'keller williams', 'kw.com'), (r'coldwell banker', 'coldwellbanker.com'), (r'western union', 'westernunion.com'), (r'associated supermarket', 'shopassociated.com'),
          (r'key food', 'keyfood.com'), (r'food universe', 'fooduniverse.com'), (r'ecoatm', 'ecoatm.com'), (r'blossom brows', 'blossombrows.com'), (r'noble dental', 'nobledentalnyc.com'),
          (r'7-?eleven', '7-eleven.com'), (r'gamestop', 'gamestop.com'), (r'staples', 'staples.com'), (r'marshalls', 'marshalls.com'), (r'tj ?maxx', 'tjmaxx.com'), (r'old navy', 'oldnavy.com'),
          (r'\bgap\b', 'gap.com'), (r'banana republic', 'bananarepublic.com'), (r'j\.? ?crew', 'jcrew.com'), (r'uniqlo', 'uniqlo.com'), (r'h ?& ?m\b', 'hm.com'), (r'urban outfitters', 'urbanoutfitters.com'),
          (r'barnes ?& ?noble', 'barnesandnoble.com'), (r'apple store', 'apple.com'), (r'best buy', 'bestbuy.com'), (r'mattress firm', 'mattressfirm.com'), (r'sleep number', 'sleepnumber.com'),
          (r'sherwin', 'sherwin-williams.com'), (r'benjamin moore', 'benjaminmoore.com'), (r'ace hardware', 'acehardware.com'), (r'home depot', 'homedepot.com'), (r'pret a manger', 'pret.com'),
          (r'dig inn|^dig\b', 'diginn.com'), (r'ample hills', 'amplehills.com'), (r'van leeuwen', 'vanleeuwenicecream.com'), (r'levain', 'levainbakery.com'), (r'insomnia cookies', 'insomniacookies.com'),
          (r'paris baguette', 'parisbaguette.com'), (r'tous les jours', 'tlj.com'), (r'gong cha', 'gong-cha-usa.com'), (r'kung fu tea', 'kungfutea.com'), (r'jet\'?s pizza', 'jetspizza.com'),
          (r"applebee'?s", 'applebees.com'), (r'buffalo wild wings', 'buffalowildwings.com'), (r'raising cane', 'raisingcanes.com'), (r'wingstop', 'wingstop.com'), (r'taco bell', 'tacobell.com'),
          (r'\bkfc\b', 'kfc.com'), (r'little caesars', 'littlecaesars.com'), (r'baskin', 'baskinrobbins.com'), (r'carvel', 'carvel.com'), (r'krispy kreme', 'krispykreme.com'),
          (r'two bros', 'twobrospizza.com'), (r'99 cents? only|dollar tree', 'dollartree.com'), (r'family dollar', 'familydollar.com'), (r'mta\b', 'mta.info'), (r'barclays center', 'barclayscenter.com'),
          (r'levy premium', 'levyrestaurants.com'), (r'equinox', 'equinox.com'), (r'soulcycle', 'soul-cycle.com'), (r'brooklyn boulders', 'brooklynboulders.com'), (r'chick-?fil-?a', 'chick-fil-a.com'),
          (r'raising canes', 'raisingcanes.com'), (r'the vitamin shoppe', 'vitaminshoppe.com'), (r'metro by t-?mobile', 'metrobyt-mobile.com'), (r'^spectrum\b', 'spectrum.com'), (r'^michaels$', 'michaels.com'), (r'ace hardware', 'acehardware.com'), (r'anthropologie', 'anthropologie.com'), (r'my gym', 'mygym.com'), (r'the joint chiro', 'thejoint.com'), (r'optimum', 'optimum.com')]
BRANDS = [(re.compile(p, re.I), d) for p, d in BRANDS]
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'}
def fetch(u, n=4000000):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25).read(n)
def square(b, ext='', least=96):
    if ext == 'svg' or b[:200].lstrip().startswith((b'<svg', b'<?xml')):
        import cairosvg
        b = cairosvg.svg2png(bytestring=b, output_width=512)
    im = Image.open(io.BytesIO(b))
    if getattr(im, 'n_frames', 1) > 1: im.seek(0)
    im = im.convert('RGBA')
    bb = im.getbbox()
    if bb: im = im.crop(bb)
    w, h = im.size
    if max(w, h) < least: return None
    if min(w, h) / max(w, h) < .12: return None   # a long thin banner reads as nothing in a square tile
    s = max(w, h); c = Image.new('RGBA', (int(s * 1.12), int(s * 1.12)), (255, 255, 255, 255))
    c.paste(im, ((c.width - w) // 2, (c.height - h) // 2), im)
    c = c.convert('RGB').resize((256, 256), Image.LANCZOS)
    # an all-white or all-one-color image is no logo
    ext_ = c.getextrema()
    if all(hi - lo < 12 for lo, hi in ext_): return None
    o = io.BytesIO(); c.save(o, 'PNG', optimize=True); return o.getvalue()
def site_logo(url, least=64, bad=frozenset()):
    """(png bytes, how) from a site, or (None, why)"""
    try:
        if not re.match(r'https?://', url): url = 'https://' + url
        html = fetch(url).decode('utf-8', 'ignore')
    except Exception as e:
        html = ''
    base = url
    cands = []
    for m in re.finditer(r'<link[^>]+>', html, re.I):
        t = m.group(0); rel = (re.search(r'rel=["\']([^"\']+)', t, re.I) or [None, ''])[1].lower(); href = (re.search(r'href=["\']([^"\']+)', t, re.I) or [None, ''])[1]
        if not href: continue
        if 'apple-touch-icon' in rel: cands.append((0, href, 'the site\'s app icon'))
        elif 'icon' in rel:
            sz = re.search(r'sizes=["\'](\d+)', t); sz = int(sz.group(1)) if sz else 0
            if sz >= 128 or href.endswith('.svg'): cands.append((2, href, 'the site\'s icon'))
    for m in re.finditer(r'<img[^>]+>', html, re.I):
        t = m.group(0)
        if re.search(r'logo', t, re.I):
            src = (re.search(r'(?:data-src|src)=["\']([^"\']+)', t, re.I) or [None, ''])[1]
            if src and not src.startswith('data:'): cands.append((1, src, 'the logo on the site'))
    cands.sort(key=lambda c: c[0])
    for _, href, how in cands[:6]:
        try:
            u = urllib.parse.urljoin(base, href.replace('&amp;', '&'))
            png = square(fetch(u), 'svg' if u.split('?')[0].endswith('.svg') else '')
            if png and hashlib.md5(png).hexdigest() not in bad: return png, how
        except Exception: continue
    dom = re.sub(r'^https?://(www\.)?', '', url).split('/')[0]
    try:   # icon.horse: the largest icon the site publishes
        png = square(fetch('https://icon.horse/icon/%s' % dom), least=least)
        if png and hashlib.md5(png).hexdigest() not in bad: return png, 'the site\'s icon'
    except Exception: pass
    return None, 'no logo found on %s' % dom
def bkey(n):
    n = n.lower().replace('&', 'and').replace('’', "'")
    n = re.sub(r'\s*(#\s*\d+|\b(store|no\.?)\s*\d+|\d{3,})\s*$', '', n)
    n = re.sub(r',.*$|\b(inc|llc|corp|ltd|pc|pllc|of colorado|the)\b\.?', '', n)
    return re.sub(r'\s+', ' ', re.sub(r"[^a-z0-9' ]", ' ', n)).strip()
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
have = lambda p: p.get('logo') and 'Logos/' not in p['logo'] and os.path.exists(os.path.normpath(os.path.join(LOGOS, p['logo'])))
BRANDLOGO = {}
for p in D['profiles']:
    if have(p) and p.get('group') in GROUPS: BRANDLOGO.setdefault(bkey(p['name']), p['logo'])
for p in D['profiles']:   # this script's own logos are found again each run
    if (p.get('logo') or '').startswith('cb6logo-'): p['logo'] = ''
todo = []
for p in D['profiles']:
    if p.get('group') not in GROUPS or have(p) or not p.get('lat'): continue
    pt = Point(float(p['lng']), float(p['lat']))
    if any(g.contains(pt) for g in BIDS): todo.append(p)
LOG_F = P('data/cb6-audit/logos.json'); LOG = json.load(open(LOG_F)) if os.path.exists(LOG_F) else {}
done = collections.Counter()
# 1. the brand's logo already in the Directory
for p in todo:
    k = bkey(p['name'])
    if k and len(k) > 3 and k in BRANDLOGO: p['logo'] = BRANDLOGO[k]; LOG[p['slug']] = [p['logo'], 'the same business\'s logo in the Directory']; done['brand in the Directory'] += 1
# 1b. a chain: the logo any of its other branches already has in the Directory
BRANDHAVE = {}
for p in D['profiles']:
    if have(p) and p.get('group') in GROUPS and not p['logo'].startswith(('bidlogo-', 'cb6logo-')):
        for rx, d in BRANDS:
            if rx.search(p['name']): BRANDHAVE.setdefault(d, p['logo']); break
for p in todo:
    if have(p): continue
    for rx, d in BRANDS:
        if rx.search(p['name']) and d in BRANDHAVE: p['logo'] = BRANDHAVE[d]; LOG[p['slug']] = [p['logo'], 'the chain\'s logo in the Directory']; done['chain in the Directory'] += 1; break
# 2. the brand's site, or the business's own site
def site_for(p):
    for rx, d in BRANDS:
        if rx.search(p['name']): return 'https://www.' + d
    w = p.get('weburl') or p.get('web') or ''
    if w and not re.search(r'facebook|instagram|yelp|google|linktr|square\.site|toasttab|grubhub|doordash|seamless|ubereats|wixsite|godaddysites|weebly|business\.site|wordpress\.com|bkcb6\.app|nyc\.gov|ny\.gov', w, re.I): return w
    return ''
work = collections.defaultdict(list)
for p in todo:
    if have(p): continue
    s = site_for(p)
    if s: work[re.sub(r'^https?://(www\.)?', '', s).split('/')[0].lower() if any(rx.search(p['name']) for rx, _ in BRANDS) else s].append(p)
BAD = set()
def job(item):
    s, ps = item
    png, how = site_logo(s, 32 if not s.startswith('http') else 64, frozenset(BAD))   # a chain's own icon, even small, is its logo
    return s, ps, png, how
with cf.ThreadPoolExecutor(12) as ex:
    res = list(ex.map(job, work.items()))
# one image on several unrelated sites is the web host's or builder's icon, not the business's logo
seen = collections.defaultdict(set)
reg = lambda s: '.'.join(re.sub(r'^https?://', '', s).split('/')[0].lower().split('.')[-2:])
for s, ps, png, how in res:
    if png: seen[hashlib.md5(png).hexdigest()].add(reg(s))
BAD |= {h for h, ds in seen.items() if len(ds) > 1}
again = [(s, ps) for s, ps, png, how in res if png and hashlib.md5(png).hexdigest() in BAD]
if again:   # those sites again, passing over the host's icon to the next image on the page
    with cf.ThreadPoolExecutor(12) as ex:
        redo = {s: (png, how) for s, ps, png, how in ex.map(job, again)}
    res = [(s, ps) + redo[s] if s in redo else (s, ps, png, how) for s, ps, png, how in res]
for s, ps, png, how in res:
        if png and hashlib.md5(png).hexdigest() in BAD: png, how = None, 'the site shows only its web host\'s icon'
        if not png:
            for p in ps: LOG[p['slug']] = ['', how]
            done['no logo on the site'] += len(ps); continue
        fn = 'cb6logo-%s.png' % hashlib.md5(png).hexdigest()[:12]
        open(os.path.join(LOGOS, fn), 'wb').write(png)
        for p in ps:
            p['logo'] = fn; LOG[p['slug']] = [fn, how + ' (' + s + ')']; BRANDLOGO.setdefault(bkey(p['name']), fn)
        done['from the site'] += len(ps)
# brands found this run, for their other listings
for p in todo:
    if not have(p):
        k = bkey(p['name'])
        if k and len(k) > 3 and k in BRANDLOGO: p['logo'] = BRANDLOGO[k]; LOG[p['slug']] = [p['logo'], 'the same business\'s logo in the Directory']; done['brand in the Directory'] += 1
# checked by eye, Nov 17, 2026: images that are not the business's logo (a web host's or Facebook's icon, an "order online"
# button, another company's logo)
REJECT = {'cb6logo-18329f1e68ad.png', 'cb6logo-0ba6dbe39cae.png', 'cb6logo-8548a53ab585.png', 'cb6logo-cf0d43883e01.png', 'cb6logo-7d3bcd06e40a.png', 'cb6logo-37a1c5406702.png'}
for p in todo:
    if p.get('logo') in REJECT: LOG[p['slug']] = ['', 'the image on the site is not the business\'s logo']; p['logo'] = ''
json.dump(LOG, open(LOG_F, 'w'), indent=0)
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('BKCB6 listings with no logo:', len(todo), '| logos found:', dict(done), '| still none:', sum(1 for p in todo if not have(p)),
      '(with no website on record: %d)' % sum(1 for p in todo if not have(p) and not site_for(p)))
