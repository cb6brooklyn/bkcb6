#!/usr/bin/env python3
"""
Build data/civic-calendar/brooklyn-cbs.json: a calendar for all eighteen
Brooklyn community boards.

Two sources, in priority order.

  feed      Four boards publish a real calendar feed (see probe.json). Those
            events are confirmed listings and carry everything the board
            actually posted.

  standing  Every board's standing full-board meeting rule is published in the
            city's own community board dataset as structured text, e.g.
            "Second Tuesday, 6:30pm". That generates a monthly meeting date for
            the fourteen boards with no feed at all.

Standing entries are the published rule, not a confirmed listing: boards move
meetings for holidays and most take a summer recess. Every generated event is
tagged source="standing" and carries the rule it came from, so the page can
label it as the standing schedule. A standing entry is suppressed in any month
where that board's own feed already supplies a meeting, so a real listing always
wins over a generated one.

Usage:  python3 scripts/build_cb_calendar.py
"""

import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone

import requests

OUT_DIR = "data/civic-calendar"
OUT = os.path.join(OUT_DIR, "brooklyn-cbs.json")
PROBE = os.path.join(OUT_DIR, "probe.json")
BOARDS_SRC = ("https://data.cityofnewyork.us/resource/ruf7-3wgc.json"
              "?$limit=100&borough=Brooklyn")
UA = {"User-Agent": "bkcb6.app civic calendar (mracioppo@cb.nyc.gov)"}
TIMEOUT = 25
MONTHS_AHEAD = 12

WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6}
ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
MONTH_NAMES = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5,
               "june": 6, "july": 7, "august": 8, "september": 9,
               "october": 10, "november": 11, "december": 12}


# --------------------------------------------------------------------------
# standing meeting rules
# --------------------------------------------------------------------------

def parse_time(text):
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m\.?", text, re.I)
    if not m:
        return None
    hour, minute, ampm = int(m.group(1)), m.group(2) or "00", m.group(3).lower()
    return "%d:%s %s" % (hour, minute, "AM" if ampm == "a" else "PM")


def parse_rule(text):
    """'Third Monday (fourth Monday in January and February), 7:00pm'

    Returns {"ordinal": 3, "weekday": 0, "time": "7:00 PM",
             "exceptions": {1: 4, 2: 4}} where exceptions map month -> ordinal.
    """
    if not text:
        return None
    lowered = text.lower()

    exceptions = {}
    for inner in re.findall(r"\(([^)]*)\)", lowered):
        ord_m = re.search(r"\b(first|second|third|fourth|fifth|last)\b", inner)
        if not ord_m:
            continue
        alt = 99 if ord_m.group(1) == "last" else ORDINALS[ord_m.group(1)]
        for name, num in MONTH_NAMES.items():
            if name in inner:
                exceptions[num] = alt

    main = re.sub(r"\([^)]*\)", " ", lowered)
    ord_m = re.search(r"\b(first|second|third|fourth|fifth|last)\b", main)
    day_m = re.search(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", main)
    if not ord_m or not day_m:
        return None
    ordinal = 99 if ord_m.group(1) == "last" else ORDINALS[ord_m.group(1)]
    return {
        "ordinal": ordinal,
        "weekday": WEEKDAYS[day_m.group(1)],
        "time": parse_time(text),
        "exceptions": exceptions,
        "text": text.strip(),
    }


def nth_weekday(year, month, weekday, ordinal):
    """ordinal 99 means the last such weekday in the month."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    days = []
    d = first + timedelta(days=offset)
    while d.month == month:
        days.append(d)
        d += timedelta(days=7)
    if not days:
        return None
    if ordinal == 99:
        return days[-1]
    if ordinal <= len(days):
        return days[ordinal - 1]
    return None


def standing_dates(rule, start, months):
    out = []
    year, month = start.year, start.month
    for _ in range(months):
        ordinal = rule["exceptions"].get(month, rule["ordinal"])
        d = nth_weekday(year, month, rule["weekday"], ordinal)
        if d and d >= start:
            out.append(d)
        month += 1
        if month > 12:
            month, year = 1, year + 1
    return out


# --------------------------------------------------------------------------
# feeds
# --------------------------------------------------------------------------

def unfold(text):
    out = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if line[:1] in (" ", "\t") and out:
            out[-1] += line[1:]
        else:
            out.append(line)
    return out


def unescape(value):
    return (value.replace("\\n", " ").replace("\\,", ",")
                 .replace("\\;", ";").replace("\\\\", "\\").strip())


def parse_ics(text):
    """Minimal VEVENT reader: enough for date, time, title, place, link."""
    events, cur = [], None
    for line in unfold(text):
        if line.startswith("BEGIN:VEVENT"):
            cur = {}
            continue
        if line.startswith("END:VEVENT"):
            if cur:
                events.append(cur)
            cur = None
            continue
        if cur is None or ":" not in line:
            continue
        name, value = line.split(":", 1)
        key = name.split(";")[0].upper()
        if key == "DTSTART":
            cur["dtstart"] = value.strip()
            cur["allday"] = "VALUE=DATE" in name.upper()
        elif key in ("SUMMARY", "LOCATION", "URL"):
            cur[key.lower()] = unescape(value)
    return events


def ics_datetime(raw):
    raw = raw.strip()
    m = re.match(r"(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2}))?", raw)
    if not m:
        return None, None
    d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    if not m.group(4):
        return d, None
    hour, minute = int(m.group(4)), m.group(5)
    ampm = "AM" if hour < 12 else "PM"
    h12 = hour % 12 or 12
    return d, "%d:%s %s" % (h12, minute, ampm)


def fetch_feed(url):
    try:
        r = requests.get(url, headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        return parse_ics(r.text)
    except Exception as exc:
        print("  feed failed (%s): %s" % (type(exc).__name__, url))
        return []


# --------------------------------------------------------------------------

def main():
    r = requests.get(BOARDS_SRC, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    boards = sorted(r.json(), key=lambda x: int(x["community_board_1"]))

    feeds = {}
    if os.path.exists(PROBE):
        probe = json.load(open(PROBE, encoding="utf-8"))
        feeds = {b["cb"]: b["feed"] for b in probe["boards"] if b.get("feed")}
    else:
        print("note: probe.json absent, standing schedules only")

    today = datetime.now(timezone.utc).date()
    horizon = date(today.year + 1, today.month, 1)
    out, counts = {}, {"feed": 0, "standing": 0}

    for row in boards:
        cb = int(row["community_board_1"][1:])
        rule = parse_rule(row.get("cb_board_meeting"))
        site = (row.get("cb_website") or {}).get("url") or None
        events = []

        feed_url = feeds.get(cb)
        feed_months = set()
        if feed_url:
            for ev in fetch_feed(feed_url):
                d, tm = ics_datetime(ev.get("dtstart", ""))
                if not d or d < today or d >= horizon:
                    continue
                obj = {
                    "date": d.isoformat(),
                    "label": ev.get("summary") or "Community Board %d meeting" % cb,
                    "source": "feed",
                }
                if tm and not ev.get("allday"):
                    obj["time"] = tm
                if ev.get("location"):
                    obj["location"] = ev["location"]
                if ev.get("url"):
                    obj["href"] = ev["url"]
                    obj["linkText"] = "Full details \u2197"
                events.append(obj)
                feed_months.add((d.year, d.month))
            counts["feed"] += len(events)

        if rule:
            for d in standing_dates(rule, today, MONTHS_AHEAD):
                if (d.year, d.month) in feed_months:
                    continue  # a real listing already covers that month
                obj = {
                    "date": d.isoformat(),
                    "label": "Brooklyn CB%d Full Board Meeting" % cb,
                    "source": "standing",
                    "rule": rule["text"],
                }
                if rule["time"]:
                    obj["time"] = rule["time"]
                if site:
                    obj["href"] = site
                    obj["linkText"] = "Board website \u2197"
                events.append(obj)
                counts["standing"] += 1
        else:
            print("  CB%d: no parseable standing rule (%r)"
                  % (cb, row.get("cb_board_meeting")))

        events.sort(key=lambda e: (e["date"], e.get("time") or "zz"))
        out[str(cb)] = {
            "cb": cb,
            "borough": "Brooklyn",
            "site": site,
            "feed": feed_url,
            "standing_rule": rule["text"] if rule else None,
            "events": events,
        }
        print("CB%-2d %-8s %2d events (%s)"
              % (cb, "feed" if feed_url else "standing", len(events),
                 rule["text"] if rule else "no rule"))

    os.makedirs(OUT_DIR, exist_ok=True)
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "borough": "Brooklyn",
        "horizon_months": MONTHS_AHEAD,
        "sources": {
            "feed": "the board's own published calendar",
            "standing": "the board's standing meeting rule, from NYC Open Data ruf7-3wgc",
        },
        "boards": out,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)

    print("\nboards: %d | feed events: %d | standing events: %d"
          % (len(out), counts["feed"], counts["standing"]))
    print("wrote: %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
