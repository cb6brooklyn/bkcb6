#!/usr/bin/env python3
"""data/dashboards/_wk.json: this week's COVID-19, flu and respiratory illness numbers for the district dashboards,
from the Health Department's respiratory illness data (github.com/nychealth/respiratory-illness-data, updated weekly).

Exact, as published:
  - percent of emergency department visits with a COVID-19 or flu diagnosis, each week, citywide and by borough
    (ED_data_COVID-19.csv, ED_data_influenza.csv).
Estimated (marked with an asterisk on the dashboards):
  - COVID-19 and flu case rates per 100,000 and the share of emergency department visits for respiratory illness,
    published by United Hospital Fund neighborhood (Case_data_by_neighborhood.csv, ED_data_by_neighborhood.csv),
    given to each district and community district as the average of the neighborhoods it covers, weighted by how much
    of the district's land is in each. Neighborhoods the Health Department combines (such as 105/106/107) are merged.
Shapes: coronavirus-data/Geography-resources/UHF_resources/UHF42.geo.json.
Usage: python3 scripts/district_resp_weekly.py [folder holding the nychealth clones]"""
import csv, glob, json, os, sys, warnings
warnings.filterwarnings('ignore')
from shapely.geometry import shape
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from district_overlaps import clean
NYCH = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/nychealth'
R = os.path.join(NYCH, 'respiratory-illness-data/data')
M = lambda x, y, z=None: (x * 84300.0, y * 111000.0)
geom = lambda gj: (lambda g: transform(M, g if g.is_valid else g.buffer(0)))(shape(clean(gj)))
BOROS = ['Bronx', 'Brooklyn', 'Manhattan', 'Queens', 'Staten Island']

def num(v):
    v = (v or '').strip()
    return float(v) if v else None

def main():
    land = geom({'type': 'GeometryCollection', 'geometries': [f['geometry'] for f in json.load(open('data/districts/city-nyc.geojson'))['features']]}).buffer(0)
    uhf = {str(f['properties']['GEOCODE']): geom(f['geometry']) for f in json.load(open(os.path.join(NYCH, 'coronavirus-data/Geography-resources/UHF_resources/UHF42.geo.json')))['features']}
    cases = list(csv.DictReader(open(os.path.join(R, 'Case_data_by_neighborhood.csv'))))
    ed = list(csv.DictReader(open(os.path.join(R, 'ED_data_by_neighborhood.csv'))))
    week = cases[0]['date']
    areas = {}
    for r in cases:
        g = unary_union([uhf[c] for c in r['neighborhood'].split('/') if c in uhf]).intersection(land)
        areas[r['neighborhood']] = {'g': g, 'covid': num(r['COVID-19 case rate']), 'flu': num(r['Flu case rate'])}
    for r in ed:
        if r['neighborhood'] in areas: areas[r['neighborhood']]['ed'] = num(r['Respiratory illness visits'])
    names = list(areas); tree = STRtree([areas[n]['g'] for n in names])
    out = {'week': week, 'about': 'Weighted by the share of the district’s land in each United Hospital Fund neighborhood; an estimate.',
           'source': 'NYC Health Department respiratory illness data, github.com/nychealth/respiratory-illness-data', 'd': {}}
    for ch in ('council', 'assembly', 'senate', 'congress', 'cb'):
        for p in sorted(glob.glob(f'data/districts/{ch}-*.geojson')):
            n = p.rsplit('-', 1)[1][:-8]
            if ch == 'cb' and not (len(n) == 3 and n.isdigit()): continue
            dg = geom({'type': 'GeometryCollection', 'geometries': [f['geometry'] for f in json.load(open(p))['features']]}).buffer(0).intersection(land)
            if dg.is_empty: continue
            parts = []
            for i in tree.query(dg):
                a = areas[names[i]]['g'].intersection(dg).area
                if a / dg.area >= 0.01: parts.append((names[i], a / dg.area))
            tot = sum(s for _, s in parts)
            row = {'uhf': [[k, round(s / tot * 100, 1)] for k, s in sorted(parts, key=lambda x: -x[1])]}
            for m in ('covid', 'flu', 'ed'):
                vs = [(areas[k].get(m), s) for k, s in parts if areas[k].get(m) is not None]
                w = sum(s for _, s in vs)
                row[m] = round(sum(v * s for v, s in vs) / w, 1) if w else None
            out['d'][f'{ch}-{n}'] = row
    for key, fn, pre in (('covid_ed', 'ED_data_COVID-19.csv', 'COVID-19 visits'), ('flu_ed', 'ED_data_influenza.csv', 'Influenza visits')):
        rows = list(csv.DictReader(open(os.path.join(R, fn))))
        out[key] = {'weeks': [r['date'] for r in rows], 'NYC': [num(r[f'{pre} overall']) for r in rows]}
        for b in BOROS: out[key][b] = [num(r.get(f'{pre} {b}')) for r in rows]
    json.dump(out, open('data/dashboards/_wk.json', 'w'), separators=(',', ':'))
    print(week, len(out['d']), json.dumps(out['d'].get('cb-306')), out['covid_ed']['Brooklyn'][-2:], out['flu_ed']['Brooklyn'][-2:])

if __name__ == '__main__':
    main()
