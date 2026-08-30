#!/usr/bin/env python3
"""
Build data/civic-calendar/council.json from the NYC Council's Legistar calendar.

Legistar's public API host (webapi.legistar.com) refuses requests from data
centre IPs, but the human calendar at legistar.council.nyc.gov/Calendar.aspx
serves the same grid: body, date, time, location, and a per-meeting detail and
iCal link. This parses that grid.

Output shape matches the calendar's own event objects so calendar.html can read
it directly, keyed by ISO date.

Usage:  python3 scripts/build_council_calendar.py
"""

import html
import json
import os
import re
import sys
from datetime import datetime, timezone

import requests

CAL_URL = "https://legistar.council.nyc.gov/Calendar.aspx"
BASE = "https://legistar.council.nyc.gov/"
OUT_DIR = "data/civic-calendar"
OUT = os.path.join(OUT_DIR, "council.json")
UA = {"User-Agent": "bkcb6.app civic calendar (mracioppo@cb.nyc.gov)"}
TIMEOUT = 30

ROW_SPLIT = re.compile(
    r'<tr[^>]*id="ctl00_ContentPlaceHolder1_gridCalendar_ctl00__\d+"')
CELL = re.compile(r"<td[^>]*>([\s\S]*?)</td>")
HREF = re.compile(r'href="([^"]+)"', re.I)


def strip_tags(chunk):
    return html.unescape(re.sub(r"<[^>]+>", " ", chunk)).replace("\xa0", " ").strip()


def norm_time(raw):
    """'1:30 PM' -> '1:30 PM'; drop anything that isn't a clock time."""
    m = re.search(r"(\d{1,2}):(\d{2})\s*([AaPp])\.?[Mm]\.?", raw or "")
    if not m:
        return None
    return "%d:%s %s" % (int(m.group(1)), m.group(2), m.group(3).upper() + "M")


def parse(page_html):
    """Legistar's grid is fixed width: body, date, blank, time, location, ...

    The time cell carries a status word instead of a clock time when a meeting
    is deferred or cancelled, so that is kept as status rather than dropped.
    """
    events = []
    for chunk in ROW_SPLIT.split(page_html)[1:]:
        cells_raw = CELL.findall(chunk)
        cells = [strip_tags(c) for c in cells_raw]
        if len(cells) < 5:
            continue
        body, date_txt = cells[0], cells[1]
        if not body or not re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", date_txt or ""):
            continue
        try:
            d = datetime.strptime(date_txt, "%m/%d/%Y").date()
        except ValueError:
            continue
        time_cell, location = cells[3], cells[4]
        time_txt = norm_time(time_cell)
        status = None
        if not time_txt and time_cell:
            status = time_cell
        if location.lower() in ("deferred", "cancelled", "canceled"):
            status = status or location
            location = ""
        detail = None
        for raw in cells_raw:
            m = HREF.search(raw)
            if m and "MeetingDetail" in m.group(1):
                detail = BASE + html.unescape(m.group(1)).lstrip("/")
                break
        events.append({
            "date": d.isoformat(),
            "body": body,
            "time": time_txt,
            "status": status,
            "location": location or None,
            "href": detail,
        })
    return events


def to_calendar_objects(events):
    """Group into the {"YYYY-MM-DD": [event, ...]} shape the calendar uses."""
    by_date = {}
    for e in events:
        obj = {
            "type": "nyccouncil",
            "label": e["body"],
            "source": "legistar",
        }
        if e["time"]:
            obj["time"] = e["time"]
        if e.get("status"):
            obj["status"] = e["status"]
        if e["location"]:
            obj["location"] = e["location"]
        if e["href"]:
            obj["href"] = e["href"]
            obj["linkText"] = "Meeting details \u2197"
        by_date.setdefault(e["date"], []).append(obj)
    for day in by_date.values():
        day.sort(key=lambda o: (o.get("time") or "zz", o["label"]))
    return dict(sorted(by_date.items()))


def main():
    r = requests.get(CAL_URL, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    events = parse(r.text)
    if not events:
        print("ERROR: parsed zero rows from the Legistar calendar", file=sys.stderr)
        return 1

    today = datetime.now(timezone.utc).date().isoformat()
    upcoming = [e for e in events if e["date"] >= today]
    by_date = to_calendar_objects(upcoming)

    os.makedirs(OUT_DIR, exist_ok=True)
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": CAL_URL,
        "jurisdiction": "New York City Council",
        "events": by_date,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)

    print("rows parsed:      %d" % len(events))
    print("upcoming kept:    %d across %d dates" % (len(upcoming), len(by_date)))
    if by_date:
        days = list(by_date)
        print("range:            %s -> %s" % (days[0], days[-1]))
        first = by_date[days[0]][0]
        print("sample:           %s | %s | %s"
              % (days[0], first.get("time", "-"), first["label"]))
    print("wrote:            %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
