#!/usr/bin/env python3
"""The streets of every election district, from data/edstreets/<1-5>.json (scripts/build_ed_streets.py):
streets on its edge (one side of the block is in the ED and the other is not) and streets inside it (both sides in it).
Writes data/edstreets/ed-desc.json: {ED: [edge streets, inside streets]}, each list ordered by blocks of that street.
Run: python3 scripts/build_ed_desc.py
"""
import json, os
from collections import defaultdict, Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
edge = defaultdict(Counter); inside = defaultdict(Counter)
for b in '12345':
    d = json.load(open(os.path.join(ROOT, 'data/edstreets/%s.json' % b)))
    for name, rows in zip(d['streets'], d['blocks']):
        for r in rows:
            L, R = set(r[4][0][2]), set(r[4][1][2])
            for e in L | R:
                if e in L and e in R: inside[e][name] += 1
                else: edge[e][name] += 1
eds = [f['properties']['id'] for f in json.load(open(os.path.join(ROOT, 'electionexplainer/map/eds.geojson')))['features']]
out = {}
for e in eds:
    ed_ = [n for n, _ in edge[e].most_common()]
    in_ = [n for n, _ in inside[e].most_common() if n not in edge[e]]
    out[e] = [ed_, in_]
json.dump(out, open(os.path.join(ROOT, 'data/edstreets/ed-desc.json'), 'w'), separators=(',', ':'))
print(len(out), 'EDs;', sum(1 for v in out.values() if not v[0] and not v[1]), 'with no streets')
