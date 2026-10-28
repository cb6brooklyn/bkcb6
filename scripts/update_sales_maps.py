#!/usr/bin/env python3
"""Build data/sales/: the for-sale versions of every file the rent map pages read, in exactly the
same formats, so the sale pages (/salescb6, /bksales, /sales-map-boroughs.html, /nycsalesmap) are the
rent pages drawing StreetEasy sales data.

Usage: python3 scripts/update_sales_maps.py <folder of StreetEasy sales zips or csvs>

The rent files are keyed by unit size. Here those slots carry home types:
    studio -> All homes      br1 -> Condos      br2 -> Co-ops      br3 -> Single-family
    all    -> All homes
Prices are StreetEasy's median asking price; listings are totalInventory, with the
all-homes count taken from totalInventory_All (not a sum of the types).
The work itself is scripts/update_rents.py, run with RENT_DATA_DIR=data/sales.
rental-index.json carries StreetEasy's sales price index (priceIndex_All).
built-vs-rent.json carries homes completed 2015 to 2024 (from data/built-vs-rent.json)
against the change in the all-homes median asking price, January 2015 to December 2024.
"""
import csv, io, json, os, shutil, subprocess, sys, tempfile, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
OUT = os.path.join(DATA, 'sales')
SLOTS = {'Studio': 'All', 'OneBd': 'Condo', 'TwoBd': 'Coop', 'ThreePlusBd': 'Sfr'}
INPUTS = ['rent-cd-crosswalk.json', 'inventory-by-bed.json', 'cc-rents.json', 'cc-borough.json', 'rent-subranges.json',
          'rent-ranges-rollup.json', 'cb6-rent-trends.json', 'cb6-nbhd-history.json', 'rent-trends-all.json',
          'rent-explorer.json', 'citywide-rents.geojson', 'neighborhood-rents.geojson', 'borough-rents.geojson',
          'bk-rents.geojson'] + sorted(f for f in os.listdir(DATA) if f.endswith('-rank-history.json'))
LABELS = [('Studio : ', 'All homes : '), ('1 Bedroom : ', 'Condos : '), ('2 Bedroom : ', 'Co-ops : '),
          ('3 Bedroom : ', 'Single-family : '), ('All : ', 'All homes : '), ('/mo', '')]


def die(m): sys.exit('update_sales_maps: ' + m)


def read_csv(src, base):
    z, c = os.path.join(src, base + '.zip'), os.path.join(src, base + '.csv')
    if os.path.exists(z):
        zf = zipfile.ZipFile(z); n = [x for x in zf.namelist() if x.endswith('.csv')][0]
        return zf.read(n).decode('utf-8-sig')
    if os.path.exists(c): return open(c, encoding='utf-8-sig').read()
    die('missing ' + base)


def main(src):
    os.makedirs(OUT, exist_ok=True)
    for f in INPUTS:
        if not os.path.exists(os.path.join(OUT, f)): shutil.copy(os.path.join(DATA, f), os.path.join(OUT, f))
    stage = tempfile.mkdtemp(prefix='sales_')
    for slot, t in SLOTS.items():
        open(os.path.join(stage, 'medianAskingRent_%s.csv' % slot), 'w').write(read_csv(src, 'medianAskingPrice_' + t))
        open(os.path.join(stage, 'rentalInventory_%s.csv' % slot), 'w').write(read_csv(src, 'totalInventory_' + t))
    open(os.path.join(stage, 'medianAskingRent_All.csv'), 'w').write(read_csv(src, 'medianAskingPrice_All'))
    open(os.path.join(stage, 'rentalInventory_All.csv'), 'w').write(read_csv(src, 'totalInventory_All'))
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'update_rents.py'), stage],
                       env=dict(os.environ, RENT_DATA_DIR=OUT))
    if r.returncode: die('update_rents.py failed')

    # labels baked into the GeoJSON text properties
    for f in os.listdir(OUT):
        if not f.endswith('.geojson'): continue
        p = os.path.join(OUT, f); s = open(p).read()
        for a, b in LABELS: s = s.replace(a, b)
        open(p, 'w').write(s)

    # per-type listings on the neighborhood map: update_rents.py leaves inv_<size> as they were, so set them
    # here from inventory-by-bed.json (latest month)
    ib = json.load(open(os.path.join(OUT, 'inventory-by-bed.json')))
    alias = {'Columbia Street Waterfront District': 'Columbia St Waterfront District'}
    p = os.path.join(OUT, 'neighborhood-rents.geojson'); g = json.load(open(p))
    for f in g['features']:
        pr = f['properties']; rec = ib['nb'].get(alias.get(pr.get('nb'), pr.get('nb')))
        for k in ['studio', 'br1', 'br2', 'br3']:
            if 'inv_' + k in pr: pr['inv_' + k] = rec[k][1][-1] if rec and k in rec else None
    json.dump(g, open(p, 'w'), separators=(',', ':'))

    ex = json.load(open(os.path.join(OUT, 'rent-explorer.json')))
    months = ex['months']

    # sales price index, same shape as rental-index.json
    rows = list(csv.DictReader(io.StringIO(read_csv(src, 'priceIndex_All'))))
    areas = [k for k in rows[0] if k != 'month']
    by = {r['month']: r for r in rows}
    idx = {'months': months, 'areas': {a: [(round(float(by[m][a])) if m in by and by[m][a] else None) for m in months] for a in areas}}
    json.dump(idx, open(os.path.join(OUT, 'rental-index.json'), 'w'), separators=(',', ':'))

    # homes built against the change in asking price
    A = {a['id']: a for a in ex['areas']}
    i15, i24 = months.index('2015-01'), months.index('2024-12')
    bv = json.load(open(os.path.join(DATA, 'built-vs-rent.json')))
    out_rows = []
    for row in bv['rows']:
        s = A.get('c:' + row['cd'])
        a = s['s']['all'][1] if s else []
        r = dict(row)
        r['chg'] = round((a[i24] / a[i15] - 1) * 100, 1) if a and a[i15] and a[i24] else None
        r['rent'] = a[-1] if a else None
        r['inv'] = s['s']['inv'][1][-1] if s else None
        out_rows.append(r)
    json.dump({'note': 'Units completed 2015 to 2024 against the change in median asking price for all homes, January 2015 to December 2024.',
               'source': bv['source'] + '; StreetEasy median asking price', 'rows': out_rows},
              open(os.path.join(OUT, 'built-vs-rent.json'), 'w'), separators=(',', ':'))

    # spot checks straight from the source CSV text
    def src_val(base, area, month):
        for r in csv.DictReader(io.StringIO(read_csv(src, base))):
            if r['areaName'] == area: return round(float(r[month])) if r[month] else None
    last = months[-1]
    for base, slot, area in [('medianAskingPrice_All', 'studio', 'Park Slope'), ('medianAskingPrice_Condo', 'br1', 'Park Slope'),
                             ('medianAskingPrice_Coop', 'br2', 'Brooklyn'), ('medianAskingPrice_Sfr', 'br3', 'NYC'),
                             ('totalInventory_All', 'inv', 'Park Slope')]:
        aid = ('x:' if area == 'NYC' else 'b:' if area == 'Brooklyn' else 'n:') + area
        got = A[aid]['s'][slot][1][-1]
        if got != src_val(base, area, last): die('spot check failed: %s %s %s' % (base, area, got))
    print('data/sales built through', last, 'and spot-checked against the source')


if __name__ == '__main__':
    if len(sys.argv) != 2: die('usage: update_sales_maps.py <folder>')
    main(sys.argv[1])
