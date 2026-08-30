#!/usr/bin/env python3
"""
Build data/civic-calendar/hearings.json: city agency public hearings.

Source is City Record Online (NYC Open Data dg92-zbpx). One caveat drives the
whole design: that dataset's start_date is the date the notice was *published*,
not the date of the hearing. The hearing date lives in the notice prose.

So this reads the notice text and extracts the hearing date and time, and it
only keeps a record when the extraction is unambiguous:

  * an explicit date in a recognised form, and
  * an explicit clock time, and
  * a hearing date on or after the notice date and inside a sane window, and
  * if the notice names a weekday, that weekday must match the parsed date.

Anything that fails those tests is skipped rather than guessed at. Skipped
counts are reported so the miss rate stays visible.

Usage:  python3 scripts/build_hearings_calendar.py
"""

import html
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone

import requests

SRC = "https://data.cityofnewyork.us/resource/dg92-zbpx.json"
OUT_DIR = "data/civic-calendar"
OUT = os.path.join(OUT_DIR, "hearings.json")
UA = {"User-Agent": "bkcb6.app civic calendar (mracioppo@cb.nyc.gov)"}
TIMEOUT = 40

SECTIONS = [
    "Public Hearings and Meetings",
    "Contract Award Hearings",
    "Public Comment on Contract Awards",
]
LOOKBACK_DAYS = 75      # how far back to read notices
HORIZON_DAYS = 210      # how far forward a hearing date may sit

MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"])}
WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6}

NUMERIC = re.compile(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b")
WORDY = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|"
    r"october|november|december)\s*(\d{1,2})(?:st|nd|rd|th)?,?\s*(20\d{2})\b",
    re.I)
TIME = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*([ap])\.?\s?m\.?", re.I)
WEEKDAY_NEAR = re.compile(
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.I)
# A later notice often cancels or moves an earlier one. Publishing a dead
# hearing is worse than publishing nothing, so those records are dropped.
CANCELLED = re.compile(
    r"\b(has been|is|was)\s+(cancell?ed|postponed|adjourned|rescheduled)\b"
    r"|\bcancell?ation of\b|\bnotice of cancell?ation\b", re.I)


def plain(raw):
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw or ""))
    text = text.replace("\u001a", "'")
    return " ".join(text.split())


def find_dates(text):
    """Every date the notice states, with the character offset it was found at."""
    hits = []
    for m in NUMERIC.finditer(text):
        try:
            hits.append((date(int(m.group(3)), int(m.group(1)), int(m.group(2))),
                         m.start(), m.end()))
        except ValueError:
            continue
    for m in WORDY.finditer(text):
        try:
            hits.append((date(int(m.group(3)), MONTHS[m.group(1).lower()],
                              int(m.group(2))), m.start(), m.end()))
        except ValueError:
            continue
    return hits


def time_after(text, pos):
    """The first clock time stated within a sentence or so of the date."""
    m = TIME.search(text, pos, pos + 220)
    if not m:
        return None
    hour = int(m.group(1))
    if hour == 0 or hour > 12:
        return None
    minute = m.group(2) or "00"
    ampm = "AM" if m.group(3).lower() == "a" else "PM"
    return "%d:%s %s" % (hour, minute, ampm)


def weekday_ok(text, start, parsed):
    """If a weekday is named just before the date, it has to match."""
    window = text[max(0, start - 40):start]
    m = None
    for m in WEEKDAY_NEAR.finditer(window):
        pass
    if not m:
        return True
    return WEEKDAYS[m.group(1).lower()] == parsed.weekday()


def extract(text, notice_date, today):
    """Return (date, time) for the hearing, or None if it is not unambiguous."""
    horizon = today + timedelta(days=HORIZON_DAYS)
    for parsed, start, end in sorted(find_dates(text), key=lambda h: h[1]):
        if parsed < notice_date or parsed > horizon:
            continue
        if not weekday_ok(text, start, parsed):
            continue
        clock = time_after(text, end)
        if not clock:
            continue
        return parsed, clock
    return None


def fetch(since):
    where = ("start_date > '%sT00:00:00' AND (%s)"
             % (since.isoformat(),
                " OR ".join("section_name='%s'" % s for s in SECTIONS)))
    params = {"$limit": 2000, "$where": where, "$order": "start_date DESC"}
    r = requests.get(SRC, params=params, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def main():
    today = datetime.now(timezone.utc).date()
    rows = fetch(today - timedelta(days=LOOKBACK_DAYS))
    print("notices read: %d" % len(rows))

    by_date, skipped, cancelled, seen = {}, 0, 0, set()
    for row in rows:
        notice_raw = (row.get("start_date") or "")[:10]
        try:
            notice_date = date.fromisoformat(notice_raw)
        except ValueError:
            skipped += 1
            continue
        text = plain(row.get("additional_description_1")) or ""
        title = plain(row.get("short_title")) or ""
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
        agency = plain(row.get("agency_name")) or "City of New York"
        label = title or ("%s public hearing" % agency)
        key = (when.isoformat(), agency, label.lower())
        if key in seen:
            continue
        seen.add(key)
        by_date.setdefault(when.isoformat(), []).append({
            "type": "hearing",
            "label": label[:160],
            "time": clock,
            "agency": agency,
            "section": row.get("section_name"),
            "source": "city-record",
            "notice_date": notice_raw,
            "href": "https://a856-cityrecord.nyc.gov/RequestDetail/%s"
                    % row.get("request_id"),
            "linkText": "Notice \u2197",
        })

    for day in by_date.values():
        day.sort(key=lambda e: (e["time"], e["agency"]))
    by_date = dict(sorted(by_date.items()))

    os.makedirs(OUT_DIR, exist_ok=True)
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "NYC Open Data dg92-zbpx (City Record Online)",
        "note": ("Hearing dates are extracted from notice text; notices whose "
                 "date or time could not be read unambiguously are omitted."),
        "sections": SECTIONS,
        "events": by_date,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)

    kept = sum(len(v) for v in by_date.values())
    print("hearings kept: %d across %d dates" % (kept, len(by_date)))
    print("notices with no unambiguous date/time: %d" % skipped)
    print("notices dropped as cancelled or postponed: %d" % cancelled)
    for day in list(by_date)[:5]:
        e = by_date[day][0]
        print("  %s %s  %s | %s" % (day, e["time"], e["agency"][:26], e["label"][:52]))
    print("wrote: %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
