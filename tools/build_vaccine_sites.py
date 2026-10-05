#!/usr/bin/env python3
# Every vaccine location on the NYC Health Map (a816-health.nyc.gov/NYCHealthMap), all 14 vaccine services,
# merged to one row per site with the vaccines it gives. Writes data/vaccine-sites.json.
import json, sys, datetime, urllib.request, http.cookiejar
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
BASE = "https://a816-health.nyc.gov/NYCHealthMap/"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.addheaders = [("User-Agent", UA)]
op.open(BASE + "ServiceCategory/Vaccines", timeout=60).read()   # passes the city's waiting room, sets its cookie
def post(ep, body):
    r = urllib.request.Request(BASE + "App/" + ep, data=json.dumps(body).encode(), method="POST",
                               headers={"Content-Type": "application/json", "Accept": "application/json"})
    return json.loads(op.open(r, timeout=120).read())
cat = json.loads(op.open(BASE + "App/GetServiceCategoryByID/?scname=Vaccines", timeout=60).read())
cat = cat.get("ServiceCategory", cat)
services = [(s["ServiceID"], s["ServiceName"]) for s in cat["ServiceList"]]
SHORT = {"COVID-19 Vaccine": "COVID-19", "Flu Vaccine": "Flu", "Hepatitis A Vaccine": "Hepatitis A", "Hepatitis B Vaccine": "Hepatitis B",
         "Human Papillomavirus (HPV) Vaccine": "HPV", "Measles, Mumps, Rubella (MMR) Vaccine": "MMR", "Meningococcal (Meningitis) Vaccine": "Meningitis",
         "Mpox Vaccine": "Mpox", "Pneumococcal (Pneumonia) Vaccine": "Pneumonia", "Polio Vaccine": "Polio",
         "Respiratory Syncytial Virus (RSV) Vaccine": "RSV", "Tetanus and Pertussis (Tdap, Td) Vaccines": "Tdap/Td",
         "Varicella (Chickenpox) Vaccine": "Chickenpox", "Zoster (Shingles) Vaccine": "Shingles"}
sites, counts = {}, {}
for sid, name in services:
    short = SHORT.get(name, name.replace(" Vaccine", ""))
    base = {"CategoryID": cat["CategoryID"], "ServiceTypeIDs": str(sid), "ServiceFilters": "", "Borough": "", "Address": "", "ZipCode": "",
            "Latitude": 0, "Longitude": 0, "Distance": 0}
    marks = {m["FacilityID"]: m for m in post("GetMarkers", base)}
    page = post("GetFacilitiesByFiltersByPaging", dict(base, Paging={"PageNum": 1, "PageSize": 10000, "SortExpression": "FacilityName", "SortDirection": "ASC"}))
    rows = page.get("FacilityList") or []
    total = rows[0]["TotalCount"] if rows else 0
    if len(rows) != total or len(marks) != total:
        sys.exit(f"{name}: {len(rows)} listed, {len(marks)} mapped, {total} total; refusing to write a partial file")
    counts[short] = total
    for r in rows:
        m = marks.get(r["FacilityID"])
        if not m: sys.exit(f"{name}: facility {r['FacilityID']} has no map point")
        key = (r["FacilityName"].strip().lower(), " ".join((r.get("FullAddress") or "").lower().split()))
        s = sites.setdefault(key, {"name": r["FacilityName"].strip(), "address": " ".join((r.get("FullAddress") or "").split()),
                                   "phone": (r.get("Phone") or "").strip(), "web": (r.get("Website") or "").strip(),
                                   "lat": round(float(m["Latitude"]), 6), "lng": round(float(m["Longitude"]), 6), "vaccines": []})
        if short not in s["vaccines"]: s["vaccines"].append(short)
order = list(SHORT.values())
out = sorted(sites.values(), key=lambda s: (s["name"].lower(), s["address"]))
for s in out: s["vaccines"].sort(key=lambda v: order.index(v) if v in order else 99)
for v, n in counts.items():
    have = sum(1 for s in out if v in s["vaccines"])
    if have != n: sys.exit(f"{v}: {have} sites after merging, the map lists {n}")
doc = {"generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
       "source": "NYC Health Map, Vaccines (NYC Department of Health and Mental Hygiene)",
       "source_url": "https://a816-health.nyc.gov/NYCHealthMap/ServiceCategory/Vaccines",
       "counts_by_vaccine": counts, "site_count": len(out), "sites": out}
dest = sys.argv[1] if len(sys.argv) > 1 else "vaccine-sites.json"
json.dump(doc, open(dest, "w"), separators=(",", ":"))
print(len(out), "sites", counts)
