#!/usr/bin/env python3
"""Election history by Election District and Community District, 2012 to today.

Sources
  * NYC BOE ED-level CSVs (vote.nyc election results summary pages, 2014 on)
  * NYC BOE cast vote records for ranked choice primaries (first choices by ED)
  * OpenElections NY 2012 general, NYC counties, by ED
  * DCP election district shapefiles (one per release) supplied by Mike

Usage
  python3 tools/build_ed_history.py geo  <shp_root>        # ED shapes per release + ED->CD
  python3 tools/build_ed_history.py results <csv_dir> <cvr_dir> <oe_dir>
Outputs to data/edhistory/
"""
import csv, glob, json, os, re, sys, collections, subprocess, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'edhistory')
BORO = {'1': 'MN', '2': 'BX', '3': 'BK', '4': 'QN', '5': 'SI'}
BORO_NAME = {'1': 'Manhattan', '2': 'Bronx', '3': 'Brooklyn', '4': 'Queens', '5': 'Staten Island'}


def cd_label(boro_cd):
    b = str(boro_cd)[0]
    n = int(str(boro_cd)[1:])
    return f"{BORO[b]}CB{n}" if n < 50 else f"{BORO[b]} JIA {n}"


# ---------------------------------------------------------------- geometry
def geo(shp_root):
    import pyogrio
    from shapely import wkb
    from shapely.geometry import shape, mapping
    from shapely.ops import transform
    from shapely.strtree import STRtree
    from pyproj import Transformer

    cds = json.load(open(os.path.join(ROOT, 'data', 'community-districts.geojson')))
    cd_geoms, cd_ids = [], []
    for f in cds['features']:
        cd_geoms.append(shape(f['geometry']).buffer(0))
        cd_ids.append(f['properties']['boro_cd'])
    tree = STRtree(cd_geoms)
    os.makedirs(os.path.join(OUT, 'geo'), exist_ok=True)
    versions = {}
    # prefer shoreline-clipped nyed over nyedwi for the same release
    rels = {}
    for d in sorted(glob.glob(os.path.join(shp_root, '*'))):
        name = os.path.basename(d)
        m = re.match(r'nyed(wi)?_(\d\d[a-z]\d?)', name)
        if not m:
            continue
        rel = m.group(2)
        if rel in rels and m.group(1):
            continue
        rels[rel] = d
    for rel, d in sorted(rels.items()):
        f = [p for p in glob.glob(d + '/*') if p.lower().endswith(('.shp', '.tab'))][0]
        meta, fids, geoms, fields = pyogrio.raw.read(f)
        names = list(meta['fields'])
        eds = fields[names.index('ElectDist')]
        tr = Transformer.from_crs(meta['crs'], 'EPSG:4326', always_xy=True)
        feats, ed2cd = [], {}
        for ed, g in zip(eds, geoms):
            if g is None:
                continue
            geom = wkb.loads(bytes(g))
            ll = transform(tr.transform, geom).buffer(0)
            key = str(int(ed))
            pt = ll.representative_point()
            best, area = None, 0
            for i in tree.query(ll):
                a = cd_geoms[i].intersection(ll).area
                if a > area:
                    best, area = cd_ids[i], a
            if best is None:
                for i in tree.query(pt.buffer(0.01)):
                    best = cd_ids[i]
                    break
            ed2cd[key] = best
            feats.append({'type': 'Feature', 'properties': {'e': key}, 'geometry': mapping(ll)})
        tmp = os.path.join(OUT, 'geo', f'_tmp_{rel}.geojson')
        json.dump({'type': 'FeatureCollection', 'features': feats}, open(tmp, 'w'))
        dst = os.path.join(OUT, 'geo', f'ed{rel}.topo.json')
        subprocess.run(['mapshaper', '-i', tmp, '-simplify', '12%', 'keep-shapes', '-o',
                        'format=topojson', 'quantization=100000', dst], check=True,
                       capture_output=True)
        os.remove(tmp)
        versions[rel] = {'eds': len(feats), 'file': f'geo/ed{rel}.topo.json', 'ed2cd': ed2cd}
        print(rel, len(feats), os.path.getsize(dst) // 1024, 'KB', 'unassigned',
              sum(1 for v in ed2cd.values() if v is None))
    json.dump(versions, open(os.path.join(OUT, 'geo', 'versions.json'), 'w'), separators=(',', ':'))


# ---------------------------------------------------------------- results
RELEASE_DATE = {'06c': '2007-01-30', '07c': '2007-12-14', '09b': '2009-11-05', '11a': '2012-01-03',
                '13a': '2013-02-28', '13b': '2013-05-29', '17b': '2017-06-02', '18c': '2018-08-08',
                '18d': '2018-11-16', '23a': '2023-02-06', '23d': '2023-11-03', '24c1': '2024-08-02',
                '24d': '2024-11-06', '25a1': '2025-04-04', '25b': '2025-05-16'}

BALLOT_UNITS = {'Public Counter', 'Emergency', 'Manually Counted Emergency', 'Absentee / Military',
                'Absentee/Military', 'Federal', 'Special Presidential', 'Affidavit'}
PARTY_ABBR = {'Democratic': 'D', 'Republican': 'R', 'Conservative': 'C', 'Working Families': 'WF',
              'Independence': 'I', 'Green': 'G', 'Libertarian': 'L', 'Women\'s Equality': 'WE',
              'Reform': 'Ref', 'SAM': 'SAM', 'Rent Is 2 Damn High': 'RTDH'}


def election_meta(folder):
    """folder like '20141104General Election' or '12-22-2020_Special_Election_12th_Council'."""
    m = re.match(r'(\d{4})(\d\d)(\d\d)\s*(.*)', folder)
    if m:
        date = f'{m.group(1)}-{m.group(2)}-{m.group(3)}'
        kind = m.group(4)
    else:
        m = re.match(r'(\d{1,2})-(\d\d)-(\d{4})_(.*)', folder)
        date = f'{m.group(3)}-{int(m.group(1)):02d}-{m.group(2)}'
        kind = m.group(4).replace('_', ' ')
    k = kind.lower()
    t = 'general' if 'general' in k else 'presidential-primary' if 'presidential' in k else \
        'primary' if 'primary' in k else 'special'
    label = {'general': 'General Election', 'primary': 'Primary Election',
             'presidential-primary': 'Presidential Primary', 'special': 'Special Election'}[t]
    eid = f"{date}-{t}"
    if t == 'special':
        sub = re.sub(r'(?i)special election', '', kind).strip(' _-')
        if sub:
            label += ' (' + sub + ')'
            eid += '-' + re.sub(r'[^a-z0-9]+', '-', sub.lower()).strip('-')
    return eid, date, t, label


def cand_name(unit):
    m = re.match(r'^(.*?)\s*\(([^()]*)\)\s*$', unit)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return unit.strip(), ''


class Contest:
    __slots__ = ('party', 'office', 'dist', 'vf', 'rows', 'status', 'conflicts', 'parties', 'source', 'rcv', 'note')

    def __init__(self, party, office, dist, vf, source):
        self.party, self.office, self.dist, self.vf = party, office, dist, vf
        self.rows = collections.defaultdict(dict)  # ed -> {unit: tally}
        self.status = {}
        self.conflicts = 0
        self.parties = collections.defaultdict(list)
        self.source = source
        self.rcv = False
        self.note = ''


def load_boe(csv_dir):
    elections = collections.OrderedDict()
    meta = {}
    files = sorted(glob.glob(os.path.join(csv_dir, '*.csv')))
    bad = []
    for f in files:
        base = os.path.basename(f)
        year, folder, fname = base.split('__', 2)
        head = open(f, 'rb').read(400).lower()
        if b'<html' in head or b'<!doc' in head:
            bad.append((folder, fname))
            continue
        eid, date, t, label = election_meta(folder)
        meta[eid] = (date, t, label)
        E = elections.setdefault(eid, {})
        with open(f, newline='', encoding='utf-8', errors='replace') as fh:
            for r in csv.reader(fh):
                if len(r) >= 22:
                    r = r[-11:]
                if len(r) < 11 or r[0] == 'AD':
                    continue
                ad, ed, county, st, event, party, office, dist, vf, unit, tally = r[:11]
                try:
                    ad_i, ed_i = int(ad), int(ed)
                    tally = int(str(tally).replace(',', '') or 0)
                except ValueError:
                    continue
                key = (party.strip(), office.strip(), dist.strip())
                C = E.get(key)
                if C is None:
                    C = E[key] = Contest(party.strip(), office.strip(), dist.strip(), vf.strip(), 'boe')
                edk = f'{ad_i}{ed_i:03d}'
                cur = C.rows[edk]
                if unit in cur:
                    if cur[unit] != tally:
                        C.conflicts += 1
                    continue
                cur[unit] = tally
                if st and st != 'IN-PLAY':
                    m = re.search(r'(\d+)/(\d+)', st)
                    if m:
                        C.status[edk] = f'{int(m.group(2))}{int(m.group(1)):03d}'
    return elections, meta, bad


def load_cvr(cvr_dir, elections, meta):
    """First choices by ED for ranked-choice contests from BOE cast vote records."""
    from python_calamine import CalamineWorkbook
    plan = [('PE2021_CVR_Final.zip', '2021-06-22-primary'), ('2023P_CVR_Final.zip', '2023-06-27-primary'),
            ('2025_Primary_CVR_2025-07-17.zip', '2025-06-24-primary'),
            ('Special_Election_2026_04_28_2026_CVR.zip', '2026-04-28-special'),
            ('2026_Primary_CVR_2026-06-23.zip', '2026-06-23-primary')]
    report = {}
    for zname, eid in plan:
        zp = os.path.join(cvr_dir, zname)
        if not os.path.exists(zp):
            continue
        z = zipfile.ZipFile(zp)
        names = [n for n in z.namelist() if n.lower().endswith('.xlsx')]
        idmap = {}
        for n in names:
            if 'candidacyid' in n.lower():
                wb = CalamineWorkbook.from_filelike(z.open(n))
                for row in wb.get_sheet_by_index(0).to_python()[1:]:
                    if row and row[0] not in ('', None):
                        idmap[str(int(float(row[0])))] = str(row[1]).strip()
        if eid not in elections:
            elections[eid] = {}
            d = eid[:10]
            t = 'special' if 'special' in eid else 'primary'
            meta[eid] = (d, t, 'Special Election' if t == 'special' else 'Primary Election')
        E = elections[eid]
        existing = {(k[1], k[2], k[0]) for k in E}
        ballots_total = 0
        for n in names:
            if 'candidacyid' in n.lower():
                continue
            wb = CalamineWorkbook.from_filelike(z.open(n))
            rows = wb.get_sheet_by_index(0).to_python()
            if not rows:
                continue
            hdr = rows[0]
            if 'Precinct' not in hdr:
                continue
            pi = hdr.index('Precinct')
            cols = []
            for i, h in enumerate(hdr):
                m = re.match(r'^(DEM|REP|CON|WOR|GRE|IND|LIB)\s+(.*?)\s+Choice 1 of (\d+)\s+(.*?)\s*\((\d+)\)$', str(h))
                if m:
                    cols.append((i, m.group(1), m.group(2), m.group(4), m.group(5)))
            for r in rows[1:]:
                p = str(r[pi])
                m = re.match(r'AD:\s*(\d+)\s*ED:\s*(\d+)', p)
                if not m:
                    continue
                edk = f'{int(m.group(1))}{int(m.group(2)):03d}'
                ballots_total += 1
                for i, pty, office, dist, cid in cols:
                    v = str(r[i]).strip()
                    if v in ('', 'None'):
                        continue
                    party = {'DEM': 'Democratic', 'REP': 'Republican', 'CON': 'Conservative',
                             'WOR': 'Working Families', 'GRE': 'Green', 'IND': 'Independence',
                             'LIB': 'Libertarian'}[pty]
                    off = {'Mayor': 'Mayor', 'Public Advocate': 'Public Advocate',
                           'Comptroller': 'Comptroller', 'Borough President': 'Borough President',
                           'Council Member': 'Member of the City Council'}.get(office, office)
                    key = (party, off, dist + ' (RCV)')
                    C = E.get(key)
                    if C is None:
                        C = E[key] = Contest(party, off, dist, '1', 'cvr')
                        C.rcv = True
                    cur = C.rows[edk]
                    if v == 'undervote':
                        u = 'Undervote'
                    elif v == 'overvote':
                        u = 'Overvote'
                    else:
                        mm = re.match(r'^(.*?)\s*\((\d+)\)$', v)
                        if mm:
                            u = mm.group(1).strip()
                        elif re.fullmatch(r'\d+', v):
                            u = idmap.get(v, 'Candidate ' + v)
                        else:
                            u = v
                        if u.lower() in ('write-in', 'writein'):
                            u = 'Write-in'
                    cur[u] = cur.get(u, 0) + 1
                    cur['__ballots'] = cur.get('__ballots', 0) + 1
        report[eid] = ballots_total
        print('cvr', eid, ballots_total, 'ballots')
    return report


def load_2012(oe_dir, elections, meta):
    eid = '2012-11-06-general'
    meta[eid] = ('2012-11-06', 'general', 'General Election')
    E = elections.setdefault(eid, {})
    offmap = {'President': ('President/Vice President', ''), 'U.S. Senate': ('United States Senator', ''),
              'U.S. House': ('Representative in Congress', None), 'State Senate': ('State Senator', None),
              'State Assembly': ('Member of the Assembly', None)}
    seen = {}
    for b in ['bronx', 'kings', 'new_york', 'queens', 'richmond']:
        for r in csv.DictReader(open(os.path.join(oe_dir, f'20121106__ny__general__{b}__precinct.csv'))):
            off, d = offmap[r['office']]
            dist = d if d is not None else r['district'].lstrip('0')
            key = ('', off, dist)
            C = E.get(key)
            if C is None:
                C = E[key] = Contest('', off, dist, '1', 'openelections')
            edk = str(int(r['precinct']))
            name = r['candidate'].strip()
            if name.upper() in ('BLANK', 'VOID', 'SCATTERING', 'WRITE-IN', 'BLANK/VOID', 'WRITEINS', 'WRITE-INS'):
                name = 'Write-in' if 'SCATTER' in name.upper() or 'WRITE' in name.upper() else '__skip'
            if name == '__skip':
                continue
            try:
                v = int(float(r['votes'] or 0))
            except ValueError:
                v = 0
            cur = C.rows[edk]
            cur[name] = cur.get(name, 0) + v
            pty = r['party'].strip()
            if pty and pty not in C.parties[name]:
                C.parties[name].append(pty)
            seen.setdefault(key, set()).add(b)
    names = {'bronx': 'the Bronx', 'kings': 'Brooklyn', 'new_york': 'Manhattan', 'queens': 'Queens', 'richmond': 'Staten Island'}
    for key, bs in seen.items():
        if key[1] in ('President/Vice President', 'United States Senator') and len(bs) < 5:
            miss = [names[b] for b in names if b not in bs]
            E[key].note = 'No results for ' + ' or '.join(miss) + ' in the source data; totals cover the other boroughs only.'


OFFICE_ORDER = ['President/Vice President', 'President', 'United States Senator', 'Governor/Lieutenant Governor',
                'Governor', 'State Comptroller', 'Attorney General', 'Mayor', 'Public Advocate',
                'Comptroller', 'City Comptroller', 'Borough President', 'President of the Borough',
                'District Attorney', 'Representative in Congress', 'State Senator', 'Member of the Assembly',
                'Member of the City Council']


def office_rank(o):
    for i, x in enumerate(OFFICE_ORDER):
        if o.lower() == x.lower():
            return i
    lo = o.lower()
    if 'proposal' in lo or 'question' in lo or 'amendment' in lo:
        return 40
    if 'judge' in lo or 'justice' in lo or 'surrogate' in lo:
        return 50
    if 'delegate' in lo or 'committee' in lo or 'leader' in lo:
        return 70
    return 60


def ordinal_district(office, dist, party):
    d = dist.replace(' (RCV)', '')
    o = office
    if d.upper() in ('NYC', 'CITYWIDE', ''):
        return o
    if re.fullmatch(r'\d+', d):
        n = int(d)
        suf = 'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        lo = o.lower()
        if 'congress' in lo: return f'{o}, {n}{suf} Congressional District'
        if 'state senator' in lo: return f'{o}, {n}{suf} Senate District'
        if 'assembly' in lo and 'member' in lo: return f'{o}, {n}{suf} Assembly District'
        if 'city council' in lo: return f'{o}, {n}{suf} Council District'
        return f'{o}, District {n}'
    return f'{o}, {d}' if d else o


def results(csv_dir, cvr_dir, oe_dir, versions_path):
    versions = json.load(open(versions_path))
    elections, meta, bad = load_boe(csv_dir)
    cvr_report = load_cvr(cvr_dir, elections, meta)
    load_2012(oe_dir, elections, meta)
    os.makedirs(os.path.join(OUT, 'e'), exist_ok=True)
    catalog = []
    audit = {'boe_unreadable_files': [{'election': a, 'file': b} for a, b in bad], 'elections': {}}
    for eid in sorted(elections, key=lambda e: (meta[e][0], e)):
        date, t, label = meta[eid]
        E = elections[eid]
        if not E:
            continue
        # choose the ED release that matches the most result EDs
        all_eds = set()
        for C in E.values():
            all_eds.update(k for k, v in C.rows.items() if k not in C.status)
        # ED numbers are reused across releases, so the release in force on election day wins:
        # the latest release published on or before the election, unless a later one matches
        # clearly better (e.g. 2022 redistricting with no 2022 release on hand).
        # ED numbers are dense ranges reused across releases, so only releases drawn on the same
        # Assembly lines as the election are eligible: 2012 lines through May 2022, 2022 lines after.
        era = ['13a', '13b', '17b', '18c', '18d'] if date < '2022-06-01' else ['23a', '23d', '24c1', '24d', '25a1', '25b']
        era = [r for r in era if r in versions]
        match = {rel: len(all_eds & set(versions[rel]['ed2cd'])) for rel in era}
        top = max(match.values())
        from datetime import date as _d
        days = lambda r: abs((_d.fromisoformat(RELEASE_DATE[r]) - _d.fromisoformat(date)).days)
        best = min([r for r in era if match[r] == top], key=days)
        score = match[best]
        ed2cd = versions[best]['ed2cd']
        edir = os.path.join(OUT, 'e', eid)
        os.makedirs(edir, exist_ok=True)
        contests = []
        e_audit = {'ed_release': best, 'eds_with_results': len(all_eds), 'eds_matched': score,
                   'unmatched_eds': sorted(all_eds - set(ed2cd)), 'contests': 0, 'conflicting_duplicate_rows': 0}
        keys = sorted(E, key=lambda k: (office_rank(E[k].office), E[k].office, E[k].party,
                                        int(re.sub(r'\D', '', E[k].dist) or 0) if re.sub(r'\D', '', E[k].dist) else 0, E[k].dist))
        for idx, key in enumerate(keys):
            C = E[key]
            e_audit['conflicting_duplicate_rows'] += C.conflicts
            # candidate totals combining party lines
            tot = collections.Counter()
            parties = collections.defaultdict(list)
            for edk, units in C.rows.items():
                for u, v in units.items():
                    if u in BALLOT_UNITS or u == '__ballots':
                        continue
                    if u == 'Scattered':
                        nm, p = 'Write-in', ''
                    else:
                        nm, p = cand_name(u) if C.source == 'boe' else (u, '')
                    tot[nm] += v
                    if p and p not in parties[nm]:
                        parties[nm].append(p)
            for nm, ps in C.parties.items():
                parties[nm] = ps
            special = [n for n in ('Write-in', 'Undervote', 'Overvote')]
            cands = [n for n, _ in tot.most_common() if n not in special] + [n for n in special if n in tot]
            ci = {n: i for i, n in enumerate(cands)}
            eds = {}
            cdt = collections.defaultdict(lambda: [0] * (len(cands) + 1))
            unm = [0] * (len(cands) + 1)
            ballots_all = 0
            for edk, units in C.rows.items():
                if edk in C.status:
                    continue
                vec = [0] * (len(cands) + 1)
                b = sum(v for u, v in units.items() if u in BALLOT_UNITS or u == '__ballots')
                vec[0] = b
                for u, v in units.items():
                    if u in BALLOT_UNITS or u == '__ballots':
                        continue
                    nm = 'Write-in' if u == 'Scattered' else (cand_name(u)[0] if C.source == 'boe' else u)
                    vec[1 + ci[nm]] += v
                ballots_all += b
                while len(vec) > 1 and vec[-1] == 0:
                    vec.pop()
                eds[edk] = vec
                cd = ed2cd.get(edk)
                tgt = cdt[cd] if cd else unm
                for i, x in enumerate(vec):
                    tgt[i] += x
            title = ordinal_district(C.office, C.dist, C.party)
            pty = C.party
            rec = {
                'id': idx, 'title': title, 'office': C.office, 'district': C.dist.replace(' (RCV)', ''),
                'party': pty, 'voteFor': C.vf, 'rcv': C.rcv, 'source': C.source, 'note': C.note,
                'cands': cands,
                'parties': [[PARTY_ABBR.get(p, p) for p in parties.get(n, [])] for n in cands],
                'total': [ballots_all] + [tot[n] for n in cands],
                'eds': eds, 'combined': C.status,
                'cd': {str(k): v for k, v in sorted(cdt.items())},
                'unmappedEDs': unm,
            }
            json.dump(rec, open(os.path.join(edir, f'{idx}.json'), 'w'), separators=(',', ':'))
            contests.append({'id': idx, 'title': title, 'office': C.office, 'party': pty, 'rcv': C.rcv,
                             'rank': office_rank(C.office), 'n': len(eds),
                             'note': C.note, 'top': [[cands[i], rec['total'][i + 1]] for i in range(min(3, len(cands)))
                                     if cands[i] not in ('Write-in', 'Undervote', 'Overvote')],
                             'cds': sorted(str(k) for k in cdt), 'um': sum(unm[1:]), 'tv': sum(rec['total'][1:])})
            e_audit['contests'] += 1
        idxrec = {'id': eid, 'date': date, 'type': t, 'label': label, 'release': best,
                  'geo': versions[best]['file'], 'ed2cd': f'geo/ed2cd{best}.json',
                  'unmatchedEDs': e_audit['unmatched_eds'], 'contests': contests}
        json.dump(idxrec, open(os.path.join(edir, 'index.json'), 'w'), separators=(',', ':'))
        catalog.append({'id': eid, 'date': date, 'type': t, 'label': label, 'contests': len(contests),
                        'release': best})
        audit['elections'][eid] = e_audit
        print(eid, best, f'{score}/{len(all_eds)}', len(contests))
    json.dump({'elections': catalog,
               'ed2cd': {rel: {'file': v['file'], 'eds': v['eds']} for rel, v in versions.items()}},
              open(os.path.join(OUT, 'catalog.json'), 'w'), separators=(',', ':'))
    # ed -> cd lookup per release, compact
    for rel, v in versions.items():
        json.dump(v['ed2cd'], open(os.path.join(OUT, 'geo', f'ed2cd{rel}.json'), 'w'), separators=(',', ':'))
    json.dump(audit, open(os.path.join(OUT, 'audit.json'), 'w'), indent=1)


if __name__ == '__main__':
    if sys.argv[1] == 'geo':
        geo(sys.argv[2])
    else:
        results(sys.argv[2], sys.argv[3], sys.argv[4], os.path.join(OUT, 'geo', 'versions.json'))
