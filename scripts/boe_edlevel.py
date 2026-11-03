#!/usr/bin/env python3
"""Results by election district from the NYC Board of Elections' "ED Level" CSVs on
https://vote.nyc/page/election-results-summary, written to data/results/2026-general.json for bkcb6.app/results/.

Each contest has one CSV: one row per election district per unit, where a unit is a candidate (with the
party line in parentheses in general elections) or a counter (Public Counter, Absentee / Military,
Affidavit, Federal, Manually Counted Emergency, Scattered). Candidates are summed across their party lines.
Election districts marked "COMBINED INTO ED/AD" report their votes in that district.

Run: python3 scripts/boe_edlevel.py [--folder 20261103] [--dry] [--out PATH]
Writes nothing if no contest is found, so the page is never blanked.
"""
import csv, io, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data/results/2026-general.json')
PAGE = 'https://vote.nyc/page/election-results-summary'
UA = {'User-Agent': 'bkcb6.app election results (community board breakdown)'}
COUNTERS = {'public counter', 'manually counted emergency', 'absentee / military', 'federal', 'affidavit', 'scattered', 'emergency'}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode('utf-8', 'ignore')

def contest_name(fname):
    base = re.sub(r'\s*EDLevel\.csv$', '', os.path.basename(fname))
    m = re.match(r'(\d+)(.*)$', base)
    cid, rest = (m.group(1), m.group(2).strip()) if m else (base, base)
    rest = re.sub(r'^(New York|Kings|Queens|Bronx|Richmond|Citywide|Crossover)\s+', '', rest)
    return cid, rest

def parse_csv(text):
    cands, ed = [], {}
    party = {}
    meta = {}
    for r in csv.reader(io.StringIO(text)):
        if len(r) < 22 or r[11] == 'AD': continue
        ad, edn, status, title, vf, unit, tally = r[11], r[12], r[14], r[17], r[19], r[20], r[21]
        meta.setdefault('title', title); meta.setdefault('vf', vf)
        if unit.strip().lower() in COUNTERS: continue
        try: n = int(str(tally).replace(',', ''))
        except ValueError: n = 0
        m = re.match(r'^(.*?)\s*\(([^)]*)\)\s*$', unit)
        name, line = (m.group(1).strip(), m.group(2).strip()) if m else (unit.strip(), '')
        if name.lower() == 'write-in' or not name: name = 'Write-in'
        if name not in party: party[name] = []; cands.append(name)
        if line and line not in party[name]: party[name].append(line)
        key = '%02d%03d' % (int(ad), int(edn))
        e = ed.setdefault(key, {'r': status.upper().startswith('IN-PLAY'), 'v': {}})
        e['v'][name] = e['v'].get(name, 0) + n
    return cands, party, ed, meta

def main():
    folder = '20261103'
    if '--folder' in sys.argv: folder = sys.argv[sys.argv.index('--folder') + 1]
    out = OUT
    if '--out' in sys.argv: out = sys.argv[sys.argv.index('--out') + 1]
    page = get(PAGE)
    links = [l for l in re.findall(r'href="([^"]+EDLevel\.csv)"', page) if folder in l]
    links = [l for l in links if '/Crossover' not in l and 'Crossover ' not in os.path.basename(l)]
    print('ED level CSVs for', folder, len(links), file=sys.stderr)
    contests = []
    for l in links:
        url = urllib.parse.urljoin(PAGE, urllib.parse.quote(l, safe='/:%'))
        try: text = get(url)
        except Exception as e:
            print('failed', l, e, file=sys.stderr); continue
        cands, party, ed, meta = parse_csv(text)
        if not ed: continue
        order = [c for c in cands if c != 'Write-in'] + (['Write-in'] if 'Write-in' in cands else [])
        eds = {k: {'r': v['r'], 'v': [v['v'].get(c, 0) for c in order]} for k, v in ed.items() if any(v['v'].values()) or v['r']}
        cid, name = contest_name(l)
        try: vf = int(meta.get('vf') or 1)
        except ValueError: vf = 1
        contests.append({'id': cid, 'name': name, 'vf': vf, 'c': [{'n': c, 'p': ' / '.join(party.get(c, []))} for c in order], 'ed': eds})
        print('contest', cid, name, len(eds), 'EDs', len(order), 'candidates', file=sys.stderr)
    if not contests:
        print('no contests; leaving', out, 'unchanged', file=sys.stderr); return 1
    # A race split into one file per county (citywide and statewide races) becomes one contest.
    merged = {}
    for c in contests:
        k = re.sub(r'\s+(Citywide|New York|Kings|Queens|Bronx|Richmond)$', '', c['name']).strip()
        if k not in merged:
            merged[k] = dict(c, name=k); continue
        m = merged[k]
        names = [x['n'] for x in m['c']]
        for x in c['c']:
            if x['n'] not in names: m['c'].append(x); names.append(x['n'])
            else:
                mp = m['c'][names.index(x['n'])]
                mp['p'] = ' / '.join(dict.fromkeys([p for p in (mp['p'].split(' / ') + x['p'].split(' / ')) if p]))
        idx = [names.index(x['n']) for x in c['c']]
        for e in m['ed'].values(): e['v'] += [0] * (len(names) - len(e['v']))
        for key, e in c['ed'].items():
            v = [0] * len(names)
            for i, n in zip(idx, e['v']): v[i] += n
            m['ed'][key] = {'r': e['r'], 'v': v}
    contests = sorted(merged.values(), key=lambda c: c['id'])
    data = {'updated': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'final': False, 'source': PAGE, 'contests': contests}
    if '--dry' in sys.argv:
        print(json.dumps({'contests': len(contests), 'eds': sum(len(c['ed']) for c in contests)})); return 0
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(data, open(out, 'w'), separators=(',', ':'))
    print('wrote', out, len(contests), 'contests', file=sys.stderr)
    return 0

if __name__ == '__main__':
    sys.exit(main())
