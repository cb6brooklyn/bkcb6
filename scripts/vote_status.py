"""The voting status button at the top of the apps' Home: a pinned fold (id "vote-now") whose title says where voting
stands right now, holding one button (tools.json list "votenow") that opens the same page as the vote button (screen:vote).

The schedule is the apps' own election file, app/data/civic/november2026.json (earlyVoting.days). Run hourly by
.github/workflows/vote-status.yml; it rewrites the words only when they change and updates app/manifest.json so phones
pick them up the next time the app opens. After Election Day it takes the fold off Home.

python3 scripts/vote_status.py [--now 2026-10-25T13:00]"""
import hashlib, json, os, re, sys
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, 'app', 'data')
APPS = ['cb6', 'bk', 'beyond']
MON = {m: i for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}


def hour(t):
    m = re.match(r'^\s*(\d+)\s*(AM|PM)\s*$', t)
    h = int(m.group(1)) % 12
    return h + 12 if m.group(2) == 'PM' else h


def hr(h):
    return f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"


def schedule():
    d = json.load(open(os.path.join(PACK, 'civic', 'november2026.json')))
    ev, ed = [], None
    for x in d['earlyVoting']['days']:
        m = re.search(r'([A-Z][a-z]{2})[a-z]*\s+(\d+)', x['date'])
        o, c = [hour(t) for t in x['hours'].split(' to ')]
        day = f"2026-{MON[m.group(1)]:02d}-{int(m.group(2)):02d}"
        if x.get('isElectionDay'):
            ed = (day, o, c)
        else:
            ev.append((day, o, c))
    return ev, ed


def status(now):
    ev, ed = schedule()
    today, h = now.strftime('%Y-%m-%d'), now.hour + now.minute / 60
    days = [d for d, _, _ in ev]
    if today in days:
        i = days.index(today)
        _, o, c = ev[i]
        left = len(ev) - i
        if h < o:
            return f"Early voting today, {hr(o)} to {hr(c)}", f"{left} day{'s' if left != 1 else ''} of early voting left"
        if h < c:
            return f"Early voting is open now, until {hr(c)}", f"{left} day{'s' if left != 1 else ''} of early voting left, including today"
        left -= 1
        if left:
            return (f"Early voting closed for today, opens tomorrow at {hr(ev[i + 1][1])}",
                    f"{left} day{'s' if left != 1 else ''} of early voting left")
        return "Early voting is over", f"Election Day is Tuesday, Nov 3, {hr(ed[1])} to {hr(ed[2])}"
    if days and days[-1] < today < ed[0]:
        return "Election Day is tomorrow", f"Tuesday, Nov 3, {hr(ed[1])} to {hr(ed[2])}"
    if today == ed[0] and h < ed[2]:
        if h < ed[1]:
            return f"Election Day: polls open at {hr(ed[1])}", f"Open until {hr(ed[2])}"
        return f"Election Day: polls are open until {hr(ed[2])}", "In line by 9 PM, you can vote"
    if days and today < days[0]:
        return f"Early voting starts {ev[0][0][5:]}", "Election Day is Tuesday, Nov 3"
    return None


def main():
    now = datetime.now(ZoneInfo('America/New_York'))
    if '--now' in sys.argv:
        now = datetime.fromisoformat(sys.argv[sys.argv.index('--now') + 1]).replace(tzinfo=ZoneInfo('America/New_York'))
    st = status(now)
    changed = []
    for a in APPS:
        hp, tp = f'civic/ui/{a}/home.json', f'civic/ui/{a}/tools.json'
        h = json.load(open(os.path.join(PACK, hp)))
        t = json.load(open(os.path.join(PACK, tp)))
        h0, t0 = json.dumps(h), json.dumps(t)
        for k, v in h.items():
            if not isinstance(v, list):
                continue
            if st is None:
                h[k] = [s for s in v if s.get('id') != 'vote-now']
            else:
                for s in v:
                    if s.get('id') == 'vote-now':
                        s['title'] = st[0]
        if st is not None and 'votenow' in t['lists']:
            for x in t['lists']['votenow']:
                x['title'] = 'Where you vote and your ballot\n' + st[1]
        if json.dumps(h) != h0:
            open(os.path.join(PACK, hp), 'w').write(json.dumps(h, indent=1, ensure_ascii=False) + '\n')
            changed.append(hp)
        if json.dumps(t) != t0:
            open(os.path.join(PACK, tp), 'w').write(json.dumps(t, indent=2, ensure_ascii=False) + '\n')
            changed.append(tp)
    if changed:
        mp = os.path.join(ROOT, 'app', 'manifest.json')
        man = json.load(open(mp))
        for rel in changed:
            b = open(os.path.join(PACK, rel), 'rb').read()
            man['files'][rel] = {'sha': hashlib.sha256(b).hexdigest(), 'size': len(b)}
        man['generated'] = datetime.now(ZoneInfo('UTC')).replace(microsecond=0).isoformat()
        open(mp, 'w').write('\n'.join(l.lstrip(' ') for l in json.dumps(man, indent=1).split('\n')))
    print(json.dumps({'now': now.isoformat(), 'status': st, 'changed': changed}))


if __name__ == '__main__':
    main()
