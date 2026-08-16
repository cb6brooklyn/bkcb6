#!/usr/bin/env python3
"""
Builds 33159by5-rank.json: total 311 complaints per community district per year.

One query per year, unscoped, grouped by community_board. Two dimensional
grouping (community_board x year) in a single query times out on Socrata, and
adding $order to any aggregate query makes it roughly 16x slower, so neither
is used here.

Output shape:
  {"built":"2026-08-16","years":{"2024":{"06 BROOKLYN":54026, ...}, ...}}

Usage: python3 build-rank.py [out.json]
"""
import json, sys, time, urllib.parse, urllib.request, os

TOKEN   = os.environ.get('SODA_APP_TOKEN', 'HvFoIfzodzpRML7a1104Ca2tM')
DS_OLD  = '76ig-c548'   # 2010-2019
DS_NEW  = 'erm2-nwe9'   # 2020-present
SPLIT   = 2020
MIN_YEAR = 2010
MAX_YEAR = time.gmtime().tm_year
OUT = sys.argv[1] if len(sys.argv) > 1 else '33159by5-rank.json'

BOROS = ['MANHATTAN', 'BRONX', 'BROOKLYN', 'QUEENS', 'STATEN ISLAND']
CD_COUNT = {'MANHATTAN': 12, 'BRONX': 12, 'BROOKLYN': 18, 'QUEENS': 14, 'STATEN ISLAND': 3}
VALID = {f'{i:02d} {b}' for b in BOROS for i in range(1, CD_COUNT[b] + 1)}
assert len(VALID) == 59


def fetch_year(year):
    ds = DS_OLD if year < SPLIT else DS_NEW
    params = {
        '$select': 'community_board as cb,count(1) as n',
        '$where': f"created_date>='{year}-01-01T00:00:00' AND created_date<'{year+1}-01-01T00:00:00'",
        '$group': 'cb',
        '$limit': '500',
        '$$app_token': TOKEN,
    }
    url = f'https://data.cityofnewyork.us/resource/{ds}.json?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=180) as r:
        rows = json.load(r)
    if len(rows) >= 500:
        raise RuntimeError(f'{year}: grouped result hit the 500 row limit; refusing to write partial data')
    # Keep only the 59 real districts. The field also carries Unspecified,
    # park and airport pseudo districts, and joint interest areas.
    return {r['cb']: int(r['n']) for r in rows if r.get('cb') in VALID}


def main():
    try:
        with open(OUT) as f:
            out = json.load(f)
    except (OSError, ValueError):
        out = {'years': {}}

    for year in range(MIN_YEAR, MAX_YEAR + 1):
        key = str(year)
        # Only the current year changes once a year is closed out.
        if key in out['years'] and year != MAX_YEAR:
            continue
        t0 = time.time()
        try:
            out['years'][key] = fetch_year(year)
        except Exception as e:
            print(f'{year}: FAILED {e}', file=sys.stderr)
            continue
        print(f'{year}: {len(out["years"][key])} districts, '
              f'{sum(out["years"][key].values()):,} complaints, {time.time()-t0:.1f}s', flush=True)

    out['built'] = time.strftime('%Y-%m-%d')
    with open(OUT, 'w') as f:
        json.dump(out, f, separators=(',', ':'), sort_keys=True)
    print(f'wrote {OUT} ({os.path.getsize(OUT):,} bytes)')


if __name__ == '__main__':
    main()
