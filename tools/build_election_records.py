#!/usr/bin/env python3
"""Election records for the look-back page: who got the most votes, who was on the most ballots, and so on,
for New York City, each borough and each community district, over all time and since 2000, 2012 and 2020.

Every record points at the election and contest it comes from (data/ballots/e or data/ballots/hist on this site)
and at the record's source: the NYC Board of Elections results pages (2000 on) or the Wikipedia election article
the historical contest was taken from (1897 to 1998).

Reads  data/edhistory/catalog.json and data/edhistory/e/<election>/*.json  (NYC BOE results, 2000 to 2026:
         by election district with community district totals from the 2012 general on, by Assembly district before)
       data/ballots/hist/*.json                                              (1897 to 1998, from Wikipedia articles)
Writes data/ballots/records/index.json and data/ballots/records/<scope>.json
       scopes: nyc, bk mn qn bx si, and the 59 community districts (101 to 503)

Run from the repo root: python3 tools/build_election_records.py
"""
import json, os, re, glob, collections, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'ballots', 'records')
os.makedirs(OUT, exist_ok=True)

BORO_CODE = {'1': 'mn', '2': 'bx', '3': 'bk', '4': 'qn', '5': 'si'}
BORO_NAME = {'mn': 'Manhattan', 'bx': 'Bronx', 'bk': 'Brooklyn', 'qn': 'Queens', 'si': 'Staten Island'}
COUNTY_TO = {'Manhattan': 'mn', 'Bronx': 'bx', 'Brooklyn': 'bk', 'Queens': 'qn', 'Staten Island': 'si'}
HIST_BORO = {'1': 'mn', '2': 'bx', '3': 'bk', '4': 'qn', '5': 'si', 'Manhattan': 'mn', 'Bronx': 'bx', 'Brooklyn': 'bk',
             'Queens': 'qn', 'Staten Island': 'si', 'Richmond': 'si', 'Kings': 'bk', 'New York': 'mn'}
PERIODS = [('all', '0000-00-00'), ('2000', '2000-01-01'), ('2012', '2012-01-01'), ('2020', '2020-01-01')]
NONCAND = re.compile(r'^(write[- ]?ins?|scattering|undervotes?|overvotes?|blank|void|yes|no|unrecorded|none of the above)$', re.I)
MIN_VOTES = 1000   # a contest counts for shares, margins and turnout only once this many votes were cast in the scope
# vote-for-one public offices: the only contests that count for vote records, wins, shares, margins and votes cast
# (judicial slates and party positions are vote-for-several or run unopposed, and ballot questions have no candidates)
PUBLIC = re.compile(r'^(President|President/Vice President|President and Vice President|Governor|Governor/Lieutenant Governor|Governor and Lieutenant Governor|Lieutenant Governor|Attorney General|State Comptroller|Comptroller|City Comptroller|Secretary of State|Treasurer|State Engineer and Surveyor|United States Senator( .*)?|Representative in Congress( .*)?|State Senator( .*)?|State Senate|Member of the Assembly( .*)?|Mayor|Public Advocate|President of the City Council|President of the Council|President of the Board of Aldermen|Borough President|District Attorney|Member of the City Council)$', re.I)


def boe_source(date):
    y = int(date[:4])
    if 2005 <= y <= 2025:
        return {'t': 'NYC Board of Elections, Election Results Summary %d' % y, 'u': 'https://vote.nyc/page/election-results-summary-%d' % y}
    return {'t': 'NYC Board of Elections, Statement and Return Reports (election results archive)', 'u': 'https://vote.nyc/page/election-results-summary'}


def norm_name(n):
    return re.sub(r'\s+', ' ', (n or '')).strip()


def norm_office(o):
    o = re.sub(r'\s+', ' ', (o or '')).strip()
    o = re.sub(r'^(Democratic|Republican|Conservative|Working Families|Green|Libertarian|Independence|Liberal) ', '', o, flags=re.I)
    o = re.sub(r'\s*-\s*(District|County)$', '', o)
    o = o.title().replace("'S", "'s").replace(' Of ', ' of ').replace(' The ', ' the ').replace(' To ', ' to ').replace(' In ', ' in ').replace(' And ', ' and ')
    return {'State Senate': 'State Senator', 'Governor/Lieutenant Governor': 'Governor and Lieutenant Governor', 'President/Vice President': 'President and Vice President',
            'President': 'President and Vice President', 'City Comptroller': 'Comptroller', 'Justices of the Supreme Court': 'Justice of the Supreme Court',
            'Delegates to the National Convention': 'Delegate to National Convention', 'Alternate Delegates to the National Convention': 'Alternate Delegate to National Convention',
            'Member of the Assembly For the Term Ending 12/31/2': 'Member of the Assembly'}.get(o, o)


# ---------- gather every contest with per-scope vote vectors ----------
# rows: {eid, date, type, label, ci (contest index in data/ballots/e, or hist index), office, dist, party, rcv, vf,
#        cands: [name...], parties: [[...]], votes: {scope: [v per cand]} , src:{t,u}, nycVotes: bool}
rows = []

# community district shares of each Assembly district's residents (2020 census blocks), by the lines in force:
# for elections the Board published only by AD (2000 to 2013), a district's votes are estimated as AD votes times this share
OV = json.load(open(os.path.join(ROOT, 'data/districthistory/overlap.json')))
_rows = {r['election']: r for r in [x for x in OV['offices'] if x['key'] == 'assembly'][0]['rows']}
ERA_YEAR = {'Census 2000 sl36': 2000, '06cav': 2002, '08cav': 2008, '10cav': 2010, '12c': 2012}
CDSHARE = {}   # year -> {cd: {ad: share of the AD's residents living in cd}}
for yr, row in _rows.items():
    adpop = collections.defaultdict(int)
    for b, lst in row['cbs'].items():
        for d, sh, res in lst:
            adpop[d] += res
    CDSHARE[yr] = {b: {str(d): res / adpop[d] for d, sh, res in lst} for b, lst in row['cbs'].items()}

# which districts of each office took in part of a community district, by election year (same source)
DIST_ERAS = {}
for off in OV['offices']:
    DIST_ERAS[off['key']] = sorted((r['election'], {b: set(str(d) for d, sh, res in lst) for b, lst in r['cbs'].items()}) for r in off['rows'])
def dists_in(office_key, year, cd):
    rows = DIST_ERAS.get(office_key) or []
    best = None
    for y, m in rows:
        if y <= year: best = m
    if best is None and rows: best = rows[0][1]
    return (best or {}).get(cd, set())
OFFICE_KEY = {'Member of the City Council': 'council', 'Member of the Assembly': 'assembly', 'State Senator': 'senate', 'State Senate': 'senate', 'Representative in Congress': 'congress'}

CAT = json.load(open(os.path.join(ROOT, 'data/edhistory/catalog.json')))
for el in CAT['elections']:
    eid = el['id']; d = os.path.join(ROOT, 'data/edhistory/e', eid)
    idx = json.load(open(os.path.join(d, 'index.json')))
    ci = -1
    for c in idx['contests']:
        f = os.path.join(d, '%s.json' % c['id'])
        if not os.path.exists(f):
            continue
        ci += 1
        x = json.load(open(f))
        cands = [norm_name(n) for n in x.get('cands', [])]
        tot = x.get('total') or []
        if len(tot) < len(cands) + 1:
            continue
        votes = {'nyc': [tot[i + 1] or 0 for i in range(len(cands))]}
        if x.get('cd'):
            for cd, arr in x['cd'].items():
                if not re.match(r'^[1-5]\d\d$', cd) or len(arr) < len(cands) + 1:
                    continue
                votes[cd] = [arr[i + 1] or 0 for i in range(len(cands))]
                b = BORO_CODE[cd[0]]
                if b not in votes:
                    votes[b] = [0] * len(cands)
                votes[b] = [votes[b][i] + votes[cd][i] for i in range(len(cands))]
        elif x.get('ads'):
            county = x.get('county') or {}
            estcd = set()
            yr = ERA_YEAR.get(idx.get('adRelease'))
            _off = norm_office(x.get('office') or x.get('title'))
            _okey = OFFICE_KEY.get(re.sub(r' .*$', '', _off) if False else _off)
            _dnum = re.sub(r'\D', '', str(x.get('district') or ''))
            if yr and PUBLIC.match(_off):
                for cd, shares in CDSHARE[yr].items():
                    # a district contest counts for a community district only if that district took in part of it
                    if _okey and _dnum and _dnum.lstrip('0') not in dists_in(_okey, int(el['date'][:4]), cd):
                        continue
                    acc = None
                    for ad, s in shares.items():
                        arr = x['ads'].get(ad)
                        if not arr or len(arr) < len(cands) + 1:
                            continue
                        if acc is None:
                            acc = [0.0] * len(cands)
                        acc = [acc[i] + (arr[i + 1] or 0) * s for i in range(len(cands))]
                    if acc is not None and sum(acc) > 0:
                        votes[cd] = [int(round(v)) for v in acc]
                        estcd.add(cd)
            for ad, arr in x['ads'].items():
                cs = county.get(ad) or []
                if len(cs) != 1 or len(arr) < len(cands) + 1:
                    continue  # ADs 60 and 64 straddle Brooklyn and Staten Island: left out of borough sums before 2014
                b = COUNTY_TO.get(cs[0])
                if not b:
                    continue
                if b not in votes:
                    votes[b] = [0] * len(cands)
                votes[b] = [votes[b][i] + (arr[i + 1] or 0) for i in range(len(cands))]
        src = boe_source(el['date'])
        if x.get('source') == 'openelections':
            src = {'t': 'OpenElections, New York 2012 general election results by election district (from the NYC Board of Elections)', 'u': 'https://github.com/openelections/openelections-data-ny'}
        rows.append({'eid': eid, 'date': el['date'], 'type': el['type'], 'label': el.get('label') or '', 'ci': ci, 'k': 'm', 'estcd': estcd if x.get('ads') else set(),
                     'office': norm_office(x.get('office') or x.get('title')), 'dist': str(x.get('district') or ''), 'party': x.get('party') or '',
                     'rcv': bool(x.get('rcv')), 'vf': int(x.get('voteFor') or 1), 'cands': cands, 'parties': x.get('parties') or [],
                     'votes': votes, 'src': src, 'nycVotes': True, 'public': bool(PUBLIC.match(norm_office(x.get('office') or x.get('title'))))})

for f in sorted(glob.glob(os.path.join(ROOT, 'data/ballots/hist/*.json'))):
    h = json.load(open(f))
    for ci, c in enumerate(h['contests']):
        if c.get('kind') == 'question':
            continue
        cands = [norm_name(x.get('n')) for x in c.get('cands', [])]
        v = [x.get('v') if isinstance(x.get('v'), (int, float)) else None for x in c.get('cands', [])]
        if not cands:
            continue
        scope = c.get('scope')
        votes = {}
        has = all(q is not None for q in v) and len(v) > 0
        nycv = scope in ('city', 'boro', 'congress')
        if has and nycv:
            votes['nyc'] = [int(q) for q in v]
            if scope == 'boro' and c.get('boro') is not None:
                b = HIST_BORO.get(str(c.get('boro')))
                if b:
                    votes[b] = [int(q) for q in v]
        rows.append({'eid': h['id'], 'date': h['date'], 'type': h.get('type') or ('special' if c.get('special') else 'general'), 'label': c.get('label') or '', 'ci': ci, 'k': 'h',
                     'office': norm_office(c.get('office')), 'dist': str(c.get('district') or (BORO_NAME.get(HIST_BORO.get(str(c.get('boro'))), '') if scope == 'boro' else ('Statewide' if scope == 'state' else 'NYC'))),
                     'party': '', 'rcv': False, 'vf': int(c.get('vf') or 1), 'cands': cands, 'parties': [x.get('p') or [] for x in c.get('cands', [])],
                     'votes': votes, 'wins': [bool(x.get('w')) for x in c.get('cands', [])], 'src': {'t': 'Wikipedia, ' + re.sub(r'_', ' ', c['src'].split('/wiki/')[-1]) if c.get('src') else 'Wikipedia', 'u': c.get('src') or 'https://en.wikipedia.org/'},
                     'nycVotes': nycv, 'statewide': scope == 'state', 'public': bool(PUBLIC.match(norm_office(c.get('office'))))})

rows.sort(key=lambda r: (r['date'], r['eid'], r['ci']))
print(len(rows), 'contests;', sum(1 for r in rows if r['k'] == 'm'), 'from the Board of Elections,', sum(1 for r in rows if r['k'] == 'h'), 'from Wikipedia articles')


# ---------- records per scope and period ----------
def ref(r, i, scope_votes=None, scope=None):
    """One candidate line: everything needed to cite it."""
    o = {'n': r['cands'][i], 'p': r['parties'][i] if i < len(r['parties']) else [], 'o': r['office'], 'd': r['dist'], 'pp': r['party'],
         'date': r['date'], 'eid': r['eid'], 'ci': r['ci'], 'k': r['k'], 'label': r['label'], 'src': r['src']}
    if scope_votes is not None:
        if scope in r.get('estcd', ()):
            o['est'] = 1
        o['v'] = scope_votes[i]
        t = sum(v for k, v in enumerate(scope_votes) if r['cands'][k] and not NONCAND.match(r['cands'][k]))
        o['pct'] = round(scope_votes[i] / t * 100, 1) if t else None
        o['tot'] = t
    return o


def in_scope(r, scope):
    """Appearance: was this contest on the ballot in the scope? (votes vector exists; for nyc any NYC contest)."""
    if scope == 'nyc':
        return True
    return scope in r['votes']


def build(scope):
    out = {'scope': scope, 'name': {'nyc': 'New York City'}.get(scope) or BORO_NAME.get(scope) or ('%s Community District %d' % (BORO_NAME[BORO_CODE[scope[0]]], int(scope[1:]))), 'periods': {}}
    sub = [r for r in rows if in_scope(r, scope)]
    for pname, start in PERIODS:
        R = [r for r in sub if r['date'] >= start]
        if not R:
            continue
        P = {'from': R[0]['date'], 'to': R[-1]['date'], 'elections': len(set(r['eid'] for r in R)), 'contests': len(R),
             'votedContests': sum(1 for r in R if scope in r['votes']), 'estimatedContests': sum(1 for r in R if scope in r.get('estcd', ()))}
        # reference per election: the most votes any vote-for-one public contest drew in the scope (a stand-in for ballots cast);
        # a contest whose leader has more votes than that is a parsing error and is left out of the vote records
        refv = collections.defaultdict(int)
        for r in R:
            vv = r['votes'].get(scope)
            if vv is None or not r['public'] or r['vf'] != 1: continue
            refv[r['eid']] = max(refv[r['eid']], sum(v for k, v in enumerate(vv) if r['cands'][k] and not NONCAND.match(r['cands'][k])))
        def countable(r, vv):
            if not r['public'] or r['vf'] != 1 or not vv: return False
            top = max(v for k, v in enumerate(vv) if r['cands'][k] and not NONCAND.match(r['cands'][k])) if any(r['cands'][k] and not NONCAND.match(r['cands'][k]) for k in range(len(vv))) else 0
            return top <= refv[r['eid']] * 1.02 if refv[r['eid']] else True
        most_one = []            # A
        career = collections.defaultdict(lambda: {'v': 0, 'c': 0, 'first': None, 'last': None, 'offices': set(), 'best': None})
        ballots = collections.defaultdict(set)   # C: name -> election dates
        offices = collections.defaultdict(set)   # D
        wins = collections.defaultdict(lambda: {'n': 0, 'first': None, 'last': None, 'offices': set(), 'ex': None})  # E
        shares, margins, turnout = [], [], []    # F G H
        for r in R:
            names = r['cands']
            real = [i for i, n in enumerate(names) if n and not NONCAND.match(n)]
            for i in real:
                ballots[names[i]].add(r['date'])
                offices[names[i]].add(r['office'])
            vv = r['votes'].get(scope)
            if not countable(r, vv):
                continue
            t = sum(vv[i] for i in real)
            for i in real:
                e = ref(r, i, vv, scope)
                most_one.append(e)
                c = career[names[i]]
                c['v'] += vv[i]; c['c'] += 1
                c['first'] = min(c['first'] or r['date'], r['date']); c['last'] = max(c['last'] or r['date'], r['date'])
                c['offices'].add(r['office'])
                if c['best'] is None or vv[i] > c['best']['v']:
                    c['best'] = e
            if len(real) >= 2 and t >= MIN_VOTES and not r['rcv']:
                ranked = sorted(real, key=lambda i: -vv[i])
                top, second = ranked[0], ranked[1]
                e = ref(r, top, vv, scope); e['runner'] = names[second]; e['runnerV'] = vv[second]; e['margin'] = vv[top] - vv[second]
                shares.append(e); margins.append(e)
            if real and t >= MIN_VOTES:
                e = ref(r, max(real, key=lambda i: vv[i]), vv, scope)
                turnout.append(e)
            # wins: the top vote-getter(s) in the scope, first choices left out for ranked-choice contests
            if real and t > 0 and not r['rcv']:
                if r['k'] == 'h' and r.get('wins'):
                    winners = [i for i in real if r['wins'][i]] if scope == 'nyc' or scope in r['votes'] else []
                else:
                    ranked = sorted(real, key=lambda i: -vv[i]); winners = [i for i in ranked[:r['vf']] if vv[i] > 0]
                for i in winners:
                    w = wins[names[i]]; w['n'] += 1
                    w['first'] = min(w['first'] or r['date'], r['date']); w['last'] = max(w['last'] or r['date'], r['date'])
                    w['offices'].add(r['office'])
                    if w['ex'] is None or vv[i] > w['ex']['v']:
                        w['ex'] = ref(r, i, vv, scope)
        def top(lst, key, n=5):
            return sorted(lst, key=key)[:n]
        P['mostOne'] = top(most_one, lambda e: -e['v'])
        P['career'] = [dict(n=k, v=c['v'], contests=c['c'], first=c['first'], last=c['last'], offices=sorted(c['offices']), best=c['best'])
                       for k, c in sorted(career.items(), key=lambda kv: -kv[1]['v'])[:5]]
        P['ballots'] = [dict(n=k, elections=len(s), first=min(s), last=max(s), offices=sorted(offices[k]), dates=sorted(s))
                        for k, s in sorted(ballots.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:5]]
        P['offices'] = [dict(n=k, offices=sorted(s), elections=len(ballots[k]), first=min(ballots[k]), last=max(ballots[k]))
                        for k, s in sorted(offices.items(), key=lambda kv: (-len(kv[1]), -len(ballots[kv[0]]), kv[0]))[:5]]
        P['wins'] = [dict(n=k, wins=w['n'], first=w['first'], last=w['last'], offices=sorted(w['offices']), ex=w['ex'])
                     for k, w in sorted(wins.items(), key=lambda kv: (-kv[1]['n'], kv[0]))[:5]]
        P['share'] = top(shares, lambda e: -(e['pct'] or 0))
        P['closest'] = top(margins, lambda e: (e['margin'], -e['tot']))
        P['turnout'] = top(turnout, lambda e: -e['tot'])
        out['periods'][pname] = P
    return out


scopes = ['nyc', 'bk', 'mn', 'qn', 'bx', 'si'] + ['%d%02d' % (b, n) for b, mx in ((1, 12), (2, 12), (3, 18), (4, 14), (5, 3)) for n in range(1, mx + 1)]
index = {'generated': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'scopes': {}, 'minVotes': MIN_VOTES,
         'notes': ['Names are counted exactly as the Board of Elections or the source article printed them; a person listed under two spellings is counted twice.',
                   'Votes for 1897 to 1998 come from Wikipedia election articles and cover citywide, borough-wide and congressional contests; statewide offices before 2000 are counted as ballot appearances but their statewide vote totals are left out.',
                   'Borough totals before 2014 leave out Assembly Districts 60 and 64, which straddle Brooklyn and Staten Island in the Board\'s recap reports.',
                   'Community district totals are counted from election districts from the November 2012 general election on. For 2000 to 2013 the Board published results only by Assembly district, so community district figures from those years are estimates, marked est.: each Assembly district\'s votes times the share of its residents (2020 census blocks) who live in the community district.',
                   'Vote records, wins, shares, closest contests and votes cast count vote-for-one public offices only (President through City Council); judicial slates, party positions and ballot questions are left out. Ballot appearances and offices sought count every contest a name appeared in.',
                   'Ranked-choice primaries (2021 on) count as ballot appearances and votes (first choices) but not as wins, shares or closest contests.',
                   'Shares, closest contests and turnout count a contest once at least %d votes were cast in the area.' % MIN_VOTES]}
for s in scopes:
    o = build(s)
    if not o['periods']:
        continue
    json.dump(o, open(os.path.join(OUT, s + '.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
    p = o['periods'].get('all') or {}
    index['scopes'][s] = {'name': o['name'], 'from': p.get('from'), 'to': p.get('to'), 'elections': p.get('elections'), 'contests': p.get('contests')}
json.dump(index, open(os.path.join(OUT, 'index.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
print(len(index['scopes']), 'scopes;', sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)) // 1024, 'KB')
for s in ('nyc', 'bk', '306'):
    p = json.load(open(os.path.join(OUT, s + '.json')))['periods']['all']
    print('==', s, p['from'], p['to'], p['elections'], 'elections', p['contests'], 'contests', p['votedContests'], 'with votes')
    print('  most in one contest:', p['mostOne'][0]['n'], p['mostOne'][0]['v'], p['mostOne'][0]['o'], p['mostOne'][0]['date'])
    print('  career:', [(c['n'], c['v'], c['contests']) for c in p['career'][:3]])
    print('  ballots:', [(c['n'], c['elections'], c['first'][:4] + '-' + c['last'][:4]) for c in p['ballots'][:3]])
    print('  offices:', [(c['n'], len(c['offices'])) for c in p['offices'][:3]])
    print('  wins:', [(c['n'], c['wins']) for c in p['wins'][:3]])
    print('  share:', (p['share'][0]['n'], p['share'][0]['pct'], p['share'][0]['o'], p['share'][0]['date']) if p['share'] else None)
    print('  closest:', (p['closest'][0]['n'], p['closest'][0]['margin'], p['closest'][0]['o'], p['closest'][0]['date']) if p['closest'] else None)
    print('  turnout:', (p['turnout'][0]['tot'], p['turnout'][0]['o'], p['turnout'][0]['date']) if p['turnout'] else None)
