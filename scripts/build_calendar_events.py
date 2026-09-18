#!/usr/bin/env python3
"""Fetch ICS feeds from partner orgs and write data/calendar-events.json."""

import json
import re
import time
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
        "url": "https://www.prospectpark.org/events/list/?ical=1",
        # Their CDN returns 403 to datacenter IPs (GitHub Actions included),
        # so fall back to The Events Calendar REST API on the same site.
        "api_url": "https://www.prospectpark.org/wp-json/tribe/events/v1/events",
        "type": "prospect",
    },
    {
        "name": "BRIC Arts Media",
        "url": "https://bricartsmedia.org/events/list/?ical=1",
        "type": "bricarts",
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
        # The venue ICS endpoint returns an empty body; the REST API works.
        "api_url": "https://brooklyncb6.cityofnewyork.us/wp-json/tribe/events/v1/events?venue=1889",
        "type": "principles",
    },
]


# ---------------------------------------------------------------------------
# Manual post-processing layer (survives the daily refresh).
#   EXCLUDES  — drop any source event whose date + label substring match.
#   OVERRIDES — patch fields on any source event whose date + label substring
#               match (e.g. swap a city-calendar link for a Zoom registration).
# ---------------------------------------------------------------------------
EXCLUDES = [
    # June 22, 2026 Business Affairs & Licenses committee meeting — removed.
    {"date": "2026-06-22", "label_contains": "Business Affairs and Licenses"},
]

OVERRIDES = [
    # Transportation, Parks and Public Infrastructure meets the third WEDNESDAY.
    # The official feed has published these on Thursdays. These move them to the
    # correct date; once the feed carries the right date they simply stop matching.
    {"date": "2026-10-15", "label_contains": "Transportation, Parks and Public Infrastructure",
     "set": {"date": "2026-10-21"}},
    {"date": "2026-11-19", "label_contains": "Transportation, Parks and Public Infrastructure",
     "set": {"date": "2026-11-18"}},
    {"date": "2026-12-17", "label_contains": "Transportation, Parks and Public Infrastructure",
     "set": {"date": "2026-12-16"}},
    # June 25, 2026 Landmarks, Land Use & Housing — meeting is on Zoom.
    {
        "date": "2026-06-25",
        "label_contains": "Landmarks, Land Use & Housing",
        "set": {
            "location": "Zoom (register to attend)",
            "href": "https://zoom.us/webinar/register/WN_m-fa5stQSni-zAO3uEOEvQ",
            "linkText": "Register on Zoom \u2197",
            "desc": "Register in advance to attend via Zoom.",
        },
    },
]


def apply_manual_layer(events):
    kept = []
    for ev in events:
        if any(
            ex["date"] == ev.get("date") and ex["label_contains"] in (ev.get("label") or "")
            for ex in EXCLUDES
        ):
            print(f"  Excluded: {ev.get('date')} {ev.get('label')}")
            continue
        for ov in OVERRIDES:
            if ov["date"] == ev.get("date") and ov["label_contains"] in (ev.get("label") or ""):
                ev.update(ov["set"])
                print(f"  Overrode: {ev.get('date')} {ev.get('label')}")
        kept.append(ev)
    return kept


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


BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "text/calendar,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}


def fetch_feed(url, fallback=None, attempts=3):
    """Fetch an ICS feed. Retries, and reports why a fetch came back unusable.

    Some hosts sit behind a CDN that refuses datacenter IPs or non-browser
    user agents, so this sends browser headers and retries with backoff.
    """
    last = None
    for u in ([url, fallback] if fallback else [url]):
        if not u:
            continue
        for attempt in range(1, attempts + 1):
            try:
                r = requests.get(u, timeout=30, headers=BROWSER_HEADERS, allow_redirects=True)
                if r.ok and "BEGIN:VCALENDAR" in r.text:
                    return r.text
                ctype = r.headers.get("content-type", "")
                last = f"HTTP {r.status_code}, {len(r.text)} bytes, content-type {ctype}"
                if r.ok and not r.text.strip():
                    last = "HTTP 200 but empty body"
                    break  # nothing to retry for
            except Exception as e:
                last = f"{type(e).__name__}: {e}"
            if attempt < attempts:
                time.sleep(2 * attempt)
        print(f"  Unusable {u}: {last}")
    return None


def fetch_api(base_url, limit=200):
    """Read events from The Events Calendar REST API and return them in the
    same shape parse_ics produces. Used when a site's ICS endpoint is blocked
    or empty but its REST API answers."""
    sep = "&" if "?" in base_url else "?"
    out = []
    page = 1
    while len(out) < limit:
        url = f"{base_url}{sep}per_page=50&page={page}&start_date={datetime.now().strftime('%Y-%m-%d')}"
        try:
            r = requests.get(url, timeout=30, headers=BROWSER_HEADERS)
            if not r.ok:
                print(f"  API {url}: HTTP {r.status_code}")
                break
            data = r.json()
        except Exception as e:
            print(f"  API {url}: {type(e).__name__}: {e}")
            break
        evs = data.get("events") or []
        if not evs:
            break
        for e in evs:
            start = e.get("start_date") or ""
            if not start:
                continue
            d = start[:10]
            t = ""
            if len(start) >= 16 and not e.get("all_day"):
                hh, mm = int(start[11:13]), start[14:16]
                ampm = "AM" if hh < 12 else "PM"
                h12 = hh % 12 or 12
                t = f"{h12}:{mm} {ampm}"
            venue = e.get("venue") or {}
            loc = ", ".join(
                x for x in [venue.get("venue"), venue.get("address"), venue.get("city")] if x
            )
            cats = ", ".join(c.get("name", "") for c in (e.get("categories") or []))
            desc = re.sub(r"<[^>]+>", " ", e.get("description") or "")
            out.append({
                "date": d,
                "summary": re.sub(r"<[^>]+>", "", e.get("title") or "").strip(),
                "url": e.get("url") or "",
                "cats": cats,
                "location": loc,
                "desc": re.sub(r"\s+", " ", desc).strip(),
                "time": t,
            })
        if len(evs) < 50:
            break
        page += 1
    return out


def load_previous():
    """Previous run's output, so a feed that fails today does not silently
    delete events that were there yesterday."""
    try:
        with open("data/calendar-events.json") as f:
            return json.load(f).get("events", [])
    except Exception:
        return []


def main():
    previous = load_previous()
    all_events = []
    failed_types = []

    for feed in FEEDS:
        print(f"Fetching {feed['name']}...")
        text = fetch_feed(feed["url"], feed.get("fallback"))
        if text:
            raw = parse_ics(text)
            print(f"  Got {len(raw)} events")
        elif feed.get("api_url"):
            raw = fetch_api(feed["api_url"])
            if not raw:
                print(f"  FAILED — no data")
                if feed.get("type"):
                    failed_types.append(feed["type"])
                continue
            print(f"  Got {len(raw)} events via REST API")
        else:
            print(f"  FAILED — no data")
            if feed.get("type"):
                failed_types.append(feed["type"])
            continue
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

    # A feed that failed this run keeps whatever it contributed last run, so a
    # temporary block or outage at the source does not wipe events off the site.
    if failed_types:
        have = {(e.get("date"), e.get("label")) for e in all_events}
        carried = 0
        for e in previous:
            if e.get("type") in failed_types and (e.get("date"), e.get("label")) not in have:
                all_events.append(e)
                carried += 1
        if carried:
            print(f"  Carried over {carried} events from the previous run for: {', '.join(sorted(set(failed_types)))}")

    all_events = apply_manual_layer(all_events)

    # The same meeting can arrive from more than one feed (a venue feed and the
    # host org's feed, say). Collapse those on date + title, keeping the record
    # that carries the most detail.
    def richness(e):
        return sum(1 for k in ("location", "desc", "href", "time") if e.get(k))

    best = {}
    order = []
    for e in all_events:
        key = (e.get("date"), re.sub(r"\s+", " ", (e.get("label") or "")).strip().lower())
        if key not in best:
            best[key] = e
            order.append(key)
        elif richness(e) > richness(best[key]):
            best[key] = e
    if len(order) < len(all_events):
        print(f"  Merged {len(all_events) - len(order)} duplicate events across feeds")
    all_events = [best[k] for k in order]

    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "events": all_events,
    }

    with open("data/calendar-events.json", "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\nWrote {len(all_events)} total events to data/calendar-events.json")


if __name__ == "__main__":
    main()
