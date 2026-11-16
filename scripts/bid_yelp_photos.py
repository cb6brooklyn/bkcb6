#!/usr/bin/env python3
"""Collects the photos and websites found for the BID businesses on their Yelp pages (read in a browser, relayed as
batches yelp-<n>.json: profile slug -> {biz: Yelp page, og: its main photo, web: the website the page links to, img: the
photo as a 320 pixel JPEG}). A business found on Yelp at its own address gets its photo (data/bid-audit/shots/<slug>.photo,
kind 'webphoto' in results.json) unless its own website already gave a logo, and its website on its Directory profile
and in the logo queue, so bid_logo_shots.js can look for the logo there. Run: python3 scripts/bid_yelp_photos.py <topic>"""
import json, os, re, sys, base64, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
TOPIC = sys.argv[1]
S = 'data/bid-audit/shots'; os.makedirs(S, exist_ok=True)
RF = os.path.join(S, 'results.json'); R = json.load(open(RF)) if os.path.exists(RF) else {}
YF = 'data/bid-audit/yelp.json'; Y = json.load(open(YF)) if os.path.exists(YF) else {}
msgs = [json.loads(l) for l in urllib.request.urlopen('https://ntfy.sh/%s/json?poll=1&since=all' % TOPIC, timeout=60).read().decode().splitlines() if l.strip()]
for m in msgs:
    a = m.get('attachment')
    if not a or not re.match(r'yelp-\d+\.json$', a['name']): continue
    try: batch = json.loads(urllib.request.urlopen(a['url'], timeout=60).read())
    except Exception: continue
    for slug, v in batch.items():
        img = v.pop('img', '')
        Y[slug] = v
        if img.startswith('data:image') and (R.get(slug, {}).get('kind') != 'logo' or not R[slug].get('used', True)):
            open(os.path.join(S, slug + '.photo'), 'wb').write(base64.b64decode(img.split(',', 1)[1]))
            R[slug] = {'kind': 'webphoto', 'how': 'the business\'s main photo on its Yelp page', 'url': 'https://www.yelp.com' + v.get('biz', '')}
json.dump(Y, open(YF, 'w'), indent=0)
json.dump(R, open(RF, 'w'), indent=0)
# websites linked from Yelp: onto the profile and the logo queue
Q = json.load(open('data/bid-audit/logo-queue.json'))
D = json.load(open('app/data/civic/orgs/orgs-profiles.json', encoding='utf-8')); BY = {p['slug']: p for p in D['profiles']}
web = 0
for q in Q:
    w = (Y.get(q[0]) or {}).get('web') or ''
    if w and not q[3] and not re.search(r'facebook|instagram|yelp|grubhub|doordash|seamless|ubereats|toasttab|linktr', w, re.I):
        q[3] = w; web += 1
        p = BY.get(q[0])
        if p is not None and not p.get('weburl'): p['weburl'] = w; p['web'] = re.sub(r'^https?://(www\.)?', '', w).split('/')[0]
json.dump(Q, open('data/bid-audit/logo-queue.json', 'w'), indent=0)
open('app/data/civic/orgs/orgs-profiles.json', 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('looked up on Yelp:', len(Y), '| found at their address:', sum(1 for v in Y.values() if v.get('biz')), '| photos:', sum(1 for v in R.values() if v.get('kind') == 'webphoto'), '| websites added:', web)
