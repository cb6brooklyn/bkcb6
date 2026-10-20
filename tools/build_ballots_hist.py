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
            by[date].append(c)
ORDER = ['President and Vice President', 'United States Senator', 'Governor', 'Lieutenant Governor']
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
