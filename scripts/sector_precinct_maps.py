#!/usr/bin/env python3
"""The precinct map on every NYPD sector profile in the apps: the precinct's boundary, all of its sectors, the sector
itself filled, and the station house. Writes app/data/civic/nypd/sectors-map.geojson and, in each app's screens.json,
a node `sector-map-<sector>`; the profile's "Precinct map" row opens it (kvdest). Rerunnable."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
SEC = json.load(open(P('data/nypd-sectors-lite.geojson')))['features']
PCT = json.load(open(P('data/police-precincts-lite.geojson')))['features']
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
profs = [p for p in D['profiles'] if p['slug'].startswith('nypd-sector-')]
pcts = sorted({re.match(r'nypd-sector-(\d+)', p['slug']).group(1) for p in profs})
feats = []
for g in PCT:
    if g['properties']['precinct'] in pcts:
        feats.append({'type': 'Feature', 'geometry': g['geometry'], 'properties': {'key': 'pct-' + g['properties']['precinct'], 'name': g['properties']['precinct'] + 'th Precinct'}})
for g in SEC:
    n = g['properties']['pct'].lstrip('0')
    if n in pcts:
        s = g['properties']['sector']
        feats.append({'type': 'Feature', 'geometry': g['geometry'], 'properties': {'key': 'in-' + n, 'name': 'Sector ' + s}})
        feats.append({'type': 'Feature', 'geometry': g['geometry'], 'properties': {'key': 'sec-' + s, 'name': 'Sector ' + s}})
out = P('app/data/civic/nypd/sectors-map.geojson')
json.dump({'type': 'FeatureCollection', 'features': feats}, open(out, 'w'), separators=(',', ':'))
FILE = 'civic/nypd/sectors-map.geojson'
nodes = {}
HOUSES = {}
for p in profs:
    s = p['slug'].split('-')[-1].upper(); n = re.match(r'(\d+)', s).group(1)
    st = next((q for q in D['profiles'] if q['slug'] == '%sth-precinct' % n), {})
    pin = [{'title': '%sth Precinct station house' % n, 'sub': st.get('addr', ''), 'lat': st['lat'], 'lng': st['lng'], 'pct': n}] if st.get('lat') else []
    if pin: HOUSES[n] = pin[0]
    nodes['sector-map-' + s.lower()] = {'title': 'Sector %s and the %sth Precinct' % (s, n), 'type': 'v', 'spacing': 10, 'children': [
        {'type': 'text', 'text': 'Sector %s filled in orange, the other %sth Precinct sectors outlined, the precinct boundary in navy.' % (s, n), 'size': 14, 'color': 'muted'},
        {'type': 'map', 'height': 560, 'fit': 'precinct', 'toggles': True, 'legend': True, 'layers': [
            {'id': 'precinct', 'title': '%sth Precinct' % n, 'on': True, 'file': FILE, 'where': {'key': 'pct-' + n}, 'stroke': '#06024d', 'width': 3.5, 'fillOpacity': 0.04, 'chip': '#06024d'},
            {'id': 'sectors', 'title': '%sth Precinct sectors' % n, 'on': True, 'file': FILE, 'where': {'key': 'in-' + n}, 'stroke': '#06024d', 'width': 1.2, 'fillOpacity': 0, 'chip': '#9aa0b4'},
            {'id': 'sector', 'title': 'Sector ' + s, 'on': True, 'file': FILE, 'where': {'key': 'sec-' + s}, 'stroke': '#f47920', 'width': 2.5, 'fill': '#f47920', 'fillOpacity': 0.35, 'chip': '#f47920'}]
          + ([{'id': 'house', 'title': 'Station house', 'on': True, 'data': {'file': 'civic/nypd/station-houses.json', 'at': 'houses', 'where': {'pct': n}}, 'pin': {'style': 'image', 'image': 'civic/orgs/logos/' + p['logo'], 'size': 34}, 'chip': '#06024d'}] if pin and p.get('logo') else [])}]}
    p['kv'] = [kv for kv in p['kv'] if kv[0] != 'Precinct map']
    p['kv'].insert(1, ['Precinct map', 'Sector %s and the %sth Precinct, on the map' % (s, n)])
    p.setdefault('kvdest', {})['Precinct map'] = 'node:sector-map-' + s.lower()
json.dump({'houses': list(HOUSES.values())}, open(P('app/data/civic/nypd/station-houses.json'), 'w'), indent=1)
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
for app in ('cb6', 'bk', 'beyond'):
    sf = P('app/data/civic/ui', app, 'screens.json'); raw = open(sf, encoding='utf-8').read(); S = json.loads(raw)
    S.setdefault('nodes', {}).update(nodes)
    ind = len(re.match(r'\{\n( *)', raw).group(1)) if raw.startswith('{\n') else None
    open(sf, 'w', encoding='utf-8').write(json.dumps(S, ensure_ascii=False, indent=ind) + ('\n' if raw.endswith('\n') else ''))
print('sector maps:', len(nodes), '| features:', len(feats))
