"""New Yorkers for Parks 2021 Open Space Profiles, all 59 community districts, as published.
Parsed from https://www.ny4p.org/client-uploads/pdf/District-Profiles-2021/NY4P-Profiles_{CODE}.pdf (page 2) by ny4p_parse.py."""
import json
R = json.load(open('/root/bkcb6/scripts/parks_policy/ny4p-raw.json'))
M = [  # key, label, group, unit, better (hi/lo/None)
 ('land', 'Total district land', 'Parkland', 'acres', None),
 ('parkland', 'City, state and federal parkland', 'Parkland', 'acres', 'hi'),
 ('pctParkland', 'Percent parkland', 'Parkland', '%', 'hi'),
 ('cityParks', 'City parks in the district', 'Parkland', 'acres', 'hi'),
 ('pctCityParks', 'Percent city parks', 'Parkland', '%', 'hi'),
 ('per1k', 'City park acres per 1,000 residents', 'Access', 'acres', 'hi'),
 ('walk', 'Residents within a 5-minute walk of a park', 'Access', '%', 'hi'),
 ('per1kKids', 'City park acres per 1,000 children', 'Access', 'acres', 'hi'),
 ('per1kSeniors', 'City park acres per 1,000 seniors', 'Access', 'acres', 'hi'),
 ('gardens', 'Community gardens', 'Amenities', '', 'hi'),
 ('reccenters', 'Recreation centers', 'Amenities', '', 'hi'),
 ('playgrounds', 'Playgrounds', 'Amenities', '', 'hi'),
 ('pools', 'Swimming pools', 'Amenities', '', 'hi'),
 ('dogruns', 'Dog runs', 'Amenities', '', 'hi'),
 ('spray', 'Sprayshowers', 'Amenities', '', 'hi'),
 ('schools', 'Public schools', 'Amenities', '', None),
 ('condition', 'Parks rated acceptable for condition', 'Amenities', '%', 'hi'),
 ('clean', 'Parks rated acceptable for cleanliness', 'Amenities', '%', 'hi'),
 ('c311', 'Park-related 311 calls per 1,000 residents', 'Stewardship', '', None),
 ('volunteer', 'Park volunteer groups', 'Stewardship', '', 'hi'),
 ('pop', 'Residents', 'Demographics', '', None),
 ('under18', 'Residents under 18', 'Demographics', '%', None),
 ('over65', 'Residents over 65', 'Demographics', '%', None),
 ('income', 'Median household income', 'Demographics', '$', None),
 ('poverty', 'Residents in poverty', 'Demographics', '%', None),
 ('asian', 'Asian', 'Demographics', '%', None), ('black', 'Black', 'Demographics', '%', None), ('white', 'White', 'Demographics', '%', None),
 ('multi', 'Multiracial', 'Demographics', '%', None), ('other', 'Another race', 'Demographics', '%', None),
 ('aian', 'American Indian or Alaska Native', 'Demographics', '%', None), ('nhpi', 'Native Hawaiian or Pacific Islander', 'Demographics', '%', None),
 ('hispanic', 'Hispanic or Latino (any race)', 'Demographics', '%', None),
 ('asthma', 'Child asthma cases per 10,000 children', 'Health and environment', '', 'lo'),
 ('childObesity', 'Child obesity rate', 'Health and environment', '%', 'lo'),
 ('life', 'Life expectancy', 'Health and environment', 'years', 'hi'),
 ('adultObesity', 'Adult obesity rate', 'Health and environment', '%', 'lo'),
 ('diabetes', 'Adult diabetes rate', 'Health and environment', '%', 'lo'),
 ('hospitals', 'Hospitals and clinics', 'Health and environment', '', None),
 ('air', 'Air pollution (fine particles, micrograms per cubic meter)', 'Health and environment', '', 'lo'),
 ('canopy', 'Tree canopy cover', 'Health and environment', '%', 'hi'),
]
def num(t):
    t = t.replace(',', '').replace('$', ''); m = 1
    if t.endswith('K'): m = 1e3; t = t[:-1]
    if t.endswith('M'): m = 1e6; t = t[:-1]
    if t.endswith('%'): t = t[:-1]
    return round(float(t) * m, 3)
code = lambda k: k[:2] + k[2:].zfill(2)
D, S = {}, {}
for k, v in R.items():
    c = code(k)
    D[c] = {m[0]: num(v[m[0]][0]) for m in M}
    S[c] = {m[0]: v[m[0]][0] for m in M}
    D[c]['rk'] = dict(zip(['pctParkland', 'walk', 'canopy'], [int(x) for x in v['ranks']]))
nyc = {m[0]: num(R['BK6'][m[0]][1]) for m in M}; nycS = {m[0]: R['BK6'][m[0]][1] for m in M}
# rank among 59 for every measure with a better direction (ties share a rank)
for key, _, _, _, b in M:
    if not b: continue
    vals = sorted(D, key=lambda c: -D[c][key] if b == 'hi' else D[c][key])
    for c in D:
        D[c].setdefault('rk', {})
        if key in D[c]['rk']: continue
        v = D[c][key]; D[c]['rk'][key] = 1 + sum(1 for o in D if (D[o][key] > v if b == 'hi' else D[o][key] < v))
out = dict(year=2021, src='New Yorkers for Parks, 2021 Open Space Profiles', url='https://www.ny4p.org/data-and-research/research-library/open-space-profiles',
           pdf='https://www.ny4p.org/client-uploads/pdf/District-Profiles-2021/NY4P-Profiles_{CODE}.pdf',
           metrics=[dict(k=m[0], l=m[1], g=m[2], u=m[3], b=m[4]) for m in M], nyc=nyc, nycS=nycS, d=D, s=S)
json.dump(out, open('/root/bkcb6/parks-policy/ny4p.json', 'w'), separators=(',', ':'))
print(len(D), D['BK06']['rk'])
