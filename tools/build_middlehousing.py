#!/usr/bin/env python3
"""Build the Brooklyn-wide consolidation data for bkcb6.app/middlehousing/.

Sources (all NYC Open Data, every Brooklyn record, nothing sampled):
  w9ak-ipjd  DOB NOW: Build, Job Application Filings   (borough = Brooklyn)
  ic3t-wcy2  DOB Job Application Filings (BIS)          (borough = BROOKLYN)
  rbx6-tga4  DOB NOW: Build, Approved Permits           (for the matched jobs)
  ipu4-2q9a  DOB Permit Issuance (BIS)                  (for the matched jobs)
  br6q-ssj3  DCP Housing Database, project level        (boro 3, plus citywide Alt Loss for ranks)

A DOB job is a match when any of its filings lists 2 or more existing
dwelling units and 1 proposed, or its description says a multi-family,
multiple dwelling, tenement or SRO building becomes one family. A Housing
Database job is a match when it is an alteration that lowers the legal unit
count (classanet < 0) and is not withdrawn. Matches are grouped into
buildings by BIN and placed in their community district, neighborhood and
historic district with the layers already on bkcb6.app. The district is the
one the city recorded: the Housing Database's commntydst, else the lot's
community district in PLUTO (64uk-42ks), else the DOB filing's community board;
the district boundary map is used only when none of those is valid.

Writes:
  middlehousing/data.json          counts, CB6 figures, Brooklyn district table, ranks
  middlehousing/bk/index.json      one row per building (map, list, search)
  middlehousing/bk/cd3NN.json      every filing, permit and Housing Database job, per district

Usage: python3 tools/build_middlehousing.py <cache_dir>
Files already in cache_dir are reused (bk_dobnow.csv, bk_bis.csv, hdb_bk.csv,
hdb_nyc_alt_loss.csv, bk_now_permits.csv, bk_bis_permits.csv).
"""
import io, json, os, re, sys, time, urllib.parse, urllib.request
import pandas as pd
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/middlehousing-cache"
os.makedirs(CACHE, exist_ok=True)
TOKEN = "HvFoIfzodzpRML7a1104Ca2tM"
NOWSEL = "job_filing_number,filing_status,house_no,street_name,borough,block,lot,bin,commmunity_board,job_type,existing_dwelling_units,proposed_dwelling_units,filing_date,current_status_date,first_permit_date,approved_date,signoff_date,job_description,latitude,longitude,initial_cost,bbl,nta"
BISSEL = "job__,doc__,borough,house__,street_name,block,lot,bin__,job_type,job_status,job_status_descrp,latest_action_date,community___board,pre__filing_date,approved,fully_permitted,signoff_date,existing_dwelling_units,proposed_dwelling_units,job_description,gis_latitude,gis_longitude,initial_cost,bbl,gis_nta_name"


def get(ds, params):
    q = urllib.parse.urlencode(params)
    for attempt in range(5):
        try:
            req = urllib.request.Request(f"https://data.cityofnewyork.us/resource/{ds}.csv?" + q, headers={"X-App-Token": TOKEN})
            return pd.read_csv(io.StringIO(urllib.request.urlopen(req, timeout=600).read().decode()), dtype=str)
        except Exception as e:
            print("retry", ds, e, flush=True)
            time.sleep(10)
    raise SystemExit("failed " + ds)


def pull(name, ds, where, order, select="*"):
    path = os.path.join(CACHE, name)
    if os.path.exists(path):
        return pd.read_csv(path, dtype=str).fillna("")
    frames, off = [], 0
    while True:
        d = get(ds, {"$select": select, "$where": where, "$limit": 50000, "$offset": off, "$order": order})
        frames.append(d)
        off += 50000
        if len(d) < 50000:
            break
    d = pd.concat(frames, ignore_index=True)
    d.to_csv(path, index=False)
    return d.fillna("")


def pull_in(name, ds, field, values, select, order):
    path = os.path.join(CACHE, name)
    if os.path.exists(path):
        return pd.read_csv(path, dtype=str).fillna("")
    frames, vals = [], sorted(set(values))
    for i in range(0, len(vals), 150):
        chunk = ",".join("'%s'" % v for v in vals[i:i + 150])
        frames.append(get(ds, {"$select": select, "$where": f"{field} in({chunk})", "$limit": 50000, "$order": order}))
    d = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    d.to_csv(path, index=False)
    return d.fillna("")


now = pull("bk_dobnow.csv", "w9ak-ipjd", "borough='Brooklyn'", "job_filing_number", NOWSEL)
bis = pull("bk_bis.csv", "ic3t-wcy2", "borough='BROOKLYN'", "job__,doc__", BISSEL)
hdb = pull("hdb_bk.csv", "br6q-ssj3", "boro='3'", "job_number")
hnyc = pull("hdb_nyc_alt_loss.csv", "br6q-ssj3", "job_type='Alteration' AND classanet<0", "job_number")
print("DOB NOW rows", len(now), "| BIS rows", len(bis), "| HDB Brooklyn rows", len(hdb), "| HDB NYC alt-loss rows", len(hnyc), flush=True)

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
PREFILTER = re.compile(r'FAM|DWEL|D\.?U|UNIT|RESID|HOUSE|HOME|S\.?R\.?O|TENEMENT|APART|APT', re.I)
# Filings the rules flag that are not consolidations when read in full.
EXCLUDE = {"320230022": "2 duplex units become a basement unit and a triplex; still 2 units"}


def says_conversion(s):
    if not s or not PREFILTER.search(s):
        return False
    s = s.upper()
    return any(p.search(s) for p in PATTERNS) and not REVERSE.search(s)


now["sys"] = "N"
now["job"] = now.job_filing_number.str.split("-").str[0]
now["doc"] = now.job_filing_number.str.split("-").str[1].fillna("")
now["addr"] = (now.house_no.str.strip() + " " + now.street_name.str.strip()).str.upper().str.strip()
now["binx"], now["cb"] = now["bin"], now.commmunity_board
now["lat"], now["lon"] = now.latitude, now.longitude
now["filed"] = now.filing_date.str[:10]
bis["sys"] = "B"
bis["job"], bis["doc"] = bis["job__"], bis["doc__"]
bis["addr"] = (bis.house__.str.strip() + " " + bis.street_name.str.strip()).str.upper().str.strip()
bis["binx"], bis["cb"] = bis["bin__"], bis.community___board
bis["lat"], bis["lon"] = bis.gis_latitude, bis.gis_longitude
bis["filed"] = pd.to_datetime(bis.pre__filing_date, errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
cols = ["sys", "job", "doc", "addr", "binx", "cb", "block", "lot", "job_type", "existing_dwelling_units", "proposed_dwelling_units", "filed", "job_description", "lat", "lon"]
rows = pd.concat([now[cols], bis[cols]], ignore_index=True).fillna("")
rows["e"] = pd.to_numeric(rows.existing_dwelling_units, errors="coerce")
rows["p"] = pd.to_numeric(rows.proposed_dwelling_units, errors="coerce")
rows["u"] = (rows.e >= 2) & (rows.p == 1)
rows["x"] = rows.job_description.map(says_conversion)
jobs_total = rows.groupby(["sys", "job"]).ngroups
g = rows.groupby(["sys", "job"]).agg(u=("u", "any"), x=("x", "any"), pmax=("p", "max")).reset_index()
g = g[(g.u | g.x) & ~g.job.isin(EXCLUDE)]
print("DOB jobs checked", jobs_total, "| matched", len(g), flush=True)
mk = set(zip(g.sys, g.job))
rm = rows[[k in mk for k in zip(rows.sys, rows.job)]]
now_m = now[now.job.isin(set(g[g.sys == "N"].job))]
bis_m = bis[bis.job.isin(set(g[g.sys == "B"].job))]

# ---------------------------------------------------------------- permits for the matched jobs
npm = pull_in("bk_now_permits.csv", "rbx6-tga4", "job_filing_number", set(now_m.job_filing_number),
              "job_filing_number,work_permit,work_type,filing_reason,permit_status,approved_date,issued_date,expired_date", "job_filing_number,work_permit")
bpm = pull_in("bk_bis_permits.csv", "ipu4-2q9a", "job__", set(bis_m.job),
              "job__,job_doc___,job_type,work_type,permit_status,filing_status,permit_type,permit_sequence__,permit_subtype,issuance_date,expiration_date,permit_si_no", "job__,job_doc___,issuance_date")
print("permits: DOB NOW", len(npm), "| BIS", len(bpm), flush=True)
npm["job"] = npm.job_filing_number.str.split("-").str[0]
PERMITS = {}
for r in npm.itertuples():
    PERMITS.setdefault(("N", r.job), []).append(dict(n=r.work_permit, t=r.work_type, st=r.permit_status, i=r.issued_date[:10], x=r.expired_date[:10], f=r.job_filing_number))
for r in bpm.itertuples():
    PERMITS.setdefault(("B", r.job__), []).append(dict(n=r.permit_si_no, t=(r.permit_type + (" " + r.permit_subtype if r.permit_subtype else "")).strip(), st=r.permit_status,
                                                     i=str(pd.to_datetime(r.issuance_date, errors="coerce"))[:10].replace("NaT", ""),
                                                     x=str(pd.to_datetime(r.expiration_date, errors="coerce"))[:10].replace("NaT", ""), f=r.job__ + "-" + r.job_doc___, s=r.permit_sequence__))


def dob_status(sysname, raw):
    if sysname == "N":
        i1 = raw[raw.job_filing_number.str.endswith("-I1")]
        base = i1.iloc[0] if len(i1) else raw.iloc[0]
        st, cost = base.filing_status, base.initial_cost
        so = sorted(x[:10] for x in raw.signoff_date if x)
    else:
        lat = raw.sort_values("latest_action_date").iloc[-1]
        st, cost = lat.job_status_descrp, raw.iloc[0].initial_cost
        so = sorted(pd.to_datetime(raw.signoff_date.replace("", pd.NA).dropna(), errors="coerce").dropna().dt.strftime("%Y-%m-%d"))
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


def clean(s):
    return re.sub(r"\s+", " ", str(s).replace("&amp;", "&")).strip()


def title_addr(a):
    t = clean(a).title()
    return re.sub(r"(\d)(St|Nd|Rd|Th)\b", lambda m: m.group(1) + m.group(2).lower(), t)


rgroups = {k: v for k, v in rm.groupby(["sys", "job"])}
ngroups = {k: v for k, v in now_m.groupby("job")}
bgroups = {k: v for k, v in bis_m.groupby("job")}
jobrows = []
for j in g.itertuples():
    f = rgroups[(j.sys, j.job)]
    raw = ngroups[j.job] if j.sys == "N" else bgroups[j.job]
    st, stage, so, cost = dob_status(j.sys, raw)
    ur = f[f.u]
    src = ur.iloc[0] if len(ur) else f.iloc[0]
    xr = f[f.x]
    desc = xr.iloc[0].job_description if len(xr) else next((d for d in f.job_description if d), "")
    fd = sorted(d for d in f.filed if d)
    ll = f[(f.lat != "") & (f.lon != "")]
    docs = sorted(set(d for d in f.doc if d))
    jobrows.append(dict(sys=j.sys, job=j.job, docs=docs, addr=f.addr.mode().iloc[0], bin=f.binx.mode().iloc[0], cb=f.cb.mode().iloc[0] if (f.cb != "").any() else "",
                        block=f.block.iloc[0].lstrip("0"), lot=f.lot.iloc[0].lstrip("0"), jt=f.job_type.iloc[0], filed=fd[0] if fd else "",
                        e=src.e, p=src.p, pmax=j.pmax, u=bool(j.u), x=bool(j.x), status=st, stage=stage, signoff=so, cost=cost, desc=clean(desc),
                        lat=float(ll.lat.iloc[0]) if len(ll) else None, lon=float(ll.lon.iloc[0]) if len(ll) else None))
JOBS = pd.DataFrame(jobrows)

# ---------------------------------------------------------------- Housing Database
for c in ["classainit", "classaprop", "classanet"]:
    hdb[c] = pd.to_numeric(hdb[c], errors="coerce")
    hnyc[c] = pd.to_numeric(hnyc[c], errors="coerce")
hdb["cy"] = pd.to_numeric(hdb.compltyear, errors="coerce")
hnyc["cy"] = pd.to_numeric(hnyc.compltyear, errors="coerce")
hdb["base"] = hdb.job_number.str.split("-").str[0]
version = hdb.version.mode().iloc[0] if len(hdb) else ""
ALT = hdb[(hdb.job_type == "Alteration") & (hdb.classanet < 0) & ~hdb.job_status.str.startswith("9")].copy()
ALT["stage"] = ALT.job_status.str[0].map({"1": "filed", "2": "filed", "3": "permitted", "5": "done"})
print("HDB Brooklyn alt-loss jobs (not withdrawn)", len(ALT), flush=True)


def is_placeholder(b):
    return (not b) or bool(re.fullmatch(r"[1-5]0{6}", str(b)))


JOBS["key"] = [a if is_placeholder(b) else b for a, b in zip(JOBS.addr, JOBS.bin)]
ALT["key"] = [(n + " " + s).upper().strip() if is_placeholder(b) else b for n, s, b in zip(ALT.addressnum, ALT.addressst, ALT.bin)]
keys = sorted(set(JOBS.key) | set(ALT.key))
RANK = {"done": 3, "permitted": 2, "filed": 1, "withdrawn": 0}


def load(path):
    return json.load(open(os.path.join(ROOT, path)))["features"]


def tree(features):
    geoms = [shape(f["geometry"]) for f in features]
    return STRtree(geoms), geoms, features


NB = tree([f for f in load("data/city-neighborhoods.geojson") if f["properties"].get("boro") == "Brooklyn"])
HD = tree([f for f in load("data/historic-districts.geojson") if f["properties"].get("borough") == "BK"])
ZN = tree(load("data/cb6-zoning-clipped.geojson"))
CD = tree([f for f in load("cd-boundaries-simple.geojson") if str(f["properties"].get("cd", "")).startswith("3")])


def hit(T, pt, prop):
    t, geoms, feats = T
    for i in t.query(pt):
        if geoms[i].contains(pt):
            return feats[i]["properties"].get(prop)
    return ""


def nearest(T, pt, prop):
    t, geoms, feats = T
    i = t.nearest(pt)
    return feats[i]["properties"].get(prop) if i is not None else ""


jgroups = {k: v for k, v in JOBS.groupby("key")}
agroups = {k: v for k, v in ALT.groupby("key")}
EMPTYJ, EMPTYA = JOBS.iloc[0:0], ALT.iloc[0:0]


def bbl10_of(dj, ha):
    if len(dj) and dj.block.iloc[0] and dj.lot.iloc[0]:
        try:
            return "3%05d%04d" % (int(dj.block.iloc[0]), int(dj.lot.iloc[0]))
        except ValueError:
            pass
    if len(ha) and ha.bbl.iloc[0]:
        b = str(ha.bbl.iloc[0]).split(".")[0]
        if len(b) == 10:
            return b
    return ""


KEYBBL = {k: bbl10_of(jgroups.get(k, EMPTYJ), agroups.get(k, EMPTYA)) for k in keys}
pl = pull_in("pluto_cdcc.csv", "64uk-42ks", "bbl", [b for b in KEYBBL.values() if b], "bbl,cd,council,version", "bbl")
PLUTO = {str(r.bbl).split(".")[0]: str(r.cd) for r in pl.itertuples()}
PLUTO_CC = {str(r.bbl).split(".")[0]: str(r.council).split(".")[0] for r in pl.itertuples()}
CC = tree(load("data/council-districts.geojson"))
CCSRC = {"hdb": 0, "pluto": 0, "map": 0, "none": 0}
pluto_version = pl.version.mode().iloc[0] if len(pl) else ""
print("PLUTO lots found", len(PLUTO), "of", len([b for b in KEYBBL.values() if b]), "version", pluto_version, flush=True)
CDSRC = {"hdb": 0, "pluto": 0, "dob": 0, "map": 0}
index_rows, details = [], {}
for k in keys:
    dj = jgroups.get(k, EMPTYJ)
    ha = agroups.get(k, EMPTYA)
    lat = next((v for v in list(dj.lat) + [pd.to_numeric(x, errors="coerce") for x in ha.latitude] if v and not pd.isna(v)), None)
    lon = next((v for v in list(dj.lon) + [pd.to_numeric(x, errors="coerce") for x in ha.longitude] if v and not pd.isna(v)), None)
    addr = dj.addr.mode().iloc[0] if len(dj) else (ha.addressnum.iloc[0] + " " + ha.addressst.iloc[0]).upper().strip()
    one_dob = dj[(dj.u) | (dj.x & ((dj.pmax.isna()) | (dj.pmax <= 1)))] if len(dj) else dj
    one_hdb = ha[ha.classaprop == 1]
    cat = "one" if (len(one_dob) or len(one_hdb)) else ("fewer" if len(ha) else "check")
    prim = dj[dj.jt.str.upper().str.contains("CO|^A1$", regex=True)] if len(dj) else dj
    stages = list(ha.stage) if len(ha) else list((prim if len(prim) else dj).stage)
    stage = max(stages, key=lambda s: RANK[s]) if stages else "filed"
    filed = sorted([d for d in list(dj.filed) + [x[:10] for x in ha.datefiled] if d])
    comp = sorted(set(int(c) for c in ha[ha.stage == "done"].cy.dropna()))
    so = sorted(d for d in (prim if len(prim) else dj).signoff if d)
    ub = [v for v in list(dj.e) + list(ha.classainit) if not pd.isna(v)]
    ua = [v for v in list(dj[dj.u].p) + list(ha.classaprop) if not pd.isna(v)] if len(dj) or len(ha) else []
    pt = Point(lon, lat) if lat and lon else None
    # District as the city records it: the Housing Database's commntydst, then the lot's
    # district in PLUTO, then the community board on the DOB filing; the district
    # boundary map only when none of those is valid.
    valid = lambda c: bool(re.fullmatch(r"3(0[1-9]|1[0-8])", str(c)))
    cands = [c for c in ha.commntydst if valid(c)]
    src = "hdb"
    if not cands and valid(PLUTO.get(KEYBBL[k], "")):
        cands, src = [PLUTO[KEYBBL[k]]], "pluto"
    if not cands:
        cands, src = [c for c in dj.cb if valid(c)], "dob"
    cd = max(set(cands), key=cands.count) if cands else ""
    if not cd and pt is not None:
        cd, src = hit(CD, pt, "cd") or "", "map"
    CDSRC[src if cd else "map"] += 1
    # Council district, same order: Housing Database councildst, PLUTO council, then the council district map.
    vcc = lambda c: bool(re.fullmatch(r"([1-9]|[1-4]\d|5[01])", str(c)))
    ccs = [str(c) for c in ha.councildst if vcc(c)]
    csrc = "hdb"
    if not ccs and vcc(PLUTO_CC.get(KEYBBL[k], "")):
        ccs, csrc = [PLUTO_CC[KEYBBL[k]]], "pluto"
    cc = max(set(ccs), key=ccs.count) if ccs else ""
    if not cc and pt is not None:
        cc, csrc = str(hit(CC, pt, "cc") or ""), "map"
    CCSRC[csrc if cc else "none"] += 1
    nb = hd = zn = ""
    if pt is not None:
        nb = hit(NB, pt, "nb") or nearest(NB, pt, "nb")
        hd = hit(HD, pt, "area_name")
        if cd == "306":
            zn = hit(ZN, pt, "zone")
    bbl = ""
    if len(dj):
        bbl = dj.block.iloc[0] + "/" + dj.lot.iloc[0]
    elif len(ha) and ha.bbl.iloc[0]:
        b = str(ha.bbl.iloc[0]).split(".")[0]
        bbl = str(int(b[1:6])) + "/" + str(int(b[6:10])) if len(b) == 10 else ""
    bid = "" if is_placeholder(k) else k
    rid = bid or re.sub(r"[^A-Z0-9]+", "-", k).strip("-")
    jl = []
    for r in dj.sort_values("filed").itertuples():
        jl.append(dict(s=r.sys, j=r.job, docs=r.docs, f=r.filed, jt=r.jt, st=r.status, g=r.stage, so=r.signoff, m=("u" if r.u else "") + ("x" if r.x else ""),
                       e=None if pd.isna(r.e) else int(r.e), p=None if pd.isna(r.p) else int(r.p), d=r.desc,
                       pm=PERMITS.get((r.sys, r.job), [])))
    hl = [dict(j=r.job_number, f=r.datefiled[:10], st=r.job_status[3:], g=r.stage, i=int(r.classainit), p=int(r.classaprop), n=int(r.classanet),
               cy=None if pd.isna(r.cy) else int(r.cy), d=clean(r.job_desc)) for r in ha.sort_values("datefiled").itertuples()]
    xd = dj[dj.x]
    main = (xd if len(xd) else dj).sort_values("filed").iloc[0] if len(dj) else None
    desc = main.desc if main is not None else (hl[0]["d"] if hl else "")
    index_rows.append([rid, title_addr(addr), bid, bbl, int(cd[1:]) if cd else 0, round(lat, 6) if lat else None, round(lon, 6) if lon else None,
                       {"one": 0, "fewer": 1, "check": 2}[cat], {"done": 0, "permitted": 1, "filed": 2, "withdrawn": 3}[stage],
                       int(filed[0][:4]) if filed else None, comp[0] if comp else (int(so[0][:4]) if so else None),
                       int(max(ub)) if ub else None, int(min(ua)) if ua else None, int(-ha.classanet.sum()) if len(ha) else 0,
                       nb, hd, zn, " ".join(sorted(set(list(dj.job) + list(ha.job_number)))), int(cc) if cc else 0])
    details.setdefault(cd or "3", {})[rid] = dict(d=desc, jobs=jl, hj=hl)

FIELDS = ["id", "a", "bin", "bbl", "cd", "lat", "lon", "c", "g", "y", "cy", "ub", "ua", "lost", "nb", "hd", "zn", "jobs", "cc"]
IDX = pd.DataFrame(index_rows, columns=FIELDS)
print("buildings", len(IDX), IDX.c.value_counts().to_dict(), "stages", IDX.g.value_counts().to_dict(), "no coords", IDX.lat.isna().sum(), "no cd", (IDX.cd == 0).sum(), flush=True)
assert IDX.id.is_unique

# ---------------------------------------------------------------- Housing Database figures
comp = hdb[hdb.job_status.str.startswith("5")]
alt_c = comp[comp.job_type == "Alteration"]


def units(df):
    return int(df.classanet.sum())


def yr(df, a, b):
    return df[(df.cy >= a) & (df.cy <= b)]


def cd_stats(h):
    c = h[h.job_status.str.startswith("5")]
    a = c[c.job_type == "Alteration"]
    nw = h[~h.job_status.str.startswith("9")]
    nwa = nw[nw.job_type == "Alteration"]
    return dict(
        loss_10_24=-units(yr(a[a.classanet < 0], 2010, 2024)), loss_jobs_10_24=int(len(yr(a[a.classanet < 0], 2010, 2024))),
        loss_20_24=-units(yr(a[a.classanet < 0], 2020, 2024)),
        gain_10_24=units(yr(a[a.classanet > 0], 2010, 2024)),
        nb_10_24=units(yr(c[c.job_type == "New Building"], 2010, 2024)),
        demo_10_24=-units(yr(c[c.job_type == "Demolition"], 2010, 2024)),
        net_10_24=units(yr(c, 2010, 2024)),
        loss_all_open=-units(nwa[nwa.classanet < 0]), loss_all_open_jobs=int((nwa.classanet < 0).sum()),
        loss_to_one_10_24=-units(yr(a[(a.classanet < 0) & (a.classaprop == 1)], 2010, 2024)),
        loss_to_one_jobs_10_24=int(len(yr(a[(a.classanet < 0) & (a.classaprop == 1)], 2010, 2024))),
        loss_by_year={int(y): int(-v) for y, v in a[a.classanet < 0].groupby("cy").classanet.sum().items()},
    )


h6 = hdb[hdb.commntydst == "306"]
stats = cd_stats(h6)
stats["version"] = version
c6 = h6[h6.job_status.str.startswith("5")]
a6 = c6[c6.job_type == "Alteration"]
stats["jobs_by_year"] = {int(y): int(v) for y, v in a6[a6.classanet < 0].groupby("cy").size().items()}
stats["gain_by_year"] = {int(y): int(v) for y, v in a6[a6.classanet > 0].groupby("cy").classanet.sum().items()}
stats["nb_by_year"] = {int(y): int(v) for y, v in c6[c6.job_type == "New Building"].groupby("cy").classanet.sum().items()}
stats["demo_by_year"] = {int(y): int(-v) for y, v in c6[c6.job_type == "Demolition"].groupby("cy").classanet.sum().items()}
n6 = h6[~h6.job_status.str.startswith("9")]
stats["pipeline_net"] = units(n6[n6.job_status.str[0].isin(["1", "2", "3"])])


def cd_label(cd):
    return {"1": "MN", "2": "BX", "3": "BK", "4": "QN", "5": "SI"}[cd[0]] + "CB" + str(int(cd[1:]))


def ranking(df):
    s = df.groupby("commntydst").classanet.sum().sort_values()
    return [[cd_label(k), int(-v)] for k, v in s.items() if re.fullmatch(r"[1-5]\d\d", str(k)) and int(str(k)[1:]) <= 18]


cn = hnyc[hnyc.job_status.str.startswith("5")]
stats["rank_10_24"] = ranking(cn[(cn.cy >= 2010) & (cn.cy <= 2024)])
stats["rank_20_24"] = ranking(cn[(cn.cy >= 2020) & (cn.cy <= 2024)])
stats["rank_open"] = ranking(hnyc[~hnyc.job_status.str.startswith("9")])

bk = {}
for n in range(1, 19):
    code = "3%02d" % n
    s = cd_stats(hdb[hdb.commntydst == code])
    s.pop("loss_by_year")
    sub = IDX[IDX.cd == n]
    s.update(b_one=int((sub.c == 0).sum()), b_fewer=int((sub.c == 1).sum()), b_check=int((sub.c == 2).sum()),
             b_one_done=int(((sub.c == 0) & (sub.g == 0)).sum()), b_pre2010=int(((sub.c == 0) & (sub.y < 2010)).sum()))
    bk[n] = s
bk_all = cd_stats(hdb)
bk_all.pop("loss_by_year")


def by_year(df):
    c = df[df.job_status.str.startswith("5")]
    a = c[c.job_type == "Alteration"]
    return dict(
        loss={int(y): int(-v) for y, v in a[a.classanet < 0].groupby("cy").classanet.sum().items()},
        loss_jobs={int(y): int(v) for y, v in a[a.classanet < 0].groupby("cy").size().items()},
        gain={int(y): int(v) for y, v in a[a.classanet > 0].groupby("cy").classanet.sum().items()},
        nb={int(y): int(v) for y, v in c[c.job_type == "New Building"].groupby("cy").classanet.sum().items()},
        demo={int(y): int(-v) for y, v in c[c.job_type == "Demolition"].groupby("cy").classanet.sum().items()},
    )


def scope(df):
    s = cd_stats(df)
    s.pop("loss_by_year")
    s["y"] = by_year(df)
    return s


ch = dict(all=scope(hdb), cd={}, cc={})
for n in range(1, 19):
    ch["cd"][n] = scope(hdb[hdb.commntydst == "3%02d" % n])
for c in sorted(set(hdb.councildst) | set(str(x) for x in IDX.cc if x), key=lambda x: int(x) if str(x).isdigit() else 999):
    if str(c).isdigit():
        ch["cc"][int(c)] = scope(hdb[hdb.councildst == str(c)])

counts = dict(dob_now_rows=len(now), bis_rows=len(bis), dob_jobs=jobs_total, dob_matched=len(JOBS),
              dob_now_matched=int((JOBS.sys == "N").sum()), bis_matched=int((JOBS.sys == "B").sum()),
              now_permits=len(npm), bis_permits=len(bpm), hdb_rows=len(hdb), hdb_alt_loss=len(ALT), buildings=len(IDX),
              bis_first=str(pd.to_datetime(bis.pre__filing_date, errors="coerce").min())[:10], pluto_version=pluto_version, cd_source=CDSRC, cc_source=CCSRC,
              now_first=str(pd.to_datetime(now.filing_date, errors="coerce").min())[:10])
out = dict(built=time.strftime("%Y-%m-%d"), counts=counts, stats=stats, bk=bk, bk_all=bk_all, ch=ch)
os.makedirs(os.path.join(ROOT, "middlehousing", "bk"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "middlehousing", "data.json"), "w"), separators=(",", ":"))
rows_out = json.loads(IDX.to_json(orient="values"))
json.dump(dict(f=FIELDS, r=rows_out), open(os.path.join(ROOT, "middlehousing", "bk", "index.json"), "w"), separators=(",", ":"), ensure_ascii=False)
for cd, det in details.items():
    json.dump(det, open(os.path.join(ROOT, "middlehousing", "bk", "cd%s.json" % cd), "w"), separators=(",", ":"), ensure_ascii=False)
tot = sum(os.path.getsize(os.path.join(ROOT, "middlehousing", "bk", f)) for f in os.listdir(os.path.join(ROOT, "middlehousing", "bk")))
print("wrote data.json, bk/index.json", os.path.getsize(os.path.join(ROOT, "middlehousing", "bk", "index.json")) // 1024, "KB, bk/ total", tot // 1024, "KB", flush=True)
print(json.dumps(counts, indent=1))
print(json.dumps({k: v for k, v in stats.items() if not isinstance(v, (dict, list))}, indent=1))
