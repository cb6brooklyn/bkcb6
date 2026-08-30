#!/usr/bin/env python3
"""
Probe every Brooklyn community board for a machine-readable calendar feed.

The existing calendar refresh already pulls CB6 over The Events Calendar iCal
endpoint, which proves that pattern works from GitHub Actions. This script asks
the same question of the other seventeen boards, plus the alternate hosts and
feed shapes their sites use, and writes what it finds to
data/civic-calendar/probe.json.

It fetches nothing but calendars and writes no site content. Run it from the
Action; local sandboxes are blocked by the nyc.gov WAF.

Usage:  python3 scripts/probe_civic_calendars.py
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

import requests

OUT_DIR = "data/civic-calendar"
OUT = os.path.join(OUT_DIR, "probe.json")
BOARDS_SRC = ("https://data.cityofnewyork.us/resource/ruf7-3wgc.json"
              "?$limit=100&borough=Brooklyn")
UA = {"User-Agent": "bkcb6.app civic calendar probe (mracioppo@cb.nyc.gov)"}
TIMEOUT = 25


def board_number(row):
    # community_board_1 is a borough-prefixed code: 306 -> Brooklyn CB6
    return int(str(row["community_board_1"])[1:])


def load_boards():
    r = requests.get(BOARDS_SRC, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    rows = r.json()
    out = []
    for row in rows:
        site = (row.get("cb_website") or {}).get("url") or ""
        out.append({
            "cb": board_number(row),
            "site": site,
            "meeting_rule": row.get("cb_board_meeting") or "",
        })
    out.sort(key=lambda b: b["cb"])
    return out


def candidates(cb, site):
    """Feed URLs worth trying for one board, most likely first."""
    urls = []
    host = ""
    m = re.match(r"https?://([^/]+)(/[^?#]*)?", site or "")
    if m:
        host, path = m.group(1), (m.group(2) or "/")
        base = "https://%s%s" % (host, path.rstrip("/"))
        # cbbrooklyn.cityofnewyork.us/cb9/ style: feeds hang off the sub-path
        if "cbbrooklyn.cityofnewyork.us" in host:
            urls += [base + "/events/list/?ical=1",
                     base + "/wp-json/tribe/events/v1/events?per_page=50"]
        # independent org sites
        elif "nyc.gov" not in host:
            root = "https://%s" % host
            urls += [root + "/events/list/?ical=1",
                     root + "/wp-json/tribe/events/v1/events?per_page=50",
                     root + "/calendar/?ical=1",
                     root + "/events/?ical=1"]
    # every board also has a cityofnewyork.us WordPress twin, which is what
    # CB6's working feed uses even though the directory lists a www1.nyc.gov URL
    twin = "https://brooklyncb%d.cityofnewyork.us" % cb
    urls += [twin + "/events/list/?ical=1",
             twin + "/wp-json/tribe/events/v1/events?per_page=50"]
    seen, uniq = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def classify(resp):
    """What did we actually get back?"""
    body = resp.text or ""
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "BEGIN:VCALENDAR" in body[:4000]:
        n = body.count("BEGIN:VEVENT")
        return "ical", n
    if "json" in ctype or body.strip().startswith("{"):
        try:
            data = resp.json()
        except ValueError:
            return "json-unparseable", 0
        if isinstance(data, dict) and "events" in data:
            return "tec-rest", len(data.get("events") or [])
        return "json-other", 0
    if "<html" in body[:2000].lower():
        return "html", 0
    return "unknown", 0


def probe_one(url):
    try:
        r = requests.get(url, headers=UA, timeout=TIMEOUT, allow_redirects=True)
    except Exception as exc:
        return {"url": url, "ok": False, "error": type(exc).__name__}
    kind, count = classify(r)
    return {
        "url": url,
        "ok": r.status_code == 200 and kind in ("ical", "tec-rest") and count > 0,
        "status": r.status_code,
        "kind": kind,
        "events": count,
        "final_url": r.url if r.url != url else None,
    }


def main():
    boards = load_boards()
    results = []
    for b in boards:
        attempts = []
        winner = None
        for url in candidates(b["cb"], b["site"]):
            res = probe_one(url)
            attempts.append(res)
            if res.get("ok"):
                winner = res
                break
        results.append({
            "cb": b["cb"],
            "site": b["site"],
            "meeting_rule": b["meeting_rule"],
            "feed": winner["url"] if winner else None,
            "feed_kind": winner["kind"] if winner else None,
            "feed_events": winner["events"] if winner else 0,
            "attempts": attempts,
        })
        tag = "FEED  " if winner else "none  "
        print("%s CB%-2d %s" % (tag, b["cb"],
                                winner["url"] if winner else b["site"]))

    os.makedirs(OUT_DIR, exist_ok=True)
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "borough": "Brooklyn",
        "boards": results,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)

    found = [r for r in results if r["feed"]]
    print("\n%d of %d Brooklyn boards expose a usable calendar feed"
          % (len(found), len(results)))
    print("total events visible across those feeds: %d"
          % sum(r["feed_events"] for r in found))
    print("no feed: %s" % (", ".join("CB%d" % r["cb"]
                                     for r in results if not r["feed"]) or "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
