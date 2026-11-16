#!/usr/bin/env python3
"""Every Directory profile that stands for a district gets its district on a map in the apps: the boundary, and the
office pinned with its logo. A "District map" row on the profile opens it (kvdest -> node:dmap-<slug>).

  school districts 1-32 and their Community Education Councils   data/districts/school-<n>.geojson
  precincts and precinct community councils                      data/police-precincts-lite.geojson
  District Attorneys (the borough)                                data/districts/borough-<1..5>.geojson
  business improvement districts with a boundary on the site     data/districts/bid-<name>.geojson
NYPD sectors have their own map (sector_precinct_maps.py). Writes app/data/civic/districtmaps/<slug>.geojson,
app/data/civic/districtmaps/offices.json and the nodes in each app's screens.json. Rerunnable."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
OUT = P('app/data/civic/districtmaps'); os.makedirs(OUT, exist_ok=True)
BOARDS = [b['borocd'] for b in json.load(open(P('app/data/civic/boards.json')))]
OFF = {o['slug']: o for o in json.load(open(P('app/data/civic/officials.json')))}
DSNY = json.load(open(P('data/dsny-sections-lite.geojson')))['features']
PCT = {f['properties']['precinct']: f['geometry'] for f in json.load(open(P('data/police-precincts-lite.geojson')))['features']}
BORO = {'manhattan': 1, 'bronx': 2, 'brooklyn': 3, 'queens': 4, 'staten-island': 5}
BID = {'atlantic-avenue-bid': 'bid-atlantic-avenue', 'north-flatbush-bid': 'bid-north-flatbush',
       'cbo-park-slope-fifth-avenue-district-management-association': 'bid-park-slope-5th-avenue'}
def geo_file(path):
    g = json.load(open(path)); return g['features'] if g.get('type') == 'FeatureCollection' else [{'type': 'Feature', 'geometry': g.get('geometry', g), 'properties': {}}]
def target(p):
    """(the district's name, its features) or None"""
    s = p['slug']
    m = re.match(r'^(school|cec)-district-(\d+)$', s)
    if m and os.path.exists(P('data/districts/school-%s.geojson' % m.group(2))):
        return 'Community School District ' + m.group(2), geo_file(P('data/districts/school-%s.geojson' % m.group(2)))
    m = re.match(r'^(?:cbo-)?(\d+)(?:st|nd|rd|th)?-(?:police-)?precinct(?:$|-community-council(?:-board)?$)', s)
    if m and m.group(1) in PCT:
        n = m.group(1); suf = 'th' if n[-2:] in ('11', '12', '13') else {'1': 'st', '2': 'nd', '3': 'rd'}.get(n[-1], 'th')
        return '%s%s Precinct' % (n, suf), [{'type': 'Feature', 'geometry': PCT[n], 'properties': {}}]
    m = re.match(r'^(manhattan|bronx|brooklyn|queens|staten-island)-district-attorneys-office$', s)
    if m: return m.group(1).replace('-', ' ').title(), geo_file(P('data/districts/borough-%d.geojson' % BORO[m.group(1)]))
    if p.get('group') == 'Community boards' and p.get('cd') and os.path.exists(P('data/districts/cb-%s.geojson' % p['cd'])):
        return p['name'], geo_file(P('data/districts/cb-%s.geojson' % p['cd']))
    m = re.match(r'^nypd-sector-(\d+[a-z])$', s)
    if m and os.path.exists(P('data/districts/sector-%s.geojson' % m.group(1).upper())):
        return 'Sector ' + m.group(1).upper(), geo_file(P('data/districts/sector-%s.geojson' % m.group(1).upper()))
    m = re.match(r'^dsny-(brooklyn|manhattan|bronx|queens|staten-island)-(\d+)$', s)
    if m:
        pre = {'brooklyn': 'BK', 'manhattan': 'MN', 'bronx': 'BX', 'queens': 'Q', 'staten-island': 'SI'}[m.group(1)]
        secs = [x for x in DSNY if x['properties']['district'][:2] == pre[:2] and x['properties']['district'][-2:] == '%02d' % int(m.group(2))]
        if secs:
            from shapely.geometry import shape, mapping
            from shapely.ops import unary_union
            u = unary_union([shape(x['geometry']).buffer(0) for x in secs]).buffer(0.00005).buffer(-0.00005)
            return 'Sanitation district %s %s' % (m.group(1).replace('-', ' ').title(), m.group(2)), [{'type': 'Feature', 'geometry': mapping(u), 'properties': {}}]
    if p.get('kind') == 'official' and p.get('official') in OFF:
        o = OFF[p['official']]; c, n, sl = o.get('chamber'), o.get('district'), o['slug']
        if c and n and os.path.exists(P('data/districts/%s-%s.geojson' % (c, n))):
            return {'council': 'Council District %s', 'assembly': 'Assembly District %s', 'senate': 'State Senate District %s', 'congress': 'Congressional District NY-%s'}[c] % n, geo_file(P('data/districts/%s-%s.geojson' % (c, n)))
        bo = {'bronx': 2, 'brooklyn': 3, 'manhattan': 1, 'queens': 4, 'statenisland': 5}
        if sl.startswith('bp') and sl[2:] in bo:
            # the borough as its community boards, since the Borough President appoints their members
            d = bo[sl[2:]]
            cds = sorted(c for c in BOARDS if c[0] == str(d) and int(c[1:]) < 20 and os.path.exists(P('data/districts/cb-%s.geojson' % c)))
            fs = [x for c in cds for x in geo_file(P('data/districts/cb-%s.geojson' % c))]
            return (o.get('boro') or sl[2:].title()) + ' and its community boards', fs or geo_file(P('data/districts/borough-%d.geojson' % d))
        if sl.startswith('da') and o.get('boro'):
            k = o['boro'].lower().replace(' ', '')
            if k in bo: return o['boro'], geo_file(P('data/districts/borough-%d.geojson' % bo[k]))
        if sl in ('mayor', 'publicadvocate', 'comptroller'): return 'New York City', geo_file(P('data/districts/city-nyc.geojson'))
        if sl in ('governor', 'lieutenantgovernor', 'attorneygeneral', 'statecomptroller') or sl.startswith('ussen'): return 'New York State', geo_file(P('data/districts/state-ny.geojson'))
    if s in BID and os.path.exists(P('data/districts', BID[s] + '.geojson')):
        return p['name'], geo_file(P('data/districts', BID[s] + '.geojson'))
    return None
def logo_path(p):
    lg = p.get('logo') or ''
    if lg.startswith('../../icons/'): return 'civic/icons/' + lg.split('/')[-1]
    if lg and os.path.exists(P('app/data/civic/orgs/logos', lg)): return 'civic/orgs/logos/' + lg
    return ''
f = P('app/data/civic/orgs/orgs-profiles.json'); D = json.load(open(f, encoding='utf-8'))
nodes, offices = {}, []
for old in os.listdir(OUT):
    if old.endswith('.geojson'): os.remove(os.path.join(OUT, old))
for p in D['profiles']:
    p['kv'] = [kv for kv in p.get('kv', []) if kv[0] != 'District map']
    if 'District map' in (p.get('kvdest') or {}): p['kvdest'].pop('District map')
    t = target(p)
    if not t: continue
    dname, feats = t
    for x in feats: x['properties'] = {'slug': p['slug']}
    json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(OUT, p['slug'] + '.geojson'), 'w'), separators=(',', ':'))
    file = 'civic/districtmaps/%s.geojson' % p['slug']
    layers = [{'id': 'district', 'title': dname, 'on': True, 'file': file, 'stroke': '#06024d', 'width': 3, 'fill': '#f47920', 'fillOpacity': 0.12, 'chip': '#06024d'}]
    lp = logo_path(p)
    if p.get('lat') and p.get('lng'):
        offices.append({'slug': p['slug'], 'title': p['name'], 'sub': p.get('addr', ''), 'lat': p['lat'], 'lng': p['lng']})
        pin = {'style': 'image', 'image': lp, 'size': 34} if lp else {'style': 'dot', 'color': '#f47920', 'size': 12}
        layers.append({'id': 'office', 'title': 'The office', 'on': True, 'data': {'file': 'civic/districtmaps/offices.json', 'at': 'offices', 'where': {'slug': p['slug']}},
                       'pin': pin, 'chip': '#f47920', 'tap': {'type': 'v', 'spacing': 2, 'children': [
                           {'type': 'text', 'text': '{title}', 'size': 16, 'weight': 'bold', 'color': 'navy'}, {'type': 'text', 'text': '{sub}', 'size': 14, 'color': 'muted'}]}})
    nodes['dmap-' + p['slug']] = {'title': p['name'], 'type': 'v', 'spacing': 10, 'children': [
        {'type': 'text', 'text': '%s, its boundary on the map.' % dname, 'size': 14, 'color': 'muted'},
        {'type': 'map', 'height': 560, 'fit': 'district', 'toggles': True, 'legend': True, 'layers': layers}]}
    p['kv'].insert(0, ['District map', dname + ', on the map'])
    p.setdefault('kvdest', {})['District map'] = 'node:dmap-' + p['slug']
json.dump({'offices': offices}, open(os.path.join(OUT, 'offices.json'), 'w'), indent=1)
open(f, 'w', encoding='utf-8').write(json.dumps(D, ensure_ascii=False, indent=1) + '\n')
for app in ('cb6', 'bk', 'beyond'):
    sf = P('app/data/civic/ui', app, 'screens.json'); raw = open(sf, encoding='utf-8').read(); S = json.loads(raw)
    S['nodes'] = {k: v for k, v in S.get('nodes', {}).items() if not k.startswith('dmap-')}
    S['nodes'].update(nodes)
    ind = len(re.match(r'\{\n( *)', raw).group(1)) if raw.startswith('{\n') else None
    open(sf, 'w', encoding='utf-8').write(json.dumps(S, ensure_ascii=False, indent=ind) + ('\n' if raw.endswith('\n') else ''))
import collections
print('district maps:', len(nodes), collections.Counter(re.sub(r'\d+', 'N', k.split('-', 1)[1])[:30] for k in nodes).most_common())
