"""Local businesses in the Organizations tab, by kind (restaurants, stores, markets, venues), each with its BID or
neighborhood in its subtitle; the BIDs have their own heading. Edits app/data/civic/orgs/orgs-profiles.json in place."""
import json
P = 'app/data/civic/orgs/orgs-profiles.json'
d = json.load(open(P))
PS, AA, NF, GW = 'In the Park Slope Fifth Avenue BID', 'In the Atlantic Avenue BID', 'In the North Flatbush BID', 'In the proposed Gowanus BID'
BIDS = 'Business improvement districts'
GO = 'Gowanus, outside the proposed BID'
RH, CG, PO = 'Red Hook: no BID', 'Carroll Gardens and Columbia Street: no BID', 'Park Slope, outside the BID'
# the headings under Local businesses: by kind of business; where it is (its BID, or none) goes in the subtitle
FOOD, STORES, MARKETS, VENUES = 'Restaurants, cafes and food', 'Stores', 'Markets', 'Venues'
TOPICS = [FOOD, STORES, MARKETS, VENUES]
KIND = {'red-hook-lobster-pound': FOOD, 'principles-gi-coffee-house': FOOD, 'strong-rope-brewery': FOOD, 'house-pepper': FOOD,
        'bark-slope': STORES, 'bird-collective': STORES, 'books-are-magic': STORES, 'record-shop': STORES,
        'park-slope-farmers-market': MARKETS, 'brooklyn-pop-up': MARKETS, 'nitehawk-prospect-park': VENUES, 'jalopy-theatre': VENUES, 'union-hall': VENUES, 'the-bell-house': VENUES}
# where each business is (from bids.geojson for the BIDs; the address for the rest)
WHERE = {'bark-slope': PS, 'park-slope-farmers-market': PO, 'nitehawk-prospect-park': PO, 'bird-collective': PO,
         'principles-gi-coffee-house': GO, 'strong-rope-brewery': GW,
         'record-shop': RH, 'red-hook-lobster-pound': RH, 'brooklyn-pop-up': RH, 'house-pepper': RH,
         'books-are-magic': CG, 'jalopy-theatre': CG, 'union-hall': PS, 'the-bell-house': GW}
CAT = {'bark-slope': 'Pet grooming and supplies', 'park-slope-farmers-market': 'Farmers market', 'nitehawk-prospect-park': 'Movie theater',
       'bird-collective': 'Apparel shop and bird walks', 'principles-gi-coffee-house': 'Cafe and event space', 'strong-rope-brewery': 'Brewery and taproom',
       'record-shop': 'Record store and music venue', 'red-hook-lobster-pound': 'Seafood restaurant', 'brooklyn-pop-up': 'Artisan market',
       'house-pepper': 'Culinary business', 'books-are-magic': 'Bookstore', 'jalopy-theatre': 'Music venue and school',
       'union-hall': 'Bar, comedy and music venue', 'the-bell-house': 'Music and comedy venue'}
def base(slug, typ, name, seat, desc, lat, lng, addr, web='', intro=(), links=(), logo='', email='', phone='', since='', kv=()):
    return {'slug': slug, 'type': typ, 'name': name, 'seat': seat, 'desc': desc, 'lat': lat, 'lng': lng, 'addr': addr, 'zip': '',
            'addr_note': '', 'phone': phone, 'email': email, 'web': web.replace('https://', '').replace('http://', '').strip('/'),
            'weburl': web, 'since': since, 'intro': list(intro), 'does': [], 'kv': list(kv) or [['Community board', 'Brooklyn Community Board 6']],
            'links': list(links), 'logo': logo, 'cal': None, 'n': 0, 'going': [], 'kind': 'org', 'official': ''}
prof = [p for p in d['profiles'] if p['slug'] not in WHERE and p['slug'] not in ('atlantic-avenue-bid', 'north-flatbush-bid', 'gowanus-bid-formation-effort')]
# the businesses join the profiles, under Local businesses, by BID
for b in d['businesses']:
    b = dict(b); nb = b['seat'].split(' · ')[-1].replace(', Brooklyn', '')
    w = {'bark-slope': 'Park Slope Fifth Avenue BID', 'strong-rope-brewery': 'Proposed Gowanus BID', 'principles-gi-coffee-house': 'Gowanus, no BID',
         'park-slope-farmers-market': 'Park Slope, no BID', 'nitehawk-prospect-park': 'Park Slope, no BID', 'bird-collective': 'Park Slope, no BID',
         'record-shop': 'Red Hook, no BID', 'red-hook-lobster-pound': 'Red Hook, no BID', 'brooklyn-pop-up': 'Red Hook, no BID', 'house-pepper': 'Red Hook, no BID',
         'books-are-magic': 'Carroll Gardens, no BID', 'jalopy-theatre': 'Columbia Street Waterfront, no BID',
         'union-hall': 'Park Slope Fifth Avenue BID', 'the-bell-house': 'Proposed Gowanus BID'}[b['slug']]
    b.update(group='Local businesses', topic=KIND[b['slug']], sort=0, kind='org', seat=f"{CAT[b['slug']]} · {w}")
    prof.append(b)
# the BIDs and business groups head their subsections
for p in prof:
    if p['slug'] == 'park-slope-fifth-avenue-bid': p.update(group=BIDS, topic='Established BIDs', sort=1)
    if p['slug'] == 'atlantic-avenue-ldc': p.update(group='Community groups', topic='Business and economic development', sort=0)
    if p['slug'] == 'red-hook-business-alliance': p.update(group=BIDS, topic='Business alliances', sort=3, logo='rhba-logo.png', seat='Business alliance \u00b7 Red Hook, no BID')
aa = base('atlantic-avenue-bid', 'atlanticavebid', 'Atlantic Avenue BID', 'Business improvement district · Atlantic Avenue',
          'Atlantic Avenue Business Improvement District, established 2011. Atlantic Avenue from Fourth Avenue to the BQE, one block north and south, in Community Boards 2 and 6.',
          40.690567, -73.997197, 'Atlantic Avenue, Fourth Avenue to the BQE', 'http://www.atlanticavebid.org/', since='2011',
          intro=['The Atlantic Avenue Business Improvement District runs along Atlantic Avenue from Fourth Avenue to the Brooklyn-Queens Expressway, with the side streets one block north and south. The north side between Court and Smith Streets is in the Court-Livingston-Schermerhorn BID instead.',
                 'It was established in 2011 and spans Community Boards 2 and 6.'],
          links=[['Their site', 'http://www.atlanticavebid.org/']])
aa.update(group=BIDS, topic='Established BIDs', sort=1)
nf = base('north-flatbush-bid', 'northflatbushbid', 'North Flatbush BID', 'Business improvement district · Flatbush Avenue',
          'North Flatbush Avenue Business Improvement District, established 1986, along Flatbush Avenue in Community Boards 2, 6 and 8.',
          40.682724, -73.975324, 'Flatbush Avenue, Atlantic Avenue to Grand Army Plaza', 'https://northflatbushbid.nyc/', since='1986',
          intro=['The North Flatbush Business Improvement District runs along Flatbush Avenue between Atlantic Avenue and Grand Army Plaza, in Community Boards 2, 6 and 8. It was established in 1986.'],
          links=[['Their site', 'https://northflatbushbid.nyc/']])
nf.update(group=BIDS, topic='Established BIDs', sort=1)
gw = base('gowanus-bid-formation-effort', 'gowanusbid', 'Gowanus BID Formation Effort', 'A business improvement district being formed · Gowanus',
          'Gowanus BID Formation Effort. A steering committee of local stakeholders, facilitated by the Gowanus Canal Conservancy and working with the Department of Small Business Services, is forming a business improvement district in Gowanus.',
          40.6745, -73.9886, 'Gowanus Canal Conservancy, 248 Third Street', 'https://gowanusimprovementdistrict.org',
          email='gowanusimprovementdistrict@gmail.com', phone='718-541-4378', logo='gcc.png',
          intro=['A steering committee of local stakeholders, facilitated by the Gowanus Canal Conservancy and working with the Department of Small Business Services, is forming a business improvement district in Gowanus, covering the Gowanus rezoning area. Its co-chairs are Andrea Parker, Chris Papamichael, Lisa Lightbody and Sam Alison-Mayne.',
                 'The effort began outreach in fall 2024 and is collecting ballots from property owners and commercial tenants; the BID needs 51 percent support before it goes to the city for approval. Public meetings: October 14 (virtual) and November 4 at Wyckoff Gardens Community Center.'],
          links=[['Their site', 'https://gowanusimprovementdistrict.org'], ['About', 'https://gowanusimprovementdistrict.org/about'], ['Questions and answers', 'https://gowanusimprovementdistrict.org/faq']])
gw['cal'] = 'gowanusbid'; gw.update(group=BIDS, topic='Being formed', sort=2)
prof += [aa, nf, gw]
d['profiles'] = prof
# calendar entries: the stray Knicks entry goes; the businesses' calendar entries come back so their profiles show their events
d['orgs'] = [o for o in d['orgs'] if o['slug'] != 'knicks']
have = {o['slug'] for o in d['orgs']}
for o in d['businessOrgs']:
    if o['slug'] not in have: d['orgs'].append(dict(o, topic=''))
if 'gowanusbid' not in have:
    d['orgs'].append({'slug': 'gowanusbid', 'name': 'Gowanus BID Formation Effort', 'logo': 'gcc.png', 'site': 'https://gowanusimprovementdistrict.org', 'cal': 'gowanus-bid-formation-effort', 'n': 2, 'group': BIDS, 'topic': '', 'sort': 2})
for g in d['groups']:
    if g['name'] == 'Local businesses': g['topics'] = TOPICS
if not any(g['name'] == BIDS for g in d['groups']):
    i = [g['name'] for g in d['groups']].index('Local businesses')
    d['groups'].insert(i, {'name': BIDS, 'topics': []})
for g in d['groups']:
    if g['name'] == BIDS: g['topics'] = ['Established BIDs', 'Being formed', 'Business alliances']
d['about'] = d['about'].replace('Local businesses sit in businesses (and their calendar entries in businessOrgs), apart from the community groups, and are listed in the Local businesses directory (civic/business/business-cb6.json).',
    'Local businesses are profiles with group Local businesses; their topic is the business improvement district they are in (or their neighborhood when outside one), and the BID itself heads that subsection with sort -2 or -1. businesses and businessOrgs keep the earlier copies.')
json.dump(d, open(P, 'w'), ensure_ascii=False, indent=1)
print(len(prof), 'profiles;', len(d['orgs']), 'calendar entries')
# the BIDs' calendar entries carry the same heading
d = json.load(open(P))
for o in d['orgs']:
    if o['slug'] in ('gowanusbid', 'ps5bid'): o.update(group=BIDS, topic='')
json.dump(d, open(P, 'w'), ensure_ascii=False, indent=1)
