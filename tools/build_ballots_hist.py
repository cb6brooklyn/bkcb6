"""Historical ballots, 1898-1999: merge data/ballots/src/{state,city,congress}.json (built from Wikipedia election
articles, each contest with its source link) into one file per election day, data/ballots/hist/<date>-<kind>.json,
and data/ballots/hist-index.json for tools/build_ballots_modern.py to fold into data/ballots/index.json."""
import json, os, collections
SRC = 'data/ballots/src'
by = collections.defaultdict(list)
for name, scope_order in (('state', 0), ('city', 1), ('congress', 2)):
    p = os.path.join(SRC, name + '.json')
    if not os.path.exists(p):
        continue
    for date, cs in json.load(open(p)).get('elections', {}).items():
        if date >= '2000-01-01':
            continue  # 2000 on comes from the Board of Elections results
        for c in cs:
            c = dict(c)
            c.setdefault('scope', {'state': 'state', 'city': 'city', 'congress': 'congress'}[name])
            c['_o'] = scope_order
            if name == 'state':
                o = c.get('office', '')
                if o == 'Comptroller':
                    c['office'] = 'State Comptroller'
                elif o.startswith('U.S. Senator'):
                    c['office'] = o.replace('U.S. Senator', 'United States Senator')
                elif o == 'U.S. Representative at-large':
                    c['office'] = 'Representative in Congress (at-large)'
                    c['_atlarge'] = 1
                if c.get('kind') == 'question' and 'cands' not in c:
                    y, n = c.get('yes'), c.get('no')
                    c['cands'] = [{'n': 'Yes', 'p': [], 'v': y, 'w': y is not None and n is not None and y > n},
                                  {'n': 'No', 'p': [], 'v': n, 'w': y is not None and n is not None and n > y}]
            by[date].append(c)
# an at-large seat already in the congress file stays there (district 0) and drops from the state file
for date, cs in by.items():
    if any(c.get('scope') == 'congress' and c.get('district') == 0 for c in cs):
        by[date] = [c for c in cs if not c.get('_atlarge')]
    for c in by[date]:
        c.pop('_atlarge', None)
ORDER = ['President and Vice President', 'United States Senator', 'Governor', 'Lieutenant Governor', 'Governor and Lieutenant Governor', 'State Comptroller', 'Attorney General', 'Representative in Congress (at-large)', 'Mayor', 'Public Advocate', 'President of the City Council', 'President of the Board of Aldermen', 'President of the Council', 'Comptroller', 'Attorney General', 'Borough President']
def key(c):
    o = c.get('office', '')
    return (c['_o'], ORDER.index(o) if o in ORDER else 9, c.get('kind') == 'question', o, str(c.get('boro', '')), c.get('district') or 0)
os.makedirs('data/ballots/hist', exist_ok=True)
idx = []
for date in sorted(by):
    cs = sorted(by[date], key=key)
    for c in cs:
        c.pop('_o', None)
    special = all(c.get('special') for c in cs)
    eid = '%s-%s-h' % (date, 'special' if special else 'general')
    json.dump({'id': eid, 'date': date, 'contests': cs}, open('data/ballots/hist/%s.json' % eid, 'w'), separators=(',', ':'))
    idx.append({'id': eid, 'date': date, 'type': 'special' if special else 'general', 'label': 'Special Election' if special else 'General Election', 'k': 'h', 'n': len(cs)})
json.dump(idx, open('data/ballots/hist-index.json', 'w'), separators=(',', ':'))
print(len(idx), 'election days;', sum(i['n'] for i in idx), 'contests')
