#!/usr/bin/env python3
"""Each block card's "nearpark": the closest real park to the block, measured to the park's edge, as the line the apps'
Your block card shows ("Prospect Park, about 6 minutes on foot"). Traffic triangles, plazas, strips, malls, parkway
medians and other non-park property types are left out. Parks come from app/data/civic/parks-nyc.json. Written into
every app/data/civic/blocks/<cd>.json.gz; the card shows it as the row {"id": "field:nearpark"} (lists.json
"MyBlock.rows"). Re-run whenever the parks file changes."""
import json, gzip, glob, os, math
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOT_PARKS = {'Undeveloped', 'Strip', 'Triangle/Plaza', 'Mall', 'Parkway', 'Lot', 'Operations', 'Buildings/Institutions', 'Managed Sites', 'Cemetery', 'Retired N/A'}
KY = 111320.0
def kx(lat): return 111320.0 * math.cos(math.radians(lat))
parks = [p for p in json.load(open(os.path.join(ROOT, 'app/data/civic/parks-nyc.json')))['parks'] if p['t'] not in NOT_PARKS and any(p['r'])]
BOX = np.array([[min(c[0] for r in p['r'] for c in r), min(c[1] for r in p['r'] for c in r), max(c[0] for r in p['r'] for c in r), max(c[1] for r in p['r'] for c in r)] for p in parks])
def inside(ring, lo, la):
    hit = False; j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]; xj, yj = ring[j]
        if (yi > la) != (yj > la) and lo < (xj - xi) * (la - yi) / (yj - yi) + xi: hit = not hit
        j = i
    return hit
def dist(p, lo, la, k):
    best = 1e12
    for ring in p['r']:
        if len(ring) > 2 and inside(ring, lo, la): return 0.0
        for a, b in zip(ring, ring[1:]):
            ax, ay = (a[0] - lo) * k, (a[1] - la) * KY; bx, by = (b[0] - lo) * k, (b[1] - la) * KY
            dx, dy = bx - ax, by - ay; l2 = dx * dx + dy * dy
            t = max(0.0, min(1.0, -(ax * dx + ay * dy) / l2)) if l2 else 0.0
            d = math.hypot(ax + t * dx, ay + t * dy)
            if d < best: best = d
    return best
def nearest(la, lo):
    k = kx(la)
    dx = np.maximum(0, np.maximum(BOX[:, 0] - lo, lo - BOX[:, 2])) * k
    dy = np.maximum(0, np.maximum(BOX[:, 1] - la, la - BOX[:, 3])) * KY
    lb = np.hypot(dx, dy); best = (1e12, None)
    for i in np.argsort(lb):
        if lb[i] >= best[0] or lb[i] > 3000: break
        d = dist(parks[i], lo, la, k)
        if d < best[0]: best = (d, parks[i]['n'])
    return best
def main():
    n = 0
    for f in sorted(glob.glob(os.path.join(ROOT, 'app/data/civic/blocks/*.json.gz'))):
        if not os.path.basename(f)[:3].isdigit(): continue
        d = json.load(gzip.open(f)); ch = False
        for b in d['blocks'].values():
            m = b.get('mid')
            if not m: continue
            dd, name = nearest(m[0], m[1])
            line = ''
            if name and dd < 3000:
                mins = max(1, int(round(dd / 80)))
                line = '%s, about %d minute%s on foot' % (name, mins, '' if mins == 1 else 's')
            if line and b.get('nearpark') != line: b['nearpark'] = line; ch = True; n += 1
            elif not line and 'nearpark' in b: del b['nearpark']; ch = True
        if ch:
            with gzip.open(f, 'wt', encoding='utf-8') as out: json.dump(d, out, ensure_ascii=False, separators=(',', ':'))
    print('blocks updated', n)
if __name__ == '__main__': main()
