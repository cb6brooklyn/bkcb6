#!/usr/bin/env python3
"""Current council members by district from NYC Open Data uvw5-9znb
(City Council Members, 1999 to Present): terms that started on or after
2026-01-01. Writes middlehousingstillmissing/bk/council-members.json."""
import json, os, time, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
q = {"$select": "district,name,term_start,term_end", "$where": "term_start>='2026-01-01'", "$order": "district", "$limit": 200}
req = urllib.request.Request("https://data.cityofnewyork.us/resource/uvw5-9znb.json?" + urllib.parse.urlencode(q), headers={"X-App-Token": "HvFoIfzodzpRML7a1104Ca2tM"})
rows = json.loads(urllib.request.urlopen(req, timeout=120).read())
by = {}
for r in rows:
    if r.get("district"):
        by.setdefault(str(int(r["district"])), []).append(r)
members = {k: dict(name=v[0]["name"], term_start=v[0]["term_start"][:10], term_end=(v[0].get("term_end") or "")[:10]) for k, v in by.items() if len(v) == 1}
dupes = {k: [x["name"] for x in v] for k, v in by.items() if len(v) > 1}
meta = json.loads(urllib.request.urlopen("https://data.cityofnewyork.us/api/views/uvw5-9znb.json", timeout=60).read())
out = dict(source="NYC Open Data uvw5-9znb, City Council Members (1999 to Present), terms starting 2026-01-01 or later", dataset="uvw5-9znb",
           updated=time.strftime("%Y-%m-%d", time.gmtime(meta["rowsUpdatedAt"])), retrieved=time.strftime("%Y-%m-%d"), members=members)
json.dump(out, open(os.path.join(ROOT, "middlehousingstillmissing", "bk", "council-members.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(len(members), "districts; more than one 2026 term (left out):", dupes, "dataset updated", out["updated"])
