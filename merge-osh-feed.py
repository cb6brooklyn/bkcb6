#!/usr/bin/env python3
"""
Merge the Old Stone House Eventbrite feed into calendar.html as type "osh".

Reads /tmp/feed2.json (the raw plugin feed response), builds one event object
per listing, and inserts it under its date key -- appending to a key that
already exists, or creating the key in correct sorted position when it does not.

Nothing is invented: title, start, end, venue, address, ticket URL and blurb all
come straight from the feed. Events already present in calendar.html on the same
date with the same label are skipped.
"""
import json, re, sys

CAL = "calendar.html"
FEED = "/tmp/feed2.json"


def esc(s):
    """Escape a Python string for a JS double-quoted literal, \\uXXXX for non-ASCII."""
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n" or ch == "\r" or ch == "\t":
            out.append(" ")
        elif ord(ch) < 32:
            continue
        elif ord(ch) < 127:
            out.append(ch)
        else:
            out.append("\\u%04x" % ord(ch))
    return "".join(out)


def fmt_time(local):
    """'2026-08-27T17:30:00' -> '5:30 PM'"""
    hh, mm = int(local[11:13]), int(local[14:16])
    ampm = "AM" if hh < 12 else "PM"
    h12 = hh % 12 or 12
    return "%d:%02d %s" % (h12, mm, ampm)


def trim(text, limit=200):
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit - 1]
    sp = cut.rfind(" ")
    if sp > limit * 0.6:
        cut = cut[:sp]
    return cut.rstrip(" ,.;:-") + "\u2026"


def scan_array(src, open_idx):
    """Given index of '[', return index just past its matching ']' (string-aware)."""
    depth = 0
    i = open_idx
    in_str = False
    quote = ""
    while i < len(src):
        ch = src[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                in_str = False
        else:
            if ch in "\"'":
                in_str = True
                quote = ch
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return i + 1
        i += 1
    raise ValueError("unbalanced array starting at %d" % open_idx)


def main():
    src = open(CAL, encoding="utf-8").read()
    b_start = src.index("const EVENTS = {")
    b_end = src.index("\n};", b_start) + 3
    block = src[b_start:b_end]

    # map every date key -> (key_line_start, array_open_idx, array_end_idx)
    keys = {}
    for m in re.finditer(r'\n(  "(\d{4}-\d{2}-\d{2})":\s*)\[', block):
        date = m.group(2)
        open_idx = m.end() - 1
        keys[date] = dict(line_start=m.start() + 1,
                          open_idx=open_idx,
                          end_idx=scan_array(block, open_idx))
    if not keys:
        sys.exit("no date keys parsed")

    feed = json.load(open(FEED))["events"]
    existing_labels = set()
    for m in re.finditer(r'label:\s*"((?:[^"\\]|\\.)*)"', block):
        existing_labels.add(m.group(1))

    additions = {}   # date -> [object strings]
    skipped = []
    for e in sorted(feed, key=lambda x: x["start"]["local"]):
        start = e["start"]["local"]
        date = start[:10]
        end = (e.get("end") or {}).get("local")
        venue = e.get("venue") or {}
        addr = (venue.get("address") or {}).get("localized_address_display")

        label = "Old Stone House: " + " ".join(e["post_title"].split())
        if esc(label) in existing_labels:
            skipped.append(label)
            continue

        parts = ['type: "osh"', 'label: "%s"' % esc(label),
                 'time: "%s"' % fmt_time(start)]
        if venue.get("name"):
            loc = venue["name"] + (" \u00b7 " + addr if addr else "")
            parts.append('location: "%s"' % esc(loc))
        if e.get("url"):
            parts.append('href: "%s"' % esc(e["url"]))
            parts.append('linkText: "Eventbrite \u2197"')
        desc = trim(e.get("post_content") or "")
        if end:
            desc = (desc + " " if desc else "") + "Ends %s." % fmt_time(end)
        if desc:
            parts.append('desc: "%s"' % esc(desc))
        parts.append("_hardcoded: true")
        additions.setdefault(date, []).append("{ " + ", ".join(parts) + " }")

    # apply edits back-to-front so indices stay valid
    edits = []
    sorted_keys = sorted(keys)
    for date, objs in additions.items():
        body = ",\n".join("    " + o for o in objs)
        if date in keys:
            edits.append((keys[date]["open_idx"] + 1, keys[date]["open_idx"] + 1,
                          "\n" + body + ","))
        else:
            nxt = next((k for k in sorted_keys if k > date), None)
            if nxt is None:
                sys.exit("no later key than %s to anchor against" % date)
            pos = keys[nxt]["line_start"]
            edits.append((pos, pos, '  "%s": [\n%s\n  ],\n' % (date, body)))

    edits.sort(key=lambda x: x[0], reverse=True)
    for s_i, e_i, text in edits:
        block = block[:s_i] + text + block[e_i:]

    open(CAL, "w", encoding="utf-8").write(src[:b_start] + block + src[b_end:])

    added = sum(len(v) for v in additions.values())
    print("events in feed:      %d" % len(feed))
    print("added:               %d across %d dates" % (added, len(additions)))
    print("skipped (already in):%d %s" % (len(skipped), skipped))
    print("new date keys:       %s" % sorted(d for d in additions if d not in keys))


if __name__ == "__main__":
    main()
