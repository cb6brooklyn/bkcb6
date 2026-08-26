#!/usr/bin/env python3
"""Build boundary overlays for the Landmarks Permits map.

Two layers per community district:
  the district outline itself, from the DCP Community Districts file
  every current historic district that overlaps it, from LPC's own ArcGIS
  service (services5.arcgis.com/Oos4pNA2538iVFA1, Historic_Districts_LPC)

The LPC service is used rather than the NYC Open Data Historic Districts
dataset because Open Data carries 141 districts and is missing Park Slope
Historic District Extension (LP-02443, 2012) and Park Slope Historic District
Extension II (LP-02558, 2016). The LPC service carries 159 and has both.

Each historic district gets a label point placed inside its own polygon using
representative_point, so labels never float outside the shape they name.
"""
import json, os, datetime
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

OUT = '/home/claude/out/assets/lpc'
os.makedirs(OUT, exist_ok=True)
BORO = {'1': 'MN', '2': 'BX', '3': 'BK', '4': 'QN', '5': 'SI'}

hd = json.load(open('/home/claude/hd.geojson'))
cds = json.load(open('/mnt/user-data/uploads/Community_Districts_20260826.geojson'))

hds = []
for f in hd['features']:
    if not f.get('geometry'):
        continue
    g = shape(f['geometry'])
    if not g.is_valid:
        g = g.buffer(0)
    if g.is_empty:
        continue
    p = f['properties']
    d = p.get('DESIG_DATE')
    year = ''
    if d:
        year = str(datetime.datetime.utcfromtimestamp(d / 1000).year)
    hds.append({'g': g, 'name': p['AREA_NAME'], 'lp': p['LP_NUMBER'],
                'year': year, 'ext': p.get('EXTENSION') == 'Yes'})
print(f'{len(hds)} current historic districts')


def simp(g, tol):
    s = g.simplify(tol, preserve_topology=True)
    return s if not s.is_empty else g


def round_geom(gj, nd=6):
    def r(c):
        if isinstance(c, (list, tuple)):
            if c and isinstance(c[0], (int, float)):
                return [round(c[0], nd), round(c[1], nd)]
            return [r(x) for x in c]
        return c
    gj['coordinates'] = r(gj['coordinates'])
    return gj


written = 0
for f in cds['features']:
    code = f['properties']['boro_cd']
    cd = f'{BORO[code[0]]}-{code[1:]}'
    if not os.path.exists(f'{OUT}/{cd.lower()}.json'):
        continue
    cg = shape(f['geometry'])
    if not cg.is_valid:
        cg = cg.buffer(0)

    dists = []
    for h in hds:
        if not h['g'].intersects(cg):
            continue
        inter = h['g'].intersection(cg)
        if inter.is_empty or inter.area < 0.02 * h['g'].area:
            continue
        # Clip to the district so a shape straddling a boundary does not
        # sprawl across the map, but label from the clipped piece.
        clipped = simp(inter, 0.000015)
        lp = clipped.representative_point()
        dists.append({
            'name': h['name'], 'lp_number': h['lp'], 'year': h['year'],
            'extension': h['ext'],
            'share': round(inter.area / h['g'].area, 4),
            'label': [round(lp.y, 6), round(lp.x, 6)],
            'geometry': round_geom(mapping(clipped)),
        })
    dists.sort(key=lambda d: -d['share'])

    outline = simp(cg, 0.00002)
    olp = outline.representative_point()
    json.dump({
        'cd': cd,
        'outline': round_geom(mapping(outline)),
        'labelPoint': [round(olp.y, 6), round(olp.x, 6)],
        'historicDistricts': dists,
        'source': ('Community district outline from the Department of City Planning. '
                   'Historic district boundaries from the Landmarks Preservation '
                   'Commission, Historic_Districts_LPC feature service.'),
        'note': ('LPC publishes 159 current historic districts here. The NYC Open Data '
                 'Historic Districts dataset carries 141 and is missing both Park Slope '
                 'extensions, so it is not used.'),
    }, open(f'{OUT}/{cd.lower()}-bounds.json', 'w'), separators=(',', ':'))
    written += 1

print(f'{written} boundary files')
tot = sum(os.path.getsize(f'{OUT}/{f}') for f in os.listdir(OUT) if f.endswith('-bounds.json'))
print(f'{tot/1e6:.2f} MB total')
b6 = json.load(open(f'{OUT}/bk-06-bounds.json'))
print('\nCB6 historic districts:')
for d in b6['historicDistricts']:
    print(f"  {d['name']:46s} {d['lp_number']}  {d['year']}  {100*d['share']:5.1f}% inside")
print('bk-06-bounds.json', round(os.path.getsize(f'{OUT}/bk-06-bounds.json') / 1024), 'KB')
