"""Rows on the 24 blocks split between two boards (civic/blocks/sides.json) keep their street names, so the card can
still read the house number there and say which board that side of the street is in. Run after 4 and 5."""
import json
D='app/data/civic/blocks/'
sides=json.load(open(D+'sides.json'));geo={r[0]:r for r in json.load(open(D+'bk-geo.json'))}
for f in ['zb','zy','zw']:
    z=json.load(open(D+f+'-geo.json'));n=0
    for r in z:
        if r[0] in sides and r[6]=='' and r[0] in geo: r[6],r[7],r[8]=geo[r[0]][6],geo[r[0]][7],geo[r[0]][8];n+=1
    if n: json.dump(z,open(D+f+'-geo.json','w'),separators=(',',':'))
    print(f,n)
