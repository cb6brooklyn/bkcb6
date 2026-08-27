#!/usr/bin/env python3
"""Build the citywide layers for the Landmarks Permits page.

The page was built one community district at a time, which meant there was no
way to look at the city as a whole or at a borough, and no way to search beyond
whichever district happened to be loaded. These three files fix that:

  city-sites.json    every landmarked site in the city, 48,409 of them, with the
                     borough, district, landmark, permit count and permit type
                     mask needed to map and search at any scope
  city-permits.json  docket number, date, permit type and work type for all
                     346,394 permits, so a docket or a kind of work can be
                     searched citywide
  city-bounds.json   all 59 district outlines, the 6 joint interest areas and
                     all 159 historic districts, simplified for a city view

Applicant and owner stay in the per district files. Carrying them citywide would
roughly triple the payload for fields that only matter once you are looking at a
specific building.
"""
import json, os, glob

OUT = '/home/claude/out/assets/lpc'
BORONAME = {'MN': 'Manhattan', 'BX': 'Bronx', 'BK': 'Brooklyn',
            'QN': 'Queens', 'SI': 'Staten Island'}

summary = json.load(open(f'{OUT}/summary.json'))
cds = sorted(summary['districts'])

cd_list, lm_list, kind_list, reg_list = [], [], [], []
lm_i, kind_i, reg_i = {}, {}, {}
sites, permits, wt_list, wt_i = [], [], [], {}


def idx(v, lst, m):
    if v not in m:
        m[v] = len(lst)
        lst.append(v)
    return m[v]


for cd in cds:
    d = json.load(open(f'{OUT}/{cd.lower()}.json'))
    if not d['sites']:
        cd_list.append([cd, d['label'], d['boro'], d.get('kind', 'cd')])
        continue
    ci = len(cd_list)
    cd_list.append([cd, d['label'], d['boro'], d.get('kind', 'cd')])

    p = json.load(open(f'{OUT}/{cd.lower()}-permits.json'))
    local_wt = p['tables']['wt']

    for si, s in enumerate(d['sites']):
        lat, lon, addr, blk, lot, lmi, ki, n, fy, ly, regset, b = s[:12]
        bad = s[12] if len(s) > 12 else 0
        mask = 0
        for r in regset:
            mask |= 1 << idx(d['reg'][r], reg_list, reg_i)
        bld = b if b else 0
        sites.append([
            lat, lon,
            (bld[0] if bld and bld[0] else addr),      # prefer the designated address
            ci,
            idx(d['lm'][lmi], lm_list, lm_i) if lmi >= 0 else -1,
            idx(d['kind'][ki], kind_list, kind_i) if ki >= 0 else -1,
            n, fy, ly, mask, bad, blk, lot,
            (bld[1] if bld else ''),                    # date
            (bld[2] if bld else ''),                    # architect
            (bld[3] if bld else ''),                    # style
        ])
        rows = []
        for pr in (p['permits'][si] if si < len(p['permits']) else []):
            rows.append([pr[0], pr[2],
                         idx(d['reg'][pr[5]], reg_list, reg_i) if pr[5] >= 0 else -1,
                         idx(local_wt[pr[6]], wt_list, wt_i)])
        permits.append(rows)

city = {
    'source': summary['source'], 'downloaded': summary['downloaded'],
    'cds': cd_list, 'lm': lm_list, 'kind': kind_list, 'reg': reg_list,
    'sites': sites,
}
json.dump(city, open(f'{OUT}/city-sites.json', 'w'), separators=(',', ':'))

json.dump({'wt': wt_list, 'permits': permits},
          open(f'{OUT}/city-permits.json', 'w'), separators=(',', ':'))

# ------------------------------------------------------------------ bounds
# Built straight from the uploaded DCP Community Districts file: every one of
# the 59 district outlines, the joint interest areas, and borough outlines
# dissolved from the districts that make them up.
import json as _j
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

BORO_CODE = {'1': 'MN', '2': 'BX', '3': 'BK', '4': 'QN', '5': 'SI'}
g = _j.load(open('/mnt/user-data/uploads/Community_Districts_20260826.geojson'))


def rnd(gj, nd=5):
    def r(c):
        if isinstance(c, (list, tuple)):
            if c and isinstance(c[0], (int, float)):
                return [round(c[0], nd), round(c[1], nd)]
            return [r(x) for x in c]
        return c
    gj['coordinates'] = r(gj['coordinates'])
    return gj


outlines, by_boro = [], {}
for f in g['features']:
    code = f['properties']['boro_cd']
    cd = f'{BORO_CODE[code[0]]}-{code[1:]}'
    geom = shape(f['geometry'])
    if not geom.is_valid:
        geom = geom.buffer(0)
    by_boro.setdefault(cd[:2], []).append(geom)
    simp = geom.simplify(0.00008, preserve_topology=True)
    lp = simp.representative_point()
    outlines.append({'cd': cd, 'geometry': rnd(mapping(simp)),
                     'labelPoint': [round(lp.y, 5), round(lp.x, 5)]})

boros = []
for b, geoms in by_boro.items():
    u = unary_union(geoms).simplify(0.00015, preserve_topology=True)
    lp = u.representative_point()
    boros.append({'boro': b, 'name': BORONAME[b], 'geometry': rnd(mapping(u)),
                  'labelPoint': [round(lp.y, 5), round(lp.x, 5)]})

hds, seen = [], set()
for f in sorted(glob.glob(f'{OUT}/*-bounds.json')):
    if os.path.basename(f).startswith('city-'):
        continue
    bnd = json.load(open(f))
    for h in bnd['historicDistricts']:
        if h['lp_number'] in seen:
            continue
        seen.add(h['lp_number'])
        hds.append({'name': h['name'], 'lp_number': h['lp_number'],
                    'year': h['year'], 'cd': bnd['cd'],
                    'label': h['label'], 'geometry': h['geometry']})

json.dump({'outlines': outlines, 'boroughs': boros, 'historicDistricts': hds,
           'source': 'Community district and borough outlines from the Department of City '
                     'Planning Community Districts file. Historic district boundaries from '
                     'the Landmarks Preservation Commission Historic_Districts_LPC service.'},
          open(f'{OUT}/city-bounds.json', 'w'), separators=(',', ':'))

for f in ['city-sites.json', 'city-permits.json', 'city-bounds.json']:
    print(f'  {f:22s} {os.path.getsize(f"{OUT}/{f}")/1e6:6.2f} MB')
print(f'  sites {len(sites):,}  permits {sum(len(r) for r in permits):,}  '
      f'districts {len(cd_list)}  historic districts {len(hds)}')
print(f'  reg types {len(reg_list)}  landmarks {len(lm_list):,}  work types {len(wt_list):,}')
