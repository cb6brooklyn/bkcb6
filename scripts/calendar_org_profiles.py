#!/usr/bin/env python3
"""Every organization on the community calendar has a profile, on the site and in the apps.

1. New profiles (data/org-profiles-cal.json, built into /<slug>/ by build_org_pages.py) for the calendar
   organizations that had none or only a thin map or business listing: Winner, Kentler International Drawing Space,
   Textile Arts Center, The Green-Wood Cemetery, Dzieci Theatre, BAM Rose Cinemas. Each gets its /o/<key>.html
   events page too. Facts come from each organization's own site, NYC Parks/Wikipedia where noted, and the
   calendar's own listings; locations from NYC Planning Labs GeoSearch (PAD).
2. The apps (app/data/civic/orgs/orgs-profiles.json): one profile per calendar organization. The calendar profiles
   that were only on the site (South Brooklyn DSA, DuBois Bunche Center, Red Hook Community Justice Center) are
   added; the thin listings the new profiles replace are folded in (the liquor license rows stay) and removed;
   every profile carries its calendar key (`cal`).
3. scripts/app-calendar-types.json: each calendar key points at its profile, so the apps' calendar opens the
   profile (rebuild the calendar files with node scripts/build_app_calendar.mjs).
4. The replaced listing pages (/biz/..., /culture-place/...) forward to the profile; the map pins link to it.
Run after build_app_calendar.mjs's type map exists, map_profiles.py and biz_site_profiles.py; then build_org_pages.py.
"""
import colorsys, html, json, os, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda p: json.load(open(os.path.join(ROOT, p), encoding='utf-8'))
def W(p, d, **k): json.dump(d, open(os.path.join(ROOT, p), 'w', encoding='utf-8'), ensure_ascii=False, **k)
APP = 'app/data/civic/orgs/orgs-profiles.json'
CAL = 'data/org-profiles-cal.json'
TMAP = 'scripts/app-calendar-types.json'

def brand(bg):
    r, g, b = (int(bg[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    s = max(s, .45)
    f = lambda L, S=s: '#%02x%02x%02x' % tuple(round(c * 255) for c in colorsys.hls_to_rgb(h, L, S))
    return {'dark': f(.17), 'mid': f(.55), 'light': f(.82), 'wash': f(.96), 'accent': f(.42), 'ink': f(.30)}

CB = {'306': '<a href="/cb-bk-6.html">Brooklyn Community Board 6</a>', '307': '<a href="/cb-bk-7.html">Brooklyn Community Board 7</a>',
      '302': '<a href="/cb-bk-2.html">Brooklyn Community Board 2</a>'}

# key, slug, bg (the calendar's color), logo file in app/data/civic/cal/icons (None: no logo of its own), record
NEW = [
 ('winner', 'winner', '#2f4356', 'winner.png', dict(
   name='Winner', seat='Bakery and caf&eacute; &middot; Park Slope, Brooklyn',
   lat='40.665684', lng='-73.982278', addr='367 7th Avenue', zip='11215', bbl='3010940001', cd='306',
   addr_note='WINNER Bakery. WINNER in the Park is at the Picnic House in Prospect Park.',
   email='info@winner.nyc', web='winner.nyc', weburl='https://www.winner.nyc',
   intro=['<b>Winner</b> is a neighborhood bakery and caf&eacute; at <b>367 7th Avenue</b> in Park Slope: bread, pastries, coffee, sandwiches, dinner and pizza. It is take-out only, with some first-come outdoor seating, and open 365 days a year.',
          'Winner also runs <b>WINNER in the Park</b> at the Picnic House in Prospect Park, Winner Butcher and Runner Up.'],
   does=['Hours at the bakery: Monday and Tuesday 7 a.m. to 7 p.m., Wednesday to Sunday 7 a.m. to 8 p.m. Lunch sandwiches 10:30 a.m. to 6 p.m., dinner pickup 3 to 8 p.m., pizza Wednesday to Sunday 5 to 8 p.m., coffee 7 a.m. to 5 p.m.',
         'On the calendar: <b>Winner and a Show</b>, its dinner and concert series.'],
   kv=[['Hours', 'Mon&ndash;Tue 7 a.m.&ndash;7 p.m.; Wed&ndash;Sun 7 a.m.&ndash;8 p.m.']],
   links=[['Their site', 'https://www.winner.nyc', True], ['The bakery', 'https://www.winner.nyc/location/winner-bakery', True],
          ['WINNER in the Park', 'https://www.prospectpark.org/visit-the-park/park-map/places-to-eat/winner/', True]],
   group=('Local businesses', 'Restaurants, cafes and food'),
   replaces=['biz-08f6e2ec26'])),
 ('kentler', 'kentler-international-drawing-space', '#4a3b2a', None, dict(
   name='Kentler International Drawing Space', seat='Nonprofit gallery for drawings and works on paper &middot; Red Hook, Brooklyn',
   lat='40.676950', lng='-74.012994', addr='353 Van Brunt Street', zip='11231', bbl='3005760004', cd='306',
   phone='718-875-2098', email='drawing@kentlergallery.org', web='kentlergallery.org', weburl='https://kentlergallery.org', since='1990',
   intro=['<b>Kentler International Drawing Space</b> is a nonprofit gallery at <b>353 Van Brunt Street</b> in Red Hook devoted to drawings and works on paper. Florence Neal and Scott Pfaffman opened it in April <b>1990</b>.'],
   does=['Kentler runs exhibitions and events, <b>K.I.D.S. Art</b> education, and <b>The Kentler Flatfiles</b>, a collection of drawings and works on paper by more than 290 artists.',
         'The gallery is open Thursday to Sunday, noon to 5 p.m., during exhibitions. On the calendar: the <b>Kentler 100 Works on Paper</b> benefit.'],
   kv=[['Founded', '1990, by Florence Neal and Scott Pfaffman'], ['Hours', 'Thu&ndash;Sun noon&ndash;5 p.m. during exhibitions']],
   links=[['Their site', 'https://kentlergallery.org', True], ['Mission and history', 'https://kentlergallery.org/news/index.php/mission', True]],
   group=('Community groups', 'Arts and culture'),
   replaces=['biz-8c2a8e5647'])),
 ('tac', 'textile-arts-center', '#1f1f1f', None, dict(
   name='Textile Arts Center', seat='Textile school and studio &middot; Gowanus, Brooklyn',
   lat='40.677110', lng='-73.985180', addr='505 Carroll Street', zip='11215', bbl='3004480013', cd='306',
   addr_note='Between Third and Fourth Avenues. R to Union Street.',
   web='textileartscenter.com', weburl='https://www.textileartscenter.com',
   intro=['The <b>Textile Arts Center</b> at <b>505 Carroll Street</b> in Gowanus is dedicated to raising awareness and understanding of textiles through creative educational programming for kids and adults.'],
   does=['Classes run from one-day and weekend intensives to two-hour evening workshops and four-week courses: weaving, tapestry, natural dyeing and indigo, screen printing, felting, quilting, embroidery and zero waste sewing. <b>Sewing Seeds</b> is its natural dye initiative.',
         'On the calendar: the <b>Give Back Market</b> and Tat &amp; Chat with the Brooklyn Lace Guild.'],
   kv=[],
   links=[['Their site', 'https://www.textileartscenter.com', True]],
   group=('Community groups', 'Arts and culture'),
   replaces=['biz-e1997ed024'])),
 ('greenwood', 'the-green-wood-cemetery', '#5f7f2e', 'greenwood.png', dict(
   name='The Green-Wood Cemetery', seat='Cemetery and National Historic Landmark &middot; Greenwood Heights, Brooklyn',
   lat='40.658098', lng='-73.994843', addr='500 25th Street', zip='11232', bbl='3009020001', cd='307',
   addr_note='Main entrance at Fifth Avenue and 25th Street', web='green-wood.com', weburl='https://www.green-wood.com', since='1838',
   intro=['<b>The Green-Wood Cemetery</b> was founded in <b>1838</b> as a rural cemetery by Henry Evelyn Pierrepont and David Bates Douglass, its engineer and landscape architect. It covers <b>478 acres</b>, with the main entrance at Fifth Avenue and 25th Street, just south of CB6 in Brooklyn Community Board 7.',
          'It was designated a National Historic Landmark in 2006. <b>Battle Hill</b>, the highest natural point in Brooklyn, is named for fighting there in the Battle of Brooklyn on August 27, 1776. About 570,000 people are buried there.'],
   does=['Green-Wood is a working nonprofit cemetery. The Green-Wood Historic Fund, a separate nonprofit, supports its preservation and public programs: tours, talks, concerts and family events.',
         'On the calendar: its public events, such as the Day of the Dead family celebration.'],
   kv=[['Founded', '1838'], ['Size', '478 acres'], ['National Historic Landmark', '2006']],
   links=[['Their site', 'https://www.green-wood.com', True], ['Events', 'https://www.green-wood.com/events/', True]],
   group=('Community groups', 'Parks, gardens and the environment'),
   replaces=[], sources='Wikipedia, Green-Wood Cemetery')),
 ('dzieci', 'dzieci-theatre', '#3a2a5a', 'dzieci.png', dict(
   name='Dzieci Theatre', seat='Experimental theatre ensemble &middot; Park Slope, Brooklyn',
   lat='40.671896', lng='-73.975720', addr='241 Garfield Place', zip='11215', bbl='3010700034', cd='306',
   addr_note='Where its Garfield Place Black Light Halloween Puppet Show is held. The company has no venue of its own.',
   web='dziecitheatre.org', weburl='http://dziecitheatre.org/', since='1997',
   intro=['<b>Dzieci Theatre</b> is an experimental ensemble founded in <b>1997</b>, directed by founding director Matt Mitler with co-founder Yvonne Brecht. It works in the tradition of Jerzy Grotowski and describes every show as a quest for deeper meaning.'],
   does=['Dzieci brings its work into hospitals and institutions serving people in need, working alongside health care professionals. Its <b>Fools Mass</b>, a comedy of medieval fools holding a mass, has played around New York City since 1998, including at the Cathedral of St. John the Divine.',
         'On the calendar: the <b>Garfield Place Black Light Halloween Puppet Show</b>.'],
   kv=[['Founded', '1997'], ['Founding director', 'Matt Mitler']],
   links=[['Their site', 'http://dziecitheatre.org/', True], ['Meet Dzieci (TDF)', 'https://tdf.org/on-stage/tdf-stages/watch-meet-dzieci-theatre', True]],
   group=('Community groups', 'Arts and culture'),
   replaces=[], sources='TDF, Groupmuse, Time Out')),
 ('bamfilm', 'bam-rose-cinemas', '#1a1a1a', 'bamfilm.png', dict(
   name='BAM Rose Cinemas', seat='Movie theater at the Brooklyn Academy of Music &middot; Fort Greene, Brooklyn',
   lat='40.686333', lng='-73.977690', addr='30 Lafayette Avenue', zip='11217', bbl='3021110015', cd='302',
   addr_note='Peter Jay Sharp Building, Brooklyn Academy of Music', web='bam.org', weburl='https://www.bam.org/film', since='1998',
   intro=['<b>BAM Rose Cinemas</b> is the Brooklyn Academy of Music&rsquo;s movie theater, four screens with 749 seats in the Peter Jay Sharp Building at <b>30 Lafayette Avenue</b>. The space, once a music hall and then a playhouse, became BAM Rose Cinemas in <b>1998</b>. It is in Brooklyn Community Board 2.'],
   does=['BAM shows first-run, repertory and festival films. On the calendar: its repertory screenings.'],
   kv=[['Screens', '4 (749 seats)'], ['Opened', '1998']],
   links=[['BAM film', 'https://www.bam.org/film', True], ['About the cinemas', 'https://www.bam.org/rentals/bam-rose-cinemas', True]],
   group=('Community groups', 'Arts and culture'),
   replaces=['map-culture-place-bam-rose-cinemas'])),
]

# calendar key -> its profile slug in the apps, for keys whose type map named no profile or a wrong one
ALIAS = {'dredgers': 'gowanus-dredgers', 'powerhouse': 'powerhouse-arts', 'school': 'nyc-public-schools-cb6',
         'bpl': 'brooklyn-public-library-cb6', 'ps5bid': 'park-slope-fifth-avenue-bid', 'nycdot': 'nyc-dot',
         'bkbp': 'office-of-the-borough-president-of-brooklyn', 'gounardes': 'andrew-gounardes', 'simon': 'jo-anne-simon',
         'marcela-mitaynes': 'marcela-mitaynes', 'dan-goldman': 'dan-goldman', 'aviles': 'alexa-aviles',
         'bric': 'bric', 'bricarts': 'bric', 'principles': 'principles-gi-coffee-house', 'artichoke': 'artichoke-dance-company',
         'barkslope': 'bark-slope', 'cga': 'carroll-gardens-association', 'rhjc': 'red-hook-community-justice-center',
         'dcp': 'nyc-planning', 'lpc': 'landmarks-preservation-commission', 'fof': 'friends-of-firefighters',
         'aaldc': 'atlantic-avenue-ldc', 'nycparks': 'nyc-parks-brooklyn', 'green615': '6-15-green', 'hpd': 'nyc-hpd',
         'rgb': 'rent-guidelines-board', 'cec15': 'cec-district-15', 'bbg': 'brooklyn-botanic-garden', 'whynotart': 'why-not-art',
         'rhi': 'red-hook-initiative', 'swbtu': 'southwest-brooklyn-tenant-union', 'ps15': 'ps-15-patrick-f-daly',
         'bergenbikebus': 'bergen-bike-bus', 'secretgarden': 'the-secret-garden', 'cuffh': 'churches-united-for-fair-housing',
         'gotf': 'gowanus-oversight-task-force', 'campfriendship': 'camp-friendship', 'strongrope': 'strong-rope-brewery',
         'housepepper': 'house-pepper', 'porchstomp': 'porch-stomp', 'cswa': 'columbia-street-waterfront-association',
         'urbanmeadow': 'urban-meadow-community-garden', 'mta': 'mta', 'bmtdc': 'brooklyn-marine-terminal-development-corporation',
         'soccer': 'south-brooklyn-soccer', 'booksaremagic': 'books-are-magic', 'dep': 'nyc-dep', 'wytchonymous': 'wytchonymous-arts',
         'pacemakers': 'pacemakers-dance-team', 'hookarts': 'hook-arts-media', 'portside': 'portside-newyork', 'streetlab': 'street-lab',
         'recordshop': 'record-shop', 'sbdsa': 'south-brooklyn-dsa', 'rooftopfilms': 'rooftop-films', 'duboisbunche': 'dubois-bunche-center',
         'rhba': 'red-hook-business-alliance', 'nfbid': 'north-flatbush-bid', 'sss': 'smith-street-stage', 'nitehawk': 'nitehawk-prospect-park',
         'bkpride': 'brooklyn-pride', 'dsny': 'dsny-brooklyn-6', 'niyn': 'nycha-cb6', 'rhlp': 'red-hook-lobster-pound',
         'artsgowanus': 'artsgowanus', 'altside': 'nyc-dot'}
# calendar profiles that were only on the site
SITE_ONLY = ['south-brooklyn-dsa', 'dubois-bunche-center']
GOV_ONLY = ['red-hook-community-justice-center']

def plain(s):
    s = re.sub(r'<[^>]+>', '', s or '')
    return html.unescape(s).replace(' ', ' ').strip()

def absu(u): return u if re.match(r'^(https?:|mailto:|tel:)', u) else 'https://bkcb6.app' + u

def app_profile(r, key, group, logo):
    kv = [[plain(k), plain(v)] for k, v in r.get('kv', [])]
    return {'slug': r['slug'], 'type': key or r['slug'], 'name': plain(r['name']), 'seat': plain(r.get('seat', '')).replace(' · ', ' · '),
            'desc': plain(r.get('desc', '')), 'lat': float(r['lat']) if r.get('lat') else None, 'lng': float(r['lng']) if r.get('lng') else None,
            'addr': r.get('addr', ''), 'zip': r.get('zip', ''), 'addr_note': plain(r.get('addr_note', '')), 'phone': r.get('phone', ''),
            'email': r.get('email', ''), 'web': r.get('web', ''), 'weburl': r.get('weburl', ''), 'since': r.get('since', ''),
            'intro': [plain(p) for p in r.get('intro', [])], 'does': [plain(p) for p in r.get('does', [])], 'kv': kv,
            'links': [[plain(t), absu(u)] for t, u, *_ in r.get('links', []) if not u.startswith('/citywide-search')],
            'logo': logo or '', 'cal': key, 'n': 0, 'going': [], 'kind': 'org', 'official': '',
            'group': group[0], 'topic': group[1], 'sort': 0}

def cal_record(key, slug, bg, logo, d):
    name = d['name']; flat = d['addr'] + ', Brooklyn'
    first = plain(d['intro'][0])
    r = {'slug': slug, 'unsigned': True, 'name': name, 'seat': d['seat'], 'title': name,
         'desc': (f'{plain(name)}, {flat}. {first}')[:240], 'lat': d['lat'], 'lng': d['lng'], 'addr': d['addr'], 'zip': d['zip'],
         'addr_note': d.get('addr_note', ''), 'cityline': '', 'phone': d.get('phone', ''), 'tel': re.sub(r'\D', '', d.get('phone', '')),
         'email': d.get('email', ''), 'web': d['web'], 'weburl': d['weburl'], 'since': d.get('since', ''),
         'intro': d['intro'], 'does_title': 'What ' + name + ' does', 'does': d['does'],
         'kv': d['kv'] + [['Community board', CB[d['cd']]], ['Tax lot (BBL)', d['bbl']]] + ([['Source', d['sources']]] if d.get('sources') else []),
         'brand': brand(bg), 'evorg': key, 'evtitle': 'Coming up with ' + name, 'evhref': f'/o/{key}.html', 'evname': 'The ' + name + ' calendar',
         'does_btns': [['What is coming up', f'/o/{key}.html', False],
                       ['Zoning and land use for the lot', '/citywide-search.html?address=' + flat.replace(' ', '%20').replace(',', '%2C'), False]],
         'links': d['links'] + [['Their calendar', f'/o/{key}.html', False], ['Search an address', '/citywide-search.html', False]]}
    if not logo: r['nologo'] = True
    return r

# the template is the hand-made events page for Dzieci, as first written (this script rewrites o/dzieci.html itself)
O_TEMPLATE = open(os.path.join(ROOT, 'scripts/o_events_template.html'), encoding='utf-8').read()

def o_page(key, slug, name, logo):
    src = O_TEMPLATE
    s = src.replace('Dzieci Theatre', name).replace('/o/dzieci.html', f'/o/{key}.html').replace('org=dzieci', f'org={key}') \
           .replace('window.ORG="dzieci"', f'window.ORG="{key}"')
    s = s.replace('<img src="/dzieci.png" alt="%s logo" style="border-radius:9px">' % name,
                  ('<img src="/site-icons/%s.png" alt="%s logo" style="border-radius:9px">' % (slug, name)) if logo else '')
    s = s.replace('<a class="chip hot" href="/calendar.html?org=%s">' % key,
                  '<a class="chip" href="/%s/">%s profile</a><a class="chip hot" href="/calendar.html?org=%s">' % (slug, name, key), 1)
    assert 'dzieci' not in s.lower() or key == 'dzieci', key
    return s

def main():
    app = J(APP); P = {p['slug']: p for p in app['profiles']}
    cal = J(CAL); C = {r['slug']: r for r in cal}
    gov = {r['slug']: r for r in J('data/gov-profiles.json')}
    tmap = J(TMAP)
    old_ty = {k: v['ty'] for k, v in tmap.items()}
    layers = J('assets/blocks/cb6-layers.json')
    removed = {}
    for key, slug, bg, logo, d in NEW:
        r = cal_record(key, slug, bg, logo, d)
        if slug in C: cal[[x['slug'] for x in cal].index(slug)] = r
        else: cal.append(r)
        C[slug] = r
        lg = ''
        if logo:
            shutil.copy(os.path.join(ROOT, 'app/data/civic/cal/icons', logo), os.path.join(ROOT, 'site-icons', slug + '.png'))
            lg = 'cal-' + logo
            shutil.copy(os.path.join(ROOT, 'app/data/civic/cal/icons', logo), os.path.join(ROOT, 'app/data/civic/orgs/logos', lg))
        a = app_profile(r, key, d['group'], lg)
        a['kv'] = [k for k in a['kv'] if k[0] != 'Tax lot (BBL)']
        a['links'].insert(0, ['Full profile', f'https://bkcb6.app/{slug}/'])
        if slug in P: a['kv'] += [k for k in P[slug]['kv'] if k[0].startswith('License') or k[0] in ('Legal name', 'Licensed since')]
        for old in d['replaces']:
            o = P.pop(old, None)
            if not o: continue
            removed[old] = slug
            a['kv'] += [k for k in o['kv'] if k[0].startswith('License') or k[0] in ('Legal name', 'Licensed since')]
        P[slug] = a
        open(os.path.join(ROOT, 'o', key + '.html'), 'w', encoding='utf-8').write(o_page(key, slug, plain(d['name']), logo))
        tmap[key] = {'ty': slug, 'org': plain(d['name'])}
    for s in SITE_ONLY:
        r = C[s]; key = r.get('evorg') or s
        if s not in P: P[s] = app_profile(r, key, ('Community groups', 'Civic and neighborhood groups'), '')
        if not any(l[0] == 'Full profile' for l in P[s]['links']): P[s]['links'].insert(0, ['Full profile', f'https://bkcb6.app/{s}/'])
    for s in GOV_ONLY:
        r = gov[s]
        if s not in P: P[s] = app_profile(r, s, ('Government agencies', 'Public safety and justice'), '')
    for key, slug in ALIAS.items():
        if slug not in P:
            print('no app profile for', key, slug); continue
        tmap[key] = {'ty': slug, 'org': P[slug]['name']}
        if not P[slug].get('cal'): P[slug]['cal'] = key
    # the map pins and the replaced pages point at the profiles
    pages = {'biz-08f6e2ec26': 'biz/winner-367-7th-ave.html', 'biz-8c2a8e5647': 'biz/kentler-international-drawing-space.html',
             'biz-e1997ed024': 'biz/textile-arts-center.html', 'map-culture-place-bam-rose-cinemas': 'culture-place/bam-rose-cinemas.html'}
    n_pins = 0
    for old, slug in removed.items():
        p = pages[old]
        for lay in layers['layers']:
            for it in lay.get('items', []):
                if it.get('u') in ('/' + p, 'https://bkcb6.app/' + p): it['u'] = f'/{slug}/'; n_pins += 1
        fp = os.path.join(ROOT, p)
        if os.path.exists(fp):
            open(fp, 'w', encoding='utf-8').write(f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>Moved</title>'
                f'<link rel="canonical" href="https://bkcb6.app/{slug}/"><meta http-equiv="refresh" content="0; url=/{slug}/"></head>'
                f'<body><a href="/{slug}/">This profile is now at bkcb6.app/{slug}/</a></body></html>')
    # events the app files already carry keep their organization from run to run, so move them too
    move = {old_ty[k]: v['ty'] for k, v in tmap.items() if k in old_ty and old_ty[k] != v['ty'] and old_ty[k] not in P}
    for f in ('app/data/civic/cal/calendar-bk.json', 'app/data/civic/cal/calendar-city.json'):
        c = J(f)
        for e in c['events']:
            if e.get('ty') in move:
                e['org'] = P[move[e['ty']]]['name'] if 'org' in e else e.get('org'); e['ty'] = move[e['ty']]
            for a in e.get('also', []):
                if a.get('ty') in move: a['org'] = P[move[a['ty']]]['name']; a['ty'] = move[a['ty']]
        for o, n in move.items():
            if o in c['types']:
                t = c['types'].pop(o); c['types'].setdefault(n, {**t, 'name': P[n]['name']})
        W(f, c, separators=(',', ':'))
    app['profiles'] = list(P.values())
    W(APP, app, indent=1)
    W(CAL, cal, indent=1)
    json.dump(dict(sorted(tmap.items())), open(os.path.join(ROOT, TMAP), 'w'), ensure_ascii=False, indent=1); open(os.path.join(ROOT, TMAP), 'a').write('\n')
    W('assets/blocks/cb6-layers.json', layers, separators=(',', ':'))
    print(len(NEW), 'new profiles;', len(removed), 'listings folded in;', n_pins, 'pins relinked;', len(ALIAS), 'calendar keys pointed at profiles')

if __name__ == '__main__':
    main()
