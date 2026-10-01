#!/usr/bin/env python3
"""Adds completions through the latest Housing Database record, and pending losses, to
middlehousingstillmissing/data.json. Run by build_middlehousing.py at the end, or alone.

All from NYC Open Data br6q-ssj3 (DCP Housing Database, project level), with the same
where clauses the page links:
  *_now        completed 2010 (or 2020) through the latest completion year
  loss_pending alterations that remove units, filed, approved or permitted, not completed or withdrawn
Scopes match the page: cd -> commntydst, Brooklyn -> boro='3', council -> boro='3' AND councildst,
boroughs -> boro, NYC -> boro in('1','2','3','4','5').
"""
import json, os, re, time, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = "HvFoIfzodzpRML7a1104Ca2tM"
LOSS = "job_type='Alteration' AND classanet<0"
DONE = "job_status like '5%'"
PEND = "job_status not like '5%' AND job_status not like '9%'"


def get(params):
    q = urllib.parse.urlencode(params)
    for a in range(8):
        try:
            req = urllib.request.Request("https://data.cityofnewyork.us/resource/br6q-ssj3.json?" + q, headers={"X-App-Token": TOKEN})
            return json.loads(urllib.request.urlopen(req, timeout=300).read())
        except Exception as e:
            print("retry", e, flush=True)
            time.sleep(5 + 5 * a)
    raise SystemExit("failed")


def grouped(where, field):
    rows = get({"$select": field + ",sum(classanet) as units,count(*) as jobs", "$where": where, "$group": field, "$limit": 5000})
    return {r.get(field): (abs(int(round(float(r.get("units") or 0)))), int(r["jobs"])) for r in rows}


def total(where):
    r = get({"$select": "sum(classanet) as units,count(*) as jobs", "$where": where})[0]
    return abs(int(round(float(r.get("units") or 0)))), int(r["jobs"])


def add_now(out):
    end = get({"$select": "max(datecomplt) as d"})[0]["d"][:10]
    Y = int(end[:4])
    rng = lambda a: DONE + " AND compltyear between '%d' and '%d'" % (a, Y)
    conds = dict(loss_now=LOSS + " AND " + rng(2010), loss_20_now=LOSS + " AND " + rng(2020),
                 loss_to_one_now=LOSS + " AND classaprop=1 AND " + rng(2010), loss_pending=LOSS + " AND " + PEND)

    def put(d, key, v):
        d[key] = v[0]
        d[key.replace("loss", "loss_jobs", 1) if key != "loss_to_one_now" else "loss_to_one_jobs_now"] = v[1]

    by_cd, by_cc, by_bo, nyc, bk = {}, {}, {}, {}, {}
    for key, c in conds.items():
        by_cd[key] = grouped(c, "commntydst")
        by_cc[key] = grouped("boro='3' AND " + c, "councildst")
        by_bo[key] = grouped(c, "boro")
        nyc[key] = total("boro in('1','2','3','4','5') AND " + c)
        bk[key] = total("boro='3' AND " + c)
        print("now", key, flush=True)
    z = (0, 0)
    for key in conds:
        put(out["stats"], key, by_cd[key].get("306", z))
        for n in range(1, 19):
            v = by_cd[key].get("3%02d" % n, z)
            put(out["bk"][str(n)] if str(n) in out["bk"] else out["bk"][n], key, v)
            put(out["ch"]["cd"][str(n)] if str(n) in out["ch"]["cd"] else out["ch"]["cd"][n], key, v)
        put(out["bk_all"], key, bk[key])
        put(out["ch"]["all"], key, bk[key])
        for c in list(out["ch"]["cc"].keys()):
            put(out["ch"]["cc"][c], key, by_cc[key].get("%02d" % int(c), z))
        for b in list(out["ch"]["boro"].keys()):
            put(out["ch"]["boro"][b], key, by_bo[key].get(str(b), z))
        put(out["ch"]["nyc"], key, nyc[key])

    def label(cd):
        return {"1": "MN", "2": "BX", "3": "BK", "4": "QN", "5": "SI"}[cd[0]] + "CB" + str(int(cd[1:]))

    def rank(d):
        return [[label(k), v[0]] for k, v in sorted(d.items(), key=lambda kv: -kv[1][0]) if k and re.fullmatch(r"[1-5]\d\d", str(k)) and int(str(k)[1:]) <= 18 and v[0] > 0]

    out["stats"]["rank_10_now"] = rank(by_cd["loss_now"])
    out["stats"]["rank_20_now"] = rank(by_cd["loss_20_now"])
    out["stats"]["rank_pending"] = rank(by_cd["loss_pending"])
    out["stats"]["hdb_end"] = end
    out["stats"]["last_year"] = Y
    return out


if __name__ == "__main__":
    p = os.path.join(ROOT, "middlehousingstillmissing", "data.json")
    out = add_now(json.load(open(p)))
    json.dump(out, open(p, "w"), separators=(",", ":"))
    s = out["stats"]
    print({k: s[k] for k in s if k.endswith("_now") or "pending" in k and not k.startswith("rank") or k in ("hdb_end", "last_year")})
    print("bk_all", {k: v for k, v in out["bk_all"].items() if "now" in k or "pending" in k})
    print("nyc", {k: v for k, v in out["ch"]["nyc"].items() if "now" in k or "pending" in k})
    print("rank_10_now", s["rank_10_now"][:6])
