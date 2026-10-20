"""Every poll site that served BKCB6 voters, 2018 to 2026: data/pollsites-history/cb6.json.
Sources: NYC Board of Elections poll site lists for Kings County (vote.nyc PDFs, Election Day and Early Voting, read
with pdftotext -layout and tools/pollsite_pdf.py), and for 2018 the BOE poll site datasets on NYC Open Data
(i3a3-qxkf election district poll sites, mifw-tguq poll site locations, October 2018). An election district is in
BKCB6 by the ED-to-community-district file for that election's ED map (data/edhistory/geo/ed2cd<release>.json).
Locations: the BOE coordinates already in data/pollsites (2026) where the street address matches, otherwise NYC
GeoSearch. Usage: python3 tools/build_pollsite_history.py <folder with the PDFs and the two 2018 JSON files>"""
import json, os, re, sys, subprocess, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from pollsite_pdf import parse
SRC = sys.argv[1]
V = 'https://vote.nyc/sites/default/files/pdf/'
LISTS = [  # election id, kind, file, published url
 ('2019-11-05-general', 'ed', 'GE2019_ElectionDay_PollSiteList_KG.pdf', V + 'publications/pollsitelist/2019/pdf/GE2019_ElectionDay_PollSiteList_KG.pdf'),
 ('2019-11-05-general', 'ev', 'GE2019_EarlyVoting_PollSiteList_KG.pdf', V + 'publications/pollsitelist/2019/pdf/GE2019_EarlyVoting_PollSiteList_KG.pdf'),
 ('2020-11-03-general', 'ed', 'GE2020_PollSiteList_KG.pdf', V + 'poll_site_list/GE2020/GE2020_PollSiteList_KG.pdf'),
 ('2021-11-02-general', 'ed', 'Poll_Site_List_General_ED_Kings_11-2021_r1_PRESS.pdf', V + 'poll_site_list/GE2021/Poll_Site_List_General_ED_Kings_11-2021_r1_PRESS.pdf'),
 ('2022-11-08-general', 'ed', 'Poll-Site-List-November-ED-Kings-2022-r1-PRESS.pdf', V + 'poll_site_list/GE2022/Poll-Site-List-November-ED-Kings-2022-r1-PRESS.pdf'),
 ('2024-06-25-primary', 'ev', 'Poll_Site_List_EV_June_2024_Primary_Kings_PRESS.pdf', V + 'poll_site_list/PE2024/Poll_Site_List_EV_June_2024_Primary_Kings_PRESS.pdf'),
 ('2024-11-05-general', 'ed', 'Poll_Site_List_Nov_General_2024_Election_Day_Kings.pdf', V + 'poll_site_list/GE2024/Poll_Site_List_Nov_General_2024_Election_Day_Kings.pdf'),
 ('2024-11-05-general', 'ev', 'Poll_Site_List_Nov_General_2024_Early_Voting_Kings.pdf', V + 'poll_site_list/GE2024/Poll_Site_List_Nov_General_2024_Early_Voting_Kings.pdf'),
 ('2025-06-24-primary', 'ed', 'Poll_Site_List_ED_June_2025_Primary_Kings.pdf', V + 'poll_site_list/PE2025/Poll_Site_List_ED_June_2025_Primary_Kings.pdf'),
 ('2025-06-24-primary', 'ev', 'Poll_Site_List_EV_June_2025_Primary_Kings.pdf', V + 'poll_site_list/PE2025/Poll_Site_List_EV_June_2025_Primary_Kings.pdf'),
 ('2025-11-04-general', 'ed', 'Poll_Site_List_Nov_Election_Day_Kings_prf.pdf', V + 'poll_site_list/GE2025/Poll_Site_List_Nov_Election_Day_Kings_prf.pdf'),
 ('2025-11-04-general', 'ev', 'Poll_Site_List_Nov_Early_Voting_Kings_prf.pdf', V + 'poll_site_list/GE2025/Poll_Site_List%20_Nov_Early_Voting_Kings_prf.pdf'),
 ('2026-06-23-primary', 'ed', 'Poll_Site_List_ED_June_2026_Primary_Kings_r1.pdf', V + 'poll_site_list/PE2026/Poll_Site_List_ED_June_2026_Primary_Kings_r1.pdf'),
 ('2026-06-23-primary', 'ev', 'Poll_Site_List_EV_June_2026_Primary_Kings_r1.pdf', V + 'poll_site_list/PE2026/Poll_Site_List_EV_June_2026_Primary_Kings_r1.pdf'),
 ('2026-11-03-general', 'ed', 'Poll_Site_List_Nov_General_2026_Election_Day_Kings_r1.pdf', V + 'poll_site_list/GE2026/Poll_Site_List_Nov_General_2026_Election_Day_Kings_r1.pdf'),
 ('2026-11-03-general', 'ev', 'Poll_Site_List_Nov_General_2026_Early_Voting_Kings.pdf', V + 'poll_site_list/GE2026/Poll_Site_List_Nov_General_2026_Early_Voting_Kings.pdf'),
]
IDX = {e['id']: e for e in json.load(open('data/ballots/index.json'))}
def release(eid):
    if eid == '2026-11-03-general':
        return '26a1'
    return json.load(open('data/ballots/e/%s.json' % eid))['geo'].replace('geo/ed', '').replace('.topo.json', '')
E2C = {}
def cb_of(eid):
    r = release(eid)
    if r not in E2C:
        E2C[r] = json.load(open('data/edhistory/geo/ed2cd%s.json' % r))
    return E2C[r]
def norm_addr(a):
    a = a.upper().replace('.', ' ')
    a = re.sub(r'\b(\d+)(ST|ND|RD|TH)\b', r'\1', a)
    rep = {'AVENUE': 'AVE', 'AVENU': 'AVE', 'STREET': 'ST', 'PLACE': 'PL', 'ROAD': 'RD', 'BOULEVARD': 'BLVD', 'PARKWAY': 'PKWY', 'HIGHWAY': 'HWY', 'HGWY': 'HWY', 'EAST': 'E', 'WEST': 'W', 'SOUTH': 'S', 'NORTH': 'N', 'PLAZA': 'PLZ', 'COURT': 'CT', 'DRIVE': 'DR', 'TERRACE': 'TER'}
    w = [rep.get(x, x) for x in re.split(r'\s+', a.strip()) if x]
    return ' '.join(w)
# coordinates the BOE gives for 2026 sites
KNOWN = {}
for f in os.listdir('data/pollsites'):
    if not f.startswith('ad-'): continue
    for ed, v in json.load(open('data/pollsites/' + f)).items():
        for k in ('s', 'e'):
            s = v.get(k)
            if s and s[5]:
                KNOWN[norm_addr(s[1].split(',')[0])] = (float(s[5]), float(s[6]), s[0])
CACHE_F = os.path.join(SRC, 'geocache.json')
CACHE = json.load(open(CACHE_F)) if os.path.exists(CACHE_F) else {}
def geocode(addr, zipc=''):
    n = norm_addr(addr)
    if n in KNOWN:
        return KNOWN[n][:2]
    if n in CACHE:
        return CACHE[n]
    q = urllib.parse.quote('%s, Brooklyn, NY %s' % (addr, zipc))
    try:
        d = json.load(urllib.request.urlopen('https://geosearch.planninglabs.nyc/v2/search?size=1&text=' + q, timeout=20))
        f = d['features'][0] if d['features'] else None
        r = [f['geometry']['coordinates'][1], f['geometry']['coordinates'][0]] if f and f['properties'].get('borough') == 'Brooklyn' else None
    except Exception:
        r = None
    CACHE[n] = r; time.sleep(0.15)
    return r
sites = {}  # normalized address -> site
def tc(x):
    return re.sub(r'(\d)(St|Nd|Rd|Th)\b', lambda m: m.group(1) + m.group(2).lower(), x.title())
def site(name, addr):
    n = norm_addr(addr)
    s = sites.get(n)
    if not s:
        s = sites[n] = {'name': name, 'addr': tc(addr), 'names': {}}
    s['names'][name] = s['names'].get(name, 0) + 1
    return n
elections = []
# 2018: NYC Open Data
eds18 = json.load(open(os.path.join(SRC, 'eds2018.json')))
locs = {x['site_number']: x for x in json.load(open(os.path.join(SRC, 'sites2018.json')))}
m = cb_of('2018-11-06-general'); per = {}
for x in eds18:
    k = '%d%03d' % (int(x['ad']), int(x['ed']))
    if m.get(k) != '306': continue
    L = locs.get(x['site_number'])
    if not L: continue
    a = ('%s %s' % (L.get('street_number', ''), L.get('street_name', ''))).strip()
    n = site(L['site_name'].strip(), a); sites[n].setdefault('zip', L.get('zip_code', ''))
    per.setdefault(n, []).append(k)
elections.append({'id': '2018-11-06-general', 'kind': 'ed', 'src': 'https://data.cityofnewyork.us/d/i3a3-qxkf', 'per': per})
for eid, kind, fn, url in LISTS:
    txt = os.path.join(SRC, fn[:-4] + '.txt')
    if not os.path.exists(txt):
        subprocess.run(['pdftotext', '-layout', os.path.join(SRC, fn), txt], check=True)
    p = parse(txt); m = cb_of(eid); per = {}
    for k, (name, addr) in p.items():
        if m.get(k) != '306': continue
        n = site(name, addr); per.setdefault(n, []).append(k)
    elections.append({'id': eid, 'kind': kind, 'src': url, 'per': per})
keys = sorted(sites)
for n in keys:
    s = sites[n]
    s['name'] = tc(max(s['names'], key=lambda x: s['names'][x])).replace('Ps ', 'PS ').replace('Jhs ', 'JHS ').replace('Is ', 'IS ').replace('Ms ', 'MS ').replace('Hs', 'HS').replace('Ymca', 'YMCA').replace('Bklyn', 'Brooklyn').replace(' Jhs', ' JHS')
    ll = KNOWN.get(n) or geocode(s['addr'], s.get('zip', ''))
    s['ll'] = [round(ll[0], 6), round(ll[1], 6)] if ll else None
json.dump(CACHE, open(CACHE_F, 'w'))
out = {'about': __doc__.split('Usage:')[0].strip(), 'board': '306',
       'sites': [{'n': sites[k]['name'], 'a': sites[k]['addr'], 'll': sites[k]['ll']} for k in keys],
       'elections': []}
for e in elections:
    ie = IDX.get(e['id'], {})
    out['elections'].append({'id': e['id'], 'date': e['id'][:10], 'label': ie.get('label', ''), 'kind': e['kind'], 'src': e['src'],
                             'sites': {str(keys.index(n)): sorted(v) for n, v in e['per'].items()}})
json.dump(out, open('data/pollsites-history/cb6.json', 'w'), separators=(',', ':'))
print(len(keys), 'sites;', [(e['id'], e['kind'], len(e['per']), sum(len(v) for v in e['per'].values())) for e in elections])
print('no location:', [sites[k]['addr'] for k in keys if not sites[k]['ll']])
