#!/usr/bin/env python3
"""Build LPC permit data for bkcb6.app.

Source: LPC Permit Application Information, NYC Open Data, downloaded 2026-08-26.

Community district is assigned by point in polygon against the DCP Community
Districts boundary file, not the LPC community_board column. That column holds
dirty values (bare numbers such as 33 and 39) and disagrees with geometry on
about 2 percent of geocoded rows. Where LPC supplied no coordinates the LPC
column is used as a fallback and the permit is flagged unmapped.

Emits per district:
  assets/lpc/<cd>.json           index: sites, facets, counts   (small, loads first)
  assets/lpc/<cd>-permits.json   full permit rows, dictionary encoded
and one assets/lpc/summary.json covering every district.
"""
import json, os
import numpy as np
import pandas as pd
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

UP = '/mnt/user-data/uploads'
OUT = '/home/claude/out/assets/lpc'
os.makedirs(OUT, exist_ok=True)

BORO = {'1': 'MN', '2': 'BX', '3': 'BK', '4': 'QN', '5': 'SI'}
BORONAME = {'MN': 'Manhattan', 'BX': 'Bronx', 'BK': 'Brooklyn',
            'QN': 'Queens', 'SI': 'Staten Island'}
DOWNLOADED = '2026-08-26'
SOURCE = 'NYC Landmarks Preservation Commission, LPC Permit Application Information'

g = json.load(open(f'{UP}/Community_Districts_20260826.geojson'))
geoms = [shape(f['geometry']) for f in g['features']]
codes = [f['properties']['boro_cd'] for f in g['features']]
tree = STRtree(geoms)

df = pd.read_csv(f'{UP}/LPC_Permit_Application_Information_20260826.csv',
                 dtype=str, low_memory=False)

lat = pd.to_numeric(df['latitude'], errors='coerce')
lon = pd.to_numeric(df['longitude'], errors='coerce')
ok = lat.notna() & lon.notna() & lat.between(40.4, 41.0) & lon.between(-74.3, -73.6)

pts = [Point(x, y) for x, y in zip(lon[ok], lat[ok])]
qi, qg = tree.query(pts, predicate='within')
assign = np.full(int(ok.sum()), -1, dtype=int)
for pi, gi in zip(qi, qg):
    if assign[pi] == -1:
        assign[pi] = gi
cdvals = [None if a == -1 else f'{BORO[codes[a][0]]}-{codes[a][1:]}' for a in assign]

df['cd'] = pd.Series(pd.NA, index=df.index, dtype=object)
df.loc[ok, 'cd'] = cdvals
df['mapped'] = df['cd'].notna()
df['lat'] = lat.round(6)
df['lon'] = lon.round(6)

fb = df['cd'].isna() & df['community_board'].fillna('').str.fullmatch(r'(MN|BX|BK|QN|SI)-\d{2}')
df.loc[fb, 'cd'] = df.loc[fb, 'community_board']


def ymd(s):
    d = pd.to_datetime(s, format='%m/%d/%Y', errors='coerce')
    return d.dt.strftime('%Y%m%d').fillna('')


df['rcv'] = ymd(df['received_date'])
df['iss'] = ymd(df['issue_date'])
df['exp'] = ymd(df['expiration_date'])

for c in ['docket', 'address', 'Block', 'Lot', 'LMNameType', 'WorkTypes',
          'regulation_type', 'applicant_name', 'applicant_co',
          'owner_name', 'owner_co', 'Regulation Number']:
    df[c] = df[c].fillna('').str.strip().replace({'0': ''})


def primary_lm(v):
    """LMNameType packs 'Name: Type' pairs, comma separated for multi designation sites."""
    if not v:
        return '', ''
    first = v.split(',')[0].strip()
    if ':' in first:
        name, kind = first.rsplit(':', 1)
        return name.strip(), kind.strip()
    return first, ''


# ------------------------------------------------- landmark building database
# Adds the designation record for the building itself: date, architect, style,
# original use. Joined on borough, block and lot. Blank and the literal '0' and
# 'Not determined' placeholders LPC uses are dropped rather than displayed.
BCOLS = ['Borough', 'Block', 'Lot', 'DESIG_ADDRESS', 'DATE_COMBO', 'ARCHITECT',
         'STYLE1', 'ORIG_USE', 'BUILD_TYPE', 'PROP_NAME']
bld = pd.read_csv(f'{UP}/Individual_Landmark_and_Historic_District_Building_Database_20260826.csv',
                  dtype=str, usecols=BCOLS)
PLACEHOLDER = {'', '0', 'not determined', 'none', 'n/a'}


def bclean(v):
    v = ('' if pd.isna(v) else str(v)).strip()
    return '' if v.lower() in PLACEHOLDER else v


for c in BCOLS:
    bld[c] = bld[c].map(bclean)
bld = bld[(bld['Block'] != '') & (bld['Lot'] != '')]
bld['key'] = (bld['Borough'] + '-' + bld['Block'].str.lstrip('0')
              + '-' + bld['Lot'].str.lstrip('0'))
FIELDS = ['DESIG_ADDRESS', 'DATE_COMBO', 'ARCHITECT', 'STYLE1', 'ORIG_USE',
          'BUILD_TYPE', 'PROP_NAME']
bld['_fill'] = (bld[FIELDS] != '').sum(axis=1)
bld = bld.sort_values('_fill', ascending=False)
counts = bld.groupby('key').size()
best = bld.drop_duplicates('key').set_index('key')
BLD = {k: [best.at[k, f] for f in FIELDS] + [int(counts[k])] for k in best.index}
print(f'building database: {len(BLD)} lots')

# LPC's own borough column, used to catch geocoding errors that drop a permit
# in the wrong borough entirely. 709 rows citywide, 136 of them landing in CB6.
BORONAME_UP = {'MANHATTAN': 'MN', 'BRONX': 'BX', 'BROOKLYN': 'BK',
               'QUEENS': 'QN', 'STATEN ISLAND': 'SI'}
df['lpc_boro'] = df['Borough'].fillna('').str.upper().map(BORONAME_UP)

df[['lm_name', 'lm_kind']] = pd.DataFrame(
    [primary_lm(v) for v in df['LMNameType']], index=df.index,
    columns=['lm_name', 'lm_kind'])

TABLES = ['wt', 'ap', 'ac', 'ow', 'oc', 'rn']


def boro_of(cdcode):
    return cdcode[:2]


# Joint Interest Areas are parks, waterways and major government installations
# that sit outside every community district. Names are DCP's own, from
# nyc.gov/site/planning/community/jias-sources.page. Calling these "Community
# District 64" would invent a district that does not exist.
JIA = {
    'BX-26': 'Van Cortlandt Park', 'BX-27': 'Bronx Park',
    'BX-28': 'Pelham Bay Park',
    'BK-55': 'Prospect Park', 'BK-56': 'Brooklyn Gateway National Recreation Area',
    'MN-64': 'Central Park',
    'QN-80': 'LaGuardia Airport', 'QN-81': 'Flushing Meadows-Corona Park',
    'QN-82': 'Forest Park', 'QN-83': 'JFK International Airport',
    'QN-84': 'Queens Gateway National Recreation Area',
    'SI-95': 'Staten Island Gateway National Recreation Area',
}
# The 59 community districts mandated by the city charter.
CD_COUNT = {'MN': 12, 'BX': 12, 'BK': 18, 'QN': 14, 'SI': 3}


def label_for(cdcode):
    if cdcode in JIA:
        return JIA[cdcode] + ' (' + BORONAME[boro_of(cdcode)] + ' joint interest area)'
    return f'{BORONAME[boro_of(cdcode)]} Community District {int(cdcode[3:])}'


def kind_for(cdcode):
    return 'jia' if cdcode in JIA else 'cd'


summary = {}
sub = df[df['cd'].notna()]

for cdcode, grp in sub.groupby('cd', sort=True):
    grp = grp.sort_values(['rcv', 'docket'], ascending=[False, False])
    regs = sorted({x for x in grp['regulation_type'] if x})
    lms = sorted({x for x in grp['lm_name'] if x})
    kinds = sorted({x for x in grp['lm_kind'] if x})
    ri = {v: i for i, v in enumerate(regs)}
    li = {v: i for i, v in enumerate(lms)}
    ki = {v: i for i, v in enumerate(kinds)}
    tb = {t: {} for t in TABLES}

    def ix(t, v):
        d = tb[t]
        if v not in d:
            d[v] = len(d)
        return d[v]

    sites, srows, unmapped = {}, [], []
    for r in grp.itertuples(index=False):
        docket = r.docket
        row = [docket[4:] if docket.startswith('LPC-') else docket,
               '', r.rcv, r.iss, r.exp, ri.get(r.regulation_type, -1),
               ix('wt', r.WorkTypes), ix('ap', r.applicant_name),
               ix('ac', r.applicant_co), ix('ow', r.owner_name),
               ix('oc', r.owner_co), ix('rn', getattr(r, '_28'))]
        if r.mapped:
            # Blank block or lot cannot be a grouping key, it would collapse
            # every unlotted permit in the district onto one pin.
            key = ((r.Borough, r.Block, r.Lot) if r.Block and r.Lot
                   else ('~', r.lat, r.lon))
            s = sites.get(key)
            if s is None:
                s = sites[key] = {'a': r.address, 'y': r.lat, 'x': r.lon,
                                  'b': r.Block, 'l': r.Lot,
                                  'k': li.get(r.lm_name, -1),
                                  't': ki.get(r.lm_kind, -1), 'p': [],
                                  'bad': 0}
            if r.lpc_boro and r.lpc_boro != boro_of(cdcode):
                s['bad'] = 1
            row[1] = '' if r.address == s['a'] else r.address
            s['p'].append(row)
        else:
            row[1] = r.address
            unmapped.append(row)

    joined = 0
    for s in sites.values():
        yrs = [p[2][:4] for p in s['p'] if p[2]]
        regset = sorted({p[5] for p in s['p'] if p[5] >= 0})
        b = BLD.get(f"{boro_of(cdcode)}-{s['b'].lstrip('0')}-{s['l'].lstrip('0')}") \
            if s['b'] and s['l'] else None
        if b:
            joined += 1
        srows.append([s['y'], s['x'], s['a'], s['b'], s['l'], s['k'], s['t'],
                      len(s['p']),
                      min(yrs) if yrs else '', max(yrs) if yrs else '', regset,
                      b or 0, s['bad']])
    order = sorted(range(len(srows)), key=lambda i: (-srows[i][7], srows[i][2]))
    srows = [srows[i] for i in order]
    plists = [list(sites.values())[i]['p'] for i in order]

    yrs_all = grp['rcv'].str[:4]
    yrs_all = yrs_all[yrs_all != '']
    boro = cdcode[:2]
    label = label_for(cdcode)

    idx = {
        'cd': cdcode, 'label': label, 'boro': boro, 'kind': kind_for(cdcode),
        'source': SOURCE, 'downloaded': DOWNLOADED,
        'method': ('Community district assigned by point in polygon against the '
                   'Department of City Planning Community Districts file. Permits '
                   'the Commission did not geocode are listed as unmapped.'),
        'totals': {'permits': int(len(grp)), 'sites': len(srows),
                   'unmapped': len(unmapped)},
        'reg': regs, 'lm': lms, 'kind': kinds,
        'byYear': {k: int(v) for k, v in sorted(yrs_all.value_counts().items())},
        'byReg': {k: int(v) for k, v in
                  grp['regulation_type'].replace('', pd.NA).dropna()
                  .value_counts().items()},
        'byLm': {k: int(v) for k, v in
                 grp['lm_name'].replace('', pd.NA).dropna()
                 .value_counts().items()},
        'bldFields': ['address', 'date', 'architect', 'style', 'origUse',
                      'buildType', 'propName', 'buildingsOnLot'],
        'bldJoined': joined,
        'boroMismatch': sum(1 for s in srows if s[12]),
        'sites': srows,
    }
    perm = {'cd': cdcode,
            'tables': {t: [k for k, _ in sorted(tb[t].items(), key=lambda kv: kv[1])]
                       for t in TABLES},
            'permits': plists, 'unmapped': unmapped}

    pi_ = f'{OUT}/{cdcode.lower()}.json'
    pp_ = f'{OUT}/{cdcode.lower()}-permits.json'
    json.dump(idx, open(pi_, 'w'), separators=(',', ':'))
    json.dump(perm, open(pp_, 'w'), separators=(',', ':'))

    summary[cdcode] = {
        'label': label, 'boro': boro, 'kind': kind_for(cdcode),
        'permits': idx['totals']['permits'], 'sites': idx['totals']['sites'],
        'firstYear': min(idx['byYear']) if idx['byYear'] else '',
        'lastYear': max(idx['byYear']) if idx['byYear'] else '',
        'ca': int(idx['byReg'].get('Certificate of Appropriateness', 0)),
        'topLm': [k for k, _ in list(idx['byLm'].items())[:6]],
        'kb': [round(os.path.getsize(pi_) / 1024), round(os.path.getsize(pp_) / 1024)],
    }

# Queens Community District 10 has no landmarks permits on file. Without a shard
# it disappears from the picker entirely, so write an empty one and let the page
# say so plainly.
for _b, _n in CD_COUNT.items():
    for _i in range(1, _n + 1):
        _cd = f'{_b}-{_i:02d}'
        if _cd in summary:
            continue
        _idx = {'cd': _cd, 'label': label_for(_cd), 'boro': _b, 'kind': 'cd',
                'source': SOURCE, 'downloaded': DOWNLOADED,
                'method': 'Community district assigned by point in polygon against the '
                          'Department of City Planning Community Districts file.',
                'totals': {'permits': 0, 'sites': 0, 'unmapped': 0},
                'reg': [], 'lm': [], 'kind_list': [], 'byYear': {}, 'byReg': {},
                'byLm': {}, 'bldFields': [], 'bldJoined': 0, 'boroMismatch': 0,
                'sites': []}
        json.dump(_idx, open(f'{OUT}/{_cd.lower()}.json', 'w'), separators=(',', ':'))
        json.dump({'cd': _cd, 'tables': {t: [] for t in TABLES},
                   'permits': [], 'unmapped': []},
                  open(f'{OUT}/{_cd.lower()}-permits.json', 'w'), separators=(',', ':'))
        summary[_cd] = {'label': label_for(_cd), 'boro': _b, 'kind': 'cd',
                        'permits': 0, 'sites': 0, 'firstYear': '', 'lastYear': '',
                        'ca': 0, 'topLm': [], 'kb': [1, 1]}
        print(f'  wrote empty shard for {_cd}')

cw = df['rcv'].str[:4]
cw = cw[cw != '']
json.dump({
    'source': SOURCE, 'downloaded': DOWNLOADED,
    'citywide': {
        'permits': int(len(df)), 'geocoded': int(df['mapped'].sum()),
        'districts': len(summary),
        'byYear': {k: int(v) for k, v in sorted(cw.value_counts().items())},
        'byReg': {k: int(v) for k, v in
                  df['regulation_type'].replace('', pd.NA).dropna()
                  .value_counts().items()},
    },
    'districts': summary,
}, open(f'{OUT}/summary.json', 'w'), separators=(',', ':'))

tot = sum(sum(v['kb']) for v in summary.values())
print(f'{len(summary)} districts, {tot/1024:.1f} MB uncompressed')
for k, v in sorted(summary.items(), key=lambda kv: -sum(kv[1]['kb']))[:6]:
    print(f"  {k} {v['permits']:6d} permits {v['sites']:5d} sites  index {v['kb'][0]}KB  permits {v['kb'][1]}KB")
print('  BK-06', summary['BK-06'])
