#!/usr/bin/env python3
"""The directory offline in the apps: every profile page on the site goes in the app pack, and every link to one
opens the packed page in the app (no connection needed for the page; its map still needs one).

  app/pack-sources.json            dirs for each profile folder (parks, schools, NYPD sectors, businesses, the map
                                   profiles, all agencies) and the files those pages load
  data/profile-index.json and      "pages": each profile page's site path -> web:<path>?app=1, so a bkcb6.app link
  app/data/civic/profile-index.json to it opens the packed copy. Paths that already open an in-app screen keep it.

Idempotent. one_profile.py rewrites the index, so it calls this at the end; run on its own after adding pages.
"""
import glob, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDERS = ['park', 'school', 'nypd-sector', 'biz', 'subway', 'citibike', 'library', 'firehouse', 'food-place',
           'culture-place', 'poll-site', 'lift-site', 'childcare', 'vaccine-site', 'agencies']
DIR_ONLY = ['site-icons/agencies/']                       # logos the agency pages show
FILES = ['assets/place-profile.css', 'data/calendar-events.json', 'assets/site-bar.js']

def pages():
    out = []
    for d in FOLDERS:
        for f in sorted(glob.glob(os.path.join(ROOT, d, '**', '*.html'), recursive=True)):
            out.append(os.path.relpath(f, ROOT))
    return out

def add_index(idx):
    n = 0
    for rel in pages():
        web = 'web:' + rel + '?app=1'
        if rel.endswith('/index.html'):
            keys = ['/' + rel[:-len('index.html')]]
        else:
            keys = ['/' + rel, '/' + rel + '/', '/' + rel[:-5] + '/']
        for k in keys:
            if idx['pages'].get(k, '').startswith(('org:', 'official:', 'board:')): continue
            if idx['pages'].get(k) != web: idx['pages'][k] = web; n += 1
    return n

def main():
    ps = os.path.join(ROOT, 'app/pack-sources.json')
    src = json.load(open(ps))
    for d in FOLDERS + DIR_ONLY:
        d = d.rstrip('/') + '/'
        src['dirs']['site/' + d] = d
    for f in FILES:
        src['files']['site/' + f] = f
    # the flip-through directory (profiles/index.html, scripts/directory_grid.py) and every logo its tiles show,
    # so the apps' Directory tab opens it from the pack
    tj = os.path.join(ROOT, 'profiles/tiles.json')
    if os.path.exists(tj):
        for f in ('profiles/index.html', 'profiles/tiles.json'):
            src['files']['site/' + f] = f
        for t in json.load(open(tj))['tiles']:
            im = t[2] if len(t) > 2 and isinstance(t[2], str) else ''
            if im.startswith('/') and os.path.exists(os.path.join(ROOT, im[1:])):
                src['files']['site' + im] = im[1:]
    json.dump(src, open(ps, 'w'), ensure_ascii=False, indent=0)
    n = 0
    for p in ('data/profile-index.json', 'app/data/civic/profile-index.json'):
        idx = json.load(open(os.path.join(ROOT, p)))
        n = add_index(idx)
        json.dump(idx, open(os.path.join(ROOT, p), 'w'), ensure_ascii=False, indent=0, sort_keys=True)
    print(len(pages()), 'profile pages packed;', n, 'index entries added')

if __name__ == '__main__':
    main()
