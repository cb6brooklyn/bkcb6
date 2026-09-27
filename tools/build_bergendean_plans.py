"""Adds plan layers to data/bergendean/layers.json:
- b65_draft: Atlantic Av (CSCL) from the B65's current western end to Washington Av, drawn from the MTA draft text
  "rerouted to travel on Atlantic Av in both directions between Downtown Brooklyn and Washington Av".
- b65_cut: the current B65 (MTA Bus Routes, bzwk-3hb4) on Dean/Bergen west of Washington Av, where the draft discontinues service.
- tr_changes: Brooklyn entries of NYC DOT's October 4, 2026 truck route changes (data/truck-routes/changes-2026-10-04.json)."""
import json, urllib.request, urllib.parse
from shapely.geometry import shape, mapping, box
from shapely.ops import unary_union, linemerge
NYC = 'https://data.cityofnewyork.us/resource/'
def cl(name):
    u = NYC + 'inkn-q76z.json?' + urllib.parse.urlencode({'$select': 'full_street_name,the_geom', '$where': f"full_street_name='{name}' AND boroughcode='3'", '$limit': 5000})
    return unary_union([shape(x['the_geom']) for x in json.load(urllib.request.urlopen(u, timeout=600))])
P = 'data/bergendean/layers.json'; L = json.load(open(P))
atl = cl('ATLANTIC AVE'); wash = cl('WASHINGTON AVE')
x = atl.intersection(wash); wlon = min(p.x for p in getattr(x, 'geoms', [x]))
u = 'https://data.ny.gov/resource/bzwk-3hb4.json?' + urllib.parse.urlencode({'$where': "route_short_name='B65' AND in_effect='true'", '$limit': 50})
R65 = json.load(urllib.request.urlopen(u, timeout=600))
g65 = unary_union([shape(r['geometry']) for r in R65]); west = g65.bounds[0]
L['b65_now'] = [{'dir': r['direction'], 'shape': r['shape_id'], 'desc': r['route_description'], 'geometry': json.loads(json.dumps(mapping(shape(r['geometry']))), parse_float=lambda s: round(float(s), 6))} for r in R65]
L['b65_query'] = u
draft = linemerge(atl.intersection(box(west, 40.6, wlon, 40.72)))
CG = json.load(open('data/bergendean/corridor.geojson'))
bd = unary_union([shape(f['geometry']) for f in CG['features'] if f['properties']['k'] in ('bergen', 'dean')]).buffer(0.00012)
cut = linemerge(g65.intersection(box(-74.1, 40.6, wlon, 40.72)).intersection(bd))
r = lambda g: json.loads(json.dumps(mapping(g.simplify(0.00003))), parse_float=lambda s: round(float(s), 6))
L['b65_draft'] = r(draft); L['b65_cut'] = r(cut); L['washington_lon'] = round(wlon, 6)
C = json.load(open('data/truck-routes/changes-2026-10-04.json'))
L['tr_changes'] = [{'kind': e['kind'], 'num': e['num'], 'text': e['text'], 'geometry': e['geometry']} for e in C['entries'] if e['boro'] == 'Brooklyn' and e.get('geometry')]
L['tr_changes_all'] = sum(1 for e in C['entries'] if e['boro'] == 'Brooklyn')
json.dump(L, open(P, 'w'), separators=(',', ':'))
print('b65 shapes', [(r['direction'], r['shape_id']) for r in R65]); print('wash lon', wlon, 'draft mi', round(draft.length * 52.5, 2), 'cut mi', round(cut.length * 52.5, 2), 'tr', len(L['tr_changes']), L['tr_changes_all'])
