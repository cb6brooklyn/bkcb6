#!/usr/bin/env python3
"""Keeps the iOS apps' landmarks and liquor data current without an App Store release.

Writes into app/data/civic/ (which the apps download through app/manifest.json):
  lpc-permits.json          every LPC permit application in Community District 6, from NYC Open Data (dpm2-m9mq),
                            one row per docket (its latest action), in the app's compact format
  liquor_cb6.json           the site's liquor dataset (data/liquor_cb6.json), copied
  liquor-applicants.json    the liquor license applicants before the Business Affairs & Licenses Committee, read from
                            the latest meeting page that carries them (the MEETING and APPS blocks)
Then rewrites app/manifest.json over every file in app/data."""
import hashlib, json, os, re, sys, time, urllib.request, glob
from datetime import datetime, timezone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'app/data/civic'); os.makedirs(OUT, exist_ok=True)
NOW = datetime.now(timezone.utc)

def fetch(url):
    # NYC Open Data answers with a 500 now and then; try again before giving up.
    import time
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'bkcb6.app app pack'})
            return urllib.request.urlopen(req, timeout=120).read()
        except Exception as e:
            if i == 3: raise
            print('retry', i + 1, e); time.sleep(15 * (i + 1))

def lpc_permits():
    rows, off = [], 0
    while True:
        u = ('https://data.cityofnewyork.us/resource/dpm2-m9mq.json?communityboard=BK-06&$limit=50000&$offset=%d'
             '&$select=docket,address,received_date,block,lot,lmnametype,worktypes,regulation_type,issue_date,latitude,longitude&$order=docket' % off)
        page = json.loads(fetch(u))
        rows += page
        if len(page) < 50000: break
        off += 50000
    by = {}
    for r in rows:
        d = r.get('docket') or ''
        if not d: continue
        if d not in by or (r.get('issue_date') or '') > (by[d].get('issue_date') or ''): by[d] = r
    def title(a): return ' '.join(w if w.isdigit() else w.capitalize() for w in (a or '').split())
    out = []
    for d, r in by.items():
        hd = (r.get('lmnametype') or '').split(':')[0].strip()
        rec = {'d': d, 'a': title(r.get('address')), 'hd': hd, 'w': r.get('worktypes') or '', 'rt': r.get('regulation_type') or '',
               'i': (r.get('issue_date') or '')[:10], 'rc': (r.get('received_date') or '')[:10], 'bl': r.get('block') or '', 'lt': r.get('lot') or ''}
        try: rec['lat'] = float(r['latitude']); rec['lon'] = float(r['longitude'])
        except (KeyError, TypeError, ValueError): pass
        out.append(rec)
    out.sort(key=lambda x: (x['i'], x['rc']), reverse=True)
    json.dump(out, open(os.path.join(OUT, 'lpc-permits.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
    print('lpc-permits', len(rows), 'rows ->', len(out), 'dockets')

def liquor():
    src = os.path.join(ROOT, 'data/liquor_cb6.json')
    if os.path.exists(src):
        open(os.path.join(OUT, 'liquor_cb6.json'), 'wb').write(open(src, 'rb').read()); print('liquor_cb6 copied')

def rents():
    # Rent history (every month since Jan 2010, every unit size, every neighborhood, board and borough) and the rent maps, copied from the site's rent files.
    rd = os.path.join(OUT, 'rents'); os.makedirs(rd, exist_ok=True); n = 0
    for f in ['rent-explorer.json', 'neighborhood-rents.geojson', 'borough-rents.geojson', 'cc-rents.json', 'bk-rents.geojson', 'rental-index.json', 'built-vs-rent.json']:
        src = os.path.join(ROOT, 'data', f)
        if os.path.exists(src): open(os.path.join(rd, f), 'wb').write(open(src, 'rb').read()); n += 1
    print('rents', n, 'files')
    # The three files the Renting in CB6 screen reads, same names and shapes as the copies built into the app.
    # rent-trends.json: CB6 vs Brooklyn vs NYC, straight from the site.
    open(os.path.join(OUT, 'rent-trends.json'), 'wb').write(open(os.path.join(ROOT, 'data/cb6-rent-trends.json'), 'rb').read())
    # rents.geojson: the six CB6 neighborhood outlines the app ships, with this month's figures from the site's neighborhood rent map.
    gp = os.path.join(OUT, 'rents.geojson'); g = json.load(open(gp))
    site = {f['properties'].get('nb'): f['properties'] for f in json.load(open(os.path.join(ROOT, 'data/neighborhood-rents.geojson')))['features']
            if f['properties'].get('cd') == 'BKCB6'}
    for f in g['features']:
        nb = f['properties']['nb']
        if nb not in site: raise Exception('no site rent figures for ' + nb)
        f['properties'] = site[nb]
    json.dump(g, open(gp, 'w'), separators=(',', ':'))
    # rent-history.json: every month for every CB6 neighborhood, CB6, Brooklyn and NYC, by unit size, from the site's rent explorer.
    ex = json.load(open(os.path.join(ROOT, 'data/rent-explorer.json'))); months = ex['months']; A = {a['id']: a for a in ex['areas']}
    ib = json.load(open(os.path.join(ROOT, 'data/inventory-by-bed.json')))
    def full(s):
        if not s: return [None] * len(months)
        st, v = s; out = [None] * st + list(v); return (out + [None] * len(months))[:len(months)]
    alias = {'Columbia Street Waterfront District': 'Columbia St Waterfront District'}
    beds = ['studio', 'br1', 'br2', 'br3']
    hoods = {}
    for f in g['features']:
        nb = f['properties']['nb']; se = alias.get(nb, nb); a = A.get('n:' + se)
        if not a: raise Exception('no rent history for ' + nb)
        d = {k: full(a['s'].get(k)) for k in beds}
        d['rent'] = full(a['s'].get('all')); d['inv'] = full(a['s'].get('inv'))
        for k in beds: d['inv_' + k] = full(ib['nb'].get(se, {}).get(k))
        hoods[nb] = d
    def area(i): a = A[i]; return {k: full(a['s'].get(k)) for k in beds + ['all']}
    hist = {'months': months, 'beds': [['studio', 'Studio'], ['br1', '1 BR'], ['br2', '2 BR'], ['br3', '3+ BR'], ['all', 'Overall']],
            'neighborhoods': hoods, 'cb6': area('c:BKCB6'),
            'compare': {'Brooklyn': {'rent': area('b:Brooklyn')}, 'NYC': {'rent': area('x:NYC')}}, 'last': ex['meta'].get('last')}
    json.dump(hist, open(os.path.join(OUT, 'rent-history.json'), 'w'), separators=(',', ':'))
    print('rent screen files', len(hoods), 'neighborhoods,', len(months), 'months, last', ex['meta'].get('last'))

def js_object(txt):
    """A JS object/array literal with bare keys and either quote style, as JSON (walked character by character)."""
    out, i, n = [], 0, len(txt)
    while i < n:
        c = txt[i]
        if c in "'\"":
            j = i + 1; buf = []
            while j < n and txt[j] != c:
                if txt[j] == '\\' and j + 1 < n: buf.append(txt[j + 1]); j += 2; continue
                buf.append(txt[j]); j += 1
            out.append(json.dumps(''.join(buf))); i = j + 1; continue
        m = re.match(r'[A-Za-z_][A-Za-z0-9_]*(?=\s*:)', txt[i:])
        if m and (not out or out[-1].rstrip()[-1:] in '{,'):
            out.append(json.dumps(m.group(0))); i += len(m.group(0)); continue
        out.append(c); i += 1
    t = re.sub(r",\s*([}\]])", r"\1", ''.join(out))
    return json.loads(t)

def applicants():
    best = None
    for f in glob.glob(os.path.join(ROOT, '*/index.html')):
        s = open(f, encoding='utf-8', errors='ignore').read()
        if 'var APPS' not in s or 'MEETING' not in s or 'Liquor license applicants' not in s: continue
        folder = os.path.basename(os.path.dirname(f))
        if not re.fullmatch(r'\d{5,6}', folder): continue
        m, d, y = (folder[0], folder[1:3], folder[3:]) if len(folder) == 5 else (folder[0:2], folder[2:4], folder[4:])
        date = '20%s-%02d-%02d' % (y, int(m), int(d))
        if best is None or date > best[0]: best = (date, f, s, folder)
    if not best: print('applicants: no meeting page found'); return
    date, f, s, folder = best
    meet = js_object(re.search(r'MEETING\s*=\s*(\{.*?\});', s, re.S).group(1))
    apps = js_object(re.search(r'APPS\s*=\s*(\[.*?\]);', s, re.S).group(1))
    title = re.search(r'<title>([^<]*)', s).group(1)
    time_m = re.search(r'(\d{1,2}(?::\d{2})?\s*[AP]M)', title)
    room = re.search(r'<b>Room</b>\s*([^<]*)', s); why = re.search(r'<b>Why</b>\s*([^<]*)', s); chair = re.search(r'<b>Committee Chair</b>\s*([^<]*)', s)
    notice = re.search(r'href="([^"]+)"[^>]*>Meeting notice', s)
    out = {'source': 'bkcb6.app/%s, the committee meeting page' % folder, 'generated': NOW.strftime('%Y-%m-%dT%H:%M:%S+00:00'),
           'meeting': {'committee': 'Business Affairs & Licenses Committee', 'date': date, 'time': time_m.group(1) if time_m else '',
                       'title': title.strip(), 'location': meet.get('name', ''), 'sub': meet.get('sub', ''), 'lat': meet.get('lat'), 'lng': meet.get('lng'),
                       'room': room.group(1).strip() if room else '', 'why': why.group(1).strip() if why else '', 'chair': chair.group(1).strip() if chair else '',
                       'notice': notice.group(1) if notice else '', 'page': 'https://bkcb6.app/%s/' % folder},
           'applicants': apps}
    json.dump(out, open(os.path.join(OUT, 'liquor-applicants.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
    print('applicants', date, len(apps))
    # Each applicant's own logo, from the meeting page's logos/ folder, for the apps' map and list.
    import shutil
    ld = os.path.join(OUT, 'liquor-applicants/logos'); shutil.rmtree(ld, ignore_errors=True); os.makedirs(ld, exist_ok=True)
    n = 0
    for ap in apps:
        src = os.path.join(os.path.dirname(f), 'logos', '%s.png' % ap.get('id', ''))
        if os.path.exists(src): shutil.copyfile(src, os.path.join(ld, os.path.basename(src))); n += 1
    print('applicant logos', n, 'of', len(apps))

def minutes():
    """Every set of minutes on bkcb6.app/minutes, in the app's format ({d, b, t}): the date from the file name,
    the committee from the page header, and the text of the page, one line per paragraph or heading."""
    import html as H
    recs = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'minutes/*.html'))):
        s = open(f, encoding='utf-8', errors='ignore').read()
        m = re.match(r'(\d{4}-\d{2}-\d{2})-', os.path.basename(f))
        art = re.search(r'<article>(.*?)</article>', s, re.S)
        cm = re.search(r'<div class="cm">(.*?)</div>', s, re.S)
        if not (m and art and cm): continue
        lines = []
        for blk in re.findall(r'<(?:h\d|p|li|pre|td|div)[^>]*>(.*?)</(?:h\d|p|li|pre|td|div)>', art.group(1), re.S):
            for ln in re.sub(r'<br\s*/?>', '\n', blk).split('\n'):
                t = H.unescape(re.sub(r'<[^>]+>', '', ln)).strip()
                if t: lines.append(t)
        b = re.sub(r'\s*\(formerly [^)]*\)', '', H.unescape(re.sub(r'<[^>]+>', '', cm.group(1)))).strip()
        b = re.sub(r'\s*·\s*Draft$', '', b).replace('Committee minute scans (multiple committees)', 'Committee minutes (scans)')
        recs.append({'d': m.group(1), 'b': b, 't': '\n'.join(lines)})
    if len(recs) < 500: raise Exception('only %d minutes pages read' % len(recs))
    json.dump(recs, open(os.path.join(OUT, 'minutes.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
    print('minutes', len(recs))

# Static trees the apps carry (logos, pages, lot files, tiles). Each is one line in app/manifest.json with the
# sha of its own index under app/index/, so a phone fetches a tree's index only when something in it changed.
# Folders other jobs write into (civic/cal, civic/feeds, civic/ui, civic/officials, civic/transport...) stay listed
# file by file in the manifest, as they always were.
DIRS = ['Logos', 'site', 'civic/apps', 'civic/basemap', 'civic/blocks', 'civic/boardlogos', 'civic/bqe', 'civic/business',
        'civic/compplan', 'civic/directory', 'civic/dsny', 'civic/fhgs', 'civic/gowanus', 'civic/liquor-logos', 'civic/lots',
        'civic/lotstiles', 'civic/orgchart', 'civic/precincts', 'civic/replogos', 'civic/tiles', 'civic/useofland', 'civic/zoning']

def manifest():
    """app/manifest.json: every file under app/data (the pack), plus the site's own files the apps carry
    (app/pack-sources.json, listed with src so the phones fetch the site's copy), plus per-app variants
    (app/data/variants/<app>/..., listed under variants so each app takes its own). The trees in DIRS are
    listed once each, with their files in app/index/<tree>.json."""
    mp = os.path.join(ROOT, 'app/manifest.json')
    base = os.path.join(ROOT, 'app/data')
    def entry(p):
        b = open(p, 'rb').read()
        return {'sha': hashlib.sha256(b).hexdigest(), 'size': len(b)}
    files = {}
    variants = {}
    for dp, _, fs in os.walk(base):
        for n in fs:
            if n == '.DS_Store': continue
            p = os.path.join(dp, n); rel = os.path.relpath(p, base).replace(os.sep, '/')
            if rel.startswith('variants/'):
                _, app, path = rel.split('/', 2)
                variants.setdefault(path, {})[app] = dict(entry(p), src='app/data/' + rel)
                continue
            files[rel] = entry(p)
    for path, apps in variants.items():
        files[path] = {'variants': apps}
    # The site's own files, served from where they live on the site.
    sp = os.path.join(ROOT, 'app/pack-sources.json')
    src = json.load(open(sp)) if os.path.exists(sp) else {}
    missing = 0
    def add(rel, site):
        nonlocal missing
        if rel in files: return
        p = os.path.join(ROOT, site)
        if not os.path.isfile(p): missing += 1; return
        files[rel] = dict(entry(p), src=site)
    for bdir, sdir in src.get('dirs', {}).items():
        sd = os.path.join(ROOT, sdir)
        for dp, _, fs in os.walk(sd):
            for n in fs:
                if n == '.DS_Store': continue
                p = os.path.join(dp, n); r = os.path.relpath(p, sd).replace(os.sep, '/')
                add(bdir + r, sdir + r)
    for rel, site in src.get('files', {}).items(): add(rel, site)
    # The static trees: one index file each, one line in the manifest.
    idir = os.path.join(ROOT, 'app/index'); os.makedirs(idir, exist_ok=True)
    dirs = {}
    for d in DIRS:
        tree = {k: v for k, v in files.items() if k.startswith(d + '/')}
        if not tree: continue
        for k in tree: del files[k]
        body = json.dumps({'files': dict(sorted(tree.items()))}, separators=(',', ':'), sort_keys=True)
        name = d.replace('/', '__') + '.json'
        open(os.path.join(idir, name), 'w').write(body)
        dirs[d] = {'sha': hashlib.sha256(body.encode()).hexdigest(), 'n': len(tree), 'index': 'app/index/' + name}
    m = {'files': dict(sorted(files.items())), 'dirs': dirs, 'generated': NOW.strftime('%Y-%m-%dT%H:%M:%S+00:00')}
    txt = '\n'.join(l.lstrip(' ') for l in json.dumps(m, indent=1).split('\n'))
    open(mp, 'w').write(txt)
    print('manifest', len(m['files']), 'files', len(dirs), 'trees holding', sum(v['n'] for v in dirs.values()), 'files;', len(variants), 'with variants;', missing, 'site sources missing')

if __name__ == '__main__':
    only = sys.argv[1:] or ['lpc', 'liquor', 'applicants', 'minutes', 'rents']
    failed = []
    for k in only:
        # One source being down keeps its last good file; the rest still publish.
        try: {'lpc': lpc_permits, 'liquor': liquor, 'applicants': applicants, 'minutes': minutes, 'rents': rents}[k]()
        except Exception as e: failed.append(k); print('FAILED', k, e)
    manifest()
    if failed: print('kept the previous file for', ', '.join(failed))
