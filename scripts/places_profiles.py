"""Schools, libraries, child care, parks, hospitals and health care, and gyms and athletic facilities in the apps' Directory
tab, under "Schools, parks and facilities". Run after biz_profiles.py; rerunnable (its own place-* entries are replaced).
Sources:
  data/facdb-cb6.json            NYC Facilities Database (data.cityofnewyork.us ji82-xba5), community district 306
  app/data/civic/parks.geojson   NYC Parks properties and athletic facilities that touch CB6
  data/parks-pools-cb6.json      NYC Parks Pools (y5rm-wagw), community board 306
  data/parks-reccenters-cb6.json NYC Parks Structures (n8q6-i44s), recreation centers in CB6
  app/data/civic/libraries.json, schools-childcare.json   websites
Gyms are the CB6 business directory's fitness and sports centres (biz_profiles.py), moved under this heading.
Writes app/data/civic/orgs/orgs-profiles.json."""
import json, re, collections
from shapely.geometry import shape, Point

C = 'app/data/civic'
P = f'{C}/orgs/orgs-profiles.json'
GROUP = 'Schools, parks and facilities'
SCHOOLS, LIBS, CARE, PARKS, FIELDS, HEALTH, GYMS = ('Schools', 'Libraries', 'Child care and pre-K', 'Parks, playgrounds and gardens',
                                                    'Courts, fields, pools and recreation centers', 'Hospitals and health care', 'Gyms, yoga, Pilates and fitness')
TOPICS = [SCHOOLS, LIBS, CARE, PARKS, FIELDS, HEALTH, GYMS]

d = json.load(open(P))
cb6 = shape(json.load(open('data/cb6_boundary.geojson'))['features'][0]['geometry'])
inside = cb6.buffer(0.0006)
hoods = {n: shape({'type': 'Polygon', 'coordinates': v}) for n, v in json.load(open(f'{C}/hoods-cb6.json')).items()}
def hood(lat, lng):
    p = Point(lng, lat)
    for n, g in hoods.items():
        if g.buffer(0.0003).contains(p): return n
    return ''

KEEP_UP = {'PS', 'P.S.', 'MS', 'M.S.', 'NYU', 'NY', 'NYC', 'LLC', 'INC', 'CDC', 'BBRU', 'II', 'III', 'K077', 'K266', 'ECC', 'HS', 'AEH',
           'ADHCP', 'FMS', 'GED', 'OMH', 'BPOS', 'PSP', 'USA'}
FIX = {'Mcdowell': 'McDowell', 'St Saviour': 'St. Saviour', 'Pave Academy': 'PAVE Academy', 'Ny-Presbyterian': 'NewYork-Presbyterian',
       'New York-Presbyterian': 'NewYork-Presbyterian', 'Newyork-Presbyterian': 'NewYork-Presbyterian', 'Psychiatri': 'Psychiatry',
       'Psychiatryy': 'Psychiatry', 'Fms-Nephro': 'FMS-Nephro', 'Fresnius': 'Fresenius', 'Revcore': 'RevCore', 'Metrokids': 'MetroKids',
       'Kindercare': 'KinderCare', 'Ged-P2g-Red Hook Com Just Ctr-Ahsep': 'High School Equivalency Program, Red Hook Community Justice Center',
       'Degraw': 'DeGraw', 'Leport': 'LePort', 'Nataie': 'Natalie', 'Bklyn': 'Brooklyn'}
SMALL = {'of', 'and', 'the', 'at', 'for', 'a', 'de', 'on', 'in'}
def title(s):
    s = re.sub(r'\s+', ' ', s or '').strip()
    out = []
    for i, w in enumerate(s.split(' ')):
        core = w.strip('(),').upper()
        if core in KEEP_UP or re.match(r'^[A-Z]\d+$', core) or re.match(r'^\d+[A-Z]$', core):
            out.append(w.upper()); continue
        lw = w.lower()
        if i and lw in SMALL: out.append(lw); continue
        out.append('-'.join(p[:1].upper() + p[1:] for p in lw.split('-')))
    s = ' '.join(out)
    s = re.sub(r"([(/]\s*)([a-z])", lambda m: m.group(1) + m.group(2).upper(), s)
    s = re.sub(r"(\d+ )the\b", r"\1The", s)
    for a, b in FIX.items(): s = s.replace(a, b)
    return re.sub(r"'S\b", "'s", s).replace("’S", "’s")
def ordinal(n):
    n = int(n)
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
def addr(a):
    if not a: return ''
    a = title(a)
    for w, n in (('First', '1st'), ('Second', '2nd'), ('Third', '3rd'), ('Fourth', '4th'), ('Fifth', '5th'), ('Sixth', '6th'), ('Seventh', '7th'), ('Eighth', '8th'), ('Ninth', '9th')):
        a = re.sub(rf'\b{w} (Street|Avenue|Place)\b', rf'{n} \1', a)
    a = re.sub(r'\b(\d+) (Street|Avenue|Place)\b', lambda m: f'{ordinal(m.group(1))} {m.group(2)}', a)
    return re.sub(r'^(\d+[A-Z]?) (\d+(?:st|nd|rd|th) )', r'\1 \2', a)
norm = lambda s: re.sub(r'[^a-z0-9]', '', (s or '').lower().replace('p.s.', 'ps').replace('m.s.', 'ms'))

def base(slug, name, topic, seat, lat, lng, address, kv, web='', links=(), intro=(), desc=''):
    nb = hood(lat, lng)
    kv = list(kv)
    if nb: kv.append(['Neighborhood', nb])
    kv.append(['Community board', 'Brooklyn Community Board 6'])
    return {'slug': slug, 'type': slug, 'name': name, 'seat': seat + (f' · {nb}' if nb and nb not in seat else ''),
            'desc': desc or f"{name}. {address + ', ' if address else ''}{nb or 'Brooklyn'}.", 'lat': round(lat, 6), 'lng': round(lng, 6),
            'addr': address, 'zip': '', 'addr_note': '', 'phone': '', 'email': '',
            'web': web.replace('https://', '').replace('http://', '').strip('/'), 'weburl': web, 'since': '', 'intro': list(intro),
            'does': [], 'kv': kv, 'links': list(links), 'logo': '', 'cal': None, 'n': 0, 'going': [], 'kind': 'org',
            'official': '', 'group': GROUP, 'topic': topic, 'sort': 0}

made = []
used = set()
def slugify(s):
    s = 'place-' + re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:60]
    k, i = s, 2
    while k in used: k = f'{s}-{i}'; i += 1
    used.add(k); return k

fac = [f for f in json.load(open('data/facdb-cb6.json')) if f.get('latitude') and inside.contains(Point(float(f['longitude']), float(f['latitude'])))]
sites = json.load(open(f'{C}/schools-childcare.json'))
def site_for(name, address=''):
    n = norm(name)
    for s in sites:
        sn = norm(s['name'])
        if sn and (sn == n or (len(sn) > 6 and (sn in n or n in sn))): return s.get('website') or ''
    return ''

# ---------- schools ----------
SCHOOL_TYPE = {'ELEMENTARY SCHOOL - PUBLIC': 'Public elementary school', 'HIGH SCHOOL - PUBLIC': 'Public high school',
               'JUNIOR HIGH-INTERMEDIATE-MIDDLE SCHOOL - PUBLIC': 'Public middle school', 'SECONDARY SCHOOL - PUBLIC': 'Public secondary school (grades 6 to 12)',
               'K-8 SCHOOL - PUBLIC, SPECIAL EDUCATION': 'Public school, special education (K to 8)', 'K-12 ALL GRADES SCHOOL - PUBLIC, SPECIAL EDUCATION': 'Public school, special education (K to 12)',
               'ELEMENTARY SCHOOL - CHARTER': 'Charter elementary school', 'HIGH SCHOOL - CHARTER': 'Charter high school', 'K-8 SCHOOL - CHARTER': 'Charter school (K to 8)',
               'SECONDARY SCHOOL - CHARTER': 'Charter secondary school', 'ELEMENTARY SCHOOL - NON-PUBLIC': 'Private school', 'HIGH SCHOOL - NON-PUBLIC': 'Private high school',
               'MIDDLE SCHOOL - NON-PUBLIC': 'Private middle school', 'SATELLITE SITE FOR STUDENTS WITH DISABILITIES': 'School for students with disabilities',
               'GED-ALTERNATIVE HIGH SCHOOL EQUIVALENCY PREP PROGRAMS': 'High school equivalency program'}
upk = {norm(f['facname']) for f in fac if f['factype'] == 'DOE UNIVERSAL PRE-K'}
upk_addr = {norm(f.get('address')) for f in fac if f['factype'] == 'DOE UNIVERSAL PRE-K'}
clinics = collections.defaultdict(list)
for f in fac:
    if f['factype'] == 'SCHOOL BASED HOSPITAL EXTENSION CLINIC': clinics[norm(f.get('address'))].append(title(f['opname']))
# school districts and parent councils: data/doe-schools-cb6.json (NYC Public Schools school locations, wg9x-4ke6, community
# district 306). The district that runs a public school is its code's first two digits (75 is District 75, citywide special
# education; 84 is a charter school). Community Education Councils cover the public elementary and middle grades of their
# district; the Citywide Council on High Schools covers public high school grades; the Citywide Council for District 75 covers
# District 75 schools. Charter and private schools have no council; they show the district they are in.
DOE = {norm(x['location_name']): x for x in json.load(open('data/doe-schools-cb6.json'))}
def grades(t):
    g = [x for x in t.split(',') if x not in ('SE',)]
    lab = lambda x: {'PK': 'Pre-K', '0K': 'K'}[x] if x in ('PK', '0K') else str(int(x))
    return f"{lab(g[0])} to {lab(g[-1])}" if len(g) > 1 else lab(g[0])
def councils(f, doe):
    geo = f.get('schooldist') or (doe or {}).get('geographical_district_code')
    if not doe or (doe.get('managed_by_name') == 'Charter'):
        return [['School district', f'District {geo}']] if geo else []
    run = doe['system_code'][:2]
    g = [x for x in (doe.get('grades_final_text') or '').split(',') if x not in ('SE', 'NULL', '')]
    lower = any(x in ('PK', '0K') or (x.isdigit() and int(x) <= 8) for x in g)
    upper = any(x.isdigit() and int(x) >= 9 for x in g)
    if run == '75':
        return [['School district', f'District 75, citywide special education (in District {geo})'], ['Parent council', 'Citywide Council for District 75']]
    out = [['School district', f'District {int(run)}']]
    if lower or not upper: out.append(['Community Education Council', f'CEC District {int(run)}'])
    if upper: out.append(['High school parent council', 'Citywide Council on High Schools'])
    return out
for f in sorted((f for f in fac if f['facgroup'] == 'SCHOOLS (K-12)'), key=lambda f: f['facname']):
    name = title(f['facname']).replace('P.S. 0', 'P.S. ')
    ty = SCHOOL_TYPE.get(f['factype'], title(f['factype']))
    kv = [['Type', ty]]
    if f.get('capacity') not in (None, '0') and f.get('captype') == 'seats': kv.append(['Seats', f['capacity']])
    if f.get('opname') and 'Department of Education' not in f['opname'] and norm(f['opname']) != norm(f['facname']): kv.append(['Run by', title(f['opname'])])
    elif 'Department of Education' in (f.get('opname') or ''): kv.append(['Run by', 'NYC Public Schools'])
    doe = DOE.get(norm(f['facname']))
    if doe and doe.get('grades_final_text') not in (None, 'NULL'): kv.append(['Grades', grades(doe['grades_final_text'])])
    for k, v in councils(f, doe): kv.append([k, v])
    if norm(f['facname']) in upk or (ty.startswith('Public elementary') and norm(f.get('address')) in upk_addr): kv.append(['Pre-K', 'Pre-K for All at this school'])
    if clinics.get(norm(f.get('address'))): kv.append(['School-based health clinic', ', '.join(sorted(set(clinics[norm(f.get('address'))])))])
    kv.append(['Source', 'NYC Facilities Database'])
    a = addr(f.get('address'))
    made.append(base(slugify(name), name, SCHOOLS, ty, float(f['latitude']), float(f['longitude']), a, kv, web=site_for(f['facname'])))

# ---------- libraries ----------
libsites = {norm(l['name']): l for l in json.load(open(f'{C}/libraries.json'))}
LIBS_LIST = [
    # the Central Library at Grand Army Plaza (community district 355, just outside CB6), from the Facilities Database citywide
    {'name': 'Central Library', 'address': '10 Grand Army Plaza', 'lat': 40.6722468777, 'lng': -73.9681108345,
     'web': 'https://www.bklynlibrary.org/locations/central', 'type': 'Brooklyn Public Library, the main library, at Grand Army Plaza'},
]
for l in json.load(open(f'{C}/libraries.json')):
    LIBS_LIST.append({'name': l['name'], 'address': l['address'], 'lat': l['lat'], 'lng': l['lon'], 'web': l.get('website', ''), 'type': 'Brooklyn Public Library branch'})
for f in fac:
    if f['facgroup'] == 'LIBRARIES' and 'POP-UP' in f['facname']:
        LIBS_LIST.append({'name': title(f['facname']).replace('Pop-Up', 'pop-up'), 'address': addr(f.get('address')), 'lat': float(f['latitude']),
                          'lng': float(f['longitude']), 'web': '', 'type': 'Brooklyn Public Library pop-up library'})
for l in LIBS_LIST:
    kv = [['Type', l['type']], ['Run by', 'Brooklyn Public Library'], ['Source', 'Brooklyn Public Library and the NYC Facilities Database']]
    made.append(base(slugify(l['name']), l['name'], LIBS, l['type'], l['lat'], l['lng'], l['address'], kv, web=l['web']))
    made[-1]['cal'] = made[-1]['slug']   # the library's own calendar (scripts/build_calendar_events.py, type lib-<branch>)
    if l['name'] in ('Carroll Gardens Library', 'Carroll Gardens pop-up Library'):
        made[-1]['intro'] = ['FALL 2026 UPDATE: Major renovation milestones are complete and BPL is well into the final, six-month second phase of the project, which includes elevator upgrades, renovated bathrooms, a water fountain, new and restored shelving, and interior improvements. Carroll Gardens Library will reopen in Fall 2026.']

# ---------- child care and pre-K ----------
CARE_TYPE = {'DAY CARE': 'Licensed child care', 'EARLY EDUCATION PROGRAM': '3-K or Pre-K for All program', 'DOE UNIVERSAL PRE-K': 'Pre-K for All',
             'PRE-K CENTER': 'Pre-K center', 'PRE-SCHOOL FOR STUDENTS WITH DISABILITIES': 'Preschool for students with disabilities',
             'SCHOOL BASED CHILD CARE - PRESCHOOL': 'Preschool at a school'}
groups = collections.OrderedDict()
SUFFIX = re.compile(r',?\s*\b(INC|LLC|CORP|CORPORATION|PARENTS?)\b\.?,?', re.I)
first = lambda n: norm(SUFFIX.sub('', n).split(' ')[0])
for f in sorted((f for f in fac if f['facgroup'] == 'DAY CARE AND PRE-KINDERGARTEN'), key=lambda f: f['facname']):
    if f['factype'] == 'DOE UNIVERSAL PRE-K': continue  # on the school's own profile
    groups.setdefault((norm(addr(f.get('address'))), norm(SUFFIX.sub('', f['facname']))[:5]), []).append(f)
for (_, _), fs in groups.items():
    names = sorted({re.sub(r'\s+', ' ', SUFFIX.sub('', f['facname'])).strip(' ,.') for f in fs}, key=len)
    name = title(names[0])
    f0 = fs[0]
    progs = sorted({CARE_TYPE.get(f['factype'], title(f['factype'])) for f in fs})
    kv = [['Programs', ', '.join(progs)]]
    ops = sorted({title(SUFFIX.sub('', f['opname'])).strip(' ,.') for f in fs if f.get('opname') and f['opname'] != 'Unknown' and norm(SUFFIX.sub('', f['opname'])) != norm(SUFFIX.sub('', f['facname']))})
    if ops: kv.append(['Run by', ', '.join(ops)])
    kv.append(['Source', 'NYC Facilities Database (Health Department child care permits and NYC Public Schools)'])
    made.append(base(slugify(name), name, CARE, progs[0], float(f0['latitude']), float(f0['longitude']), addr(f0.get('address')), kv,
                     web=site_for(name)))

# ---------- parks, and their courts and fields ----------
feats = json.load(open(f'{C}/parks.geojson'))['features']
parks = collections.OrderedDict()
for x in feats:
    p = x['properties']
    if p['layer'] != 'park' or p['name'] in ('Park', None): continue
    parks.setdefault(p['name'], []).append(x)
SPORT = {'HDB': 'Handball courts', 'BKB': 'Basketball courts', 'SFB': 'Softball fields', 'BSB': 'Baseball fields', 'SCR': 'Soccer fields',
         'CRK': 'Cricket pitches', 'VLB': 'Volleyball courts', 'TNS': 'Tennis courts', 'BOC': 'Bocce courts', 'TRK': 'Running tracks',
         'HKY': 'Hockey rinks', 'MPPA': 'Multipurpose play areas', 'FTB': 'Football fields'}
ath = collections.defaultdict(collections.Counter)
for x in feats:
    p = x['properties']
    # Brooklyn Bridge Park's courts and fields are all kept (the city's records mark them inactive; the park runs them itself)
    if p['layer'] == 'athletic_facility' and (p.get('status', 'Active') == 'Active' or p['name'] == 'Brooklyn Bridge Park'):
        ath[p['name']][SPORT.get(p['sport'], title(p.get('facility_type') or 'Other'))] += 1
pools = collections.defaultdict(list)
for pl in json.load(open('data/parks-pools-cb6.json')): pools[pl['gispropnum']].append(pl)
PTYPE = {'Garden': 'Community garden', 'Playground': 'Playground', 'Jointly Operated Playground': 'Playground shared with a school',
         'Triangle/Plaza': 'Plaza or triangle', 'Neighborhood Park': 'Neighborhood park', 'Community Park': 'Community park',
         'Flagship Park': 'Flagship park', 'Recreational Field/Courts': 'Fields and courts', 'Strip': 'Park strip', 'Undeveloped': 'Undeveloped park land'}
park_slug = {}
PARK_CAL = {}   # calendar type park-<property> -> this park's profile
for name, xs in parks.items():
    xs.sort(key=lambda x: -float(x['properties'].get('acres') or 0))
    p = xs[0]['properties']
    g = shape(xs[0]['geometry'])
    pt = g.representative_point() if not g.intersects(cb6) else g.intersection(cb6).representative_point()
    if name in ('Prospect Park',): pt = Point(-73.9701, 40.6602)
    acres = sum(float(x['properties'].get('acres') or 0) for x in xs)
    ty = PTYPE.get(p.get('type_category'), title(p.get('type_category') or 'Park'))
    kv = [['Type', ty], ['Size', f'{acres:,.2f} acres' if acres < 10 else f'{acres:,.0f} acres']]
    if p.get('location'): kv.append(['Where', p['location']])
    if ath.get(name): kv.append(['Courts and fields', ', '.join(f'{v} {k.lower() if v > 1 else k.lower().rstrip("s")}' for k, v in sorted(ath[name].items()))])
    for pl in pools.get(p['gispropnum'], []): kv.append(['Pool', f"{pl['name']} ({pl['location'].lower()}, {pl['pooltype'].lower()})"])
    kv += [['Run by', 'Brooklyn Bridge Park Corporation' if name == 'Brooklyn Bridge Park' else 'Prospect Park Alliance and NYC Parks' if name == 'Prospect Park' else 'NYC Parks'],
           ['Source', 'NYC Parks properties']]
    web = {'Prospect Park': 'https://www.prospectpark.org', 'Brooklyn Bridge Park': 'https://www.brooklynbridgepark.org'}.get(name, f"https://www.nycgovparks.org/parks/{p['gispropnum']}")
    slug = slugify(name); park_slug[name] = slug
    made.append(base(slug, name, PARKS, ty, pt.y, pt.x, addr(p.get('address')) if p.get('address') and not re.search(r'[a-z]', p['address']) else (p.get('address') or ''), kv, web=web))
    # The park's own calendar: NYC Parks events there (scripts/build_calendar_events.py, type park-<property>), or its operator's.
    made[-1]['cal'] = {'Prospect Park': 'prospect-park-alliance', 'Brooklyn Bridge Park': 'brooklyn-bridge-park'}.get(name, slug)
    for x in xs:
        g_ = x['properties'].get('gispropnum')
        if g_ and name not in ('Prospect Park', 'Brooklyn Bridge Park'): PARK_CAL[f'park-{g_.lower()}'] = {'ty': slug, 'org': name}

# athletic facilities: each park's courts and fields, the pools, the recreation center
for name, cnt in ath.items():
    if name not in parks: continue
    x = parks[name][0]; p = x['properties']
    pts = [shape(f['geometry']).centroid for f in feats if f['properties']['layer'] == 'athletic_facility' and f['properties']['name'] == name]
    if name != 'Brooklyn Bridge Park': pts = [q for q in pts if cb6.buffer(0.0006).contains(q)] or pts
    lat = sum(q.y for q in pts) / len(pts); lng = sum(q.x for q in pts) / len(pts)
    kv = [[k, str(v)] for k, v in sorted(cnt.items())] + [['Park', name], ['Run by', 'NYC Parks' if name not in ('Brooklyn Bridge Park',) else 'Brooklyn Bridge Park Corporation'],
                                                         ['Source', 'NYC Parks athletic facilities']]
    total = sum(cnt.values())
    made.append(base(slugify(name + ' courts and fields'), f'{name}: courts and fields', FIELDS, f'{total} courts and fields in the park' if total > 1 else '1 court or field in the park',
                     lat, lng, '', kv, web=f"https://www.nycgovparks.org/parks/{p['gispropnum']}/facilities" if name != 'Brooklyn Bridge Park' else 'https://www.brooklynbridgepark.org'))
by_prop = {x[0]['properties']['gispropnum']: n for n, x in parks.items()}
for prop, pls in pools.items():
    main = sorted(pls, key=lambda pl: 'Wading' in pl['name'])[0]
    c = shape(main['polygon']).centroid
    kv = [['Pools', ', '.join(f"{pl['name']} ({pl['pooltype'].lower()})" for pl in pls)], ['Indoor or outdoor', main['location']],
          ['Park', by_prop.get(prop, '')], ['Run by', 'NYC Parks'], ['Source', 'NYC Parks pools']]
    made.append(base(slugify(main['name']), main['name'], FIELDS, f"{main['location']} public pool", c.y, c.x, '', kv,
                     web=f'https://www.nycgovparks.org/parks/{prop}/facilities/outdoor-pools'))
for r in json.load(open('data/parks-reccenters-cb6.json')):
    kv = [['Type', 'NYC Parks recreation center'], ['Park', by_prop.get(r['gispropnum'], '')], ['Built', r.get('built') or ''],
          ['Run by', 'NYC Parks'], ['Source', 'NYC Parks structures']]
    made.append(base(slugify(r['name']), r['name'], FIELDS, 'NYC Parks recreation center', r['lat'], r['lng'], r['address'], [k for k in kv if k[1]],
                     web=f"https://www.nycgovparks.org/parks/{r['gispropnum']}/facilities/recreation-centers"))

# ---------- hospitals and health care ----------
HTYPE = {'HOSPITAL': 'Hospital', 'HOSPITAL EXTENSION CLINIC': 'Hospital clinic', 'DIAGNOSTIC AND TREATMENT CENTER': 'Diagnostic and treatment center',
         'DIAGNOSTIC AND TREATMENT CENTER EXTENSION CLINIC': 'Clinic (diagnostic and treatment center)', 'NURSING HOME': 'Nursing home',
         'OUTPATIENT MENTAL HEALTH': 'Outpatient mental health clinic', 'INPATIENT MENTAL HEALTH': 'Inpatient mental health',
         'METHADONE MAINTENANCE': 'Methadone treatment program', 'ADULT DAY HEALTH CARE PROGRAM - OFFSITE': 'Adult day health care',
         'CERTIFIED HOME HEALTH AGENCY': 'Home health agency'}
HORDER = list(HTYPE)
# Places that have a hand-written profile of their own; the Facilities Database copy is not made again.
HANDWRITTEN = {'Cobble Hill Health Center'}
for f in sorted((f for f in fac if f['facgroup'] == 'HEALTH CARE' and f['factype'] in HTYPE), key=lambda f: (HORDER.index(f['factype']), f['facname'])):
    name = title(re.sub(r'\s+', ' ', SUFFIX.sub('', f['facname'])).strip(' ,.'))
    if name in HANDWRITTEN: continue   # has its own hand-written profile (with its calendar) in orgs-profiles.json
    ty = HTYPE[f['factype']]
    kv = [['Type', ty]]
    if f.get('opname') and norm(f['opname']) != norm(f['facname']): kv.append(['Run by', title(f['opname']).replace('The New York and Presbyterian Hospital', 'NewYork-Presbyterian')])
    if f.get('capacity') not in (None, '0') and f.get('captype'): kv.append(['Capacity', f"{f['capacity']} {f['captype']}"])
    kv.append(['Source', 'NYC Facilities Database (New York State Department of Health and Office of Mental Health)'])
    made.append(base(slugify(name), name, HEALTH, ty, float(f['latitude']), float(f['longitude']), addr(f.get('address')), kv))

# ---------- gyms: the business directory's fitness and sports centres ----------
gyms = 0
for p in d['profiles']:
    if p['slug'].startswith('biz-') and any(k == 'Kind' and v in ('Fitness centre', 'Sports centre', 'Dojo') for k, v in p['kv']):
        p['group'], p['topic'] = GROUP, GYMS
        p['seat'] = p['seat'].replace('Fitness centre', 'Gym').replace('Sports centre', 'Sports center').replace('Dojo', 'Martial arts')
        for kv in p['kv']:
            if kv[0] == 'Kind' and kv[1] == 'Dojo': kv[1] = 'Martial arts'
        gyms += 1

# the business directory's logo and website for the same place
import os, shutil
rowsb = json.load(open(f'{C}/business/business-cb6.json'))['rows']
byname = {}
for r in rowsb:
    byname.setdefault(norm(r[0]), r)
logos = 0
for m in made:
    r = byname.get(norm(m['name']))
    if not r: continue
    if r[8] and not m['logo'] and os.path.exists(f'{C}/business/logos/{r[8]}.png'):
        lf = f'biz-{r[8]}.png'; dst = f'{C}/orgs/logos/{lf}'
        if not os.path.exists(dst): shutil.copyfile(f'{C}/business/logos/{r[8]}.png', dst)
        m['logo'] = lf; logos += 1
    if r[7] and not m['weburl']:
        m['weburl'] = r[7].strip(); m['web'] = m['weburl'].replace('https://', '').replace('http://', '').strip('/')
print(logos, 'logos from the business directory')
# Brooklyn Bridge Park, all of it: the park's own size and extent (85 acres, Atlantic Avenue to Jay Street), not the 21 acre
# NYC Parks parcel; no community board line
for m in made:
    if m['name'] == 'Brooklyn Bridge Park':
        m['logo'] = 'bbp.png'
        m['addr'] = 'East River waterfront, Atlantic Avenue to Jay Street'
        m['seat'] = 'Waterfront park, 85 acres'
        m['kv'] = [k for k in m['kv'] if k[0] not in ('Size', 'Where', 'Community board')]
        m['kv'][1:1] = [['Size', '85 acres'], ['Where', 'East River waterfront, Atlantic Avenue to Jay Street']]
for m in made:
    if m['name'].startswith('Brooklyn Bridge Park'): m['kv'] = [k for k in m['kv'] if k[0] != 'Community board']
for p in d['profiles']:
    if p['slug'] == 'brooklyn-bridge-park':
        p['kv'] = [k for k in p['kv'] if k[0] != 'Community board']
for m in made:
    for k, v in m['kv']:
        if k == 'Community Education Council' and v == 'CEC District 15': m['kvdest'] = {v: 'org:cec-district-15'}
# the schools' own logos (assets/school-logos, from Mike's Drive folder of cleaned 1080 px logos; logos.json maps profile name to file)
SCHOOL_LOGOS = {norm(k): v for k, v in json.load(open('assets/school-logos/logos.json')).items()}
n_school_logos = 0
for m in made:
    f = SCHOOL_LOGOS.get(norm(m['name']))
    if f:
        shutil.copyfile(f'assets/school-logos/{f}', f'{C}/orgs/logos/{f}'); m['logo'] = f; n_school_logos += 1
print(n_school_logos, 'school logos')
# every other place's logo: the ones Mike compiled (site-icons, the business directory, the organizations' logos), by name;
# NYC Parks' logo for any park, court, field, pool or recreation center without its own; Brooklyn Public Library's for the libraries
from PIL import Image
BIZ_LOGO = {}
for r in rowsb:
    if r[8] and os.path.exists(f'{C}/business/logos/{r[8]}.png'): BIZ_LOGO.setdefault(norm(r[0]), f'{C}/business/logos/{r[8]}.png')
SI = lambda n: f'site-icons/{n}.png'
OL = lambda n: f'{C}/orgs/logos/{n}'
PLACE_LOGOS = {
    # child care and pre-K
    '14th Street Preschool': SI('14th-street-preschool'), 'Alonzo A. Daughtry Memorial Day Care': SI('alonzo-daughtry-day-care'),
    'BBRU 8th Street': SI('bumblebeesrus-8th-street'), 'Bumblebees R Us': SI('bumblebeesrus-8th-street'),
    'BBRU Lorraine': SI('bumblebeesrus-red-hook'), 'Bumblebees-R-Us': SI('bumblebeesrus-red-hook'),
    'Chai Tots': SI('chai-tots-park-slope'), "Charlotte's Place": SI('charlottes-place'), 'Cobble Hill Playschool': SI('cobble-hill-playschool'),
    "Eladia's Kids": SI('eladias-kids'), "Eladia's Kids 266 Flatbush Avenue": SI('eladias-kids'), 'Kane Street Kids': SI('kane-street-kids'),
    'Lady Bug Preschool': SI('ladybug-smith-street'), 'Ladybug Playgroup': SI('ladybug-union-street'),
    'Learning Wheel Childcare': SI('learning-wheel-childcare'), 'Maven Valley Prep': SI('maven-valley-prep'),
    'Brooklyn Free Space': SI('brooklyn-free-space'), 'Brooklyn Preschool of Science': SI('brooklyn-preschool-of-science-park-slope'),
    'Wonderforest Nature Preschool': SI('wonderforest-nature-preschool'), 'Smith Street Workshop': SI('smith-street-workshop-carroll-street'),
    'The Little Brooklyn Pre-K Center at 305-307 Third Avenue': f'{C}/icons/nyc-public-schools-logo.png',
    'Beansprouts': BIZ_LOGO.get('beansprouts'), 'Beansprouts of Brooklyn': BIZ_LOGO.get('beansprouts'),
    'Congregation Beth Elohim ECC': BIZ_LOGO.get('congregationbethelohim'), 'Open House Nursery School': BIZ_LOGO.get('openhouse'),
    'NY Kids Club': BIZ_LOGO.get('nypreschoolkidsclub'), 'Al-Madinah': BIZ_LOGO.get('almadinahschool'),
    # libraries
    'Central Library': OL('bpl.png'), 'Park Slope Library': OL('bpl.png'), 'Carroll Gardens Library': OL('bpl.png'), 'Red Hook Library': OL('bpl.png'),
    'Red Hook pop-up Library': OL('bpl.png'), 'Carroll Gardens pop-up Library': OL('bpl.png'),
    # parks
    'Prospect Park': OL('prospect-park.png'), 'Brooklyn Bridge Park': OL('bbp.png'), 'Brooklyn Bridge Park: courts and fields': OL('bbp.png'),
    # hospitals and health care
    'Center for Community Health': BIZ_LOGO.get('newyorkpresbyterianbrooklynmethodisthospital'),
    'NewYork-Presbyterian Brooklyn Methodist Hospital Infusion Services': BIZ_LOGO.get('newyorkpresbyterianbrooklynmethodisthospital'),
    "NewYork-Presbyterian Brooklyn Methodist Hospital, Rehab Center and Women & Children's Clinics": BIZ_LOGO.get('newyorkpresbyterianbrooklynmethodisthospital'),
    'NewYork-Presbyterian Brooklyn Methodist Hospital Psychiatry': BIZ_LOGO.get('newyorkpresbyterianbrooklynmethodisthospital'),
    'NYU Langone Hospital - Joseph S. and Diane H. Steinberg Ambulatory Care Center': BIZ_LOGO.get('nyulangonepremierimaging'),
    'NYU Langone Health Red Hook Family Health Center': BIZ_LOGO.get('nyulangonepremierimaging'),
    # gyms
    'Stretch Lab': BIZ_LOGO.get('stretchlab'),
}
PLACE_LOGOS = {norm(k): v for k, v in PLACE_LOGOS.items() if v}
NYC_PARKS = SI('nyc-parks-brooklyn')
def place_logo(src, slug):
    out = 'place-' + os.path.basename(src).rsplit('.', 1)[0] + '.png'
    dst = f'{C}/orgs/logos/{out}'
    if not os.path.exists(dst):
        im = Image.open(src).convert('RGBA'); im.thumbnail((400, 400)); im.save(dst, optimize=True)
    return out
n_place_logos = 0
for m in made:
    src = PLACE_LOGOS.get(norm(m['name']))
    if not src and m['topic'] in (PARKS, FIELDS): src = NYC_PARKS
    if src and (not m['logo'] or src != NYC_PARKS):
        m['logo'] = place_logo(src, m['slug']); n_place_logos += 1
# gyms' logos Mike sent (assets/place-logos, logos.json maps name to file)
SENT = {norm(k): f'assets/place-logos/{v}' for k, v in json.load(open('assets/place-logos/logos.json')).items()}
for p in d['profiles']:
    if p.get('topic') == GYMS and SENT.get(norm(p['name'])):
        p['logo'] = place_logo(SENT[norm(p['name'])], p['slug']); n_place_logos += 1
for p in d['profiles']:
    if p.get('topic') == GYMS and not p['logo'] and BIZ_LOGO.get(norm(p['name'])):
        p['logo'] = place_logo(BIZ_LOGO[norm(p['name'])], p['slug']); n_place_logos += 1
print(n_place_logos, 'other place logos')
# the business directory's own copies of park facilities (OSM) are the NYC Parks entries above
DUPES = {'carroll park athletic field', 'dimattina field', 'sol goldman recreation center and pool', 'douglass & degraw pool'}
d['profiles'] = [p for p in d['profiles'] if not (p['slug'].startswith('biz-') and p['name'].lower() in DUPES)]
for m in made:
    if m['name'] == 'Red Hook Recreation Center': m['kv'].insert(1, ['Also called', 'Sol Goldman Recreation Center and Pool'])
d['profiles'] = [p for p in d['profiles'] if not p['slug'].startswith('place-')] + made
gs = [g for g in d['groups'] if g['name'] != GROUP]
i = next(k for k, g in enumerate(gs) if g['name'] == 'Local businesses')
d['groups'] = gs[:i] + [{'name': GROUP, 'topics': TOPICS}] + gs[i:]
note = ' Schools, libraries, child care, parks, hospitals and health care, and gyms and athletic facilities are profiles too (slug place-*, scripts/places_profiles.py), under Schools, parks and facilities.'
if 'places_profiles.py' not in d['about']: d['about'] += note
json.dump(d, open(P, 'w'), ensure_ascii=False, indent=1)
# Each park's calendar type, for the app calendar (scripts/build_app_calendar.mjs reads scripts/app-calendar-types.json).
TM = 'scripts/app-calendar-types.json'
tm = {k: v for k, v in json.load(open(TM)).items() if not k.startswith('park-')}
tm.update(PARK_CAL)
json.dump(tm, open(TM, 'w'), ensure_ascii=False, indent=1)
json.dump(sorted(k[5:].upper() for k in PARK_CAL) + ['B073', 'B431'], open('data/cb6-park-ids.json', 'w'))
print('park calendars', len(PARK_CAL))
print(collections.Counter(m['topic'] for m in made), gyms, 'gyms moved')
