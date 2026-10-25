#!/usr/bin/env python3
"""Build the CB6 glossary and guide to regulations.

Reads every data/glossary/sources/*.json (one file per source document or page)
and writes:
  data/glossary.json            the site's glossary + rules, by policy area and agency
  app/data/civic/glossary.json  the apps' glossary (same terms, keeps the app's old keys)

Run: python3 tools/build_glossary.py
"""
import glob, json, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AREAS = [
    ("zoning", "Zoning & Land Use"),
    ("process", "Public Review & Approvals"),
    ("env", "Environmental Review"),
    ("preservation", "Landmarks & Preservation"),
    ("buildings", "Buildings & Construction"),
    ("housing", "Housing: Tenants & Owners"),
    ("streets", "Streets & Transportation"),
    ("sanitation", "Sanitation & Recycling"),
    ("business", "Business & Licensing"),
    ("government", "Laws, Budget & Government"),
]
AREA_KEYS = {k for k, _ in AREAS}

# code: (name, logo path or None)
AGENCIES = {
    "DCP": ("Department of City Planning", "/assets/agency-logos/dcp.png"),
    "CPC": ("City Planning Commission", "/assets/agency-logos/dcp.png"),
    "DOB": ("Department of Buildings", "/assets/agency-logos/dob.png"),
    "HPD": ("Housing Preservation & Development", "/assets/agency-logos/hpd.png"),
    "NYCHA": ("NYC Housing Authority", "/assets/agency-logos/nycha.png"),
    "RGB": ("Rent Guidelines Board", "/assets/agency-logos/rgb.png"),
    "HCR": ("NYS Homes & Community Renewal", "/assets/agency-logos/nys/homes-and-community-renewal.png"),
    "DOT": ("Department of Transportation", "/assets/agency-logos/nyc-dot.png"),
    "DSNY": ("Department of Sanitation", "/assets/agency-logos/dsny.png"),
    "DEP": ("Department of Environmental Protection", "/assets/agency-logos/dep.png"),
    "Parks": ("NYC Parks", "/assets/agency-logos/dpr.png"),
    "LPC": ("Landmarks Preservation Commission", "/assets/agency-logos/lpc.png"),
    "BSA": ("Board of Standards and Appeals", "/assets/agency-logos/bsa.png"),
    "FDNY": ("Fire Department", "/assets/agency-logos/fdny.png"),
    "DOHMH": ("Department of Health", "/assets/agency-logos/dohmh.png"),
    "DCWP": ("Consumer and Worker Protection", "/assets/agency-logos/dcwp.png"),
    "SBS": ("Small Business Services", "/assets/agency-logos/sbs.png"),
    "SLA": ("State Liquor Authority", "/assets/agency-logos/nysla.png"),
    "NYPD": ("Police Department", "/assets/agency-logos/nypd.png"),
    "MTA": ("Metropolitan Transportation Authority", "/assets/agency-logos/nys/metropolitan-transportation-authority.png"),
    "Council": ("City Council", "/assets/agency-logos/nycc.png"),
    "Mayor": ("Office of the Mayor", "/assets/agency-logos/om.png"),
    "OMB": ("Office of Management and Budget", "/assets/agency-logos/omb.png"),
    "Comptroller": ("City Comptroller", "/assets/agency-logos/office-of-the-new-york-city-comptroller.png"),
    "PublicAdvocate": ("Public Advocate", "/assets/agency-logos/pub-adv.png"),
    "BP": ("Borough President", "/assets/agency-logos/office-of-the-borough-president-of-brooklyn.png"),
    "CB": ("Community Board", "/assets/agency-logos/cb.png"),
    "OATH": ("Office of Administrative Trials and Hearings", "/assets/agency-logos/oath.png"),
    "DOF": ("Department of Finance", "/assets/agency-logos/dof.png"),
    "EDC": ("Economic Development Corporation", "/site-icons/agencies/nycedc.png"),
    "HDC": ("Housing Development Corporation", "/site-icons/agencies/nyc-hdc.png"),
    "TLC": ("Taxi and Limousine Commission", "/assets/agency-logos/tlc.png"),
    "DDC": ("Department of Design and Construction", "/assets/agency-logos/ddc.png"),
    "SCA": ("School Construction Authority", "/assets/agency-logos/sca.png"),
    "NYS": ("New York State", None),
    "NYSDEC": ("NYS Department of Environmental Conservation", "/assets/agency-logos/nys/department-of-environmental-conservation.png"),
    "Courts": ("Courts (Housing Court and others)", None),
    "Loft Board": ("Loft Board", "/assets/agency-logos/loft.png"),
    "PDC": ("Public Design Commission", "/assets/agency-logos/pdc.png"),
    "DCLA": ("Department of Cultural Affairs", "/assets/agency-logos/dcla.png"),
    "HRA": ("Human Resources Administration", "/assets/agency-logos/hra.png"),
    "BIC": ("Business Integrity Commission", "/assets/agency-logos/bic.png"),
    "OTI": ("Office of Technology and Innovation", "/assets/agency-logos/oti.png"),
    "CCHR": ("Commission on Human Rights", "/assets/agency-logos/cchr.png"),
    "OER": ("Office of Environmental Remediation", "/assets/agency-logos/oer.png"),
    "MOPD": ("Mayor's Office for People with Disabilities", "/assets/agency-logos/mopd.png"),
    "Fed": ("Federal government", None),
}
ALIASES = {
    "NYCDOT": "DOT", "DPR": "Parks", "PARKS": "Parks", "CITYCOUNCIL": "Council", "COUNCIL": "Council",
    "DHCR": "HCR", "NYSHCR": "HCR", "ECB": "OATH", "MAYOR": "Mayor", "COMPTROLLER": "Comptroller",
    "PUBLICADVOCATE": "PublicAdvocate", "PA": "PublicAdvocate", "BOROUGHPRESIDENT": "BP",
    "COMMUNITYBOARD": "CB", "DCA": "DCWP", "DOHMH": "DOHMH", "DOH": "DOHMH", "NYSLA": "SLA",
    "NYCEDC": "EDC", "NYCHDC": "HDC", "DEC": "NYSDEC", "HOUSINGCOURT": "Courts", "COURT": "Courts",
    "COURTS": "Courts", "STATE": "NYS", "NYSTATE": "NYS", "FEDERAL": "Fed", "HUD": "Fed", "DOITT": "OTI", "LOFTBOARD": "Loft Board",
}
# Order sources are trusted when two define the same term (first wins the definition).
PRIORITY = ["cb6", "dcp-glossary", "zoning-handbook", "dob", "hpd-abcs", "sdm", "dsny", "nycbusiness", "concretebills", "dcp-abcs"]


def canon_agency(a):
    if not a:
        return None
    k = re.sub(r"[^A-Za-z]", "", a)
    if a in AGENCIES:
        return a
    if k.upper() in ALIASES:
        return ALIASES[k.upper()]
    for code in AGENCIES:
        if code.upper() == k.upper():
            return code
    return a.strip()


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", norm(s))).strip("-")[:80]


def clean(s):
    if s is None:
        return None
    s = s.replace("—", ", ").replace(" ,", ",").replace(",,", ",")
    return re.sub(r"\s+", " ", s).strip()


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "data/glossary/sources/*.json")))
    srcs, terms, rules = {}, {}, []
    order = {k: i for i, k in enumerate(PRIORITY)}
    loaded = []
    for f in files:
        d = json.load(open(f))
        s = d["source"]
        loaded.append((order.get(s["key"], 99), s, d))
    loaded.sort(key=lambda x: x[0])
    for _, s, d in loaded:
        key = s["key"]
        srcs[key] = {"name": s["name"], "url": s.get("url"), "agency": canon_agency(s.get("agency"))}
        for t in d.get("terms", []):
            name = clean(t.get("term"))
            df = clean(t.get("def"))
            if not name or not df:
                continue
            area = t.get("area") if t.get("area") in AREA_KEYS else None
            ags = [canon_agency(a) for a in (t.get("agencies") or []) if canon_agency(a)]
            ref = {"src": key}
            if t.get("page"):
                ref["page"] = t["page"]
            if t.get("url"):
                ref["url"] = t["url"]
            k = norm(name)
            if k in terms:
                e = terms[k]
                for a in ags:
                    if a not in e["agencies"]:
                        e["agencies"].append(a)
                for a in t.get("aka") or []:
                    if a and a not in e["aka"] and norm(a) != k:
                        e["aka"].append(clean(a))
                if not any(r["src"] == key for r in e["refs"]):
                    e["refs"].append(ref)
                if not e["area"] and area:
                    e["area"] = area
                continue
            terms[k] = {
                "id": slug(name), "term": name, "aka": [clean(a) for a in (t.get("aka") or []) if a],
                "def": df, "area": area or "government", "agencies": ags, "refs": [ref],
                "tags": clean(t.get("tags")) or "",
            }
            if t.get("legal"):
                terms[k]["zr"] = True
        for r in d.get("rules", []):
            if not r.get("rule") or not r.get("what"):
                continue
            ref = {"src": key}
            if r.get("page"):
                ref["page"] = r["page"]
            if r.get("url"):
                ref["url"] = r["url"]
            rules.append({
                "id": "rule-" + slug(key + " " + r["rule"]), "rule": clean(r["rule"]), "what": clean(r["what"]),
                "who": clean(r.get("who")), "penalty": clean(r.get("penalty")),
                "area": r.get("area") if r.get("area") in AREA_KEYS else "government",
                "agencies": [canon_agency(a) for a in (r.get("agencies") or []) if canon_agency(a)], "refs": [ref],
            })
    tl = sorted(terms.values(), key=lambda e: norm(e["term"]))
    seen = {}
    for e in tl:  # unique ids
        if e["id"] in seen:
            seen[e["id"]] += 1
            e["id"] += "-" + str(seen[e["id"]])
        else:
            seen[e["id"]] = 1
    # rule ids unique too
    rs = {}
    for r in rules:
        if r["id"] in rs:
            rs[r["id"]] += 1
            r["id"] += "-" + str(rs[r["id"]])
        else:
            rs[r["id"]] = 1
    used = sorted({a for x in tl + rules for a in x["agencies"]})
    ag = {a: {"name": AGENCIES.get(a, (a, None))[0], "logo": AGENCIES.get(a, (a, None))[1]} for a in used}
    out = {
        "updated": __import__("datetime").date.today().isoformat(),
        "areas": [{"key": k, "name": n} for k, n in AREAS],
        "agencies": ag, "sources": srcs, "terms": tl, "rules": rules,
    }
    json.dump(out, open(os.path.join(ROOT, "data/glossary.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    app = {
        "categories": dict([("all", "All")] + AREAS),
        "terms": [{"term": e["term"], "cat": e["area"], "def": e["def"], "agencies": e["agencies"]} for e in tl],
        "rules": [{"rule": r["rule"], "cat": r["area"], "what": r["what"], "who": r["who"], "penalty": r["penalty"], "agencies": r["agencies"]} for r in rules],
    }
    json.dump(app, open(os.path.join(ROOT, "app/data/civic/glossary.json"), "w"), ensure_ascii=False, indent=1)
    by_area = {}
    for x in tl:
        by_area[x["area"]] = by_area.get(x["area"], 0) + 1
    print(f"{len(tl)} terms, {len(rules)} rules, {len(ag)} agencies, {len(srcs)} sources")
    print("terms by area:", by_area)
    missing = [a for a in ag if not ag[a]["logo"] or not os.path.exists(ROOT + (ag[a]["logo"] or "/x"))]
    print("agencies without logo file:", missing)


if __name__ == "__main__":
    main()
