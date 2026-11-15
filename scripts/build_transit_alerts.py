#!/usr/bin/env python3
"""Subway, bus and rail service alerts for the apps' notifications.

Reads the MTA's public alerts feed (no key) and writes:
  app/data/civic/alerts/transit.json  {"updated", "alerts": [{id, kind, routes, type, status, title, body, start, end}]}
      Only alerts in effect right now. status is "now" for delays and changes as they happen, "planned" for planned work.
  app/data/civic/alerts/routes.json   {"subway": [...], "bus": [...]} each {value, label, color}
      The lines a person can choose in the app, from transit.json and every board's bus map.
The apps' notifications.json topics point at these files, so a new kind of alert is a file change, not a build.
"""
import glob, json, os, re, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "app/data/civic/alerts")
FEED = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fall-alerts.json"
KIND = {"MTASBWY": "subway", "MTA NYCT": "bus", "MTABC": "bus", "LI": "lirr", "MNR": "metro-north"}


def text(t):
    for tr in (t or {}).get("translation", []):
        if tr.get("language") == "en":
            return re.sub(r"\s+\n", "\n", tr.get("text", "")).strip()
    return ""


def routes():
    subway = json.load(open(os.path.join(ROOT, "app/data/civic/transit.json"))).get("routes", {})
    sub = [{"value": k, "label": f"{k} train", "color": v.get("color", "")} for k, v in subway.items()]
    order = lambda r: (not r["value"][0].isdigit(), r["value"])
    bus = {}
    for f in glob.glob(os.path.join(ROOT, "app/data/civic/transport/cb-*.json")):
        for b in json.load(open(f)).get("bus", []):
            p = b.get("p") or []
            if len(p) >= 3 and p[0] not in bus:
                bus[p[0]] = {"value": p[0], "label": f"{p[0]} · {p[2]}", "color": "#" + p[1].lstrip("#")}
    nat = lambda v: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", v)]
    return {"subway": sorted(sub, key=order), "bus": sorted(bus.values(), key=lambda r: nat(r["value"]))}


def main():
    req = urllib.request.Request(FEED, headers={"User-Agent": "bkcb6.app"})
    feed = json.load(urllib.request.urlopen(req, timeout=60))
    now = time.time()
    out = []
    for e in feed.get("entity", []):
        a = e.get("alert", {})
        per = a.get("active_period") or [{}]
        live = [p for p in per if p.get("start", 0) <= now <= (p.get("end") or 9e12)]
        if not live:
            continue
        ents = a.get("informed_entity", [])
        kinds = sorted({KIND.get(i.get("agency_id"), "other") for i in ents})
        rts = sorted({i.get("route_id") for i in ents if i.get("route_id")})
        if not rts:
            continue
        m = a.get("transit_realtime.mercury_alert", {})
        typ = m.get("alert_type", "")
        head, body = text(a.get("header_text")), text(a.get("description_text"))
        out.append({
            "id": e.get("id"), "kind": kinds, "routes": rts, "type": typ,
            "status": "planned" if typ.startswith("Planned") else "now",
            "title": head[:180], "body": (body or head)[:400],
            "start": live[0].get("start"), "end": live[0].get("end"),
        })
    out.sort(key=lambda r: r["id"])
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "transit.json")
    old = json.load(open(path)) if os.path.exists(path) else {}
    # Only rewrite when the alerts themselves change, so a quiet feed makes no commit.
    if old.get("alerts") != out:
        json.dump({"updated": int(now), "alerts": out}, open(path, "w"), ensure_ascii=False, separators=(",", ":"))
    r = routes()
    rp = os.path.join(OUT, "routes.json")
    if not os.path.exists(rp) or json.load(open(rp)) != r:
        json.dump(r, open(rp, "w"), ensure_ascii=False, indent=0)
    print(len(out), "alerts in effect;", len(r["subway"]), "subway lines,", len(r["bus"]), "bus routes")


if __name__ == "__main__":
    main()
