#!/usr/bin/env python3
"""Fetch ICS feeds from partner orgs and write data/calendar-events.json."""

import json
import re
import requests
from datetime import datetime, timezone

FEEDS = [
    {
        "name": "CB6",
        "url": "https://brooklyncb6.cityofnewyork.us/events/list/?shortcode=f0b1cb7d&ical=1",
        "type": None,  # classified by content
    },
    {
        "name": "Gowanus Dredgers",
        "url": "https://gowanusdredgers.org/events/list/?ical=1",
        "type": "dredgers",
    },
    {
        "name": "Prospect Park",
        "url": "https://www.prospectpark.org/events/?ical=1",
        "type": "prospect",
    },
    {
        "name": "Old Stone House",
        "url": "https://theoldstonehouse.org/?post_type=tribe_events&ical=1&eventDisplay=list",
        "type": "osh",
        "fallback": "https://theoldstonehouse.org/events/list/?ical=1",
    },
    {
        "name": "Principles GI Coffee House (via CB6)",
        "url": "https://brooklyncb6.cityofnewyork.us/venue/principles-gi-coffee-house/?ical=1",
        "type": "principles",
    },
]


def classify_event(summary, cats, url, forced_type):
    if forced_type:
        return forced_type
    s = (summary or "").lower()
    c = (cats or "").lower()
    u = (url or "").lower()
    if "full board" in s or "full board" in c:
        return "board"
    if "alternate side" in s or "asp suspended" in s:
        return "altside"
    if "committee" in s or "upcoming meeting" in c:
        return "committee"
    if "ulurp" in s or "scoping" in s or "eis" in s:
        return "ulurp"
    if "prospectpark.org" in u or "prospect park" in s:
        return "prospect"
    if "theoldstonehouse.org" in u or "old stone house" in s:
        return "osh"
    if "gowanusdredgers.org" in u or "gowanus dredger" in s:
        return "dredgers"
    if "vanalen.org" in u or "van alen" in s:
        return "vanalen"
    if "bkcm.org" in u or "brooklyn conservatory" in s:
        return "bkcm"
    if "powerhousearts.org" in u or "powerhouse arts" in s:
        return "powerhouse"
    if "artsgowanus.org" in u or "arts gowanus" in s:
        return "artsgowanus"
    if "gowanuscanalconservancy.org" in u or "gowanus blooms" in s:
        return "gcc"
    return "community"


def parse_ics_date(raw):
    raw = raw.strip()
    # Remove TZID= prefix
    if ":" in raw:
        raw = raw.split(":")[-1]
    if re.match(r"^\d{8}$", raw):
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    m = re.match(r"^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})", raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def parse_ics_time(raw):
    raw = raw.strip()
    if ":" in raw:
        raw = raw.split(":")[-1]
    m = re.match(r"T(\d{2})(\d{2})", raw)
    if not m:
        return None
    h, mn = int(m.group(1)), m.group(2)
    ampm = "PM" if h >= 12 else "AM"
    if h > 12:
        h -= 12
    if h == 0:
        h = 12
    return f"{h}:{mn} {ampm}"


def parse_ics(text):
    events = []
    blocks = text.split("BEGIN:VEVENT")
    for block in blocks[1:]:
        def get(key):
            # Handle folded lines (lines starting with space/tab are continuations)
            unfolded = re.sub(r"\r?\n[ \t]", "", block)
            r = re.search(rf"^{key}[^:\r\n]*:([^\r\n]+)", unfolded, re.MULTILINE | re.IGNORECASE)
            if r:
                return r.group(1).replace("\\,", ",").replace("\\n", " ").replace("\\;", ";").strip()
            return ""

        dtstart_raw = get("DTSTART")
        summary = get("SUMMARY")
        url = get("URL")
        cats = get("CATEGORIES")
        location = get("LOCATION")
        desc = get("DESCRIPTION")

        date = parse_ics_date(dtstart_raw)
        time = parse_ics_time(dtstart_raw)

        if not date or not summary:
            continue

        events.append({
            "date": date,
            "summary": summary,
            "url": url,
            "cats": cats,
            "location": location,
            "desc": re.sub(r"\s+", " ", desc).strip() if desc else "",
            "time": time,
        })
    return events


def fetch_feed(url, fallback=None):
    for u in ([url, fallback] if fallback else [url]):
        if not u:
            continue
        try:
            r = requests.get(u, timeout=15, headers={"User-Agent": "bkcb6.app calendar/1.0"})
            if r.ok and "BEGIN:VCALENDAR" in r.text:
                return r.text
        except Exception as e:
            print(f"  Failed {u}: {e}")
    return None


def main():
    all_events = []

    for feed in FEEDS:
        print(f"Fetching {feed['name']}...")
        text = fetch_feed(feed["url"], feed.get("fallback"))
        if not text:
            print(f"  FAILED — no data")
            continue
        raw = parse_ics(text)
        print(f"  Got {len(raw)} events")
        for ev in raw:
            etype = classify_event(ev["summary"], ev["cats"], ev["url"], feed.get("type"))
            # Skip CB6 board/committee if coming from Dredgers feed etc.
            display_time = ev["time"]
            if not display_time and etype in ("board", "committee"):
                display_time = "6:30 PM"
            all_events.append({
                "date": ev["date"],
                "type": etype,
                "label": ev["summary"],
                "time": display_time,
                "location": ev["location"] or None,
                "desc": ev["desc"] or None,
                "href": ev["url"] or None,
                "linkText": "Full details \u2197" if ev["url"] else None,
            })

    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "events": all_events,
    }

    with open("data/calendar-events.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\nWrote {len(all_events)} total events to data/calendar-events.json")


if __name__ == "__main__":
    main()
