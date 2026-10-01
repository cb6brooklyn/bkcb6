#!/usr/bin/env python3
"""data/truesum.json for bkcb6.app/truesum/: the true sum of housing built.

All from NYC Open Data, pulled the same day:
  br6q-ssj3  DCP Housing Database, project level (built, lost, net by year completed; jobs still
             filed, approved or permitted by year filed)
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
            print("retry", ds, e, getattr(e, "read", lambda: b"")()[:200], params, flush=True)
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
HDB_END = get("br6q-ssj3", {"$select": "max(datecomplt) as d"})[0]["d"][:10]
LAST_YEAR = int(HDB_END[:4])
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

# ---- pipeline: jobs not completed and not withdrawn, by status and year filed
ST = {"1": "f", "2": "a", "3": "p", "4": "p"}
for kind, cond in KINDS.items():
    for dim, pre in [(None, "nyc"), ("boro", "boro"), ("commntydst", "cd"), ("councildst", "cc")]:
        g = (dim + "," if dim else "") + "job_status"
        rows = get("br6q-ssj3", {"$select": g + ",date_extract_y(datefiled) as fy,sum(classanet) as units,count(*) as jobs", "$where": "job_status not like '5%' AND job_status not like '9%' AND " + cond,
                                 "$group": g + ",fy", "$limit": 50000})
        for r in rows:
            if not r.get("units") or not r.get("job_status"):
                continue
            if dim:
                v = r.get(dim)
                if not v or (dim == "boro" and v not in "12345") or (dim == "commntydst" and v not in VALID_CD):
                    continue
                key = pre + ":" + (str(int(v)) if dim == "councildst" else v)
            else:
                key = "nyc"
            st = ST[r["job_status"][0]]
            d = sc(key)["pipe"].setdefault(kind, {}).setdefault(st, {})
            fy = r.get("fy") or "?"
            d[fy] = d.get(fy, 0) + abs(n(r["units"]))
    print("pipe", kind, flush=True)

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
                             "$where": "building_completion_date <= '" + HDB_END + "T23:59:59'", "$group": g + "reporting_construction_type,y", "$limit": 50000})
    for r in rows:
        k = hkey(dim, r.get(dim) if dim else None)
        if not k or not r.get("y"):
            continue
        t = "nc" if r["reporting_construction_type"] == "New Construction" else "pres"
        d = sc(k)["hpd"][t]
        d[r["y"]] = d.get(r["y"], 0) + n(r.get("u"))
    rows = get("hg8x-zxpr", {"$select": g + ",".join("sum(%s) as %s" % (c, c) for c in INC + BED),
                             "$where": "building_completion_date between '2014-01-01T00:00:00' and '" + HDB_END + "T23:59:59' AND reporting_construction_type='New Construction'",
                             **({"$group": dim} if dim else {}), "$limit": 50000})
    for r in rows:
        k = hkey(dim, r.get(dim) if dim else None)
        if not k:
            continue
        sc(k)["hpd"]["inc"] = {c: n(r.get(c)) for c in INC}
        sc(k)["hpd"]["bed"] = {c: n(r.get(c)) for c in BED}
    rows = get("hg8x-zxpr", {"$select": g + "reporting_construction_type,sum(all_counted_units) as u", "$where": "building_completion_date IS NULL OR building_completion_date > '" + HDB_END + "T23:59:59'",
                             "$group": g + "reporting_construction_type", "$limit": 50000})
    for r in rows:
        k = hkey(dim, r.get(dim) if dim else None)
        if not k:
            continue
        sc(k)["hpd"]["prog"]["nc" if r["reporting_construction_type"] == "New Construction" else "pres"] = n(r.get("u"))
    print("hpd", dim, flush=True)

out = dict(built=time.strftime("%Y-%m-%d"), hdb_version=hdb_version, hdb_end=HDB_END, last_year=LAST_YEAR,
           updated={d: meta(d) for d in ("br6q-ssj3", "hg8x-zxpr")}, s=S)
json.dump(out, open(os.path.join(ROOT, "data", "truesum.json"), "w"), separators=(",", ":"))
tot = lambda d, a, b: sum(v for y, v in d.items() if y.isdigit() and a <= int(y) <= b)
for k in ("nyc", "boro:3", "cd:306", "cc:39"):
    h = S[k]["hdb"]; Y = LAST_YEAR; bu = tot(h["nb"], 2010, Y) + tot(h["gain"], 2010, Y); lo = tot(h["loss"], 2010, Y) + tot(h["demo"], 2010, Y)
    pp = {kd: {st: sum(v.values()) for st, v in d.items()} for kd, d in S[k]["pipe"].items()}
    print(k, "built", bu, "lost", lo, "net", bu - lo, "pipe", pp, "hpd nc", tot(S[k]["hpd"]["nc"], 2014, Y), "prog", S[k]["hpd"]["prog"])
print("scopes", len(S), HDB_END, out["updated"])
