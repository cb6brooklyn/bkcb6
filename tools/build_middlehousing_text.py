#!/usr/bin/env python3
"""Build middlehousingstillmissing/thesis.json from the text export of
"Middle Housing Gone Missing" (Rebecca Kobert, Pratt Institute, 2025).

Usage: python3 tools/build_middlehousing_text.py <text export .txt>
The export is the Drive text rendering of the thesis PDF, with page markers
of the form "| [**Page N**]() |". PDF page N is page N-1 of the page images
served from /middlehousingstillmissing/pages/ (the PDF opens with one blank page).
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw = open(sys.argv[1]).read()
if raw.lstrip().startswith("{"):
    raw = json.loads(raw)["fileContent"]
parts = re.split(r"\|\s*\[\*\*Page (\d+)\*\*\]\(\)\s*\|", raw)
pdf = {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}


def clean(s):
    s = re.sub(r"\[([^\]]*)\]\(\)", r"\1", s)
    s = re.sub(r"\[\s*(https?://[^\]]*)\]\((https?://[^)]*)\)", r"\2", s)
    s = s.replace("\\-", "-").replace("\\.", ".").replace("\\<", "<").replace("\\#", "#").replace("\\*", "*")
    return s


def lines_of(body):
    body = re.sub(r"-{5}\s*\|\s*\|\s*\|\s*:-:\s*\|", "", body)
    out = []
    for ln in body.split("\n"):
        ln = clean(ln).rstrip()
        if not ln.strip() or re.fullmatch(r"\s*\|?\s*(:-:)?\s*\|?\s*", ln) or ln.strip() in ("-----",):
            continue
        out.append(ln.strip())
    return out


def strip_md(s):
    return re.sub(r"\*+", "", s).strip()


PAGES = []
for pno in sorted(pdf):
    if pno == 1:
        continue  # blank lead page in the PDF, not in the page images
    view = pno - 1
    ls = lines_of(pdf[pno])
    printed = None
    if ls and re.fullmatch(r"\d{1,3}", ls[-1]):
        printed = int(ls[-1])
        ls = ls[:-1]
    blocks, cur = [], []
    width = max([len(l) for l in ls] + [90])

    def flush(kind="p"):
        global cur
        if cur:
            blocks.append([kind, " ".join(cur).replace("- ", "-") if False else " ".join(cur)])
        cur = []

    for ln in ls:
        bold = re.fullmatch(r"\*\*(.+)\*\*", ln)
        ital = re.fullmatch(r"\*{1,3}(.+?)\*{1,3}", ln)
        if ln.startswith("***Figure") or ln.startswith("**Figure") or re.match(r"^\*{0,3}Figure \d", ln):
            flush()
            blocks.append(["fig", strip_md(ln)])
            continue
        if bold and len(ln) < 90:
            flush()
            blocks.append(["h", strip_md(ln)])
            continue
        if ital and (ln.startswith("*Source") or ln.startswith("*Sources") or ln.startswith("*“") or ln.startswith("*Recorded") or ln.startswith("*Brooklyn CD6")):
            flush()
            blocks.append(["src", strip_md(ln)])
            continue
        if re.match(r"^(\d+\.|[-•])\s", ln):
            flush()
        t = strip_md(ln) if ln.startswith("*") and ln.endswith("*") else ln.replace("**", "").replace("*", "")
        cur.append(t)
        if re.search(r"[.:?!”\")]$", t) and len(ln) < width * 0.86:
            flush()
    flush()
    # merge caption continuations into the preceding src block
    merged = []
    for b in blocks:
        if merged and b[0] == "src" and merged[-1][0] == "src":
            merged[-1][1] += " " + b[1]
        else:
            merged.append(b)
    text = " ".join(b[1] for b in merged)
    PAGES.append(dict(n=view, pr=printed, b=merged, t=text))

# join paragraphs that run across a page break
for i in range(1, len(PAGES)):
    prev, cur = PAGES[i - 1]["b"], PAGES[i]["b"]
    if prev and cur and prev[-1][0] == "p" and cur[0][0] == "p" and not re.search(r"[.:?!”\")]$", prev[-1][1]) and not re.match(r"^(\d+\.|[-•])\s", cur[0][1]):
        prev[-1][1] += " " + cur[0][1]
        cur.pop(0)
NPAGES = len(PAGES)
print("pages", NPAGES)

# ------------------------------------------------------------ sections located by heading text
HEADS = [
    ("Title page", 1, 1, "Middle Housing Gone Missing"),
    ("Table of Contents", 1, 2, "Table of Contents"),
    ("Acknowledgements", 1, 3, "Acknowledgements"),
    ("Abstract", 1, 4, "ABSTRACT"),
    ("Introduction", 1, None, "INTRODUCTION"),
    ("Purpose", 2, None, "Purpose"),
    ("Housing Consolidation", 2, None, "Housing Consolidation"),
    ("The Missing Middle Housing", 2, None, "The Missing Middle Housing"),
    ("City of Yes", 2, None, "City of Yes"),
    ("Methodology", 2, None, "Methodology"),
    ("Research Design", 2, None, "Research Design"),
    ("Analytical Limitations", 2, None, "Analytical Limitations"),
    ("Background", 1, None, "BACKGROUND"),
    ("History", 2, None, "History"),
    ("The Neighborhoods", 2, None, "The Neighborhoods"),
    ("Regulations", 2, None, "Regulations"),
    ("Literature Review", 1, None, "LITERATURE REVIEW"),
    ("Competing Ideologies", 2, None, "Competing Ideologies"),
    ("The Right to the City and The Just City", 2, None, "The Right to the City"),
    ("Zoning and Exclusionary Outcomes", 2, None, "Zoning and Exclusionary Outcomes"),
    ("Preservation and Exclusionary Outcomes", 2, None, "Preservation and Exclusionary Outcomes"),
    ("Adaptability and Conversions", 2, None, "Adaptability and Conversions"),
    ("Risk Displacement", 2, None, "Risk Displacement"),
    ("Findings", 1, None, "FINDINGS"),
    ("Housing Supply", 2, None, "Housing Supply"),
    ("Zoning Changes", 2, None, "Zoning Changes"),
    ("Demographic and Housing Changes", 2, None, "Demographic and Housing Changes"),
    ("City of Yes", 2, None, "CB6 endorsed the City of Yes"),
    ("Analysis", 1, None, "ANALYSIS"),
    ("Consolidations", 2, None, "Consolidations"),
    ("Contextual Zoning and Preservation", 2, None, "Contextual Zoning and Preservation"),
    ("Neighborhood Change", 2, None, "Neighborhood Change"),
    ("Homeownership Typologies", 2, None, "Homeownership Typologies"),
    ("An Example of Townhouse Acquisition", 2, None, "An Example of Townhouse Acquisition"),
    ("Housing in an Aging Neighborhood", 2, None, "Housing in an Aging Neighborhood"),
    ("Riskscapes", 2, None, "Riskscapes"),
    ("Recommendations: Reversing the Incentives", 1, None, "RECOMMENDATIONS"),
    ("Address market conditions through tax reform", 2, None, "Address market conditions through tax reform"),
    ("Consolidation Tax to combat unit loss", 2, None, "Consolidation Tax to combat unit loss"),
    ("Reform property taxes", 2, None, "Reform property taxes"),
    ("Employ a vacancy tax to deter warehousing", 2, None, "Employ a vacancy tax to deter warehousing"),
    ("Reform the housing landscape", 2, None, "Reform the housing landscape"),
    ("Optimize the City of Yes", 2, None, "Optimize the City of Yes"),
    ("Reverse contextual rezonings", 2, None, "Reverse contextual rezonings"),
    ("Expand LPC’s purview", 2, None, "Expand LPC"),
    ("Redensify rowhouses", 2, None, "Redensify rowhouses"),
    ("Allow age-in-place subdivisions", 2, None, "Allow age-in-place subdivisions"),
    ("Create a co-purchasing fund", 2, None, "Create a co-purchasing fund"),
    ("Conclusion", 1, None, "CONCLUSION"),
    ("Bibliography", 1, None, "Bibliography"),
]


def find_head(needle, start):
    nl = needle.lower()
    for P in PAGES:
        if P["n"] < start:
            continue
        for bi, b in enumerate(P["b"]):
            if b[0] == "h" and b[1].lower().startswith(nl):
                return P["n"], bi
    for P in PAGES:
        if P["n"] < start:
            continue
        for bi, b in enumerate(P["b"]):
            if b[1].lower().startswith(nl):
                return P["n"], bi
    for P in PAGES:
        if P["n"] >= start and nl in P["t"].lower():
            return P["n"], 0
    return None, None


secs, cursor = [], 4
for title, lvl, fixed, needle in HEADS:
    if fixed:
        secs.append(dict(t=title, l=lvl, p=fixed, bi=0))
        continue
    p, bi = find_head(needle, cursor)
    if p is None:
        print("NOT FOUND", title)
        continue
    secs.append(dict(t=title, l=lvl, p=p, bi=bi))
    cursor = p

# body blocks per section (from its heading up to the next heading)
flat = [(P["n"], bi, b) for P in PAGES for bi, b in enumerate(P["b"])]
pos = {(n, bi): i for i, (n, bi, b) in enumerate(flat)}
for i, s in enumerate(secs):
    if s["p"] <= 3:
        s["c"] = []
        continue
    a = pos.get((s["p"], s["bi"]), 0)
    nxt = [pos.get((t["p"], t["bi"]), len(flat)) for t in secs[i + 1:] if t["p"] > 3]
    e = min([x for x in nxt if x > a] or [len(flat)])
    body = flat[a:e]
    if body and body[0][2][0] == "h":
        body = body[1:]
    s["c"] = [[b[0], b[1], n] for n, bi, b in body]
    del s["bi"]

figs = []
for P in PAGES:
    for b in P["b"]:
        m = re.match(r"Figure\s+(\d+[A-Z]?)\.\s*(.+)", b[1])
        if b[0] == "fig" and m:
            figs.append(dict(id=m.group(1), t=m.group(2).strip().rstrip("."), p=P["n"]))

out = dict(title="Middle Housing Gone Missing: Mediations of Neighborhood Change in Brooklyn Community District 6, 2003-2024",
           author="Rebecca J. Kobert", n=NPAGES, pages=[dict(n=P["n"], pr=P["pr"], t=P["t"]) for P in PAGES], secs=secs, figs=figs)
json.dump(out, open(os.path.join(ROOT, "middlehousingstillmissing", "thesis.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print("sections", len(secs), "figures", len(figs))
for s in secs:
    print(s["l"], s["p"], s["t"], len(s.get("c", [])))
print([ (f["id"], f["p"]) for f in figs])
