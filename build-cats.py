#!/usr/bin/env python3
"""
Builds 33159by5-cats.json: complaints per community district, per year, per
category. The map uses it to shade each district by its most common category.

One query per year returning community_board x complaint_type, then the same
categorisation the page applies client side. That 2D grouping takes about
2.5 minutes per year on Socrata, so years run in parallel and the file is
written incrementally.

Output:
  {"built":"2026-08-16","cats":[...],"years":{"2025":{"06 BROOKLYN":{"parking":17755,...}}}}

Usage: python3 build-cats.py [out.json]
"""
import json, os, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

TOKEN = os.environ.get('SODA_APP_TOKEN', 'HvFoIfzodzpRML7a1104Ca2tM')
DS_OLD, DS_NEW, SPLIT = '76ig-c548', 'erm2-nwe9', 2020
MIN_YEAR, MAX_YEAR = 2010, time.gmtime().tm_year
OUT = sys.argv[1] if len(sys.argv) > 1 else '33159by5-cats.json'

BOROS = ['MANHATTAN', 'BRONX', 'BROOKLYN', 'QUEENS', 'STATEN ISLAND']
CD_COUNT = {'MANHATTAN': 12, 'BRONX': 12, 'BROOKLYN': 18, 'QUEENS': 14, 'STATEN ISLAND': 3}
VALID = {f'{i:02d} {b}' for b in BOROS for i in range(1, CD_COUNT[b] + 1)}

# Must stay in step with CAT_MAP in 33159by5.html.
CAT_MAP = {
    'noise': ['Noise', 'Noise - Commercial', 'Noise - Residential', 'Noise - Street/Sidewalk',
              'Noise - Vehicle', 'Noise - Helicopter', 'Noise - House of Worship', 'Illegal Fireworks'],
    'parking': ['Illegal Parking', 'Blocked Driveway', 'Abandoned Vehicle', 'Derelict Vehicle',
                'For Hire Vehicle Complaint', 'Abandoned Bike', 'Taxi Complaint'],
    'housing': ['HEAT/HOT WATER', 'HEATING', 'PLUMBING', 'ELECTRIC', 'PAINT', 'DOOR/WINDOW',
                'WATER LEAK', 'UNSANITARY CONDITION', 'Lead', 'Elevator', 'General Construction',
                'Maintenance or Facility', 'NONCONST', 'APPLIANCE', 'Building/Use', 'FLOORING/STAIRS', 'SAFETY', 'OUTSIDE BUILDING', 'GENERAL', 'Plumbing', 'Boilers', 'Asbestos', 'Mold'],
    'streets': ['Street Condition', 'Sidewalk Condition', 'Curb Condition', 'Traffic Signal Condition',
                'Street Light Condition', 'Water System', 'Sewer', 'Root/Sewer/Sidewalk Condition',
                'Obstruction', 'Broken Muni Meter', 'Highway Condition', 'Bridge Condition', 'Street Sign', 'Traffic', 'Sewer Backup'],
    'sanitation': ['Dirty Condition', 'Rodent', 'Illegal Dumping', 'Missed Collection', 'Air Quality',
                   'Commercial Disposal Complaint', 'Residential Disposal Complaint', 'Dead Animal',
                   'Dumpster Complaint', 'Request Large Bulky Item Collection', 'Sanitation Condition', 'Sweeping/Missed', 'Sweeping/Inadequate', 'Recycling Enforcement', 'Litter Basket'],
    'social': ['Non-Emergency Police Matter', 'Encampment', 'Homeless Person Assistance', 'Panhandling',
               'Animal-Abuse', 'Smoking or Vaping', 'Urinating in Public', 'Drug Activity', 'DHS Advantage - Tenant', 'DHS Advantage -Landlord/Broker', 'Homeless Encampment'],
    'snow': ['Snow or Ice', 'Snow'],
    'food': ['Food Establishment', 'Food Poisoning', 'Consumer Complaint', 'Mobile Food Vendor',
             'Vendor Enforcement', 'Day Care'],
    'graffiti': ['Graffiti'],
    'trees': ['Tree'],
}
CAT_ORDER = list(CAT_MAP)


def categorize(ct):
    t = (ct or '').strip().lower()
    if not t:
        return 'other'
    for cat in CAT_ORDER:
        for name in CAT_MAP[cat]:
            if name.lower() in t:
                return cat
    return 'other'


def fetch_year(year):
    ds = DS_OLD if year < SPLIT else DS_NEW
    params = {
        '$select': 'community_board as cb,complaint_type as ct,count(1) as n',
        '$where': f"created_date>='{year}-01-01T00:00:00' AND created_date<'{year+1}-01-01T00:00:00'",
        '$group': 'cb,ct',
        '$limit': '50000',
        '$$app_token': TOKEN,
    }
    url = f'https://data.cityofnewyork.us/resource/{ds}.json?' + urllib.parse.urlencode(params)
    t0 = time.time()
    # Socrata returns 503 under load on these heavy 2D groupings; back off and retry.
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=600) as r:
                rows = json.load(r)
            break
        except Exception as e:
            if attempt == 3:
                raise
            wait = 20 * (attempt + 1)
            print(f'{year}: {type(e).__name__}, retrying in {wait}s', flush=True)
            time.sleep(wait)
    out = {}
    for row in rows:
        cb = row.get('cb')
        if cb not in VALID:
            continue
        cat = categorize(row.get('ct'))
        d = out.setdefault(cb, {})
        d[cat] = d.get(cat, 0) + int(row['n'])
    print(f'{year}: {len(out)} districts, {len(rows)} type-rows, {time.time()-t0:.0f}s', flush=True)
    return year, out


def main():
    try:
        with open(OUT) as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {'years': {}}

    todo = [y for y in range(MIN_YEAR, MAX_YEAR + 1)
            if str(y) not in data['years'] or y == MAX_YEAR]
    if not todo:
        print('nothing to do')
        return

    # as_completed, not map: one failed year must not discard the others.
    failed = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch_year, y): y for y in todo}
        for fut in as_completed(futures):
            y = futures[fut]
            try:
                year, res = fut.result()
            except Exception as e:
                print(f'{y}: FAILED {e}', file=sys.stderr, flush=True)
                failed.append(y)
                continue
            data['years'][str(year)] = res
            data['built'] = time.strftime('%Y-%m-%d')
            data['cats'] = CAT_ORDER + ['other']
            with open(OUT, 'w') as f:
                json.dump(data, f, separators=(',', ':'), sort_keys=True)
    if failed:
        print('incomplete years: ' + ', '.join(map(str, sorted(failed))), file=sys.stderr)

    print(f'wrote {OUT} ({os.path.getsize(OUT):,} bytes)')


if __name__ == '__main__':
    main()
