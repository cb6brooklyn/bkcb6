#!/usr/bin/env python3
"""Early voting sites on Halloween (Sat Oct 31, 2026) for the Spooky CB6 map: data/trick-or-streets/earlyvote.json.
Every early voting site assigned to a CB6 election district (an ED at least half inside the CB6 boundary), from the same
files bkcb6.app's election pages use: app/data/civic/ed-pollsites.json (BOE sites by ED), data/eds/ad{44,51,52,61}.geojson,
and the Oct 31 early voting hours in elections.html."""
import json, re, collections
from shapely.geometry import shape

DAY = "2026-10-31"
html = open("elections.html").read()
m = re.search(r"\['%s','[A-Za-z]+','[^']+',(\d+),(\d+)\]" % DAY, html)
o, c = int(m.group(1)), int(m.group(2))
clock = lambda h: f"{(h % 12) or 12}:00 {'PM' if h >= 12 else 'AM'}"
cb = json.load(open("data/cb6_boundary.geojson"))
g = shape(cb["features"][0]["geometry"] if "features" in cb else cb.get("geometry", cb))
ps = json.load(open("app/data/civic/ed-pollsites.json"))
sites = collections.OrderedDict()
for ad in (44, 51, 52, 61):
    for f in json.load(open(f"data/eds/ad{ad}.geojson"))["features"]:
        sh = shape(f["geometry"])
        if not sh.is_valid:
            sh = sh.buffer(0)
        if not sh.area or sh.intersection(g).area / sh.area < 0.5:
            continue
        r = ps.get(f["properties"]["e"])
        if not r or not r.get("e"):
            continue
        e = r["e"]
        s = sites.setdefault(e[1], {"name": e[0], "addr": e[1], "entrance": e[3], "lat": float(e[5]), "lng": float(e[6]), "eds": []})
        s["eds"].append(f["properties"]["e"])
items = []
for s in sites.values():
    addr = re.sub(r",\s*Brooklyn,\s*NY\s+\d{5}$", "", s["addr"]).strip()
    items.append({"src": "vote", "id": "v-" + re.sub(r"[^a-z0-9]+", "-", s["name"].lower()).strip("-"), "name": s["name"],
                  "kind": "Early voting", "group": "vote", "org": "NYC Board of Elections", "date": DAY,
                  "time": f"{clock(o)} to {clock(c)}", "where": addr + (" · " + s["entrance"][0].upper() + s["entrance"][1:] if s["entrance"] and not re.search(r"\d+\s+\d*\w+\s+(street|avenue)", s["entrance"], re.I) else ""),
                  "eds": len(s["eds"]), "cds": [6], "lat": s["lat"], "lng": s["lng"], "lines": []})
json.dump({"about": "Early voting sites for CB6 election districts on Saturday, October 31, 2026, with that day's hours, from the bkcb6.app election pages.", "items": items},
          open("data/trick-or-streets/earlyvote.json", "w"), indent=1, ensure_ascii=False)
print(len(items), "sites", clock(o), "to", clock(c))
