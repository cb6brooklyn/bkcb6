#!/usr/bin/env python3
"""data/dashboards/_ehdp.json: every Environment and Health Data Portal measure the Health Department publishes by
community district, latest period for each, exactly as published (no estimates), plus the citywide value for the same
period. Source: github.com/nychealth/EHDP-data (indicators/data/*.json, indicators/metadata). Topic names come from
data/health/index.json (the portal's own topic lists).
Usage: python3 scripts/district_ehdp.py [path to an EHDP-data clone]"""
import glob, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
E = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/nychealth/EHDP-data'
meta = json.load(open(os.path.join(E, 'indicators/metadata/metadata.json')))
tps = {t['TimePeriodID']: t['TimePeriod'] for t in json.load(open(os.path.join(E, 'indicators/metadata/TimePeriods.json')))}
topic = {}
for t, ids in json.load(open('data/health/index.json'))['topics'].items():
    for i in ids: topic.setdefault(int(i), t)
out = {'source': 'NYC Health Department, Environment and Health Data Portal (a816-dohbesp.nyc.gov/IndicatorPublic), github.com/nychealth/EHDP-data',
       'm': {}}
for ind in meta:
    ms = [m for m in ind['Measures'] if 'CD' in m['AvailableGeoTypes']]
    if not ms: continue
    f = os.path.join(E, 'indicators/data/%s.json' % ind['IndicatorID'])
    if not os.path.exists(f): continue
    d = json.load(open(f)); n = len(d['MeasureID'])
    rows = [{k: d[k][i] for k in d} for i in range(n)]
    for m in ms:
        mid = m['MeasureID']
        cd = [r for r in rows if r['MeasureID'] == mid and r['GeoType'] == 'CD' and r['Value'] is not None]
        if not cd: continue
        tp = max(r['TimePeriodID'] for r in cd)
        city = next((r for r in rows if r['MeasureID'] == mid and r['GeoType'] == 'Citywide' and r['TimePeriodID'] == tp), None)
        out['m'][str(mid)] = {'ind': ind['IndicatorName'], 'name': m['MeasureName'], 'type': m['MeasurementType'],
                              'src': m.get('Sources', ''), 'topic': topic.get(mid, 'Other'), 'period': tps.get(tp, str(tp)),
                              'city': city['Value'] if city else None,
                              'v': {str(r['GeoID']): r['Value'] for r in cd if r['TimePeriodID'] == tp}}
json.dump(out, open('data/dashboards/_ehdp.json', 'w'), separators=(',', ':'))
print(len(out['m']), 'measures;', os.path.getsize('data/dashboards/_ehdp.json'), 'bytes;', sorted({t['topic'] for t in out['m'].values()}))
print(json.dumps(out['m'].get('1'))[:300])
