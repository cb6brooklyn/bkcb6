#!/usr/bin/env python3
"""Fetch ICS feeds from partner orgs and write data/calendar-events.json."""

import json
import re
import time
import requests
from datetime import datetime, timezone

FEEDS = [
    {
        # Union Hall lists on Eventbrite; its organizer page carries the upcoming events as JSON.
        "name": "Union Hall",
        "url": "https://www.eventbrite.com/o/union-hall-17899496497",
        "kind": "eventbrite_org",
        "type": "unionhall",
        "venue": "Union Hall \u00b7 702 Union Street",
    },
    {
        # The Bell House's shows page carries each show as schema.org Event data.
        "name": "The Bell House",
        "url": "https://www.thebellhouseny.com/shows",
        "kind": "ldjson",
        "type": "bellhouse",
        "venue": "The Bell House \u00b7 149 7th Street",
    },
    {
        # Powerhouse Arts' calendar (a Webflow list, two or more pages): classes, workshops, events and exhibitions.
        "name": "Powerhouse Arts",
        "url": "https://powerhousearts.org/calendar",
        "kind": "powerhouse",
        "type": "powerhouse",
        "venue": "Powerhouse Arts \u00b7 322 3rd Avenue",
    },
    {
        # Littlefield's all-shows page lists its Eventbrite shows as cards (wfea-venue__event).
        "name": "Littlefield",
        "url": "https://littlefieldnyc.com/all-shows/",
        "kind": "wfea",
        "type": "littlefield",
        "venue": "Littlefield \u00b7 635 Sackett Street",
    },
    {
        # Brooklyn Bridge Park's events (a WordPress post type, with each event's date and any repeat dates in its fields).
        "name": "Brooklyn Bridge Park",
        "url": "https://brooklynbridgepark.org/wp-json/wp/v2/events",
        "kind": "bbp",
        "type": "bbp",
        "venue": "Brooklyn Bridge Park",
    },
    {
        # Brooklyn Conservatory of Music: every event on bkcm.org (WooCommerce event products, with each event's date,
        # time and place in its fields), all of it on BKCM's calendar and its profile page.
        "name": "Brooklyn Conservatory of Music",
        "url": "https://bkcm.org/wp-json/wp/v2/product",
        "kind": "bkcm",
        "type": "bkcm",
        "venue": "BKCM \u00b7 58 Seventh Avenue, Park Slope",
    },
    {
        # NewYork-Presbyterian Brooklyn Methodist Hospital: every event NYP lists for its Brooklyn campus on events.nyp.org
        # (a Localist calendar; campus 282 is the Brooklyn page), all of it on the hospital's calendar and its profile page.
        "name": "NewYork-Presbyterian Brooklyn Methodist Hospital",
        "url": "https://events.nyp.org/api/2/events?campus_id=282&days=365&pp=100",
        "kind": "localist",
        "type": "nyp",
        "venue": "NYP Brooklyn Methodist Hospital \u00b7 506 6th Street, Park Slope",
    },
    {
        # NYC Parks' events feed (the next two weeks, citywide), kept to the parks in CB6; each event goes to its park's calendar.
        "name": "NYC Parks",
        "url": "https://www.nycgovparks.org/xml/events_300_rss.json",
        "kind": "nycparks",
        "type": "nycparks",
        "venue": "",
    },
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
        "api_first": True,   # the ICS list stops at 30 events; the REST API has every one
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
    # Sept 24, 2026 Landmarks, Land Use & Housing committee meeting — removed.
    {"date": "2026-09-24", "label_contains": "Landmarks, Land Use & Housing"},
]

OVERRIDES = [
    # Oct 31, 2026 Gowanus Dredgers Pirates of the Gowanus Halloween party: the flyer Mike sent.
    {"date": "2026-10-31", "label_contains": "Pirates of the Gowanus",
     "set": {"flyer": "https://bkcb6.app/flyer-gowanus-dredgers-pirates-of-the-gowanus-2026-10-31.jpg", "time": "5:30 PM"}},
    # Oct 30, 2026 BKCM Halloween Movie Night: the flyer Mike sent.
    {"date": "2026-10-30", "label_contains": "Halloween Movie Night: Honoring Tim Curry",
     "set": {"flyer": "https://bkcb6.app/flyer-bkcm-halloween-movie-night-2026-10-30.jpg"}},
    # Oct 22, 2026 Landmarks, Land Use & Housing committee meeting: canceled.
    {"date": "2026-10-22", "label_contains": "Landmarks, Land Use",
     "set": {"label": "CANCELED: CB6 Committee Meeting- Landmarks, Land Use & Housing",
             "desc": "This meeting has been canceled.", "location": None}},
    # Oct 14, 2026 Full Board: the meeting graphic, Zoom, and the agenda map embedded under the event.
    {"date": "2026-10-14", "label_contains": "CB6 Full Board Meeting",
     "set": {"flyer": "https://bkcb6.app/101426/meeting.png", "embed": "https://bkcb6.app/101426/?embed=map",
             "href": "https://zoom.us/j/97336327750", "linkText": "Join on Zoom \u2197",
             "desc": ("At Van Alen Institute, 303 Bond Street, and on Zoom (Webinar ID 973 3632 7750). "
                      "Agenda: I. Adoption of minutes. II. Chairperson\u2019s report. III. District Manager\u2019s report. "
                      "IV. Committee reports. A. Business Affairs & Licenses: motion to approve liquor licenses for 508 Degraw Street, "
                      "744 Clinton Street, 446A Dean Street, 420 Carroll Street, 348 Douglass Street, 381 7th Avenue and 256 5th Avenue. "
                      "C. Transportation: motion to approve changes presented by DOT, supporting the Public E-Bike Charging program "
                      "and its two CB6 locations, Dean Street and 5th Avenue (northwest corner) and Court Street and 1st Place "
                      "(northeast corner), and asking for more. V. New/other business. VI. Community session. VII. Adjournment. "
                      "The agenda mapped out: https://bkcb6.app/101426/")},
     "append_desc": None},
    # Nov 18, 2026 Full Board: the meeting graphic and the Zoom webinar registration.
    {"date": "2026-11-18", "label_contains": "CB6 Full Board Meeting",
     "set": {"flyer": "https://bkcb6.app/flyer-cb6-full-board-2026-11-18.png",
             "href": "https://zoom.us/webinar/register/WN_QoUatvEQT6OeKhVfJhp3jw", "linkText": "Register on Zoom \u2197",
             "desc": "At Van Alen Institute, 303 Bond Street, and on Zoom. Register for the webinar to attend virtually: https://zoom.us/webinar/register/WN_QoUatvEQT6OeKhVfJhp3jw"}},
    # Transportation, Parks and Public Infrastructure meets the third WEDNESDAY.
    # The official feed has published these on Thursdays. These move them to the
    # correct date; once the feed carries the right date they simply stop matching.
    {"date": "2026-10-15", "label_contains": "Transportation, Parks and Public Infrastructure",
     "set": {"date": "2026-10-21"}},
    {"date": "2026-11-19", "label_contains": "Transportation, Parks and Public Infrastructure",
     "set": {"date": "2026-11-18"}},
    {"date": "2026-12-17", "label_contains": "Transportation, Parks and Public Infrastructure",
     "set": {"date": "2026-12-16"}},
    # Landmarks, Land Use & Housing meets on Thursday. The official feed has the
    # Oct 2026 meeting on Friday the 23rd; it is Thursday the 22nd.
    {"date": "2026-10-23", "label_contains": "Landmarks, Land Use",
     "set": {"date": "2026-10-22", "label": "CANCELED: CB6 Committee Meeting- Landmarks, Land Use & Housing",
             "desc": "This meeting has been canceled.", "location": None}},
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


# ADDITIONS — events added by hand. Multi-day events get one entry per day so
# they show on every day they run. If a feed later carries the same date and
# title, the duplicate merge below collapses the two into one entry.
_POWER_BROKER = {
    "type": "judgybaby",
    "label": "A Marathon Reading of The Power Broker",
    "time": "All day",
    "location": "Judgy Baby, 170 2nd Avenue, Gowanus, Brooklyn",
    "desc": "A marathon reading of Robert A. Caro\u2019s The Power Broker, November 12-15, 2026. Volunteer readers take 10-minute slots across the full 1,100+ page book.",
    "href": "https://brooklyncb6.cityofnewyork.us/event/a-marathon-reading-of-the-power-broker/",
    "linkText": "Full details \u2197",
    "flyer": "https://bkcb6.app/flyer-power-broker-marathon-reading-2026-11-12.jpg",
}
ADDITIONS = [dict(_POWER_BROKER, date=d) for d in ("2026-11-12", "2026-11-13", "2026-11-14", "2026-11-15")]
# Brooklyn Public Library events at the CB6 branches (data/bpl-events.json), each on its library's calendar.
try:
    ADDITIONS.extend(json.load(open("data/bpl-events.json"))["events"])
except Exception as _e:
    print("  bpl-events.json unreadable:", _e)
# Oct 22, 2026 Landmarks, Land Use & Housing committee meeting. The official
# feed carries it on the wrong day (Friday the 23rd); the override above moves
# that copy to the 22nd and the duplicate merge folds it into this one.
ADDITIONS.append({
    "date": "2026-10-22",
    "type": "committee",
    "label": "CANCELED: CB6 Committee Meeting- Landmarks, Land Use & Housing",
    "time": "6:30 PM",
    "location": None,
    "desc": "This meeting has been canceled.",
    "href": "https://brooklyncb6.cityofnewyork.us/event/cb6-committee-meeting-landmarks-land-use-housing-8/",
    "linkText": "Full details \u2197",
})

# Oct 31, 2026 Redemption Church Fall Festival in Coffey Park (flyer from Mike).
ADDITIONS.append({
    "date": "2026-10-31",
    "type": "community",
    "label": "Redemption Church Fall Festival",
    "time": "12:00 PM",
    "location": "Coffey Park \u00b7 85 Richards Street, Red Hook",
    "desc": "12:00 PM to 3:00 PM. Games, music and treats, fun for all ages. Come dressed in your favorite costume.",
    "flyer": "https://bkcb6.app/flyer-redemption-church-fall-festival-2026-10-31.jpg",
    "href": None,
    "linkText": None,
})

# NewYork-Presbyterian Brooklyn Methodist Hospital: the Medical Arts Pavilion driveway on 5th Street is repaved Oct 29 and 30,
# 2026 (from NYP's community notice of Oct 26, 2026).
for _d in ("2026-10-29", "2026-10-30"):
    ADDITIONS.append({
        "date": _d,
        "type": "nyp",
        "label": "NYP Brooklyn Methodist: Medical Arts Pavilion driveway repaving on 5th Street",
        "time": "8:00 AM",
        "location": "Medical Arts Pavilion driveway \u00b7 5th Street, Park Slope",
        "desc": "8:00 AM to 5:00 PM. Contractors remove the metal plates and pour concrete over the driveway entrance, with flaggers redirecting traffic. Parts of the sidewalk are closed, with a pedestrian walkway kept around the site. The concrete cures over the weekend; the driveway and part of the sidewalk stay closed for four days, with the goal of reopening Monday, November 2. Questions: community@nyp.org.",
        "href": "https://www.nyp.org/locations/brooklyn/nyp-brooklyn-methodist-hospital",
        "linkText": "nyp.org \u2197",
    })

# Nov 18, 2026 Full Board meeting at Van Alen Institute.
ADDITIONS.append({
    "date": "2026-11-18",
    "type": "board",
    "label": "CB6 Full Board Meeting",
    "time": "6:30 PM",
    "location": "Van Alen Institute, 303 Bond Street",
    "desc": "At Van Alen Institute, 303 Bond Street, and on Zoom. Register for the webinar to attend virtually: https://zoom.us/webinar/register/WN_QoUatvEQT6OeKhVfJhp3jw",
    "href": "https://zoom.us/webinar/register/WN_QoUatvEQT6OeKhVfJhp3jw",
    "linkText": "Register on Zoom \u2197",
    "flyer": "https://bkcb6.app/flyer-cb6-full-board-2026-11-18.png",
})


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
                ev.update(ov.get("set", {}))
                if ov.get("append_desc") and ov["append_desc"] not in (ev.get("desc") or ""):
                    ev["desc"] = ((ev.get("desc") or "").rstrip() + " " + ov["append_desc"]).strip()
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
                # The official site's host caches the feed; a fresh query string gets the current events.
                fresh = u + ("&" if "?" in u else "?") + f"_={int(time.time())}" if "cityofnewyork.us" in u else u
                r = requests.get(fresh, timeout=30, headers=BROWSER_HEADERS, allow_redirects=True)
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


def _clock(hhmm):
    """"22:00:00" or "2026-10-10T18:00:00-04:00" -> "10:00 PM"."""
    m = re.search(r"(\d{2}):(\d{2})(?::\d{2})?(?!.*T)", hhmm) if "T" not in hhmm else re.search(r"T(\d{2}):(\d{2})", hhmm)
    if not m:
        return None
    return parse_ics_time("T" + m.group(1) + m.group(2))


def fetch_eventbrite_org(url, venue, pages=6):
    """Every upcoming event of an Eventbrite organizer, in parse_ics's shape: the organizer's events API, reached with the
    cookies its public page sets (90 events for Union Hall); the page's own first-page data when the API fails."""
    oid = re.search(r"(\d{6,})", url).group(1)
    out, seen = [], set()
    def add(date, name, href, desc, clock):
        key = (date, name.lower())
        if key in seen or not date or not name:
            return
        seen.add(key)
        out.append({"date": date, "summary": name, "url": (href or "").split("?")[0], "cats": "", "location": venue,
                    "desc": re.sub(r"\s+", " ", desc or "").strip(), "time": clock})
    sess = requests.Session()
    sess.headers.update(dict(BROWSER_HEADERS, Accept="text/html,*/*"))
    try:
        page_html = sess.get(url, timeout=30).text
    except Exception as e:
        print(f"  Unusable {url}: {type(e).__name__}: {e}")
        return []
    api = {"Accept": "application/json", "Referer": url, "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": sess.cookies.get("csrftoken", "")}
    for page in range(1, pages + 1):
        try:
            r = sess.get(f"https://www.eventbrite.com/api/v3/organizers/{oid}/events/?status=live&order_by=start_asc&page={page}", timeout=30, headers=api)
            j = r.json() if r.ok else {}
        except Exception as e:
            print(f"  Eventbrite events API: {type(e).__name__}: {e}")
            j = {}
        evs = j.get("events") or []
        for e in evs:
            if e.get("status") not in (None, "live") or e.get("listed") is False:
                continue
            start = ((e.get("start") or {}).get("local") or "")
            add(start[:10], re.sub(r"\s+", " ", ((e.get("name") or {}).get("text") or "")).strip(), e.get("url"),
                ((e.get("description") or {}).get("text") or ""), _clock(start) if "T" in start else None)
        if not evs or not (j.get("pagination") or {}).get("has_more_items"):
            break
    if not out:
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page_html, re.S)
        try:
            evs = json.loads(m.group(1))["props"]["pageProps"].get("upcomingEvents") or [] if m else []
        except Exception:
            evs = []
        for e in evs:
            if e.get("is_cancelled"):
                continue
            add(e.get("start_date") or "", (e.get("name") or "").strip(), e.get("url"), e.get("summary") or "", _clock(e.get("start_time") or ""))
        if evs:
            print("  (first page only: the events API did not answer)")
    return out


def fetch_powerhouse_events(url, venue):
    """Powerhouse Arts' calendar pages. A class or exhibition that runs over several weeks is one entry, on its first day
    (or today, while it is running), with its dates in the description."""
    import html as _html
    from urllib.parse import urljoin
    MON = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
    today = datetime.now().date()
    def day(txt):
        m = re.match(r"([A-Z][a-z]{2})[a-z]*\.?\s+(\d{1,2})", txt.strip())
        if not m or m.group(1) not in MON:
            return None
        mo, dd = MON[m.group(1)], int(m.group(2))
        y = today.year + (1 if mo < today.month - 6 else 0) - (1 if mo > today.month + 6 else 0)
        try:
            return datetime(y, mo, dd).date()
        except ValueError:
            return None
    out, seen, page, pages = [], set(), 1, 1
    while page <= pages and page <= 20:
        u = url if page == 1 else f"{url}?10962f75_page={page}"
        try:
            r = requests.get(u, timeout=30, headers=dict(BROWSER_HEADERS, Accept="text/html,*/*"))
        except Exception as e:
            print(f"  Unusable {u}: {type(e).__name__}: {e}")
            break
        if not r.ok:
            print(f"  Unusable {u}: HTTP {r.status_code}")
            break
        s = r.text
        pages = max([pages] + [int(n) for n in re.findall(r"10962f75_page=(\d+)", s)])
        T = list(re.finditer(r'<h2[^>]*><span>([^<]*)</span></h2>', s))
        D = [m.start() for m in re.finditer(r"event_day", s)]
        prev = 0
        for t in T:
            before = s[prev:t.start()]
            days = [x for x in re.findall(r'event_day[^"]*"><span>([^<]*)<', before) if x.strip() != "-"]
            times = [x for x in re.findall(r'event_(?:start|end)_time[^"]*"><span>([^<]*)<', before) if x.strip() != "-"]
            if not days:
                prev = t.end()
                continue
            nxt = min([d for d in D if d > t.end()] + [len(s)])
            after = s[t.end():nxt]
            prev = nxt
            start, end = day(days[0]), day(days[1]) if len(days) > 1 else None
            if not start:
                continue
            if end and end < start:
                end = end.replace(year=end.year + 1)
            if (end or start) < today:
                continue
            name = _html.unescape(t.group(1)).strip()
            if (start, name.lower()) in seen:
                continue
            seen.add((start, name.lower()))
            link = re.search(r'href="([^"]+)"[^>]*class="clickable_link', after) or re.search(r'clickable_link[^>]*href="([^"]+)"', after)
            cat = re.search(r'filter_reference_text[^>]*>([^<]*)<', after)
            ds = re.search(r'w-richtext[^>]*>(.*?)</div>', after, re.S)
            desc = _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", ds.group(1)))).strip() if ds else ""
            when = f"{start:%b} {start.day} to {end:%b} {end.day}. " if end else ""
            kind = _html.unescape(cat.group(1)).strip().capitalize() + ". " if cat else ""
            out.append({
                "date": max(start, today).isoformat(),
                "summary": name + (f" (through {end:%b} {end.day})" if end else ""),
                "url": urljoin(url, _html.unescape(link.group(1))) if link else url,
                "cats": "",
                "location": venue,
                "desc": (kind + when + desc).strip(),
                "time": _clock_text(times[0]) if times else None,
                "_running": start < today,
                "_kind": _html.unescape(cat.group(1)).strip().lower() if cat else "",
            })
        page += 1
    return condense_running(out, "Powerhouse Arts", url, venue, today)


def condense_running(out, org, url, venue, today):
    """Classes, workshops and exhibitions that started earlier and are still running would each sit on today's date,
    every day, so one organization could fill a day with a dozen entries. They become one entry a day instead:
    "<org>: N classes & workshops and exhibitions in session", listing each with its last day."""
    running = [e for e in out if e.get("_running")]
    kinds = sorted({e.get("_kind", "") for e in running} - {""})
    for e in out:
        e.pop("_running", None)
        e.pop("_kind", None)
    if len(running) < 2:
        return out
    rest = [e for e in out if e not in running]
    names = "; ".join(e["summary"] for e in running)
    label = f"{org}: {len(running)} " + (" and ".join(kinds) if kinds else "classes and exhibitions") + " in session"
    return rest + [{
        "date": today.isoformat(),
        "summary": label,
        "url": url,
        "cats": "",
        "location": venue,
        "desc": f"In session now, each listed with its last day: {names}. New sessions and shows are on the calendar on their first day.",
        "time": None,
    }]


def _clock_text(t):
    m = re.match(r"(\d{1,2})(?::(\d{2}))?\s*([ap])\.?m", t.strip(), re.I)
    return f"{int(m.group(1))}:{m.group(2) or '00'} {m.group(3).upper()}M" if m else None


def fetch_bbp_events(url, venue):
    """Brooklyn Bridge Park's events from its WordPress API, every upcoming date of each (repeat dates included)."""
    import html as _html
    today = datetime.now().strftime("%Y%m%d")
    out, seen = [], set()
    for page in range(1, 20):
        try:
            r = requests.get(f"{url}?per_page=100&page={page}&_fields=id,link,title,acf", timeout=40, headers=BROWSER_HEADERS)
        except Exception as e:
            print(f"  Unusable {url}: {type(e).__name__}: {e}")
            break
        if not r.ok:
            break
        items = r.json()
        if not items:
            break
        for it in items:
            a = it.get("acf") or {}
            if (a.get("status") or "").lower() in ("canceled", "cancelled", "postponed"):
                continue
            full = _html.unescape(re.sub(r"<[^>]+>", "", (it.get("title") or {}).get("rendered", ""))).strip()
            # One post per date of a series ("Open Hours ... – February 5"): the date is the post's own; the series list names its siblings.
            name = re.sub(r"\s+[\u2013-]\s+[A-Z][a-z]+ \d{1,2}$", "", full)
            days = set()
            if re.fullmatch(r"\d{8}", a.get("date") or ""):
                days.add(a["date"])
            if name == full:
                for m in re.finditer(r"\(([A-Z][a-z]+ \d{1,2}, \d{4})\)", a.get("recurring_events_list") or ""):
                    try: days.add(datetime.strptime(m.group(1), "%B %d, %Y").strftime("%Y%m%d"))
                    except ValueError: pass
            desc = _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", a.get("description") or ""))).strip()
            for d in sorted(days):
                if d < today or (d, name.lower()) in seen:
                    continue
                seen.add((d, name.lower()))
                out.append({"date": f"{d[:4]}-{d[4:6]}-{d[6:]}", "summary": name, "url": it.get("link") or "", "cats": "",
                            "location": venue, "desc": desc[:600], "time": _clock(a.get("start_time") or "") if a.get("start_time") else None})
    return out


def fetch_localist_events(url, venue):
    """A Localist calendar's API (events.nyp.org): one row per upcoming date, with the event's time, place and page."""
    import html as _html
    out, page = [], 1
    while page and page <= 10:
        try:
            r = requests.get(url + f"&page={page}", timeout=30, headers=BROWSER_HEADERS)
            if not r.ok:
                print(f"  Localist {url}: HTTP {r.status_code}")
                break
            data = r.json()
        except Exception as e:
            print(f"  Localist {url}: {type(e).__name__}: {e}")
            break
        for x in data.get("events") or []:
            e = x.get("event") or {}
            title = _html.unescape(e.get("title") or "").strip()
            if not title:
                continue
            if e.get("experience") == "virtual":
                loc = "Online"
            else:
                loc = ", ".join(v for v in [e.get("location_name"), e.get("room_number"), e.get("address")] if v) or venue
            desc = re.sub(r"\s+", " ", _html.unescape(e.get("description_text") or "")).strip()
            for inst in e.get("event_instances") or []:
                i = inst.get("event_instance") or {}
                start = i.get("start") or ""
                if len(start) < 10:
                    continue
                t = ""
                if not i.get("all_day") and len(start) >= 16:
                    hh, mm = int(start[11:13]), start[14:16]
                    t = f"{hh % 12 or 12}:{mm} {'AM' if hh < 12 else 'PM'}"
                out.append({"date": start[:10], "summary": title, "url": e.get("localist_url") or e.get("url") or "",
                            "cats": "", "location": loc, "desc": desc, "time": t})
        page = (data.get("page") or {}).get("next_page")
    return out


def fetch_bkcm_events(url, venue):
    """Brooklyn Conservatory of Music's events: WooCommerce event products on bkcm.org, upcoming dates only."""
    import html as _html
    today = datetime.now().strftime("%Y-%m-%d")
    places = {}
    try:
        for page in range(1, 5):
            r = requests.get(url.replace("/product", "/location") + f"?per_page=100&page={page}&_fields=id,name", timeout=40, headers=BROWSER_HEADERS)
            if not r.ok or not r.json():
                break
            places.update({str(x["id"]): _html.unescape(x["name"]) for x in r.json()})
    except Exception as e:
        print(f"  BKCM places unreadable: {type(e).__name__}: {e}")
    out, seen = [], set()
    for page in range(1, 30):
        try:
            r = requests.get(f"{url}?per_page=100&page={page}&_fields=id,link,title,meta,location,excerpt,yoast_head_json.og_image", timeout=40, headers=BROWSER_HEADERS)
        except Exception as e:
            print(f"  Unusable {url}: {type(e).__name__}: {e}")
            break
        if not r.ok:
            break
        items = r.json()
        if not items:
            break
        for it in items:
            m = it.get("meta") or {}
            try:
                d = datetime.strptime((m.get("WooCommerceEventsDate") or "").strip(), "%B %d, %Y").strftime("%Y-%m-%d")
            except ValueError:
                continue
            if d < today:
                continue
            name = _html.unescape(re.sub(r"<[^>]+>", "", (it.get("title") or {}).get("rendered", ""))).strip()
            if (d, name.lower()) in seen:
                continue
            seen.add((d, name.lower()))
            hh, mm = m.get("WooCommerceEventsHour"), m.get("WooCommerceEventsMinutes") or "00"
            t = None
            if hh and str(hh).isdigit() and not (hh in ("0", "00") and mm in ("0", "00")):
                h = int(hh); t = f"{(h % 12) or 12}:{int(mm):02d} {'PM' if h >= 12 else 'AM'}"
            locs = [places.get(str(x)) for x in (it.get("location") or []) if places.get(str(x))]
            where = venue
            if locs:
                where = "BKCM \u00b7 963 President Street (Prospect Park West)" if "963 President" in locs[0] else ("BKCM \u00b7 58 Seventh Avenue, Park Slope" if locs[0] in ("BKCM", "BKCM Concert Hall", "BKCM Garden") else locs[0])
            desc = _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", (it.get("excerpt") or {}).get("rendered", "")))).strip()
            he, me = m.get("WooCommerceEventsHourEnd"), m.get("WooCommerceEventsMinutesEnd") or "00"
            if t and he and str(he).isdigit() and str(me).isdigit():
                end = f"{(int(he) % 12) or 12}:{int(me):02d} {'PM' if int(he) >= 12 else 'AM'}"
                if end != t:
                    desc = f"{t} to {end}. " + desc   # BKCM's own end time, as on its flyers
            img = ((it.get("yoast_head_json") or {}).get("og_image") or [{}])[0].get("url")
            ev = {"date": d, "summary": name, "url": it.get("link") or "", "cats": "", "location": where, "desc": desc[:600], "time": t}
            if img:
                ev["flyer"] = img
            out.append(ev)
    return out


def fetch_nycparks_events(url, venue):
    """NYC Parks' events feed, kept to CB6's parks (data/cb6-park-ids.json); each event's type is its park's calendar."""
    import html as _html
    try:
        ids = set(json.load(open("data/cb6-park-ids.json")))
        r = requests.get(url, timeout=60, headers=BROWSER_HEADERS)
        items = r.json() if r.ok else []
    except Exception as e:
        print(f"  Unusable {url}: {type(e).__name__}: {e}")
        return []
    out = []
    for it in items:
        pids = [p.strip() for p in str(it.get("parkids") or "").split(",")]
        hit = next((p for p in pids if p in ids), None)
        if not hit:
            continue
        ty = "prospect" if hit == "B073" else "bbp" if hit == "B431" else f"park-{hit.lower()}"
        st = (it.get("starttime") or "").strip()
        out.append({"date": it.get("startdate") or "", "summary": _html.unescape(it.get("title") or "").strip(),
                    "url": (it.get("link") or "").replace("http://", "https://"), "cats": it.get("categories") or "",
                    "location": _html.unescape(", ".join(x for x in [it.get("location"), it.get("parknames")] if x)),
                    "desc": _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", it.get("description") or ""))).strip()[:600],
                    "time": None if st.startswith("0:00") else _clock(st), "type": ty})
    return out


def fetch_wfea_events(url, venue):
    """Events from a WordPress page of Eventbrite cards (the wfea plugin), in parse_ics's shape."""
    try:
        r = requests.get(url, timeout=30, headers=dict(BROWSER_HEADERS, Accept="text/html,*/*"))
    except Exception as e:
        print(f"  Unusable {url}: {type(e).__name__}: {e}")
        return []
    if not r.ok:
        print(f"  Unusable {url}: HTTP {r.status_code}")
        return []
    import html as _html
    from urllib.parse import urljoin
    out, seen = [], set()
    for a in re.findall(r'<article class="wfea-venue__event.*?</article>', r.text, re.S):
        if "status-live" not in a[:200]:
            continue
        t = re.search(r'datetime="([^"]+)"', a)
        h = re.search(r'<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', a, re.S)
        if not t or not h:
            continue
        start = t.group(1)
        name = _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h.group(2)))).strip()
        key = (start[:10], name.lower())
        if key in seen:
            continue
        seen.add(key)
        ex = re.search(r'wfea-venue__excerpt[^>]*>(.*?)<a', a, re.S)
        out.append({
            "date": start[:10],
            "summary": name,
            "url": urljoin(url, _html.unescape(h.group(1))),
            "cats": "",
            "location": venue,
            "desc": _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", ex.group(1)))).strip() if ex else "",
            "time": _clock(start) if "T" in start else None,
        })
    return out


def fetch_ldjson_events(url, venue):
    """Events from a page's schema.org Event blocks, in parse_ics's shape."""
    try:
        r = requests.get(url, timeout=30, headers=dict(BROWSER_HEADERS, Accept="text/html,*/*"))
    except Exception as e:
        print(f"  Unusable {url}: {type(e).__name__}: {e}")
        return []
    if not r.ok:
        print(f"  Unusable {url}: HTTP {r.status_code}")
        return []
    out, seen = [], set()
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', r.text, re.S):
        try:
            o = json.loads(block)
        except Exception:
            continue
        for it in (o if isinstance(o, list) else [o]):
            if not isinstance(it, dict) or "Event" not in str(it.get("@type")) or not it.get("startDate") or not it.get("name"):
                continue
            start = it["startDate"]
            date = start[:10]
            name = re.sub(r"\s+", " ", it["name"]).strip()
            key = (date, name.lower())
            if key in seen:
                continue
            seen.add(key)
            status = str(it.get("eventStatus") or "")
            if "Cancelled" in status or "Postponed" in status:
                continue
            offers = it.get("offers") or {}
            href = it.get("url") or (offers.get("url") if isinstance(offers, dict) else "")
            out.append({
                "date": date,
                "summary": name,
                "url": href or "",
                "cats": "",
                "location": venue,
                "desc": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", it.get("description") or "")).strip(),
                "time": _clock(start) if "T" in start else None,
            })
    return out


def fetch_api(base_url, limit=2000):
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
        if feed.get("kind") in ("eventbrite_org", "ldjson", "wfea", "powerhouse", "bbp", "nycparks", "bkcm", "localist"):
            raw = {"localist": fetch_localist_events, "bkcm": fetch_bkcm_events, "eventbrite_org": fetch_eventbrite_org, "ldjson": fetch_ldjson_events, "wfea": fetch_wfea_events, "powerhouse": fetch_powerhouse_events, "bbp": fetch_bbp_events, "nycparks": fetch_nycparks_events}[feed["kind"]](feed["url"], feed["venue"])
            if not raw:
                print(f"  FAILED \u2014 no data")
                failed_types.append(feed["type"])
                continue
            print(f"  Got {len(raw)} events")
            text = None
        elif feed.get("api_first"):
            text = None
        else:
            text = fetch_feed(feed["url"], feed.get("fallback"))
        if feed.get("kind") in ("eventbrite_org", "ldjson", "wfea", "powerhouse", "bbp", "nycparks", "bkcm", "localist"):
            pass
        elif not text and not feed.get("api_url") and not feed.get("type"):
            # the CB6 feed (its events are classified by content): keep last run's board, committee and community events
            print(f"  FAILED \u2014 no data; keeping last run's events")
            failed_types.append(None)
            continue
        elif text:
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
            etype = ev.get("type") or classify_event(ev["summary"], ev["cats"], ev["url"], feed.get("type"))
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
                **({"flyer": ev["flyer"]} if ev.get("flyer") else {}),
            })

    # A feed that failed this run keeps whatever it contributed last run, so a
    # temporary block or outage at the source does not wipe events off the site.
    if failed_types:
        have = {(e.get("date"), e.get("label")) for e in all_events}
        forced = {f.get("type") for f in FEEDS if f.get("type")}
        carried = 0
        for e in previous:
            keep = e.get("type") in failed_types or (None in failed_types and e.get("type") not in forced)
            if keep and (e.get("date"), e.get("label")) not in have:
                all_events.append(e)
                carried += 1
        if carried:
            print(f"  Carried over {carried} events from the previous run for: {', '.join(sorted(str(t) for t in set(failed_types)))}")

    all_events.extend(dict(a) for a in ADDITIONS)
    all_events = apply_manual_layer(all_events)

    # The same meeting can arrive from more than one feed (a venue feed and the
    # host org's feed, say). Collapse those on date + title, keeping the record
    # that carries the most detail.
    best = {}
    order = []
    for e in all_events:
        key = (e.get("date"), re.sub(r"\s+", " ", (e.get("label") or "")).strip().lower())
        if str(e.get("type") or "").startswith("lib-"):
            key += (e.get("type"), e.get("time"))   # each branch's sessions are their own events
        if key not in best:
            best[key] = dict(e)
            order.append(key)
            continue
        # Same event from another feed: fill in anything the first copy lacks
        # rather than choosing between them, so no detail is dropped.
        kept = best[key]
        for k, v in e.items():
            if v and not kept.get(k):
                kept[k] = v
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
