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

def manifest():
    mp = os.path.join(ROOT, 'app/manifest.json')
    m = json.load(open(mp)) if os.path.exists(mp) else {'files': {}}
    # Files removed from app/data (e.g. last meeting's logos) leave the manifest too.
    m['files'] = {k: v for k, v in m.get('files', {}).items() if os.path.exists(os.path.join(ROOT, 'app/data', k))}
    base = os.path.join(ROOT, 'app/data')
    for dp, _, fs in os.walk(base):
        for n in fs:
            p = os.path.join(dp, n); rel = os.path.relpath(p, base).replace(os.sep, '/')
            b = open(p, 'rb').read()
            m.setdefault('files', {})[rel] = {'sha': hashlib.sha256(b).hexdigest(), 'size': len(b)}
    m['generated'] = NOW.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    txt = '\n'.join(l.lstrip(' ') for l in json.dumps(m, indent=1).split('\n'))
    open(mp, 'w').write(txt); print('manifest', len(m['files']), 'files')

if __name__ == '__main__':
    only = sys.argv[1:] or ['lpc', 'liquor', 'applicants', 'minutes']
    failed = []
    for k in only:
        # One source being down keeps its last good file; the rest still publish.
        try: {'lpc': lpc_permits, 'liquor': liquor, 'applicants': applicants, 'minutes': minutes}[k]()
        except Exception as e: failed.append(k); print('FAILED', k, e)
    manifest()
    if failed: print('kept the previous file for', ', '.join(failed))
