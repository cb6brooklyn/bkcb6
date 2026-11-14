#!/usr/bin/env python3
"""The citywide dashboard on CrashCount's profile in the apps, from crashcount.nyc/citywide/nyc/.

Reads the crash counter on CrashCount's citywide page (crashes, all injuries, moderate and serious injuries, deaths,
this year to date, highways excluded, with the police records' date range) and writes it to CrashCount's entry in
app/data/civic/orgs/orgs-profiles.json: the first card (with the button that opens the citywide crash map and counter
in the app) and the first Details rows. Leaves the file alone if the page did not give every number. Runs daily in
app-feeds.yml.
"""
import json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, 'app/data/civic/orgs/orgs-profiles.json')
URL = 'https://crashcountnyc.com/citywide/nyc/'
METRICS = [('total_crashes', 'Crashes'), ('total_injuries', 'Injuries'), ('moderate_injuries', 'Moderate injuries'),
           ('serious_injuries', 'Serious injuries'), ('total_deaths', 'Deaths')]

req = urllib.request.Request(URL, headers={'User-Agent': 'bkcb6.app'})
html = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')
vals = {}
for key, _ in METRICS:
    m = re.search(r'data-metric=["\']?' + key + r'["\']?>([\d,]+)<', html)
    if not m: sys.exit('no %s on the page; file left as it was' % key)
    vals[key] = m.group(1)
rng = re.search(r'Police records: ([A-Z][a-z]{2} \d{1,2}, \d{4})-([A-Z][a-z]{2} \d{1,2}, \d{4})', html)
if not rng: sys.exit('no police records date range on the page; file left as it was')
start, end = rng.groups()
year = end[-4:]

d = json.load(open(F, encoding='utf-8'))
p = next(x for x in d['profiles'] if x['slug'] == 'crashcount')
card = {'id': 'crashcount-citywide', 'img': 'crashcount-banner.png', 'kicker': 'New York City · %s to %s' % (start, end),
        'title': '%s crashes, %s injuries and %s deaths so far in %s' % (vals['total_crashes'], vals['total_injuries'], vals['total_deaths'], year),
        'text': '%s serious and %s moderate injuries. From NYPD crash reports, highways excluded, as CrashCount counts them. '
                "The crash map shows this year's crashes by board and block by block, and every crash in which someone was killed." % (vals['serious_injuries'], vals['moderate_injuries']),
        'until': '', 'btns': [['Open the crash map', 'https://bkcb6.app/crashcount/map/', 'hot'],
                              ['CrashCount citywide', 'https://bkcb6.app/crashcount/citywide-nyc/', ''],
                              ['Brooklyn', 'https://bkcb6.app/crashcount/borough-brooklyn/', '']]}
p['going'] = [card] + [g for g in (p.get('going') or []) if g.get('id') != 'crashcount-citywide']
rows = [['%s, %s' % (label, year), vals[key]] for key, label in METRICS] + [['Counted', '%s to %s, from NYPD crash reports, highways excluded' % (start, end)]]
keep = [r for r in p['kv'] if not re.match(r'(Crashes|Injuries|Moderate injuries|Serious injuries|Deaths), \d{4}$', r[0]) and r[0] != 'Counted']
p['kv'] = [r for r in keep if r[0] == 'Crash map'] + rows + [r for r in keep if r[0] != 'Crash map']
open(F, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=1) + '\n')
print('CrashCount citywide:', vals, start, end)
