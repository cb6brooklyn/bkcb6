#!/usr/bin/env python3
"""Second pass for scripts/school_web.py: a school with no website from NYC Public Schools or the search gets its own
domain tried from its name (packer.edu, berkeleycarroll.org, ...); a domain counts only when its page title or
description names the school and reads as a school's. Then the same logo and description reading as school_web.py.
Updates data/schools-web/web.json. Usage: python3 scripts/school_web_guess.py"""
import concurrent.futures as cf, html, json, os, re, socket, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import school_web as w
socket.setdefaulttimeout(4)
STOP = {'the', 'of', 'for', 'and', 'school', 'schools', 'inc', 'at', 'a', 'an', 'in', 'on', 'new', 'york', 'ny', 'nyc', 'site', 'annex', 'program'}
def domains(name):
    n = html.unescape(name).lower().replace('&', ' and ').replace("'", '')
    n = re.sub(r'\b(st|saint)\b\.?', 'st', n)
    ws = [x for x in re.findall(r'[a-z0-9]+', n) if x not in STOP]
    allw = [x for x in re.findall(r'[a-z0-9]+', n) if x not in ('the', 'inc', 'of', 'and', 'for', 'a', 'an', 'at')]
    if not ws: return []
    stems = {''.join(ws), ''.join(ws[:2]), ''.join(ws[:3]), ws[0], ''.join(x[0] for x in ws), ''.join(allw), '-'.join(ws[:3]), ''.join(ws) + 'school', ''.join(ws[:2]) + 'school',
             ''.join(x[0] for x in allw)}
    if len(ws[0]) < 4: stems.discard(ws[0])
    out = []
    for s in stems:
        if len(s) < 3: continue
        for t in ('.org', '.edu', '.com', '.net', '.us'):
            out.append(s + t)
    return out
def resolves(d):
    try: socket.gethostbyname(d); return True
    except Exception: return False
def guess(s):
    words = [x for x in re.findall(r'[a-z]{4,}', html.unescape(s['name']).lower()) if x not in ('school', 'schools', 'academy', 'high', 'elementary', 'middle',
             'charter', 'center', 'learning', 'program', 'site', 'annex', 'brooklyn', 'queens', 'bronx', 'manhattan', 'staten', 'island', 'york', 'with', 'from', 'the')]
    if not words: return ''
    need = len(words) if len(words) <= 2 else -(-len(words) * 6 // 10)
    for d in domains(s['name']):
        if not resolves(d): continue
        for pre in ('https://www.', 'https://'):
            p = w.get(pre + d + '/')
            if not p or p.status_code != 200 or 'html' not in p.headers.get('content-type', ''): continue
            t = (w.T((re.search(r'<title[^>]*>(.*?)</title>', p.text, re.S | re.I) or [None, ''])[1]) + ' ' + w.meta(p.text, 'description') + ' ' + w.meta(p.text, 'og:site_name') + ' ' + w.meta(p.text, 'og:title')).lower()
            full = p.text
            street = re.sub(r'^\d+\S*\s+', '', (s.get('addr') or '').lower()).split(' ')[0] if s.get('addr') else ''
            here = (s.get('zip') and s['zip'] in full) or (len(street) > 4 and street in full.lower()) or ((s.get('boro') or '').lower() not in ('', 'manhattan') and s['boro'].lower() in full.lower())   # its own zip, street or borough on the page
            if here and sum(1 for x in words if x in t) >= need and w.SCHOOLWORD.search(t) and not re.search(r'for sale|domain|parked|godaddy|hugedomains', t):
                return p.url
            break
    return ''
def one(s):
    o = w.W.get(s['slug']) or {}
    url = guess(s)
    if not url: return s['slug'], None
    o['website'] = url; o['found_by_domain'] = True
    x = w.site(url, s['name'])
    if x:
        o['website_final'] = x['final']; o['desc'] = x['desc']; o['desc_src'] = x['desc_src']; o['site_title'] = x['title']
        u, kind = w.fetch_logo(s['slug'], x['cands']); o['logo_src'] = u; o['logo_kind'] = kind
    o['logo'] = os.path.exists(os.path.join(w.LOGO, s['slug'] + '.png'))
    o['checked'] = time.strftime('%Y-%m-%d')
    return s['slug'], o
todo = [s for s in w.R if not (w.W.get(s['slug']) or {}).get('website')]
print('to do:', len(todo), flush=True)
n = 0
with cf.ThreadPoolExecutor(32) as ex:
    for slug, o in ex.map(one, todo):
        if o: w.W[slug] = o; n += 1
json.dump(w.W, open(w.OUT, 'w'), ensure_ascii=False, indent=0)
v = list(w.W.values())
print('found by domain:', n, '| website:', sum(1 for x in v if x.get('website')), '| description:', sum(1 for x in v if x.get('desc')), '| logo:', sum(1 for x in v if x.get('logo')))
