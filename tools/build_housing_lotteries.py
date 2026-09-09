#!/usr/bin/env python3
"""Rebuild data/housing-lotteries.json from the NYC Housing Connect public API.

Source: the same endpoints the Housing Connect 2.0 site itself calls
(https://a806-housingconnectapi.nyc.gov/HPDPublicAPI/api/).
  POST Lottery/SearchLotteries            -> every open rental lottery
  GET  Lottery/GetLotteryAdvertisement    -> per-unit AMI band, rent, income limits by household size

Community district is assigned by point-in-polygon against data/community-districts.geojson.
Run from the repo root:  python3 tools/build_housing_lotteries.py
"""
import json, re, sys, datetime, urllib.request
from collections import OrderedDict

API = "https://a806-housingconnectapi.nyc.gov/HPDPublicAPI/api/"
UA = {"User-Agent": "Mozilla/5.0 (bkcb6.app lottery refresh)", "Accept": "application/json"}
BORO_CODE = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"}
BED = {"Studio": "Studio", "1 Bedroom": "1BR", "2 Bedroom": "2BR", "3 Bedroom": "3BR",
       "4 Bedroom": "4BR", "5 Bedroom": "5BR", "6 Bedroom": "6BR"}
BEDORDER = ["Studio", "1BR", "2BR", "3BR", "4BR", "5BR", "6BR"]


def get(path):
    req = urllib.request.Request(API + path, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def post(path, body):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(),
                                 headers=dict(UA, **{"Content-Type": "application/json"}), method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def title(s):
    s = re.sub(r"\s+", " ", (s or "")).strip()
    if s.isupper():
        s = s.title()
    return s


def clean_address(a):
    a = re.sub(r"\s+", " ", (a or "")).strip()
    if a.isupper():
        a = a.title()
    return a


def geocode(address, city, zip_):
    """NYC Planning Labs geosearch fallback when Housing Connect has no coordinates."""
    import urllib.parse, time
    q = ", ".join(x for x in [address, city, ("NY " + zip_) if zip_ else "NY"] if x)
    url = "https://geosearch.planninglabs.nyc/v2/search?" + urllib.parse.urlencode({"text": q, "size": 1})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            j = json.load(r)
        time.sleep(0.15)
        feats = j.get("features") or []
        if feats:
            lng, lat = feats[0]["geometry"]["coordinates"]
            return float(lat), float(lng)
    except Exception as e:
        print("  geocode failed for %s: %s" % (q, e), file=sys.stderr)
    return None, None


def program(desc):
    d = (desc or "").lower()
    if "mitchell" in d:
        return "Mitchell-Lama"
    if "485" in d:
        return "485-X Tax Incentive"
    if "421" in d:
        return "421-a Tax Incentive"
    if "inclusionary" in d:
        return "Inclusionary Housing"
    if "ella" in d:
        return "ELLA (HDC/HPD)"
    return None


# ---- community district lookup ----
def load_cds():
    try:
        from shapely.geometry import shape, Point
        from shapely.strtree import STRtree
    except ImportError:
        return None
    g = json.load(open("data/community-districts.geojson"))
    geoms, codes = [], []
    for f in g["features"]:
        geoms.append(shape(f["geometry"]))
        codes.append(str(f["properties"]["boro_cd"]))
    tree = STRtree(geoms)

    def lookup(lat, lng):
        p = Point(lng, lat)
        for i in tree.query(p):
            if geoms[i].contains(p):
                return codes[i]
        return None
    return lookup


def main():
    lookup_cd = load_cds()
    search = post("Lottery/SearchLotteries", {
        "UnitTypes": [], "NearbyPlaces": [], "NearbySubways": [], "Amenities": [], "Applied": None,
        "HPDUserId": None, "Boroughs": [], "Neighborhoods": [], "HouseholdSize": None, "Income": "",
        "HouseholdType": 2, "OwnerTypes": [], "PreferanceTypes": [], "LotteryTypes": [],
        "Min": None, "Max": None, "RentalSubsidy": None})
    rentals = search.get("rentals") or []
    out = []
    for s in rentals:
        lid = s["lotteryId"]
        adv = get("Lottery/GetLotteryAdvertisement?lotteryId=%d" % lid)
        end = (adv.get("endDate") or s.get("lotteryEndDate") or "")[:10]
        bldgs = adv.get("lotteryBuildings") or []
        addresses = [clean_address(b["address"]) for b in bldgs if b.get("address")]
        first = bldgs[0] if bldgs else None
        lat = float(first["latitude"]) if first and first.get("latitude") else None
        lng = float(first["longitude"]) if first and first.get("longitude") else None
        if first and (lat is None or lng is None):
            lat, lng = geocode(clean_address(first.get("address")), clean_address(first.get("city")), first.get("zip"))
        borough = (s.get("borough") or "").strip()
        cd_num, cb = None, None
        if lookup_cd and lat is not None and lng is not None:
            code = lookup_cd(lat, lng)
            if code:
                borough = BORO_CODE.get(code[0], borough)
                cd_num = int(code[1:])
                cb = "%s CB%d" % (borough, cd_num)
        # aggregate identical unit rows: (bed, ami, rent) -> count, min, max by household size
        agg = OrderedDict()
        for u in adv.get("units") or []:
            bed = BED.get(u.get("unitLayoutTypeName"), u.get("unitLayoutTypeName"))
            key = (bed, int(u.get("unitRegulatoryMechanismAmi") or 0), int(round(u.get("actualRent") or 0)))
            row = agg.setdefault(key, {"ami": key[1], "bed": bed, "rent": key[2], "count": 0, "min": None, "max": {}})
            row["count"] += 1
            for inc in u.get("unitIncome") or []:
                hh = str(inc["houseHoldSize"])
                mn, mx = int(round(inc["minimumIncome"])), int(round(inc["maximumIncome"]))
                row["min"] = mn if row["min"] is None else min(row["min"], mn)
                row["max"][hh] = max(row["max"].get(hh, 0), mx)
            cap = u.get("maximumAssetCap") or 0
            if cap:
                row["asset_limit"] = int(round(cap))
        detail = sorted(agg.values(), key=lambda r: (BEDORDER.index(r["bed"]) if r["bed"] in BEDORDER else 99, r["ami"], r["rent"]))
        unit_mix = OrderedDict()
        for r in detail:
            unit_mix[r["bed"]] = unit_mix.get(r["bed"], 0) + r["count"]
        hh_sizes = [int(h) for r in detail for h in r["max"].keys()]
        mins = [r["min"] for r in detail if r["min"] is not None]
        maxs = [m for r in detail for m in r["max"].values()]
        rec = OrderedDict()
        rec["id"] = str(lid)
        rec["name"] = title(adv.get("lotteryName") or s.get("lotteryName"))
        rec["address"] = (", ".join(x for x in [addresses[0] if addresses else None,
                                               clean_address(first.get("city")) if first else None,
                                               ("NY " + first["zip"]) if first and first.get("zip") else None] if x)) or None
        rec["addresses"] = addresses
        rec["lat"], rec["lng"] = lat, lng
        rec["neighborhood"] = (s.get("neighborhood") or "").strip() or None
        rec["borough"] = borough
        rec["cb"] = cb
        rec["cd_num"] = cd_num
        rec["units"] = sum(unit_mix.values()) or int(s.get("units") or 0)
        rec["end"] = end
        rec["is_open"] = bool(end) and end >= str(datetime.date.today())
        rec["income_min"] = min(mins) if mins else (int(s["minIncome"]) if s.get("minIncome") else None)
        rec["income_max"] = max(maxs) if maxs else (int(s["maxIncome"]) if s.get("maxIncome") else None)
        rec["hh_min"] = min(hh_sizes) if hh_sizes else s.get("minHouseholdSize")
        rec["hh_max"] = max(hh_sizes) if hh_sizes else s.get("maxHouseholdSize")
        rec["program"] = program(adv.get("lotteryDescription"))
        rec["waitlist"] = bool(adv.get("isPhasedLottery"))
        rec["mitchell_lama"] = bool(adv.get("isMitchelLamaLottery"))
        prefs = adv.get("lotterySetAsidePreferences") or []
        for p in prefs:
            if p.get("preferenceTypeId") == 3 or "community board" in (p.get("name") or "").lower():
                rec["cb_pref"] = int(p.get("requirementAllocation") or 0)
                m = re.search(r"\((.*?)\)", p.get("name") or "")
                rec["cb_pref_text"] = (m.group(1) if m else p.get("name")).replace("CB ", "CB") + " residents"
        rec["preferences"] = [{"name": p.get("name"), "pct": p.get("requirementAllocation"), "set_aside": bool(p.get("isSetAside"))} for p in prefs]
        rec["unit_mix"] = unit_mix
        rec["detail"] = detail
        out.append(rec)
        print("  %-46s %-13s CB%-4s %4d units  ends %s" % (rec["name"][:46], borough, cd_num, rec["units"], end), file=sys.stderr)
    out.sort(key=lambda r: (r["end"] or "9999", r["name"]))
    data = OrderedDict()
    data["updated"] = str(datetime.date.today())
    data["source"] = "NYC Housing Connect public API (a806-housingconnectapi.nyc.gov/HPDPublicAPI), the same feed the Housing Connect site reads. Community district assigned from each building's coordinates."
    data["total_on_housing_connect"] = len(rentals)
    data["lotteries"] = out
    json.dump(data, open("data/housing-lotteries.json", "w"), indent=1)
    print("wrote %d rental lotteries" % len(out), file=sys.stderr)


if __name__ == "__main__":
    main()
