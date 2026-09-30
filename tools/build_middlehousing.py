#!/usr/bin/env python3
"""Build middlehousing/data.json for bkcb6.app/middlehousing/.

Cross-references three City sources for Brooklyn Community District 6:
  1. DOB NOW job filings (w9ak-ipjd) and DOB BIS job filings (ic3t-wcy2),
     every CB6 filing (community board 306), classified for multi-family to
     one-family conversions by description and by unit counts.
  2. The DCP Housing Database project-level file (br6q-ssj3): every CB6
     alteration that lowers the legal unit count ("Alt Loss"), plus the
     citywide Alt Loss totals used to rank community districts.
Every building is placed in its neighborhood, historic district and zoning
district using the layers already on bkcb6.app.

Usage: python3 tools/build_middlehousing.py [cache_dir]
A cache_dir with cb6_dobnow_filings.csv / cb6_bis_filings.csv / hdb_*.csv is
used instead of downloading when present.
"""
import io, json, os, re, sys, time, urllib.parse, urllib.request
import pandas as pd
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = sys.argv[1] if len(sys.argv) > 1 else None
TOKEN = "HvFoIfzodzpRML7a1104Ca2tM"


def pull(ds, where, order):
    frames, off = [], 0
    while True:
        q = urllib.parse.urlencode({"$where": where, "$limit": 50000, "$offset": off, "$order": order})
        req = urllib.request.Request(f"https://data.cityofnewyork.us/resource/{ds}.csv?" + q, headers={"X-App-Token": TOKEN})
        d = pd.read_csv(io.StringIO(urllib.request.urlopen(req, timeout=300).read().decode()), dtype=str)
        frames.append(d)
        off += 50000
        if len(d) < 50000:
            break
    return pd.concat(frames, ignore_index=True)


def cached(name, ds, where, order):
    if CACHE and os.path.exists(os.path.join(CACHE, name)):
        return pd.read_csv(os.path.join(CACHE, name), dtype=str)
    d = pull(ds, where, order)
    if CACHE:
        d.to_csv(os.path.join(CACHE, name), index=False)
    return d


now = cached("cb6_dobnow_filings.csv", "w9ak-ipjd", "commmunity_board='306'", "job_filing_number").fillna("")
bis = cached("cb6_bis_filings.csv", "ic3t-wcy2", "community___board='306'", "job__,doc__").fillna("")
hdb = cached("hdb_cb6.csv", "br6q-ssj3", "commntydst='306'", "job_number").fillna("")
hnyc = cached("hdb_nyc_alt_loss.csv", "br6q-ssj3", "job_type='Alteration' AND classanet<0", "job_number").fillna("")
print("DOB NOW rows", len(now), "| BIS rows", len(bis), "| HDB CB6 rows", len(hdb), "| HDB NYC alt-loss rows", len(hnyc))

# ---------------------------------------------------------------- classify DOB filings
N = r'(?:TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|[2-9]|1[0-9])'
MULTI = r'(?:' + N + r'|MULTI|MULTIPLE|MULTI-FAMILY|MULTIFAMILY)'
RES = r'(?:FAMILY|FAMILIES|FAM\b|FAM\.|FAMIL\w*|DWEL\w*|D\.?U\.?\b|UNITS?|APARTMENTS?|APTS?|RESIDEN\w*|HOUSE|HOME|TOWN\s?HOUSE|M\.?D\.?\b)'
ONEF = r'[\(\s]*(?:ONE|1|SINGLE)\b[\s\-\(\)1]*(?:ONE\s+)?(?:FAMILY|FAM\b|FAM\.|FAMIL\w*)'
TO = r'\b(?:TO|INTO|AS|TOO)\b\s*(?:(?:CREATE|MAKE|FORM|ESTABLISH|BECOME|BE|OBTAIN)\s+)?(?:AN?\s+|THE\s+)?(?:NEW\s+|PRIVATE\s+|LEGAL\s+)?'
PATTERNS = [
    re.compile(r'\b' + MULTI + r'\b[\s\-\(\)0-9]*(?:\w+\s+){0,2}?' + RES + r'.{0,100}?' + TO + ONEF, re.S),
    re.compile(ONEF + r'.{0,60}?\bFROM\b\s*(?:AN?\s+|THE\s+)?' + MULTI + r'\b[\s\-\(\)0-9]*' + RES, re.S),
    re.compile(r'(?:MULTIPLE\s*DWEL\w*|MULTI-?\s?FAMILY|OLD\s+LAW\s+TENEMENT|TENEMENT|\bS\.?R\.?O\.?\b|ROOMING\s+HOUSE|LODGING\s+HOUSE).{0,100}?' + TO + ONEF, re.S),
    re.compile(r'\bFROM\b\s*(?:AN?\s+)?' + MULTI + r'\b[\s\-\(\)]*(?:' + RES + r')?.{0,50}?\bTO\b\s*(?:AN?\s+)?[\(\s]*(?:ONE|1|SINGLE)\b[\s\-\(\)1]*(?:FAMILY|FAM\b|FAM\.|FAMIL\w*|DWELLING|D\.?U\.?\b|UNIT)', re.S),
    re.compile(r'COMBIN\w*.{0,80}?\b(?:ALL|THE|' + N + r')\b.{0,30}?(?:APARTMENTS|UNITS|FAMILIES).{0,80}?\b(?:TO|INTO)\b\s*(?:MAKE\s+|CREATE\s+|FORM\s+)?(?:AN?\s+|THE\s+)?[\(\s]*(?:ONE|SINGLE|1)\b[\s\-\(\)1]*(?:FAMILY|RESIDENCE|HOUSE|HOME|DWELLING(?!\s*UNIT))', re.S),
]
REVERSE = re.compile(ONEF + r'.{0,50}?\b(?:TO|INTO)\b\s*(?:AN?\s+)?[\(\s]*' + N + r'\b[\s\-\(\)0-9]*(?:FAMILY|FAMILIES|FAM\b|DWELLING|UNITS)', re.S)
# Filings the rules flag that are not consolidations when read in full.
EXCLUDE = {"320230022": "2 duplex units become a basement unit and a triplex; still 2 units"}


def says_conversion(s):
    s = s.upper()
    return any(p.search(s) for p in PATTERNS) and not REVERSE.search(s)


def num(s):
    try:
        return float(s)
    except Exception:
        return None


now["sys"] = "DOB NOW"
now["job"] = now.job_filing_number.str.split("-").str[0]
now["addr"] = (now.house_no.str.strip() + " " + now.street_name.str.strip()).str.upper()
now["binx"] = now["bin"]
now["lat"], now["lon"] = now.latitude, now.longitude
now["filed"] = now.filing_date.str[:10]
bis["sys"] = "BIS"
bis["job"] = bis["job__"]
bis["addr"] = (bis.house__.str.strip() + " " + bis.street_name.str.strip()).str.upper()
bis["binx"] = bis["bin__"]
bis["lat"], bis["lon"] = bis.gis_latitude, bis.gis_longitude
bis["filed"] = pd.to_datetime(bis.pre__filing_date, errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
cols = ["sys", "job", "addr", "binx", "block", "lot", "job_type", "existing_dwelling_units", "proposed_dwelling_units", "filed", "job_description", "lat", "lon"]
rows = pd.concat([now[cols], bis[cols]], ignore_index=True).fillna("")
rows["e"] = rows.existing_dwelling_units.map(num)
rows["p"] = rows.proposed_dwelling_units.map(num)
rows["u"] = rows.apply(lambda r: r.e is not None and r.p is not None and r.e >= 2 and r.p == 1, axis=1)
rows["x"] = rows.job_description.map(says_conversion)
jobs_total = rows.groupby(["sys", "job"]).ngroups
g = rows.groupby(["sys", "job"]).agg(u=("u", "any"), x=("x", "any"), pmax=("p", lambda s: max([v for v in s if v is not None], default=None))).reset_index()
g = g[(g.u | g.x) & ~g.job.isin(EXCLUDE)]


def dob_status(sysname, raw):
    if sysname == "DOB NOW":
        i1 = raw[raw.job_filing_number.str.endswith("-I1")]
        base = i1.iloc[0] if len(i1) else raw.iloc[0]
        st = base.filing_status
        so = [x[:10] for x in raw.signoff_date if x]
        cost = base.initial_cost
    else:
        lat = raw.sort_values("latest_action_date").iloc[-1]
        st = lat.job_status_descrp
        so = sorted(pd.to_datetime(raw.signoff_date.replace("", pd.NA).dropna(), errors="coerce").dropna().dt.strftime("%Y-%m-%d"))
        cost = raw.iloc[0].initial_cost
    u = st.upper()
    if so or u in ("SIGNED OFF", "CO ISSUED", "LOC ISSUED"):
        stage = "done"
    elif "PERMIT" in u or u == "APPROVED" or "PLAN EXAM - APPROVED" in u:
        stage = "permitted"
    elif "WITHDRAWN" in u:
        stage = "withdrawn"
    else:
        stage = "filed"
    return st, stage, (so[0] if so else ""), cost


jobrows = []
for _, j in g.iterrows():
    f = rows[(rows.sys == j.sys) & (rows.job == j.job)]
    raw = now[now.job == j.job] if j.sys == "DOB NOW" else bis[bis.job == j.job]
    st, stage, so, cost = dob_status(j.sys, raw)
    ur = f[f.u]
    src = ur.iloc[0] if len(ur) else f.iloc[0]
    xr = f[f.x]
    desc = xr.iloc[0].job_description if len(xr) else next((d for d in f.job_description if d), "")
    fd = [d for d in f.filed if d]
    ll = f[(f.lat != "") & (f.lon != "")]
    jobrows.append(dict(sys=j.sys, job=j.job, addr=f.addr.mode().iloc[0], bin=f.binx.iloc[0], block=f.block.iloc[0].lstrip("0"), lot=f.lot.iloc[0].lstrip("0"),
                        jt=f.job_type.iloc[0], filed=min(fd) if fd else "", e=src.e, p=src.p, pmax=j.pmax, u=bool(j.u), x=bool(j.x),
                        status=st, stage=stage, signoff=so, cost=cost, desc=re.sub(r"\s+", " ", desc.replace("&amp;", "&")).strip(),
                        lat=float(ll.lat.iloc[0]) if len(ll) else None, lon=float(ll.lon.iloc[0]) if len(ll) else None))
JOBS = pd.DataFrame(jobrows)
print("DOB jobs checked", jobs_total, "| matched", len(JOBS))

# ---------------------------------------------------------------- Housing Database
for c in ["classainit", "classaprop", "classanet"]:
    hdb[c] = pd.to_numeric(hdb[c], errors="coerce")
    hnyc[c] = pd.to_numeric(hnyc[c], errors="coerce")
hdb["cy"] = pd.to_numeric(hdb.compltyear, errors="coerce")
hnyc["cy"] = pd.to_numeric(hnyc.compltyear, errors="coerce")
hdb["base"] = hdb.job_number.str.split("-").str[0]
version = hdb.version.mode().iloc[0] if "version" in hdb and len(hdb) else ""
ALT = hdb[(hdb.job_type == "Alteration") & (hdb.classanet < 0) & ~hdb.job_status.str.startswith("9")].copy()
STAGE = {"1": "filed", "2": "filed", "3": "permitted", "5": "done"}
ALT["stage"] = ALT.job_status.str[0].map(STAGE)
print("HDB CB6 alt-loss jobs (not withdrawn)", len(ALT))

# ---------------------------------------------------------------- buildings
def is_placeholder(b):
    return (not b) or bool(re.fullmatch(r"[1-5]0{6}", b))


JOBS["key"] = JOBS.apply(lambda r: r.addr if is_placeholder(r.bin) else r.bin, axis=1)
ALT["key"] = ALT.apply(lambda r: (r.addressnum + " " + r.addressst).upper() if is_placeholder(r.bin) else r.bin, axis=1)
keys = sorted(set(JOBS.key) | set(ALT.key))
RANK = {"done": 3, "permitted": 2, "filed": 1, "withdrawn": 0}


def load(path):
    return json.load(open(os.path.join(ROOT, path)))["features"]


nb_f = [f for f in load("data/city-neighborhoods.geojson") if f["properties"].get("boro") == "Brooklyn"]
hd_f = load("data/cb6-historic-clipped.geojson")
zn_f = load("data/cb6-zoning-clipped.geojson")
cb6 = shape(load("data/cb6_boundary.geojson")[0]["geometry"])


def index(features):
    geoms = [shape(f["geometry"]) for f in features]
    return STRtree(geoms), geoms


nb_t, nb_g = index(nb_f)
hd_t, hd_g = index(hd_f)
zn_t, zn_g = index(zn_f)
CB6_NB = ["Park Slope", "Carroll Gardens", "Cobble Hill", "Red Hook", "Gowanus", "Columbia Street Waterfront District"]


def hit(tree, geoms, feats, pt, prop):
    for i in tree.query(pt):
        if geoms[i].contains(pt):
            return feats[i]["properties"].get(prop)
    return ""


def nearest_nb(pt):
    best, bd = "", 1e9
    for i, gm in enumerate(nb_g):
        n = nb_f[i]["properties"]["nb"]
        if n not in CB6_NB:
            continue
        d = gm.distance(pt)
        if d < bd:
            best, bd = n, d
    return best


buildings = []
for k in keys:
    dj = JOBS[JOBS.key == k]
    ha = ALT[ALT.key == k]
    lat = next((v for v in list(dj.lat) + [num(x) for x in ha.latitude] if v), None)
    lon = next((v for v in list(dj.lon) + [num(x) for x in ha.longitude] if v), None)
    addr = dj.addr.mode().iloc[0] if len(dj) else (ha.addressnum.iloc[0] + " " + ha.addressst.iloc[0]).upper()
    one_dob = dj[(dj.u) | (dj.x & ((dj.pmax.isna()) | (dj.pmax <= 1)))]
    part_dob = dj[~dj.index.isin(one_dob.index)]
    one_hdb = ha[ha.classaprop == 1]
    if len(one_dob) or len(one_hdb):
        cat = "one"      # became a one-family
    elif len(ha):
        cat = "fewer"    # lost units, 2 or more remain (Housing Database)
    else:
        cat = "check"    # description says one family, the filing's unit counts disagree
    # Stage comes from the job that changes the certificate of occupancy: the Housing
    # Database job when there is one, otherwise the DOB Alt-CO / Alt-1 application.
    prim = dj[dj.jt.str.upper().str.contains("CO|^A1$", regex=True)]
    stages = list(ha.stage) if len(ha) else list((prim if len(prim) else dj).stage)
    stage = max(stages, key=lambda s: RANK[s]) if stages else "filed"
    filed = sorted([d for d in list(dj.filed) + [x[:10] for x in ha.datefiled] if d])
    comp = sorted(set(int(c) for c in ha[ha.stage == "done"].cy.dropna()))
    so = sorted(d for d in (prim if len(prim) else dj).signoff if d)
    ubefore = [v for v in list(dj.e) + list(ha.classainit) if v is not None and not pd.isna(v)]
    uafter = [v for v in list(dj[dj.u].p) + list(ha.classaprop) if v is not None and not pd.isna(v)]
    lost_hdb = int(-ha.classanet.sum()) if len(ha) else 0
    pt = Point(lon, lat) if lat and lon else None
    nb = hd = zn = ""
    if pt is not None:
        nb = hit(nb_t, nb_g, nb_f, pt, "nb")
        if nb not in CB6_NB:
            nb = nearest_nb(pt)
        hd = hit(hd_t, hd_g, hd_f, pt, "area_name")
        zn = hit(zn_t, zn_g, zn_f, pt, "zone")
    xd = dj[dj.x]
    main = (xd if len(xd) else dj).sort_values("filed").iloc[0] if len(dj) else None
    hmain = ha.sort_values("datefiled").iloc[0] if len(ha) else None
    desc = main.desc if main is not None else re.sub(r"\s+", " ", str(hmain.job_desc)).strip()
    j_list = [dict(s="N" if r.sys == "DOB NOW" else "B", j=r.job, f=r.filed, st=r.status, g=r.stage, e=None if r.e is None or pd.isna(r.e) else int(r.e),
                   p=None if r.p is None or pd.isna(r.p) else int(r.p), so=r.signoff, d=r.desc, h=1 if r.job in set(ha.base) else 0) for r in dj.sort_values("filed").itertuples()]
    h_list = [dict(j=r.job_number, f=r.datefiled[:10], st=r.job_status[3:], g=r.stage, i=int(r.classainit), p=int(r.classaprop), n=int(r.classanet),
                   cy=None if pd.isna(r.cy) else int(r.cy), d=re.sub(r"\s+", " ", str(r.job_desc)).strip()[:400]) for r in ha.sort_values("datefiled").itertuples()]
    buildings.append(dict(
        a=addr.title().replace(" St ", " St ").strip(), bin="" if is_placeholder(k) else k,
        bbl=(dj.block.iloc[0] + "/" + dj.lot.iloc[0]) if len(dj) else "",
        lat=round(lat, 6) if lat else None, lon=round(lon, 6) if lon else None,
        c=cat, g=stage, nb=nb, hd=hd, zn=zn,
        y=int(filed[0][:4]) if filed else None, cy=comp[0] if comp else (int(so[0][:4]) if so else None),
        ub=int(max(ubefore)) if ubefore else None, ua=int(min(uafter)) if uafter else None, lost=lost_hdb,
        src=("D" if len(dj) else "") + ("H" if len(ha) else ""),
        ev=("x" if one_dob.x.any() else "") + ("u" if one_dob.u.any() else "") + ("h" if len(one_hdb) else "") if len(one_dob) else ("h" if len(one_hdb) else ""),
        d=desc[:600], jobs=j_list, hj=h_list,
    ))
B = pd.DataFrame(buildings)
print("buildings", len(B), B.c.value_counts().to_dict(), B.g.value_counts().to_dict(), "no coords", B.lat.isna().sum())

# ---------------------------------------------------------------- Housing Database figures
comp = hdb[hdb.job_status.str.startswith("5")]
alt_c = comp[comp.job_type == "Alteration"]


def units(df):
    return int(df.classanet.sum())


def yr(df, a, b):
    return df[(df.cy >= a) & (df.cy <= b)]


loss_by_year = {int(y): int(-v) for y, v in alt_c[alt_c.classanet < 0].groupby("cy").classanet.sum().items()}
jobs_by_year = {int(y): int(v) for y, v in alt_c[alt_c.classanet < 0].groupby("cy").size().items()}
gain_by_year = {int(y): int(v) for y, v in alt_c[alt_c.classanet > 0].groupby("cy").classanet.sum().items()}
nb_by_year = {int(y): int(v) for y, v in comp[comp.job_type == "New Building"].groupby("cy").classanet.sum().items()}
demo_by_year = {int(y): int(-v) for y, v in comp[comp.job_type == "Demolition"].groupby("cy").classanet.sum().items()}
nw = hdb[~hdb.job_status.str.startswith("9")]
nw_alt = nw[nw.job_type == "Alteration"]
stats = dict(
    version=version,
    loss_10_24=-units(yr(alt_c[alt_c.classanet < 0], 2010, 2024)), loss_jobs_10_24=int(len(yr(alt_c[alt_c.classanet < 0], 2010, 2024))),
    loss_20_24=-units(yr(alt_c[alt_c.classanet < 0], 2020, 2024)),
    gain_10_24=units(yr(alt_c[alt_c.classanet > 0], 2010, 2024)),
    nb_10_24=units(yr(comp[comp.job_type == "New Building"], 2010, 2024)),
    demo_10_24=-units(yr(comp[comp.job_type == "Demolition"], 2010, 2024)),
    net_10_24=units(yr(comp, 2010, 2024)),
    loss_all_open=-units(nw_alt[nw_alt.classanet < 0]), loss_all_open_jobs=int((nw_alt.classanet < 0).sum()),
    pipeline_net=units(nw[nw.job_status.str[0].isin(["1", "2", "3"])]),
    loss_by_year=loss_by_year, jobs_by_year=jobs_by_year, gain_by_year=gain_by_year, nb_by_year=nb_by_year, demo_by_year=demo_by_year,
    loss_to_one_10_24=-units(yr(alt_c[(alt_c.classanet < 0) & (alt_c.classaprop == 1)], 2010, 2024)),
    loss_to_one_jobs_10_24=int(len(yr(alt_c[(alt_c.classanet < 0) & (alt_c.classaprop == 1)], 2010, 2024))),
)
cds = json.load(open(os.path.join(ROOT, "cd-boundaries-simple.geojson")))["features"]


def cd_label(cd):
    b = {"1": "MN", "2": "BX", "3": "BK", "4": "QN", "5": "SI"}[cd[0]]
    return b + "CB" + str(int(cd[1:]))


def ranking(df):
    s = df.groupby("commntydst").classanet.sum().sort_values()
    return [[cd_label(k), int(-v)] for k, v in s.items() if re.fullmatch(r"[1-5]\d\d", k) and int(k[1:]) <= 18]


cn = hnyc[hnyc.job_status.str.startswith("5")]
stats["rank_10_24"] = ranking(cn[(cn.cy >= 2010) & (cn.cy <= 2024)])
stats["rank_20_24"] = ranking(cn[(cn.cy >= 2020) & (cn.cy <= 2024)])
stats["rank_open"] = ranking(hnyc[~hnyc.job_status.str.startswith("9")])

out = dict(
    built=time.strftime("%Y-%m-%d"),
    counts=dict(dob_now_rows=len(now), bis_rows=len(bis), dob_jobs=jobs_total, dob_matched=len(JOBS), hdb_rows=len(hdb), hdb_alt_loss=len(ALT)),
    stats=stats,
    b=json.loads(B.to_json(orient="records")),
)
os.makedirs(os.path.join(ROOT, "middlehousing"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "middlehousing", "data.json"), "w"), separators=(",", ":"))
print("wrote middlehousing/data.json", os.path.getsize(os.path.join(ROOT, "middlehousing", "data.json")) // 1024, "KB")
print(json.dumps({k: v for k, v in stats.items() if not isinstance(v, (dict, list))}, indent=1))
