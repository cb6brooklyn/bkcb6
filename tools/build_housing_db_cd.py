#!/usr/bin/env python3
"""Refresh data/housing-db-cd.json (All Housing Built and district pages) from
NYC DCP Housing Database by Community District, NYC Open Data dbdt-5s7j.
Keeps the 59 community districts and the file's existing shape; years 2010-2024."""
import json, os, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = "HvFoIfzodzpRML7a1104Ca2tM"
path = os.path.join(ROOT, "data", "housing-db-cd.json")
old = json.load(open(path))
for a in range(6):
    try:
        req = urllib.request.Request("https://data.cityofnewyork.us/resource/dbdt-5s7j.json?$limit=500&$select=commntydst,comp2010ap," + ",".join("comp%d" % y for y in range(2010, 2025)) + ",cenunits20,filed,approved,permitted,withdrawn,inactive", headers={"X-App-Token": TOKEN})
        rows = json.loads(urllib.request.urlopen(req, timeout=120).read())
        break
    except Exception as e:
        print("retry", e); time.sleep(15)
meta = json.loads(urllib.request.urlopen("https://data.cityofnewyork.us/api/views/dbdt-5s7j.json", timeout=60).read())
upd = time.strftime("%Y-%m-%d", time.gmtime(meta["rowsUpdatedAt"]))
B = {"1": ("MN", "Manhattan"), "2": ("BX", "Bronx"), "3": ("BK", "Brooklyn"), "4": ("QN", "Queens"), "5": ("SI", "Staten Island")}
n = lambda v: int(round(float(v or 0)))
cd = {}
for r in rows:
    c = r["commntydst"]
    key = B[c[0]][0] + "-" + c[1:]
    if key not in old["cd"]:
        continue
    comp = {str(y): n(r.get("comp%d" % y)) for y in range(2010, 2025)}
    cd[key] = dict(boro=B[c[0]][1], comp=comp, comp2010ap=n(r.get("comp2010ap")), total=sum(comp.values()), cen2020=n(r.get("cenunits20")),
                   filed=n(r.get("filed")), approved=n(r.get("approved")), permitted=n(r.get("permitted")), withdrawn=n(r.get("withdrawn")), inactive=n(r.get("inactive")))
assert len(cd) == len(old["cd"]), (len(cd), len(old["cd"]))
out = dict(old)
out["cd"] = cd
out["source"] = "NYC DCP Housing Database by Community District (NYC Open Data dbdt-5s7j), updated " + upd + ", retrieved " + time.strftime("%Y-%m-%d")
json.dump(out, open(path, "w"), separators=(",", ":"))
print(out["source"]); print("BK-06 total", cd["BK-06"]["total"], "NYC total", sum(v["total"] for v in cd.values()))
for k in sorted(cd):
    if cd[k]["total"] != old["cd"][k]["total"]:
        print(" changed", k, old["cd"][k]["total"], "->", cd[k]["total"])
