#!/usr/bin/env python3
"""Elections before 2014 by Assembly district, from the NYC Board of Elections "Statement and Return
Report for Certification" recap PDFs (vote.nyc election results summary pages, 2005 to 2013).

The Board of Elections publishes these years only by Assembly district, so results here are by AD.
Elections already in data/edhistory at the election district level (the 2012 general) are skipped.

Usage: python3 tools/build_ad_history.py <dir of pdftotext -layout .txt files>
Writes data/edhistory/e/<election>/ and adds the elections to data/edhistory/catalog.json
"""
import collections, glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'edhistory')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from build_ed_history import office_rank, PARTY_ABBR  # noqa: E402

BALLOT = {'PUBLIC COUNTER', 'EMERGENCY', 'MANUALLY COUNTED EMERGENCY', 'ABSENTEE/MILITARY', 'ABSENTEE / MILITARY',
          'FEDERAL', 'SPECIAL PRESIDENTIAL', 'AFFIDAVIT'}
SKIP = {'TOTAL BALLOTS', 'TOTAL VOTES', 'UNRECORDED', 'TOTAL APPLICABLE BALLOTS',
        'LESS - INAPPLICABLE FEDERAL/SPECIAL PRESIDENTIAL BALLOTS'}
COUNTIES = {'New York County': 'Manhattan', 'Bronx County': 'Bronx', 'Kings County': 'Brooklyn',
            'Queens County': 'Queens', 'Richmond County': 'Staten Island'}
NUM = re.compile(r'^\s{2,}(.+?)\s{2,}([\d,]+)\s*$')


def title_case(n):
    def fix(w):
        if re.fullmatch(r'[IVX]+', w) and len(w) <= 4:
            return w
        if w.upper() in ('JR', 'JR.', 'SR', 'SR.'):
            return w.capitalize()
        w = w.lower().capitalize()
        w = re.sub(r"^(Mc|O')(\w)", lambda m: m.group(1) + m.group(2).upper(), w)
        return '-'.join(p[:1].upper() + p[1:] for p in w.split('-'))
    return ' '.join(fix(w) for w in n.split())


def parse(path):
    lines = open(path, encoding='utf-8', errors='replace').read().split('\n')
    event = date = county = party = title = vote_for = None
    out = []  # (event, date, county, party, title, voteFor, ad, unit, value)
    ad = None
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = re.search(r'IN THE CITY OF NEW YORK\s+(.+?)\s*-\s*(\d\d?/\d\d?/\d{4})\s*$', ln)
        if m:
            event = m.group(1).strip()
            mm, dd, yy = m.group(2).split('/')
            date = f'{yy}-{int(mm):02d}-{int(dd):02d}'
            # PRINTED AS OF: <county>  / <time> <party> / <title line>
            c = re.search(r'PRINTED AS OF:\s+(.+?)\s*$', lines[i + 1])
            county = c.group(1).strip() if c else None
            p = re.search(r'\d+:\d+:\d+\s*[AP]M\s+(.+?)\s*$', lines[i + 2])
            party = p.group(1).strip() if p else ''
            j = i + 3
            while j < len(lines) and not lines[j].strip():
                j += 1
            t = lines[j].strip()
            m2 = re.match(r'^(.*), vote for (\d+)$', t, re.I)
            m3 = re.match(r'^FOR (.*?) NO\. OF CANDIDATES TO BE ELECTED (\d+)$', t, re.I)
            if m2:
                title, vote_for = m2.group(1).strip(), m2.group(2)
            elif m3:
                title, vote_for = m3.group(1).strip(), m3.group(2)
            ad = None
            i = j + 1
            continue
        a = re.match(r'^\s?(?:Assembly District|ASSEMBLY DISTRICT)\s+(\d+)\s*$', ln)
        if a:
            ad = int(a.group(1))
            i += 1
            continue
        if re.match(r'^\s?\S', ln) and not ln.startswith('  '):
            # any other block header (county name in crossover files, page headers)
            if not re.match(r'^\s?(?:Assembly District|ASSEMBLY DISTRICT)', ln):
                if ln.strip() and not ln.strip().startswith(('BOARD OF ELECTIONS', 'PRINTED AS OF', 'IN THE CITY')):
                    ad = None
        n = NUM.match(ln)
        if n and ad is not None and title:
            unit = re.sub(r'\s+', ' ', n.group(1)).strip()
            out.append((event, date, county, party, title, vote_for, ad, unit, int(n.group(2).replace(',', ''))))
        i += 1
    return out


def election_id(event, date):
    e = event.lower()
    if 'runoff' in e or 'run-off' in e or 'run off' in e:
        t, label = 'runoff', 'Primary Runoff'
    elif 'presidential' in e:
        t, label = 'presidential-primary', 'Presidential Primary'
    elif 'special' in e:
        t, label = 'special', 'Special Election'
    elif 'primary' in e:
        t, label = 'primary', 'Primary Election'
    elif date[5:7] == '11':
        t, label = 'general', 'General Election'
    else:
        t, label = 'special', 'Special Election'  # the BOE labels some off-cycle specials "General Election"
    eid = f'{date}-{t}'
    if t == 'special':
        pass  # specials are labeled by their contests below
    return eid, t, label


def norm_party(p):
    p = p.replace(' Party', '').strip()
    return '' if p.lower().startswith('all parties') else p


def norm_title(title, party):
    t = re.sub(r'^(Democratic|Republican|Conservative|Working Families|Independence|Green|Libertarian)\s+', '', title)
    t = re.sub(r'^FOR\s+', '', t, flags=re.I)
    if t.isupper():
        t = title_case(t)
    t = re.sub(r'\s*\((Citywide|NYC|Nyc)\)\s*$', '', t)
    return t.strip()


def main(txt_dir):
    existing = json.load(open(os.path.join(OUT, 'catalog.json')))
    have = {e['id'] for e in existing['elections'] if e.get('level') != 'ad'}
    overlap = json.load(open(os.path.join(ROOT, 'data', 'districthistory', 'overlap.json')))
    arows = [o for o in overlap['offices'] if o['key'] == 'assembly'][0]['rows']

    def ad_geo(year):
        y = max(year, arows[0]['election'])
        best = [r for r in arows if r['election'] <= y][-1]
        return best['geo'], best['release']

    data = collections.defaultdict(lambda: collections.defaultdict(lambda: {
        'rows': collections.defaultdict(dict), 'county': {}, 'vf': '1', 'party': '', 'title': '', 'conf': 0}))
    meta = {}
    files = sorted(glob.glob(os.path.join(txt_dir, '*.txt')))
    unparsed = []
    for f in files:
        rows = parse(f)
        if not rows:
            unparsed.append(os.path.basename(f))
            continue
        for event, date, county, party, title, vf, ad, unit, v in rows:
            eid, t, label = election_id(event, date)
            if eid in have:
                continue
            meta[eid] = (date, t, label)
            pty = norm_party(party)
            ttl = norm_title(title, pty)
            C = data[eid][(pty, ttl)]
            C['party'], C['title'], C['vf'] = pty, ttl, vf
            if county in COUNTIES:
                C['county'].setdefault(ad, [])
                if COUNTIES[county] not in C['county'][ad]:
                    C['county'][ad].append(COUNTIES[county])
            # an Assembly district can cross a county line (AD 60 in 2002 to 2012), so each county's part is kept
            # separately and the parts are added together below
            cur = C['rows'][(county, ad)]
            if unit in cur and cur[unit] != v and unit.upper() not in SKIP:
                C['conf'] += 1
                continue
            cur[unit] = v
    catalog_add, audit = [], {'unparsed_files': unparsed, 'elections': {}}
    for eid in sorted(data, key=lambda e: meta[e][0]):
        date, t, label = meta[eid]
        geo, release = ad_geo(int(date[:4]))
        edir = os.path.join(OUT, 'e', eid)
        os.makedirs(edir, exist_ok=True)
        contests = []
        keys = sorted(data[eid], key=lambda k: (office_rank(k[1]), k[1], k[0]))
        conf = 0
        for idx, key in enumerate(keys):
            C = data[eid][key]
            conf += C['conf']
            tot = collections.Counter()
            parties = collections.defaultdict(list)
            merged = collections.defaultdict(collections.Counter)
            for (cty, ad), units in C['rows'].items():
                for u, v in units.items():
                    merged[ad][u] += v
            for ad, units in merged.items():
                for u, v in units.items():
                    if u.upper() in BALLOT or u.upper() in SKIP:
                        continue
                    m = re.match(r'^(.*?)\s*\(([^()]*)\)\s*$', u)
                    nm, p = (m.group(1), m.group(2)) if m else (u, '')
                    if p.upper() == 'WRITE-IN':
                        nm, p = 'Write-in', ''
                    nm = title_case(nm) if nm.isupper() else nm
                    tot[nm] += v
                    if p and p.title() not in parties[nm]:
                        parties[nm].append(p.title())
            cands = [n for n, _ in tot.most_common() if n != 'Write-in'] + (['Write-in'] if 'Write-in' in tot else [])
            ci = {n: i for i, n in enumerate(cands)}
            ads = {}
            allb = 0
            for ad, units in merged.items():
                vec = [0] * (len(cands) + 1)
                vec[0] = sum(v for u, v in units.items() if u.upper() in BALLOT)
                for u, v in units.items():
                    if u.upper() in BALLOT or u.upper() in SKIP:
                        continue
                    m = re.match(r'^(.*?)\s*\(([^()]*)\)\s*$', u)
                    nm, p = (m.group(1), m.group(2)) if m else (u, '')
                    if p.upper() == 'WRITE-IN':
                        nm = 'Write-in'
                    nm = title_case(nm) if nm.isupper() else nm
                    vec[1 + ci[nm]] += v
                allb += vec[0]
                ads[str(ad)] = vec
            title = C['title']
            rec = {'id': idx, 'title': title, 'office': re.sub(r'\s*\(.*\)$', '', title), 'district': (re.search(r'\(([^()]*)\)\s*$', title) or [None, ''])[1],
                   'party': C['party'], 'voteFor': C['vf'], 'rcv': False, 'source': 'boe-recap', 'note': '',
                   'level': 'ad', 'cands': cands,
                   'parties': [[PARTY_ABBR.get(p, p) for p in parties.get(n, [])] for n in cands],
                   'total': [allb] + [tot[n] for n in cands], 'ads': ads,
                   'county': {str(k): v for k, v in C['county'].items()}}
            json.dump(rec, open(os.path.join(edir, f'{idx}.json'), 'w'), separators=(',', ':'))
            contests.append({'id': idx, 'title': title, 'office': rec['office'], 'party': C['party'], 'rcv': False,
                             'rank': office_rank(rec['office']), 'n': len(ads), 'note': '',
                             'ads': sorted(ads, key=int), 'tv': sum(rec['total'][1:]), 'um': 0})
        if t == 'special':
            names = []
            for c in contests:
                o = re.sub(r'^Member of the ', '', c['title'])
                if o not in names:
                    names.append(o)
            label = 'Special Election (' + ', '.join(names[:3]) + (' and more' if len(names) > 3 else '') + ')'
        json.dump({'id': eid, 'date': date, 'type': t, 'label': label, 'level': 'ad', 'adGeo': geo, 'adRelease': release,
                   'contests': contests}, open(os.path.join(edir, 'index.json'), 'w'), separators=(',', ':'))
        catalog_add.append({'id': eid, 'date': date, 'type': t, 'label': label, 'contests': len(contests), 'level': 'ad'})
        audit['elections'][eid] = {'contests': len(contests), 'conflicting_duplicate_rows': conf}
        print(eid, label, len(contests), 'conflicts', conf)
    existing['elections'] = sorted([e for e in existing['elections'] if e.get('level') != 'ad'] + catalog_add, key=lambda e: (e['date'], e['id']))
    json.dump(existing, open(os.path.join(OUT, 'catalog.json'), 'w'), separators=(',', ':'))
    json.dump(audit, open(os.path.join(OUT, 'audit_ad.json'), 'w'), indent=1)
    print('unparsed files', len(unparsed))


if __name__ == '__main__':
    main(sys.argv[1])
