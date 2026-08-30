#!/usr/bin/env python3
"""
Build data/civic-calendar/bp.json: borough president public hearings.

None of the five borough president websites publishes a machine-readable
calendar (see probe.json), but all five file their public hearing notices in the
City Record under "Borough President - <Borough>", which is where their ULURP
and land use hearings appear. This reuses the City Record extractor, so the same
rules apply: an unambiguous date and time or the record is skipped, and
cancelled or postponed notices are dropped.

Notices are sparse, a handful per borough per year, so this reads a wider
window than the agency hearings build.

Usage:  python3 scripts/build_bp_calendar.py
"""

import json
import os
import sys
from datetime import date, datetime, timedelta, timezone

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_hearings_calendar import (  # noqa: E402
    CANCELLED, SRC, UA, TIMEOUT, extract, plain)

OUT_DIR = "data/civic-calendar"
OUT = os.path.join(OUT_DIR, "bp.json")
LOOKBACK_DAYS = 270

BOROUGHS = ["Brooklyn", "Bronx", "Manhattan", "Queens", "Staten Island"]
AGENCIES = ["Borough President - %s" % b for b in BOROUGHS]
SITES = {
    "Brooklyn": "https://brooklyn-usa.org/",
    "Bronx": "https://bronxboropres.nyc.gov/",
    "Manhattan": "https://www.manhattanbp.nyc.gov/",
    "Queens": "https://queensbp.nyc.gov/",
    "Staten Island": "https://www.statenislandusa.com/",
}


def fetch(since):
    where = ("start_date > '%sT00:00:00' AND (%s)"
             % (since.isoformat(),
                " OR ".join("agency_name='%s'" % a for a in AGENCIES)))
    r = requests.get(SRC, params={"$limit": 2000, "$where": where,
                                  "$order": "start_date DESC"},
                     headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def main():
    today = datetime.now(timezone.utc).date()
    rows = fetch(today - timedelta(days=LOOKBACK_DAYS))
    print("borough president notices read: %d" % len(rows))

    by_borough = {b: [] for b in BOROUGHS}
    skipped = cancelled = 0
    seen = set()

    for row in rows:
        agency = plain(row.get("agency_name")) or ""
        borough = agency.replace("Borough President - ", "").strip()
        if borough not in by_borough:
            skipped += 1
            continue
        notice_raw = (row.get("start_date") or "")[:10]
        try:
            notice_date = date.fromisoformat(notice_raw)
        except ValueError:
            skipped += 1
            continue
        title = plain(row.get("short_title")) or ""
        text = plain(row.get("additional_description_1")) or ""
        if CANCELLED.search(title) or CANCELLED.search(text[:400]):
            cancelled += 1
            continue
        found = extract(title + ". " + text, notice_date, today)
        if not found:
            skipped += 1
            continue
        when, clock = found
        if when < today:
            continue
        key = (borough, when.isoformat(), title.lower())
        if key in seen:
            continue
        seen.add(key)
        by_borough[borough].append({
            "date": when.isoformat(),
            "label": title or ("%s Borough President public hearing" % borough),
            "time": clock,
            "borough": borough,
            "source": "city-record",
            "notice_date": notice_raw,
            "href": "https://a856-cityrecord.nyc.gov/RequestDetail/%s"
                    % row.get("request_id"),
            "linkText": "Notice \u2197",
        })

    for events in by_borough.values():
        events.sort(key=lambda e: (e["date"], e["time"]))

    os.makedirs(OUT_DIR, exist_ok=True)
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "NYC Open Data dg92-zbpx (City Record Online)",
        "note": ("Borough president hearing dates are extracted from City "
                 "Record notice text; notices whose date or time could not be "
                 "read unambiguously are omitted."),
        "sites": SITES,
        "boroughs": {b: {"borough": b, "site": SITES[b], "events": ev}
                     for b, ev in by_borough.items()},
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)

    total = sum(len(v) for v in by_borough.values())
    for b in BOROUGHS:
        print("  %-14s %d upcoming" % (b, len(by_borough[b])))
    print("upcoming hearings kept: %d" % total)
    print("notices with no unambiguous date/time: %d" % skipped)
    print("notices dropped as cancelled or postponed: %d" % cancelled)
    print("wrote: %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
