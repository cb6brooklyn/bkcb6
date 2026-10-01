#!/usr/bin/env python3
"""data/truesum.json for bkcb6.app/truesum/: the true sum of housing built.

All from NYC Open Data, pulled the same day:
  br6q-ssj3  DCP Housing Database, project level (built, lost, net, by year completed)
  dbdt-5s7j  DCP Housing Database by Community District (pipeline: filed, approved, permitted)
  szq8-b4uy  DCP Housing Database by 2024 City Council district (pipeline)
  hg8x-zxpr  HPD Affordable Housing Production by Building (income-restricted units)
Scopes: nyc, boro:1-5, cd:<3-digit district>, cc:<council district>. Every figure
is built from grouped SoQL queries that the page links to.
"""
import json, os, time, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = "HvFoIfzodzpRML7a1104Ca2tM"


def get(ds, params):
    q = urllib.parse.urlencode(params)
    for a in range(8):
        try:
            req = urllib.request.Request(f"https://data.cityofnewyork.us/resource/{ds}.json?" + q, headers={"X-App-Token": TOKEN})
            return json.loads(urllib.request.urlopen(req, timeout=300).read())
        except Exception as e:
            print("retry", ds, e, flush=True)
            time.sleep(5 + 5 * a)
    raise SystemExit("failed " + ds)


def meta(ds):
    m = json.loads(urllib.request.urlopen(f"https://data.cityofnewyork.us/api/views/{ds}.json", timeout=60).read())
    return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(m["rowsUpdatedAt"]))


n = lambda v: int(round(float(v or 0)))
S = {}
sc = lambda k: S.setdefault(k, {"hdb": {t: {} for t in ("nb", "gain", "loss", "demo")}, "pipe": {}, "hpd": {"nc": {}, "pres": {}, "inc": {}, "bed": {}, "prog": {}}})
VALID_CD = {b + "%02d" % i for b, m in [("1", 12), ("2", 12), ("3", 18), ("4", 14), ("5", 3)] for i in range(1, m + 1)}

# ---- Housing Database, completed jobs by year
DONE = "job_status like '5%'"
KINDS = {"nb": "job_type='New Building'", "gain": "job_type='Alteration' AND classanet>0", "loss": "job_type='Alteration' AND classanet<0", "demo": "job_type='Demolition'"}
hdb_version = ",".join(r["version"] for r in get("br6q-ssj3", {"$select": "version", "$group": "version"}))
for kind, cond in KINDS.items():
    for dim, pre in [(None, "nyc"), ("boro", "boro"), ("commntydst", "cd"), ("councildst", "cc")]:
        sel = (dim + "," if dim else "") + "compltyear,sum(classanet) as units"
        rows = get("br6q-ssj3", {"$select": sel, "$where": DONE + " AND " + cond, "$group": (dim + "," if dim else "") + "compltyear", "$limit": 50000})
        for r in rows:
            if not r.get("compltyear") or not r.get("units"):
                continue
            if dim:
                v = r.get(dim)
                if not v:
                    continue
                if dim == "boro" and v not in "12345":
                    continue
                if dim == "commntydst" and v not in VALID_CD:
                    continue
                if dim == "councildst":
                    v = str(int(v))
                key = pre + ":" + v
            else:
                key = "nyc"
            d = sc(key)["hdb"][kind]
            y = r["compltyear"]
            d[y] = d.get(y, 0) + abs(n(r["units"]))
    print("hdb", kind, flush=True)

# ---- pipeline
for ds, field, pre in [("dbdt-5s7j", "commntydst", "cd"), ("szq8-b4uy", "councildst", "cc")]:
    rows = get(ds, {"$select": field + ",filed,approved,permitted", "$limit": 500})
    for r in rows:
        v = r.get(field)
        if not v:
            continue
        p = {k: n(r.get(k)) for k in ("filed", "approved", "permitted")}
        if pre == "cd":
            if v in VALID_CD:
                sc("cd:" + v)["pipe"] = p
            for key in ("boro:" + v[0], "nyc"):
                q = sc(key)["pipe"]
                for k in p:
                    q[k] = q.get(k, 0) + p[k]
        else:
            sc("cc:" + str(int(v)))["pipe"] = p
print("pipeline", flush=True)

# ---- HPD
BORO = {"Manhattan": "1", "Bronx": "2", "Brooklyn": "3", "Queens": "4", "Staten Island": "5"}
CBMAP = {"MN": "1", "BX": "2", "BK": "3", "QN": "4", "SI": "5"}
INC = ["extremely_low_income_units", "very_low_income_units", "low_income_units", "moderate_income_units", "middle_income_units", "other_income_units"]
BED = ["studio_units", "_1_br_units", "_2_br_units", "_3_br_units", "_4_br_units", "_5_br_units", "_6_br_units", "unknown_br_units"]


def hkey(dim, v):
    if dim is None:
        return "nyc"
    if not v:
        return None
    if dim == "borough":
        return "boro:" + BORO[v] if v in BORO else None
    if dim == "community_board":
        c = CBMAP.get(v[:2], "") + v[3:]
        return "cd:" + c if c in VALID_CD else None
    return "cc:" + str(int(v)) if v.isdigit() else None


for dim in (None, "borough", "community_board", "council_district"):
    g = (dim + "," if dim else "")
    rows = get("hg8x-zxpr", {"$select": g + "reporting_construction_type,date_extract_y(building_completion_date) as y,sum(all_counted_units) as u",
                             "$where": "building_completion_date IS NOT NULL", "$group": g + "reporting_construction_type,y", "$limit": 50000})
    for r in rows:
        k = hkey(dim, r.get(dim) if dim else None)
        if not k or not r.get("y"):
            continue
        t = "nc" if r["reporting_construction_type"] == "New Construction" else "pres"
        d = sc(k)["hpd"][t]
        d[r["y"]] = d.get(r["y"], 0) + n(r.get("u"))
    rows = get("hg8x-zxpr", {"$select": g + ",".join("sum(%s) as %s" % (c, c) for c in INC + BED),
                             "$where": "building_completion_date between '2014-01-01T00:00:00' and '2024-12-31T23:59:59' AND reporting_construction_type='New Construction'",
                             **({"$group": dim} if dim else {}), "$limit": 50000})
    for r in rows:
        k = hkey(dim, r.get(dim) if dim else None)
        if not k:
            continue
        sc(k)["hpd"]["inc"] = {c: n(r.get(c)) for c in INC}
        sc(k)["hpd"]["bed"] = {c: n(r.get(c)) for c in BED}
    rows = get("hg8x-zxpr", {"$select": g + "reporting_construction_type,sum(all_counted_units) as u", "$where": "building_completion_date IS NULL",
                             "$group": g + "reporting_construction_type", "$limit": 50000})
    for r in rows:
        k = hkey(dim, r.get(dim) if dim else None)
        if not k:
            continue
        sc(k)["hpd"]["prog"]["nc" if r["reporting_construction_type"] == "New Construction" else "pres"] = n(r.get("u"))
    print("hpd", dim, flush=True)

out = dict(built=time.strftime("%Y-%m-%d"), hdb_version=hdb_version,
           updated={d: meta(d) for d in ("br6q-ssj3", "dbdt-5s7j", "szq8-b4uy", "hg8x-zxpr")}, s=S)
json.dump(out, open(os.path.join(ROOT, "data", "truesum.json"), "w"), separators=(",", ":"))
tot = lambda d, a, b: sum(v for y, v in d.items() if a <= int(y) <= b)
for k in ("nyc", "boro:3", "cd:306", "cc:39"):
    h = S[k]["hdb"]; bu = tot(h["nb"], 2010, 2024) + tot(h["gain"], 2010, 2024); lo = tot(h["loss"], 2010, 2024) + tot(h["demo"], 2010, 2024)
    print(k, "built", bu, "lost", lo, "net", bu - lo, "pipe", S[k]["pipe"], "hpd nc 14-24", tot(S[k]["hpd"]["nc"], 2014, 2024), "pres", tot(S[k]["hpd"]["pres"], 2014, 2024), "prog", S[k]["hpd"]["prog"])
print("scopes", len(S), out["updated"])
