#!/usr/bin/env python3
"""How each community board's Council, Assembly, State Senate and Congressional districts changed, 2006 to today.

Inputs
  dist_dir: DCP BYTES of the BIG APPLE district shapefile zips, one release per year
            (nycc_*, nyss_*, nyad_*, nycg_*), from s-media.nyc.gov/agencies/dcp/assets/files/zip/data-tools/bytes/
  nys csvs: NYS Board of Elections results exports (results.elections.ny.gov "Search Results CSV"), 2006 to 2026
  council csv: City Council Members 1999 to Present (NYC Open Data export)

Usage: python3 tools/build_district_history.py <dist_dir> <council_members.csv> <Census TIGER 2020 tl_2020_36_tabblock20.zip>
Output: data/districthistory/
"""
import csv, glob, hashlib, json, os, re, subprocess, sys, zipfile, collections, tempfile
import pyogrio
from shapely import wkb
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Transformer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'districthistory')
MIN_SHARE = 0.005  # districts holding under half a percent of a board's residents are left out as slivers

OFFICES = [
    # key, label, file prefix, district field, NYS office name, elections (year, release year, served label)
    ('council', 'City Council', 'nycc', 'CounDist', None,
     [(2005, '06', '2006–2009'), (2009, '10', '2010–2013'), (2013, '14', '2014–2017'),
      (2017, '17', '2018–2021'), (2021, '21', '2022–2023'), (2023, '23', '2024–2025'),
      (2025, '25', '2026–2029')]),
    ('assembly', 'State Assembly', 'nyad', 'AssemDist', 'Member of Assembly',
     [(y, str(y)[2:], f'{y+1}–{y+2}') for y in range(2006, 2025, 2)]),
    ('senate', 'State Senate', 'nyss', 'StSenDist', 'State Senator',
     [(y, str(y)[2:], f'{y+1}–{y+2}') for y in range(2006, 2025, 2)]),
    ('congress', 'Congress', 'nycg', 'CongDist', 'Representative in Congress',
     [(y, str(y)[2:], f'{y+1}–{y+2}') for y in range(2006, 2025, 2)]),
]


def load_blocks(block_zip):
    """2020 census blocks in the five boroughs: internal point (EPSG:2263), residents, and community board."""
    import numpy as np
    from shapely import contains_xy
    meta, fids, geoms, fields = pyogrio.raw.read(f'/vsizip/{block_zip}/tl_2020_36_tabblock20.shp', read_geometry=False,
                                                 columns=['COUNTYFP20', 'INTPTLAT20', 'INTPTLON20', 'POP20'])
    cnty, lat, lon, pop = fields
    keep = np.isin(cnty, ['005', '047', '061', '081', '085']) & (pop.astype(int) > 0)
    lat = lat[keep].astype(float); lon = lon[keep].astype(float); pop = pop[keep].astype(int)
    tr = Transformer.from_crs('EPSG:4326', 'EPSG:2263', always_xy=True)
    xs, ys = tr.transform(lon, lat)
    d = json.load(open(os.path.join(ROOT, 'data', 'community-districts.geojson')))
    board = np.array([''] * len(xs), dtype=object)
    for f in d['features']:
        c = f['properties']['boro_cd']
        if int(c[1:]) > 18:
            continue
        g = transform(tr.transform, shape(f['geometry'])).buffer(0)
        board[contains_xy(g, xs, ys) & (board == '')] = c
    return np.asarray(xs), np.asarray(ys), pop, board


def read_release(zpath, field):
    tmp = tempfile.mkdtemp()
    zipfile.ZipFile(zpath).extractall(tmp)
    shp = [p for p in glob.glob(tmp + '/**/*', recursive=True) if p.lower().endswith('.shp')][0]
    meta, fids, geoms, fields = pyogrio.raw.read(shp)
    names = list(meta['fields'])
    ids = fields[names.index(field)]
    out = collections.defaultdict(list)
    for i, g in zip(ids, geoms):
        if g is not None:
            out[int(i)].append(wkb.loads(bytes(g)).buffer(0))
    from shapely.ops import unary_union
    tr = None
    crs = meta['crs'] or ''
    if '2263' not in crs and 'Lambert' not in crs and 'lambert' not in crs.lower():
        tr = Transformer.from_crs(crs, 'EPSG:2263', always_xy=True)
    res = {}
    for k, gs in out.items():
        g = unary_union(gs)
        if tr:
            g = transform(tr.transform, g)
        res[k] = g
    return res


def geo_signature(dists):
    return hashlib.md5(json.dumps(sorted((k, round(g.area / 1e5)) for k, g in dists.items())).encode()).hexdigest()[:10]


def write_topo(dists, name):
    tr = Transformer.from_crs('EPSG:2263', 'EPSG:4326', always_xy=True)
    feats = [{'type': 'Feature', 'properties': {'d': k}, 'geometry': mapping(transform(tr.transform, g.simplify(20)))}
             for k, g in sorted(dists.items())]
    tmp = os.path.join(OUT, 'geo', f'_{name}.geojson')
    json.dump({'type': 'FeatureCollection', 'features': feats}, open(tmp, 'w'))
    dst = os.path.join(OUT, 'geo', f'{name}.topo.json')
    subprocess.run(['mapshaper', '-i', tmp, '-simplify', '20%', 'keep-shapes', '-o', 'format=topojson',
                    'quantization=100000', dst], check=True, capture_output=True)
    os.remove(tmp)
    return f'geo/{name}.topo.json'


def nys_winners(dist_dir):
    rows = []
    for f in sorted(glob.glob(os.path.join(dist_dir, 'nys_*.csv'))):
        rows += list(csv.DictReader(open(f, encoding='utf-8')))
    win = collections.defaultdict(list)  # (office, district) -> [(date, type, name)]
    seen = set()
    for r in rows:
        if r['is_winner'] != 'true' or r['election_type'] == 'Primary' or r['election_type'] == 'Presidential Primary':
            continue
        if not re.fullmatch(r'\d+', r['district_name'] or ''):
            continue
        k = (r['office_name'], int(r['district_name']), r['election_date'][:10], re.sub(r'\s+', ' ', r['candidate_name']).strip())
        if k in seen:
            continue
        seen.add(k)
        win[(r['office_name'], int(r['district_name']))].append((r['election_date'][:10], r['election_type'], re.sub(r'\s+', ' ', r['candidate_name']).strip()))
    # one spelling per person: the most common form among names sharing a last name and first initial
    forms = collections.Counter()
    for v in win.values():
        for _, _, n in v:
            forms[n] += 1
    def key(n):
        p = n.replace('.', '').split()
        return (p[0][0].lower() if p else '', re.sub(r',.*$', '', p[-1].lower()) if p else '')
    best = {}
    for n, c in forms.most_common():
        best.setdefault(key(n), n)
    return {k: [(d, t, best[key(n)]) for d, t, n in v] for k, v in win.items()}


def council_members(path):
    by = collections.defaultdict(list)
    for r in csv.DictReader(open(path, encoding='utf-8')):
        if not r['District']:
            continue
        def iso(s):
            m, d, y = s.split('/')
            return f'{y}-{m}-{d}'
        by[int(r['District'])].append((iso(r['Term Start']), iso(r['Term End']), r['Council Member Name'].replace('  ', ' ').strip()))
    return by


def main(dist_dir, council_csv, block_zip):
    os.makedirs(os.path.join(OUT, 'geo'), exist_ok=True)
    global BX, BY, BPOP, BOARD
    BX, BY, BPOP, BOARD = load_blocks(block_zip)
    winners = nys_winners(dist_dir)
    cmem = council_members(council_csv)
    sigs = {}
    result = {'minShare': MIN_SHARE, 'weight': '2020 census residents', 'offices': [],
              'boardPop': {c: int(BPOP[BOARD == c].sum()) for c in sorted(set(BOARD) - {''})}}
    for key, label, prefix, field, nysname, elections in OFFICES:
        off = {'key': key, 'label': label, 'rows': []}
        for year, ry, served in elections:
            z = sorted(glob.glob(os.path.join(dist_dir, f'{prefix}_{ry}*.zip')))
            z = [p for p in z if os.path.basename(p).startswith(f'{prefix}_{ry}')]
            if not z:
                print('missing', prefix, ry)
                continue
            zp = z[-1]
            release = re.sub(r'^[a-z]+_|\.zip$', '', os.path.basename(zp))
            dists = read_release(zp, field)
            sig = geo_signature(dists)
            if sig not in sigs:
                sigs[sig] = write_topo(dists, f'{key}_{release}')
            # overlaps: share of each board's residents (2020 census blocks) living in each district
            import numpy as np
            from shapely import contains_xy
            dist_of = np.zeros(len(BX), dtype=int)
            for k, g in dists.items():
                minx, miny, maxx, maxy = g.bounds
                cand = (BX >= minx) & (BX <= maxx) & (BY >= miny) & (BY <= maxy) & (dist_of == 0)
                idx = np.where(cand)[0]
                hit = contains_xy(g, BX[idx], BY[idx])
                dist_of[idx[hit]] = k
            ov = {}
            for c in sorted(set(BOARD) - {''}):
                m = BOARD == c
                tot = BPOP[m].sum()
                sums = collections.Counter()
                for k, p in zip(dist_of[m], BPOP[m]):
                    sums[int(k)] += int(p)
                lst = [[k, float(round(v / tot, 4)), int(v)] for k, v in sums.items() if k and v / tot >= MIN_SHARE]
                unassigned = sums.get(0, 0)
                lst.sort(key=lambda x: -x[1])
                ov[c] = lst
                if unassigned / tot > 0.01:
                    print('  note', key, year, c, 'residents outside any district', unassigned)
            # members
            served_from = int(served[:4])
            served_to = int(served[-4:])
            mem = {}
            used = sorted({x[0] for l in ov.values() for x in l})
            for d in used:
                if key == 'council':
                    ms = []
                    for s, e, n in sorted(cmem.get(d, [])):
                        if int(s[:4]) <= served_to and int(e[:4]) >= served_from and e >= f'{served_from}-01-02':
                            if not any(m['name'] == n for m in ms):
                                ms.append({'name': n, 'from': s, 'to': e})
                            else:
                                for m in ms:
                                    if m['name'] == n:
                                        m['from'] = min(m['from'], s); m['to'] = max(m['to'], e)
                    mem[str(d)] = ms
                else:
                    ms = []
                    for dt, typ, n in sorted(winners.get((nysname, d), [])):
                        if typ == 'General' and dt[:4] == str(year) and dt[5:7] == '11':
                            ms.insert(0, {'name': n, 'elected': dt, 'type': 'general'})
                        elif f'{year}-11-30' < dt < f'{served_to}-11-01':
                            ms.append({'name': n, 'elected': dt, 'type': 'special'})
                    mem[str(d)] = ms
            off['rows'].append({'election': year, 'served': served, 'release': release, 'geo': sigs[sig], 'cbs': ov, 'members': mem})
            print(key, year, release, 'CB306', [x[:2] for x in ov.get('306', [])])
        result['offices'].append(off)
    json.dump(result, open(os.path.join(OUT, 'overlap.json'), 'w'), separators=(',', ':'), ensure_ascii=False)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
