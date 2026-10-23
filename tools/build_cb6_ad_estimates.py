#!/usr/bin/env python3
"""BKCB6 results for 2000 to 2013, estimated from Assembly district results.

The Board of Elections published those years only by Assembly district. CB6 lies across parts of ADs 44, 51, 52
and 57 (lines of 1992, 2002 and 2012). For each AD piece inside CB6 the estimate takes the AD's vote for each
candidate times the share of the AD's residents who live in CB6 (2020 census blocks, data/districthistory/overlap.json).

Writes
  data/cbhistory/ed306/ad_<release>.json   AD pieces clipped to CB6, with each piece's share (f) of its AD
  data/cbhistory/ed306/elections.json      the 2000 to 2013 elections added in front of the ED-level ones, r = ad_<release>
  data/cbhistory/ed306/index.json          the AD releases added
Run from the repo root: python3 tools/build_cb6_ad_estimates.py
"""
import json, os, collections
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CB = '306'
OUT = os.path.join(ROOT, 'data', 'cbhistory', 'ed306')

# which overlap row (election year of the lines) goes with which AD geometry release
ERA = {'Census 2000 sl36': ('census2000sl36', 2000), '06cav': ('06cav', 2002), '08cav': ('08cav', 2008), '10cav': ('08cav', 2010), '12c': ('12c', 2012)}  # 10cav lines are the 08cav lines (same file)


def topo_to_features(path):
    t = json.load(open(path))
    sc, tr = t['transform']['scale'], t['transform']['translate']
    arcs = []
    for a in t['arcs']:
        x = y = 0; pts = []
        for dx, dy in a:
            x += dx; y += dy
            pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
        arcs.append(pts)
    def ring(idx):
        out = []
        for i in idx:
            pts = arcs[i] if i >= 0 else arcs[~i][::-1]
            if out and out[-1] == pts[0]:
                out.extend(pts[1:])
            else:
                out.extend(pts)
        return out
    feats = []
    for name, obj in t['objects'].items():
        for g in obj['geometries']:
            if g['type'] == 'Polygon':
                geom = Polygon(ring(g['arcs'][0]), [ring(h) for h in g['arcs'][1:]])
            elif g['type'] == 'MultiPolygon':
                geom = MultiPolygon([Polygon(ring(p[0]), [ring(h) for h in p[1:]]) for p in g['arcs']])
            else:
                continue
            feats.append((g.get('properties', {}), geom.buffer(0)))
    return feats


def main():
    ov = json.load(open(os.path.join(ROOT, 'data/districthistory/overlap.json')))
    rows = [x for x in ov['offices'] if x['key'] == 'assembly'][0]['rows']
    byyear = {r['election']: r for r in rows}
    cbgeo = json.load(open(os.path.join(ROOT, 'data/cb6vote/boundary.geojson')))
    cb = unary_union([shape(f['geometry']) for f in cbgeo['features']]).buffer(0)

    shares = {}   # release -> {ad: (f, residents_in_cb6, ad_residents)}
    for key, (rel, yr) in ERA.items():
        if rel in shares:
            continue
        row = byyear[yr]
        adpop = collections.defaultdict(int)
        for b, lst in row['cbs'].items():
            for d, sh, res in lst:
                adpop[d] += res
        mine = {d: (res / adpop[d], res, adpop[d]) for d, sh, res in row['cbs'][CB]}
        shares[rel] = mine
        print(rel, 'AD shares of residents in CB6:', {d: round(v[0], 3) for d, v in mine.items()})

    index = json.load(open(os.path.join(OUT, 'index.json')))
    index = [x for x in index if not str(x['r']).startswith('ad_')]
    done = set()
    for key, (rel, yr) in ERA.items():
        if rel in done:
            continue
        done.add(rel)
        feats = topo_to_features(os.path.join(ROOT, 'data/districthistory/geo/assembly_%s.topo.json' % rel))
        out = []
        for props, geom in feats:
            d = int(props['d'])
            if d not in shares[rel]:
                continue
            piece = geom.intersection(cb)
            if piece.is_empty:
                continue
            if piece.geom_type == 'GeometryCollection':
                piece = unary_union([g for g in piece.geoms if g.geom_type in ('Polygon', 'MultiPolygon')])
            f, res, tot = shares[rel][d]
            out.append({'type': 'Feature', 'properties': {'e': 'A%02d' % d, 'ad': d, 'f': round(f, 4), 'res': res, 'adres': tot, 'est': 1},
                        'geometry': mapping(piece.simplify(0.00002, preserve_topology=True))})
        fc = {'type': 'FeatureCollection', 'release': 'ad_' + rel, 'date': {'census2000sl36': '2000-01-01', '06cav': '2002-01-01', '08cav': '2008-01-01', '12c': '2012-01-01'}[rel],
              'estimate': 'Assembly district results, each AD piece weighted by the share of its residents (2020 census blocks) who live in BKCB6', 'features': out}
        json.dump(fc, open(os.path.join(OUT, 'ad_%s.json' % rel), 'w'), separators=(',', ':'))
        index.append({'r': 'ad_' + rel, 'date': fc['date'], 'n': len(out), 'label': 'Assembly districts (%s lines), estimated' % {'census2000sl36': '1992', '06cav': '2002', '08cav': '2002', '12c': '2012'}[rel], 'est': 1})
        print('ad_' + rel, len(out), 'pieces', [o['properties']['e'] for o in out])
    index.sort(key=lambda x: x['date'])
    json.dump(index, open(os.path.join(OUT, 'index.json'), 'w'), separators=(',', ':'))

    # elections: AD-level ones from the catalog, with the contests that drew votes in the CB6 Assembly districts
    cat = json.load(open(os.path.join(ROOT, 'data/edhistory/catalog.json')))
    els = json.load(open(os.path.join(OUT, 'elections.json')))
    els = [e for e in els if not str(e.get('r', '')).startswith('ad_')]
    have = set(e['id'] for e in els)
    added = []
    for el in cat['elections']:
        d = os.path.join(ROOT, 'data/edhistory/e', el['id'])
        ix = json.load(open(os.path.join(d, 'index.json')))
        if ix.get('level') != 'ad' or el['id'] in have:
            continue
        rel = ERA.get(ix.get('adRelease'), (None,))[0]
        if not rel:
            print('no era for', el['id'], ix.get('adRelease')); continue
        ads = set(shares[rel].keys())
        contests = []
        for c in ix['contests']:
            f = os.path.join(d, '%s.json' % c['id'])
            if not os.path.exists(f):
                continue
            x = json.load(open(f))
            if any(str(a) in map(str, ads) and (x['ads'].get(str(a)) or [0])[0] for a in ads):
                contests.append({'id': c['id'], 't': x.get('title') or c.get('title'), 'p': x.get('party') or '', 'rcv': bool(x.get('rcv'))})
        if contests:
            added.append({'id': el['id'], 'date': el['date'], 'label': el.get('label') or el['type'], 'r': 'ad_' + rel, 'est': 1, 'contests': contests})
    els = added + els
    els.sort(key=lambda e: e['date'])
    json.dump(els, open(os.path.join(OUT, 'elections.json'), 'w'), separators=(',', ':'))
    print(len(added), 'elections added (estimated);', len(els), 'in all;', els[0]['id'], 'to', els[-1]['id'])


if __name__ == '__main__':
    main()
