#!/usr/bin/env python3
"""Pull the next upcoming calendar event for places that have a profile page.

The calendar already tags every event with a type. Matching those types to
pages is done by hand below, not by name similarity: fuzzy matching put Bark
Slope's dog fashion show on Spark Slope's page, which is a different business
on a different block.
"""
import re, json, os, datetime, unicodedata

# calendar type -> the page that should show its next event
OWNERS = {
    'barkslope':  {'page': '/barkslope',                    'name': 'Bark Slope'},
    'ps5bid':     {'page': '/bid-park-slope-5th-avenue/',   'name': 'Park Slope 5th Avenue BID'},
    'osh':        {'page': '/oldstonehouse/',               'name': 'Old Stone House'},
}

ROOT = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(ROOT, 'calendar.html'), encoding='utf-8').read()
blocks = re.findall(r'"(\d{4}-\d{2}-\d{2})":\s*\[(.*?)\n  \]', src, re.S)
today = datetime.date.today().isoformat()


def field(rest, key):
    m = re.search(key + r':\s*"((?:[^"\\]|\\.)*)"', rest)
    if not m:
        return None
    v = m.group(1)
    if '\\u' in v:
        try:
            v = v.encode().decode('unicode_escape')
        except Exception:
            pass
    return v.replace('\\"', '"').replace("\\'", "'")


def slugify(t):
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')


by = {}
for date, body in blocks:
    if date < today:
        continue
    for m in re.finditer(r'\{\s*type:\s*"([a-z0-9_]+)"(.*?)\}\s*(?:,|$)', body, re.S):
        t, rest = m.group(1), m.group(2)
        if t not in OWNERS or '_alt: true' in rest:
            continue
        label = field(rest, 'label')
        if not label:
            continue
        slug = date + '-' + slugify(label)
        # every event has a calendar entry; only some have a share page
        url = ('/e/' + slug + '.html'
               if os.path.exists(os.path.join(ROOT, 'e', slug + '.html'))
               else '/calendar.html?event=' + slug)
        ev = {'date': date, 'label': label, 'time': field(rest, 'time'),
              'location': field(rest, 'location'), 'url': url}
        flyer = field(rest, 'flyer')
        if flyer:
            # the calendar stores absolute urls; keep them same-origin so the
            # image is not refetched from the network on our own page
            ev['flyer'] = re.sub(r'^https?://bkcb6\.app', '', flyer)
        by.setdefault(t, []).append(ev)

out = {}
for t, evs in by.items():
    evs.sort(key=lambda e: (e['date'], e['time'] or ''))
    out[t] = {'page': OWNERS[t]['page'], 'name': OWNERS[t]['name'], 'events': evs[:3]}

path = os.path.join(ROOT, 'data/business-events.json')
json.dump({'generated': today, 'owners': out}, open(path, 'w'), separators=(',', ':'))
for t, v in out.items():
    print(f"{t:12} {len(v['events'])} upcoming -> {v['page']}")
    for e in v['events']:
        print(f"    {e['date']}  {e['label'][:52]:54} {e['url']}")
