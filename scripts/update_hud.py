#!/usr/bin/env python3
"""Build data/hud-nyc.json: HUD's federal budget over time, and HUD money awarded in New York City.

Usage: python3 scripts/update_hud.py [OMB table 4.1 xlsx] [OMB table 5.2 xlsx]
  With no files it downloads the FY 2027 Historical Tables.

Sources
  * OMB Historical Tables, FY 2027 Budget: Table 4.1 Outlays by Agency (1962 on) and Table 5.2 Budget
    Authority by Agency (1976 on), millions of dollars, line "Department of Housing and Urban Development".
    Columns marked "estimate" are the President's budget estimates, kept and flagged.
  * USAspending.gov API: obligations on awards from HUD (awarding agency) whose place of performance is in
    one of the five NYC counties (Bronx 005, Kings 047, New York 061, Queens 081, Richmond 085), by federal
    fiscal year. USAspending carries award data from FY 2008, but NYC place-of-performance reporting for HUD
    is near zero before FY 2010, so the series starts at FY 2010.
    Recipients are grouped from the ten largest each year as USAspending names them: NYCHA, City of New York
    agencies, and everyone else (the remainder of the total).
"""
import datetime, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OMB = 'https://www.whitehouse.gov/wp-content/uploads/2026/04/'
API = 'https://api.usaspending.gov/api/v2/'
NYC = [{'country': 'USA', 'state': 'NY', 'county': c} for c in ['005', '047', '061', '081', '085']]
AGENCY = [{'type': 'awarding', 'tier': 'toptier', 'name': 'Department of Housing and Urban Development'}]


def die(m): sys.exit('update_hud: ' + m)


def curl(args):
    for _ in range(4):
        r = subprocess.run(['curl', '-s', '-m', '180'] + args, capture_output=True)
        if r.returncode == 0 and r.stdout: return r.stdout
    die('request failed: %s' % args[-1])


def post(path, body):
    return json.loads(curl(['-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(body), API + path]))


def omb_row(path, label='Department of Housing and Urban Development'):
    import openpyxl
    rows = list(openpyxl.load_workbook(path, data_only=True).active.iter_rows(values_only=True))
    hdr = next(r for r in rows if r and str(r[0]).strip().startswith('Department or other unit'))
    hud = next(r for r in rows if r and str(r[0]).strip() == label)
    out = []
    for h, v in zip(hdr[1:], hud[1:]):
        if h is None or v is None: continue
        h = str(h).strip()
        m = re.match(r'^(\d{4})( estimate)?$', h)
        if not m: continue          # skips the 1976 transition quarter "TQ"
        out.append({'fy': int(m.group(1)), 'm': v, 'est': bool(m.group(2))})
    return out


def main(f41, f52):
    outlays, ba, fed = omb_row(f41), omb_row(f52), omb_row(f41, 'Total outlays')
    nyc = []
    for fy in range(2010, datetime.date.today().year + 1):
        tp = [{'start_date': '%d-10-01' % (fy - 1), 'end_date': '%d-09-30' % fy}]
        tot = post('search/spending_over_time/', {'group': 'fiscal_year', 'filters': {
            'time_period': tp, 'agencies': AGENCY, 'place_of_performance_locations': NYC}})['results']
        tot = sum(r['aggregated_amount'] for r in tot)
        top = post('search/spending_by_category/recipient/', {'category': 'recipient', 'limit': 10, 'page': 1, 'filters': {
            'time_period': tp, 'agencies': AGENCY, 'place_of_performance_locations': NYC}})['results']
        g = {'nycha': 0.0, 'city': 0.0}
        names = []
        for r in top:
            n = (r.get('name') or '').upper()
            if 'HOUSING AUTHORITY' in n and ('NEW YORK CITY' in n or 'NYC' in n) or 'NEW YORK CITY HSG AUTHORITY' in n:
                g['nycha'] += r['amount']
            elif n.startswith('CITY OF NEW YORK') or n.startswith('THE CITY OF NEW YORK') or n.startswith('NEW YORK CITY '):
                g['city'] += r['amount']
            names.append([r.get('name'), round(r['amount'])])
        nyc.append({'fy': fy, 'total': round(tot), 'nycha': round(g['nycha']), 'city': round(g['city']),
                    'other': round(tot - g['nycha'] - g['city']), 'top': names})
        print(fy, round(tot / 1e6), 'M')
    out = {'built': datetime.date.today().isoformat(),
           'budget': {'outlays': outlays, 'budget_authority': ba, 'federal_outlays': fed, 'units': 'millions of dollars',
                      'source': 'OMB Historical Tables, FY 2027 Budget: Table 4.1 (outlays) and Table 5.2 (budget authority), Department of Housing and Urban Development',
                      'url': 'https://www.whitehouse.gov/omb/budget/historical-tables/'},
           'nyc': {'years': nyc, 'units': 'dollars obligated',
                   'source': 'USAspending.gov: obligations on HUD awards with place of performance in the five NYC counties, by federal fiscal year (October to September)',
                   'url': 'https://www.usaspending.gov/search',
                   'note': 'Recipients are grouped from the ten largest each year, by the names USAspending uses; "everyone else" is the rest of the total. Includes NYCHA public housing and voucher funds, grants to City agencies, and project-based rental assistance to private owners.'}}
    json.dump(out, open(os.path.join(ROOT, 'data', 'hud-nyc.json'), 'w'), separators=(',', ':'))
    print('wrote data/hud-nyc.json')


if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        d = tempfile.mkdtemp()
        for f in ['hist04z1_fy2027.xlsx', 'hist05z2_fy2027.xlsx']:
            open(os.path.join(d, f), 'wb').write(curl(['-A', 'Mozilla/5.0', OMB + f]))
        main(os.path.join(d, 'hist04z1_fy2027.xlsx'), os.path.join(d, 'hist05z2_fy2027.xlsx'))
