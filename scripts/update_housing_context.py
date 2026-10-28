#!/usr/bin/env python3
"""Build data/housing-context.json: housing supply by community district each year, the Rent Guidelines
Board's renewal lease guidelines since 1968, the rent stabilized stock (2023 NYCHVS), and HPD's adopted
expense budget by fund.

Usage: python3 scripts/update_housing_context.py

  supply  NYC Department of City Planning, Housing Database by Community District (NYC Open Data dbdt-5s7j):
          net Class A housing units completed each calendar year (new buildings + alterations - demolitions),
          2010 (from April 1, 2010) to the current year to date; 2020 Census housing units.
          Boroughs and the city are the sums of every row (districts and joint interest areas).
  rgb     Rent Guidelines Board, "Apartment Orders #1 through #58" summary chart
          (rentguidelinesboard.cityofnewyork.us/wp-content/uploads/2025/07/RGB-Apartment-Chart.pdf),
          one- and two-year renewal guidelines as printed; where the chart gives a split or a dollar minimum
          it is kept in "note" and the plotted figure is the one named there.
  stab    2023 NYC Housing and Vacancy Survey, Selected Initial Findings (HPD; RGB Appendix Z).
  hpd     NYC Office of Management and Budget, Expense Budget Funding (NYC Open Data 39g5-gbp3), agency 806
          (HPD), adopted budget by fund, from the June publication for each fiscal year.
"""
import datetime, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = 'HvFoIfzodzpRML7a1104Ca2tM'
BORO = {'1': 'MN', '2': 'BX', '3': 'BK', '4': 'QN', '5': 'SI'}
BNAME = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}


def die(m): sys.exit('update_housing_context: ' + m)


def soda(ds, q):
    url = 'https://data.cityofnewyork.us/resource/%s.json?%s&$$app_token=%s' % (ds, q, TOKEN)
    r = subprocess.run(['curl', '-s', '-m', '180', '-g', url], capture_output=True)
    d = json.loads(r.stdout or b'null')
    if not isinstance(d, list): die('Open Data error on %s: %s' % (ds, str(d)[:200]))
    return d


# one-year / two-year renewal guidelines, Apartment Orders #1 to #58, as printed in the RGB summary chart
RGB = [
    (58, '2026-10', 0.0, 0.0, ''), (57, '2025-10', 3.0, 4.5, ''), (56, '2024-10', 2.75, 5.25, ''),
    (55, '2023-10', 3.0, 2.75, 'Two-year: 2.75% the first year, 3.2% the second'),
    (54, '2022-10', 3.25, 5.0, ''),
    (53, '2021-10', 0.0, 2.5, 'One-year: 0% the first six months, 1.5% the last six'),
    (52, '2020-10', 0.0, 0.0, 'Two-year: 0% the first year, 1% the second'),
    (51, '2019-10', 1.5, 2.5, ''), (50, '2018-10', 1.5, 2.5, ''), (49, '2017-10', 1.25, 2.0, ''),
    (48, '2016-10', 0.0, 2.0, ''), (47, '2015-10', 0.0, 2.0, ''), (46, '2014-10', 1.0, 2.75, ''),
    (45, '2013-10', 4.0, 7.75, ''), (44, '2012-10', 2.0, 4.0, '2% or $20 (one-year), 4% or $40 (two-year), whichever is greater'),
    (43, '2011-10', 3.75, 7.25, ''), (42, '2010-10', 2.25, 4.5, ''),
    (41, '2009-10', 3.0, 6.0, 'Where the owner provides heat; 2.5% and 5% where the tenant pays for heat'),
    (40, '2008-10', 4.5, 8.5, 'Where the owner provides heat; 4% and 8% where the tenant pays for heat'),
    (39, '2007-10', 3.0, 5.75, ''),
    (38, '2006-10', 4.25, 7.25, 'Where the owner provides heat; 3.75% and 6.75% where the tenant pays for heat'),
    (37, '2005-10', 2.75, 5.5, 'Where the owner provides heat; 2.25% and 4.5% where the tenant pays for heat'),
    (36, '2004-10', 3.5, 6.5, 'Where the owner provides heat; 3% and 6% where the tenant pays for heat'),
    (35, '2003-10', 4.5, 7.5, ''), (34, '2002-10', 2.0, 4.0, ''), (33, '2001-10', 4.0, 6.0, ''),
    (32, '2000-10', 4.0, 6.0, 'Rent of $500 or less: add $15'), (31, '1999-10', 2.0, 4.0, 'Rent of $500 or less: add $15'),
    (30, '1998-10', 2.0, 4.0, 'Rent under $450: add $15'), (29, '1997-10', 2.0, 4.0, 'Rent of $400 or less: add $15'),
    (28, '1996-10', 5.0, 7.0, 'Rent of $400 or less: add $20'), (27, '1995-10', 2.0, 4.0, 'Rent of $400 or less: add $20'),
    (26, '1994-10', 2.0, 4.0, 'Rent under $400: add $15'), (25, '1993-10', 3.0, 5.0, ''), (24, '1992-10', 3.0, 5.0, ''),
    (23, '1991-10', 4.0, 6.5, ''), (22, '1990-10', 4.5, 7.0, ''), (21, '1989-10', 5.5, 9.0, ''), (20, '1988-10', 6.0, 9.0, ''),
    (19, '1987-10', 3.0, 6.5, ''), (18, '1986-10', 6.0, 9.0, ''), (17, '1985-10', 4.0, 6.5, ''), (16, '1984-10', 6.0, 9.0, ''),
    (15, '1983-10', 4.0, 7.0, ''), (14, '1982-10', 4.0, 7.0, ''),
    (13, '1981-10', 10.0, 13.0, 'Where the owner provides heat; 6.5% and 9.5% where the tenant pays for heat'),
    (12, '1980-07', 11.0, 14.0, 'A fifteen-month guideline period; owner provides heat (5% and 7% where the tenant pays)'),
    (11, '1979-07', 8.5, 12.0, 'Plus an $8 monthly fuel surcharge for one year'),
    (10, '1978-07', 4.5, 6.5, 'Plus fuel adjustments set by Orders #10b to #10e'),
    (9, '1977-07', 6.5, 8.5, ''), (8, '1976-07', 6.5, 8.0, ''), (7, '1975-07', 7.5, 9.5, ''), (6, '1974-07', 8.5, 10.5, ''),
    (5, '1973-07', 6.5, 8.5, ''), (4, '1972-07', 6.0, 8.0, 'Plus a 0.5% stabilizer'), (3, '1971-07', 7.0, 9.0, 'Plus a 1.0% stabilizer'),
    (2, '1970-07', 6.0, 8.0, ''), (1, '1968-07', 10.0, 10.0, 'A two-year guideline period, July 1968 to June 1970'),
]


def main():
    rows = soda('dbdt-5s7j', '$limit=200')
    yrs = sorted(int(k[4:]) for k in rows[0] if k.startswith('comp') and k[4:].isdigit())
    cd, boro, city = {}, {}, {}
    def add(store, key, r):
        rec = store.setdefault(key, {'comp': {}, 'cen20': 0})
        for y in yrs:
            v = r.get('comp%d' % y)
            if v not in (None, ''): rec['comp'][str(y)] = rec['comp'].get(str(y), 0) + round(float(v))
        rec['cen20'] += round(float(r.get('cenunits20') or 0))
    for r in rows:
        c = r['commntydst']; b = c[0]; n = int(c[1:])
        if n <= 18: add(cd, '%sCB%d' % (BORO[b], n), r)
        add(boro, BNAME[b], r); add(city, 'NYC', r)
    if len(cd) != 59: die('expected 59 districts, got %d' % len(cd))
    ytd = str(yrs[-1])

    hpd = []
    for x in soda('39g5-gbp3', '$select=fiscal_year,publication_date,sum(total_adopted_budget_amount),sum(city_funds_adopted_budget_amount),'
                  'sum(federal_funds_adopted_budget_amount),sum(community_development_funds_adopted_budget_amount),sum(state_funds_adopted_budget_amount),'
                  'sum(inter_fund_agreement_funds_adopted_budget_amount),sum(intra_city_sales_funds_adopted_budget_amount),sum(other_categorical_funds_adopted_budget_amount)'
                  '&agency_number=806&$group=fiscal_year,publication_date&$order=fiscal_year,publication_date&$limit=500'):
        if x['publication_date'][4:6] != '06': continue      # the adopted budget, published in June
        g = lambda k: round(float(x.get('sum_%s_adopted_budget_amount' % k) or 0))
        hpd.append({'fy': int(x['fiscal_year']), 'pub': x['publication_date'], 'total': g('total'), 'city': g('city_funds'),
                    'federal': g('federal_funds'), 'cd': g('community_development_funds'), 'state': g('state_funds'),
                    'other': g('inter_fund_agreement_funds') + g('intra_city_sales_funds') + g('other_categorical_funds')})

    out = {'built': datetime.date.today().isoformat(),
           'supply': {'years': yrs, 'ytd': ytd, 'cd': cd, 'boro': boro, 'nyc': city['NYC'],
                      'note': 'Net Class A housing units completed each year (new buildings plus alterations minus demolitions); %s is the year to date.' % ytd,
                      'source': 'NYC Department of City Planning, Housing Database by Community District (NYC Open Data)',
                      'url': 'https://data.cityofnewyork.us/d/dbdt-5s7j'},
           'rgb': {'orders': [{'order': o, 'start': s, 'one': a, 'two': b, 'note': n} for o, s, a, b, n in sorted(RGB)],
                   'source': 'NYC Rent Guidelines Board, Apartment Orders #1 through #58 (summary chart)',
                   'url': 'https://rentguidelinesboard.cityofnewyork.us/wp-content/uploads/2025/07/RGB-Apartment-Chart.pdf'},
           'stab': {'year': 2023, 'units': 996600, 'share_all': 27, 'share_rentals': 41, 'etpa_units': 758700, 'vacancy': 0.98, 'vacancy_2021': 4.57,
                    'controlled': 24020, 'market_rentals': 1139000,
                    'source': '2023 New York City Housing and Vacancy Survey, Selected Initial Findings (HPD), Rent Guidelines Board Appendix Z',
                    'url': 'https://rentguidelinesboard.cityofnewyork.us/wp-content/uploads/2019/08/appendixz.pdf'},
           'hpd': {'years': hpd, 'source': 'NYC Office of Management and Budget, Expense Budget Funding (NYC Open Data 39g5-gbp3), Housing Preservation and Development (agency 806), adopted budget',
                   'url': 'https://data.cityofnewyork.us/d/39g5-gbp3',
                   'note': 'Expense budget only; HPD’s capital budget, which pays for most new affordable housing, is separate. "Community development" is the federal Community Development Block Grant; "other" is inter-fund agreements, intra-city sales and other categorical funds.'}}
    json.dump(out, open(os.path.join(ROOT, 'data', 'housing-context.json'), 'w'), separators=(',', ':'))
    print('supply years', yrs[0], '-', yrs[-1], '| CB6', cd['BKCB6']['comp'], '| NYC 2024', city['NYC']['comp'].get('2024'), '| HPD', [(h['fy'], h['total'] // 10**6) for h in hpd])


if __name__ == '__main__':
    main()
