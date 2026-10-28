#!/usr/bin/env python3
"""Build data/adjusters.json: price indexes and populations used to show the housing-cost section's dollar
figures adjusted for inflation and per person.

Usage: python3 scripts/update_adjusters.py [folder of FRED csv downloads]
  With no folder it downloads from FRED.

  cpi_us   CPI-U, U.S. city average, all items, not seasonally adjusted (BLS, FRED CPIAUCNS)
  cpi_ny   CPI-U, New York-Newark-Jersey City, all items (BLS, FRED CUURA101SA0)
  pop_us   U.S. population, thousands (BEA, FRED POPTHM), annual average of monthly figures
  pop_nyc  New York City population, thousands: sum of the five county estimates (Census, FRED
           NYBRON5POP, NYKING7POP, NYNEWY1POP, NYQUEE1POP, NYRICH5POP)
Annual values are the average of the months published for that calendar year. A year with fewer than
12 months is flagged in "partial". The base year is the latest year with CPI data (today's dollars).
"""
import csv, datetime, io, json, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERIES = ['CPIAUCNS', 'CUURA101SA0', 'POPTHM', 'NYBRON5POP', 'NYKING7POP', 'NYNEWY1POP', 'NYQUEE1POP', 'NYRICH5POP']


def die(m): sys.exit('update_adjusters: ' + m)


def load(folder, sid):
    p = os.path.join(folder, sid + '.csv')
    if not os.path.exists(p):
        r = subprocess.run(['curl', '-s', '-m', '90', 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=' + sid], capture_output=True)
        if not r.stdout: die('could not download ' + sid)
        open(p, 'wb').write(r.stdout)
    by = {}
    for row in csv.reader(io.StringIO(open(p).read())):
        if not row or not row[0][:4].isdigit(): continue
        try: v = float(row[1])
        except ValueError: continue
        by.setdefault(row[0][:4], []).append(v)
    return by


def annual(by):
    return {y: round(sum(v) / len(v), 3) for y, v in sorted(by.items())}, sorted(y for y, v in by.items() if len(v) < 12)


def main(folder):
    cpi_us, p1 = annual(load(folder, 'CPIAUCNS'))
    raw_ny = load(folder, 'CUURA101SA0')
    cpi_ny = {y: round(sum(v) / len(v), 3) for y, v in sorted(raw_ny.items())}
    pop_us, p3 = annual(load(folder, 'POPTHM'))
    counties = [load(folder, s) for s in SERIES[3:]]
    years = sorted(set.intersection(*[set(c) for c in counties]))
    pop_nyc = {y: round(sum(c[y][0] for c in counties), 3) for y in years}
    base = max(cpi_us)   # dollars of the latest year with any CPI (a partial year is the average of its published months)
    out = {'built': datetime.date.today().isoformat(), 'base': base,
           'cpi_us': cpi_us, 'cpi_ny': cpi_ny, 'pop_us': pop_us, 'pop_nyc': pop_nyc,
           'partial': {'cpi_us': p1, 'pop_us': p3, 'cpi_ny': [y for y in [max(cpi_ny)] if len(raw_ny[y]) < 12]},
           'source': 'BLS CPI-U (U.S. city average, and New York-Newark-Jersey City), BEA U.S. population, Census county population estimates, all via FRED',
           'url': 'https://fred.stlouisfed.org/'}
    json.dump(out, open(os.path.join(ROOT, 'data', 'adjusters.json'), 'w'), separators=(',', ':'))
    print('base', base, 'cpi_us', min(cpi_us), max(cpi_us), 'cpi_ny', min(cpi_ny), max(cpi_ny), 'pop_nyc', min(pop_nyc), max(pop_nyc), pop_nyc[max(pop_nyc)])


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp())
