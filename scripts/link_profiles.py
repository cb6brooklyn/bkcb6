#!/usr/bin/env python3
"""Every official, agency and community board named on the government pages links to its one profile page instead
of its outside website: bkcb6.app/govhub.html (the org charts, the City Charter and the State Constitution) and
charter.html on the site, and the apps' copy of the org chart (app/data/civic/orgchart/orgchart.html), where the
links are full bkcb6.app addresses that the apps open as their in-app profile (app/data/civic/profile-index.json).
Links to documents, laws and news stay as they are. Run after scripts/one_profile.py."""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
idx = json.load(open(os.path.join(ROOT, 'data/profile-index.json')))
def norm(u):
    u = (u or '').strip().lower()
    u = re.sub(r'^https?://', '', u); u = re.sub(r'^(www1?|m)\.', '', u); u = u.split('#')[0].split('?')[0]
    u = re.sub(r'/index\.(page|html|shtml)$', '', u); return u.rstrip('/')

def page_for(href):
    if href.startswith(('http://', 'https://')):
        k = norm(href)
        if k.startswith('bkcb6.app'):
            p = '/' + k[len('bkcb6.app'):].strip('/') + '/'
            return idx['forward'].get(p) or (p if p in idx['pages'] else None)
        return idx['urls'].get(k)
    if href.startswith('/'):
        p = href.split('#')[0].split('?')[0]
        return idx['forward'].get(p) or idx['forward'].get(p.rstrip('/') + '/')
    return None

A = re.compile(r'<a\b([^>]*?)href="([^"]+)"([^>]*)>(.*?)</a>', re.S)
def fix(path, app=False):
    s = open(path, encoding='utf-8').read()
    n = 0
    def sub(m):
        nonlocal n
        pre, href, post, inner = m.groups()
        page = page_for(href)
        if not page: return m.group(0)
        n += 1
        target = ('https://bkcb6.app' + page) if app else page
        attrs = re.sub(r'\s*(target|rel)="[^"]*"', '', pre + post)
        inner = re.sub(r'\s*(↗|&#8599;|&nearr;)\s*', '', inner)
        attrs = attrs.strip()
        return '<a %shref="%s">%s</a>' % ((attrs + ' ') if attrs else '', target, inner)
    t = A.sub(sub, s)
    if t != s: open(path, 'w', encoding='utf-8').write(t)
    print(os.path.relpath(path, ROOT), n, 'links to profiles')

for f in ('govhub.html', 'charter.html'):
    if os.path.exists(os.path.join(ROOT, f)): fix(os.path.join(ROOT, f))
fix(os.path.join(ROOT, 'app/data/civic/orgchart/orgchart.html'), app=True)
