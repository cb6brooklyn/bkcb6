#!/usr/bin/env python3
"""Build data/housing-loss.json for bkcb6.app/bk/allhousing/: what gets built
against what is lost, from the DCP Housing Database project-level files
(NYC Open Data br6q-ssj3), completed jobs counted by year completed.

  built  = new buildings + alterations that add units
  lost   = alterations that remove units + demolitions
  net    = built - lost (every completed job)

Grouped for New York City, each borough, each community district and each
council district, using the same SoQL queries the page links to.
"""
import json, os, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = "HvFoIfzodzpRML7a1104Ca2tM"
DONE = "job_status like '5%'"
KINDS = {
    "nb": "job_type='New Building'",
    "gain": "job_type='Alteration' AND classanet>0",
    "loss": "job_type='Alteration' AND classanet<0",
    "demo": "job_type='Demolition'",
}
BORO = {"1": "MN", "2": "BX", "3": "BK", "4": "QN", "5": "SI"}


def get(params):
    q = urllib.parse.urlencode(params)
    for a in range(5):
        try:
            req = urllib.request.Request("https://data.cityofnewyork.us/resource/br6q-ssj3.json?" + q, headers={"X-App-Token": TOKEN})
            return json.loads(urllib.request.urlopen(req, timeout=300).read())
        except Exception as e:
            print("retry", e, flush=True)
            time.sleep(5)
    raise SystemExit("failed")


version = get({"$select": "version", "$group": "version"})
version = ",".join(r["version"] for r in version)
valid_cd = set(json.load(open(os.path.join(ROOT, "data", "housing-db-cd.json")))["cd"].keys())
out = dict(version=version, built=time.strftime("%Y-%m-%d"), boro={}, cd={}, cc={})
ALL = {}


def add(target, key, kind, year, units):
    d = target.setdefault(key, {k: {} for k in KINDS})
    d[kind][year] = d[kind].get(year, 0) + abs(int(round(float(units))))


for kind, cond in KINDS.items():
    for r in get({"$select": "compltyear,sum(classanet) as units", "$where": DONE + " AND " + cond, "$group": "compltyear", "$limit": 5000}):
        if r.get("compltyear") and r.get("units"):
            add(ALL, "nyc", kind, int(r["compltyear"]), r["units"])
    for dim, bucket in [("boro", "boro"), ("commntydst", "cd"), ("councildst", "cc")]:
        rows = get({"$select": dim + ",compltyear,sum(classanet) as units", "$where": DONE + " AND " + cond, "$group": dim + ",compltyear", "$limit": 50000})
        for r in rows:
            v, y = r.get(dim), r.get("compltyear")
            if not v or not y or not r.get("units"):
                continue
            if bucket == "boro":
                if v not in BORO:
                    continue
                key = BORO[v]
            elif bucket == "cd":
                if len(v) != 3 or v[0] not in BORO:
                    continue
                key = BORO[v[0]] + "-" + v[1:]
                if key not in valid_cd:
                    continue
            else:
                if not v.isdigit() or not 1 <= int(v) <= 51:
                    continue
                key = str(int(v))
            add(out[bucket], key, kind, int(y), r["units"])
    print(kind, "done", flush=True)

out["nyc"] = ALL["nyc"]
path = os.path.join(ROOT, "data", "housing-loss.json")
json.dump(out, open(path, "w"), separators=(",", ":"))
tot = lambda d, k: sum(v for y, v in d[k].items() if 2010 <= y <= 2024)
n = out["nyc"]
print("version", version, "NYC 2010-2024 nb", tot(n, "nb"), "gain", tot(n, "gain"), "loss", tot(n, "loss"), "demo", tot(n, "demo"))
print("cd", len(out["cd"]), "cc", len(out["cc"]), "boro", len(out["boro"]))
b6 = out["cd"]["BK-06"]
print("BK-06", {k: tot(b6, k) for k in KINDS})
