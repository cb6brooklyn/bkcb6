#!/usr/bin/env python3
"""Build data/sales-explorer.json from StreetEasy Data Dashboard sales downloads.

Usage: python3 scripts/update_sales.py <folder of StreetEasy sales zips or csvs>

Files read, for each home type All / Condo / Coop / Sfr:
    medianAskingPrice_X   median asking price of homes listed for sale
    totalInventory_X      number of homes listed for sale
    medianSalesPrice_X    median recorded sale price

Same rules as update_rents.py:
  * Values stay in the month they belong to. Blanks are kept as null.
  * A community district's price is the median of its member neighborhoods,
    and its listings count is their sum. Staten Island districts have no
    StreetEasy neighborhoods in the crosswalk, so they use the borough figure.
  * Council districts use the same neighborhood crosswalk as the rents page
    (today's district lines), applied to every month. Councils with no
    StreetEasy neighborhoods use their borough figure.
  * Every value written is re-derived from the source CSVs and checked.
"""
import csv, io, json, os, statistics, sys, zipfile, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
TYPES = {'all': 'All', 'condo': 'Condo', 'coop': 'Coop', 'sfr': 'Sfr'}
METRICS = {'ask': 'medianAskingPrice', 'inv': 'totalInventory', 'sale': 'medianSalesPrice'}
ALIAS = {'Columbia Street Waterfront District': 'Columbia St Waterfront District'}


def die(msg):
    sys.exit('update_sales: ' + msg)


def read(src, base):
    z = os.path.join(src, base + '.zip')
    c = os.path.join(src, base + '.csv')
    if os.path.exists(z):
        zf = zipfile.ZipFile(z)
        name = [n for n in zf.namelist() if n.endswith('.csv')][0]
        return list(csv.DictReader(io.TextIOWrapper(zf.open(name), encoding='utf-8-sig')))
    if os.path.exists(c):
        return list(csv.DictReader(open(c, encoding='utf-8-sig')))
    die('missing ' + base)


def num(v):
    v = (v or '').strip()
    if not v: return None
    return round(float(v))


def median(vals):
    v = [x for x in vals if x is not None]
    return round(statistics.median(v)) if v else None


def total(vals):
    v = [x for x in vals if x is not None]
    return sum(v) if v else None


def main(src):
    months = None
    raw = {}   # (type, metric) -> {area: [values]}
    boro_of = {}
    kind = {}
    for t, T in TYPES.items():
        for m, M in METRICS.items():
            rows = read(src, '%s_%s' % (M, T))
            ms = [k for k in rows[0] if len(k) == 7 and k[4] == '-']
            if months is None: months = ms
            elif ms != months: die('%s_%s months differ from the others' % (M, T))
            raw[(t, m)] = {r['areaName']: [num(r[k]) for k in months] for r in rows}
            for r in rows:
                boro_of[r['areaName']] = r['Borough']
                kind[r['areaName']] = r['areaType']
    n = len(months)
    blank = [None] * n

    def s(area, t, m):
        return raw[(t, m)].get(ALIAS.get(area, area), blank)

    def agg(members, t, m):
        f = total if m == 'inv' else median
        return [f([s(a, t, m)[i] for a in members]) for i in range(n)]

    def series(fn):
        return {t: {m: fn(t, m) for m in METRICS} for t in TYPES}

    crosswalk = json.load(open(os.path.join(DATA, 'rent-cd-crosswalk.json')))
    cc = json.load(open(os.path.join(DATA, 'cc-rents.json')))
    cc_boro = json.load(open(os.path.join(DATA, 'cc-borough.json')))

    out_cd, cd_rule = {}, {}
    for code, members in crosswalk.items():
        usable = [a for a in members if ALIAS.get(a, a) in raw[('all', 'ask')]]
        if code.startswith('SI') or not usable:
            out_cd[code] = series(lambda t, m: list(s('Staten Island' if code.startswith('SI') else None, t, m)))
            cd_rule[code] = 'borough'
        else:
            out_cd[code] = series(lambda t, m, u=usable: agg(u, t, m))
            cd_rule[code] = usable

    out_cc, cc_rule = {}, {}
    for cd in [str(i) for i in range(1, 52)]:
        members = cc['crosswalk'].get(cd, [])
        usable = [a for a in members if ALIAS.get(a, a) in raw[('all', 'ask')]]
        if usable:
            out_cc[cd] = series(lambda t, m, u=usable: agg(u, t, m))
            cc_rule[cd] = usable
        else:
            b = (cc_boro.get(cd) or {}).get('main')
            if not b or b not in raw[('all', 'ask')]: die('council %s has no data' % cd)
            out_cc[cd] = series(lambda t, m, b=b: list(s(b, t, m)))
            cc_rule[cd] = 'borough:' + b

    out_nb, out_boro = {}, {}
    for a, k in kind.items():
        rec = series(lambda t, m, a=a: list(s(a, t, m)))
        if k == 'neighborhood': out_nb[a] = rec
        elif k in ('borough', 'city'): out_boro[a] = rec
    nb_boro = {a: boro_of[a] for a in out_nb}

    # ---- verify every value against the source ----
    checked = 0
    for t in TYPES:
        for m in METRICS:
            f = total if m == 'inv' else median
            for code, rule in cd_rule.items():
                for i in range(n):
                    want = s('Staten Island', t, m)[i] if rule == 'borough' else f([raw[(t, m)].get(ALIAS.get(a, a), blank)[i] for a in rule])
                    if out_cd[code][t][m][i] != want: die('CD %s %s %s %s mismatch' % (code, t, m, months[i]))
                    checked += 1
            for cd, rule in cc_rule.items():
                for i in range(n):
                    if rule.startswith('borough:') if isinstance(rule, str) else False:
                        want = raw[(t, m)][rule[8:]][i]
                    else:
                        want = f([raw[(t, m)].get(ALIAS.get(a, a), blank)[i] for a in rule])
                    if out_cc[cd][t][m][i] != want: die('Council %s %s %s %s mismatch' % (cd, t, m, months[i]))
                    checked += 1
            for a in out_nb:
                if out_nb[a][t][m] != raw[(t, m)][a]: die('nb %s mismatch' % a)
                checked += n
    # spot check straight from the CSV text, not the parsed table
    rows = read(src, 'medianAskingPrice_All')
    ps = [r for r in rows if r['areaName'] == 'Park Slope'][0]
    if out_nb['Park Slope']['all']['ask'][-1] != round(float(ps[months[-1]])): die('Park Slope spot check failed')

    out = {
        'source': 'StreetEasy Data Dashboard (sales)',
        'built': datetime.date.today().isoformat(),
        'months': months,
        'types': {'all': 'All homes', 'condo': 'Condos', 'coop': 'Co-ops', 'sfr': 'Single-family'},
        'metrics': {'ask': 'Median asking price', 'inv': 'Homes listed for sale', 'sale': 'Median sale price'},
        'note': ('Community district and council district prices are the median of their StreetEasy '
                 'neighborhoods; listings are the sum. Staten Island community districts and councils '
                 '%s use the Staten Island borough figure. Council districts are today\'s lines applied to every month.'
                 % ', '.join(sorted([c for c, r in cc_rule.items() if isinstance(r, str)], key=int))),
        'cd': out_cd, 'cc': out_cc, 'nb': out_nb, 'nbBoro': nb_boro, 'boro': out_boro,
    }
    path = os.path.join(DATA, 'sales-explorer.json')
    with open(path, 'w') as fh:
        json.dump(out, fh, separators=(',', ':'))
    print('wrote %s (%d KB): %d months %s to %s, %d CDs, %d councils, %d neighborhoods; verified %d values'
          % (path, os.path.getsize(path) // 1024, n, months[0], months[-1], len(out_cd), len(out_cc), len(out_nb), checked))


if __name__ == '__main__':
    if len(sys.argv) != 2: die('usage: update_sales.py <folder>')
    main(sys.argv[1])
