#!/usr/bin/env python3
"""data/fasttrack.json for bkcb6.app/fasttrack/: the Affordable Housing Fast Track, 2021-2026 cycle.

Sources (NYC Department of City Planning, released October 1, 2026):
  AHFT CD Summary, 2021-2026 cycle (every community district: 2020 Census units, net new units
    4/1/20 to 6/30/21, denominator, new affordable units, rate, rank)
  AHFT Affordable Projects, 2021-2026 cycle (every HPD project/building counted, with start date,
    DOB job, permit date, district, rank and units)
Each project is matched by HPD project and building ID to NYC Open Data hg8x-zxpr
(HPD Affordable Housing Production by Building) for its address and location.
"""
import io, json, os, time, urllib.parse, urllib.request
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = "HvFoIfzodzpRML7a1104Ca2tM"
BASE = "https://s-media.nyc.gov/agencies/dcp/assets/files/excel/data-tools/bytes/ahft/"
F_SUM = "Affordable-Housing-Fast-Track-Community-District-Summary-2021-2026-Cycle.xlsx"
F_PRJ = "Affordable-Housing-Fast-Track-Affordable-Projects-2021-2026-Cycle.xlsx"


def dl(name):
    return io.BytesIO(urllib.request.urlopen(BASE + name, timeout=120).read())


def soda(params):
    q = urllib.parse.urlencode(params)
    for a in range(6):
        try:
            req = urllib.request.Request("https://data.cityofnewyork.us/resource/hg8x-zxpr.json?" + q, headers={"X-App-Token": TOKEN})
            return json.loads(urllib.request.urlopen(req, timeout=180).read())
        except Exception as e:
            print("retry", e, flush=True)
            time.sleep(5 + 5 * a)
    raise SystemExit("hg8x failed")


s = pd.read_excel(dl(F_SUM))
s.columns = ["cd", "cen", "net", "den", "num", "rate", "rank"]
p = pd.read_excel(dl(F_PRJ))
p.columns = ["id", "start", "job", "permit", "cd", "rank", "units"]

B = {"BK": "3", "BX": "2", "MN": "1", "QN": "4", "SI": "5"}
code = lambda c: B[c[:2]] + c[2:]
dist = [dict(cd=r.cd, code=code(r.cd), cen=int(r.cen), net=int(r.net), den=int(r.den), num=int(r.num), rate=float(r.rate), rank=int(r["rank"])) for _, r in s.iterrows()]

# addresses from HPD by building ID
bids = sorted({str(x).split("/")[1] for x in p.id})
addr = {}
for i in range(0, len(bids), 150):
    chunk = bids[i:i + 150]
    rows = soda({"$select": "project_id,building_id,project_name,house_number,street_name,latitude,longitude,building_completion_date",
                 "$where": "building_id in(" + ",".join(chunk) + ")", "$limit": 5000})
    for r in rows:
        addr[r["project_id"] + "/" + r["building_id"]] = r
print("hpd matched", len(addr), "of", len(p), flush=True)


def d(v):
    return None if pd.isna(v) else str(v)[:10]


prj = []
for _, r in p.iterrows():
    a = addr.get(str(r.id), {})
    prj.append([str(r.id), d(r.start), str(r.job), d(r.permit), r.cd, int(r.units),
                ((a.get("house_number") or "") + " " + (a.get("street_name") or "")).strip() or None,
                a.get("project_name"), float(a["latitude"]) if a.get("latitude") else None, float(a["longitude"]) if a.get("longitude") else None,
                (a.get("building_completion_date") or "")[:10] or None])

out = dict(built=time.strftime("%Y-%m-%d"), cycle="July 1, 2021 to June 30, 2026", released="2026-10-01",
           files=dict(summary=BASE + F_SUM, projects=BASE + F_PRJ), dist=dist,
           pf=["id", "start", "job", "permit", "cd", "units", "addr", "name", "lat", "lon", "done"], p=prj)
json.dump(out, open(os.path.join(ROOT, "data", "fasttrack.json"), "w"), separators=(",", ":"))
print("districts", len(dist), "projects", len(prj), "units", sum(x[5] for x in prj), "fast track units", sum(x["num"] for x in dist if x["rank"] <= 12),
      "geocoded", sum(1 for x in prj if x[8] is not None))
