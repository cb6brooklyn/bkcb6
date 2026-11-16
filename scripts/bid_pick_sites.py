#!/usr/bin/env python3
"""From the web search for each BID business with no website on record (data/bid-audit/search.json: profile slug ->
the top results, [url, title], from a search on its name and address), picks the business's own website: the first
result that is not a listings, delivery, review or social site and whose address or title carries the business's name.
The website goes on the Directory profile (weburl) and into data/bid-audit/logo-queue.json, so bid_logo_shots.js can
take the logo from it. Rerunnable."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
NOT = re.compile(r'yelp|google|facebook|instagram|tiktok|twitter|x\.com|linkedin|tripadvisor|grubhub|doordash|seamless|ubereats|postmates|caviar|slice(life)?|menupages|allmenus|'
                 r'opentable|resy|tock|toasttab|mapquest|yellowpages|yp\.com|bbb\.org|manta|chamberofcommerce|bizapedia|opencorporates|dnb\.com|zoominfo|loopnet|streeteasy|'
                 r'propertyshark|zillow|redfin|apartments|trulia|compass\.com|cityrealty|corcoran|elliman|npiregistry|npidb|healthgrades|zocdoc|vitals|webmd|sharecare|doximity|'
                 r'usnews|wellness\.com|ratemds|bkmag|timeout|nymag|eater|theinfatuation|infatuation|nytimes|brownstoner|patch\.com|zomato|foursquare|restaurantji|restaurantguru|'
                 r'sirved|menuism|beyondmenu|chownow|order\.online|clover\.com|square\.site|squareup|fresha|vagaro|booksy|styleseat|mindbody|classpass|groupon|nextdoor|'
                 r'wikipedia|joe\.coffee|cylex|hotfrog|brownbook|merchantcircle|superpages|citysearch|local\.com|nyc\.gov|ny\.gov|wanderlog|apple\.com|bing\.com|waze|'
                 r'locations\.|stores\.|storelocator|dentalplans|lawyers?\.com|avvo|justia|martindale|findlaw|realtor|bhsusa|homes\.com|cars\.com|carfax|bkcb6|github|pinterest|'
                 r'youtube|reddit|quora|tumblr|blogspot|medium\.com|substack|yahoo|aol\.com|msn\.com', re.I)
STOP = {'the', 'and', 'of', 'inc', 'llc', 'corp', 'nyc', 'ny', 'brooklyn', 'bklyn', 'park', 'slope', 'deli', 'grocery', 'restaurant', 'cafe', 'bar', 'pizza', 'salon',
        'nail', 'nails', 'spa', 'shop', 'store', 'market', 'avenue', 'ave', 'street', 'st', 'atlantic', 'flatbush', 'fifth', '5th', 'new', 'york', 'pc', 'pllc', 'dds', 'md',
        'dental', 'care', 'center', 'services', 'service', 'group', 'co', 'company', 'by', 'at', 'on', 'in', 'for', 'a', 'de', 'la', 'el', 'law', 'office', 'offices'}
def toks(n): return [w for w in re.findall(r'[a-z0-9]+', n.lower().replace('&', ' ').replace("'", '')) if w not in STOP and len(w) > 2]
Q = json.load(open('data/bid-audit/logo-queue.json'))
S = json.load(open('data/bid-audit/search.json'))
D = json.load(open('app/data/civic/orgs/orgs-profiles.json', encoding='utf-8')); BY = {p['slug']: p for p in D['profiles']}
found = 0
for q in Q:
    if q[3] or q[0] not in S: continue
    ts = toks(q[1])
    if not ts: continue
    for r in S[q[0]]:
        if not isinstance(r, list) or len(r) < 2: continue
        u, title = r
        host = re.sub(r'^https?://(www\.)?', '', u).split('/')[0].lower()
        if not host or NOT.search(host): continue
        hk = re.sub(r'[^a-z0-9]', '', host.split('.')[0])
        if any(t in hk for t in ts if len(t) >= 4) or (len(ts) and all(t in title.lower() for t in ts[:2])):
            q[3] = 'https://' + re.sub(r'^https?://', '', u).split('/')[0] + '/'
            p = BY.get(q[0])
            if p is not None and not p.get('weburl'):
                p['weburl'] = q[3]; p['web'] = host
            found += 1; break
json.dump(Q, open('data/bid-audit/logo-queue.json', 'w'), indent=0)
open('app/data/civic/orgs/orgs-profiles.json', 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
print('websites found:', found, 'of', sum(1 for q in Q if q[0] in S))
