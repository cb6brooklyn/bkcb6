#!/usr/bin/env python3
"""Make each CB6 park's profile in the apps (app/data/civic/orgs/orgs-profiles.json) say what its page on the site says.

For every park place profile: the same name as the site, the NYC Parks description and history (intro), and the
details rows: where, size, type, a park since, hours (posted or GreenThumb), dogs, what's here, inspections, what
New Yorkers for Parks has published about it, Parks ID; links to the full profile, the rules and NYC Parks.
The small spaces (Todd Triangle, Cough Triangle) become one profile, "Small park spaces in CB6", as on the site.
Run after places_profiles.py, park_signs.py and park_banners.py.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_park_profiles as B
import park_profiles_src as S

ROOT = B.ROOT
P = os.path.join(ROOT, 'app/data/civic/orgs/orgs-profiles.json')
CALT = os.path.join(ROOT, 'scripts/app-calendar-types.json')
SUFFIX = ('-courts-and-fields', '-pool', '-recreation-center')
DAYS = B.DAYS

def pid_of(i):
    return next((g for g, parts in B.GROUPS.items() if i in parts), i)

def dog_line(pid):
    ws = {x['what'] for x in B.signs_for(pid)}
    if any('Off-Leash OK' in w for w in ws): return 'Off leash allowed before 9 a.m. and after 9 p.m.; leashed the rest of the day'
    if any(w.startswith('Dog Run') or w.startswith('Park with Dog Run') for w in ws): return 'Dog run here; leashed everywhere else'
    if any('No Off' in w for w in ws): return 'Leashed at all times; no off-leash hours'
    return ''

def whats_here(pid, ps, src):
    import collections
    am = collections.Counter(); sp = collections.Counter()
    for p in ps: am.update(p['amen']); sp.update(p['sports'])
    bits = [B.num(am[k], a, b) for k, a, b in B.AMEN if am.get(k)]
    for k in B.SPORT_ORDER:
        if sp.get(k):
            unit = ' court' if k in ('Basketball', 'Handball', 'Tennis', 'Bocce', 'Volleyball') else '' if k in ('Running track', 'Multi-purpose') else ' field'
            lab = {'Multi-purpose': 'multi-purpose field', 'Running track': 'running track'}.get(k, k.lower() + unit)
            bits.append(B.num(sp[k], lab, lab + 's'))
    if bits: return ', '.join(bits)
    if src.get('facilities'): return ', '.join(src['facilities']).lower()
    return ''

def rows(pid, ps):
    p0 = ps[0]; src = S.P.get(pid, {})
    acres = sum(p['acres'] for p in ps)
    kv = [['Where', p0['loc'] or ''], ['Size', f'{acres:,.2f} acres'], ['Type', B.TYPE.get(p0['type'], p0['type'])]]
    if p0.get('acq') and p0['acq'] > '1800': kv.append(['A park since', p0['acq']])
    h = B.park_hours(pid)
    if h: kv.append(['Hours', h + ' (posted)'])
    if pid in S.GT: kv.append(['Garden hours', '; '.join(f'{DAYS[d]} {t}' for d, t in S.GT[pid][3])])
    if pid in S.GT_IN and S.GT_IN[pid][2]: kv.append(['Garden inside', f'{S.GT_IN[pid][0]}: ' + '; '.join(f'{DAYS[d]} {t}' for d, t in S.GT_IN[pid][2])])
    elif pid in S.GT_IN: kv.append(['Garden inside', S.GT_IN[pid][0]])
    dl = dog_line(pid)
    if dl: kv.append(['Dogs', dl])
    w = whats_here(pid, ps, src)
    if w: kv.append(["What's here", w])
    ins = sorted([r for p in ps for r in p['insp']['rows']], key=lambda r: r['d'], reverse=True)
    if ins:
        ok = sum(r['o'] == 'A' for r in ins)
        kv.append(['Inspections', f'Acceptable overall {ok} of {len(ins)} times, {B.dl(B.WIN[0])} to {B.dl(B.WIN[1])}; last {B.dl(ins[0]["d"])}: {"acceptable" if ins[0]["o"] == "A" else "unacceptable"}'])
    for t, u, s in S.NY4P.get(pid, []):
        kv.append(['NY4P ' + t, s])
    if pid in S.NY4P_LIST: kv.append(['NY4P', f'Listed among CB6\'s parks in New Yorkers for Parks\' {B.NY["year"]} Open Space Profile'])
    kv += [['Parks ID', ', '.join(p['id'] for p in ps)], ['Run by', 'NYC Parks'], ['Community board', 'Brooklyn Community Board 6'],
           ['Source', 'NYC Parks (park page and history, properties, inspections, facilities, signs), GreenThumb, New Yorkers for Parks']]
    return [r for r in kv if r[1]]

def links(pid, ps, url):
    p0 = ps[0]
    L = [['Full park profile', url], ['Park rules', 'https://bkcb6.app/park/rules.html']]
    if pid not in S.GT:
        L.append(['NYC Parks page', f'https://www.nycgovparks.org/parks/{p0["id"]}'])
        if S.P.get(pid, {}).get('history'): L.append(['History on NYC Parks', f'https://www.nycgovparks.org/parks/{p0["id"]}/history'])
    else:
        L.append(['GreenThumb', 'https://greenthumb.nycgovparks.org/'])
    L.append(['Parks in CB6 map', f'https://bkcb6.app/parks-policy/#park-{p0["id"]}'])
    return L

def main():
    d = json.load(open(P))
    keep = []; small_done = False; n = 0
    pins = json.load(open(os.path.join(ROOT, 'park/pins/pins.json')))
    for p in d['profiles']:
        m = re.search(r'nycgovparks\.org/parks/(B[0-9A-Z]+)', p.get('weburl') or '') if p['slug'].startswith('place-') else None
        if m and p['slug'].endswith(SUFFIX):
            p['name'] = p['name'].replace('Dimattina', 'DiMattina')
        if not m or p['slug'].endswith(SUFFIX):
            keep.append(p); continue
        pid = pid_of(m.group(1))
        if pid in B.SMALL:
            if not small_done:
                keep.append(small_profile(p, pins)); small_done = True
            continue
        if pid not in B.SLUG:
            keep.append(p); continue
        ps = B.parts(pid); src = S.P.get(pid, {})
        name = B.NAME.get(pid) or ps[0]['n']
        url = f'https://bkcb6.app/park/{B.SLUG[pid]}.html'
        p['name'] = name
        p['intro'] = list(src.get('about', [])) + list(src.get('history', []))
        if not p['intro'] and pid in S.GT:
            p['intro'] = [f'{S.GT[pid][0]} is a GreenThumb community garden on NYC Parks land at {S.GT[pid][1]} ({S.GT[pid][2][0].lower() + S.GT[pid][2][1:]}).']
        p['kv'] = rows(pid, ps)
        p['links'] = links(pid, ps, url)
        p['desc'] = f'{name}. {p0_addr(ps[0])}'.strip()
        n += 1
        keep.append(p)
    d['profiles'] = keep
    json.dump(d, open(P, 'w'), ensure_ascii=False, indent=1)
    # park events at the small spaces go to the one small-spaces profile
    t = json.load(open(CALT))
    for k in ('park-b126a', 'park-b210c'):
        if k in t: t[k]['ty'] = 'place-cb6-small-spaces'; t[k]['org'] = 'Small park spaces in CB6'
    json.dump(t, open(CALT, 'w'), ensure_ascii=False, indent=1)
    print(n, 'park profiles;', 'small spaces merged' if small_done else 'no small spaces found')

def p0_addr(p):
    a = p.get('addr') or ''
    return (a.title() if a.isupper() else a) + (', Brooklyn' if a else '')

def small_profile(base, pins):
    q = dict(base)
    sp = [B.PK[i] for i in B.SMALL]
    q.update(slug='place-cb6-small-spaces', type='place-cb6-small-spaces', cal='place-cb6-small-spaces', name='Small park spaces in CB6',
             seat='Plazas, triangles and lots · Brooklyn Community Board 6', addr='', zip='', addr_note='', phone='', email='',
             web='bkcb6.app/park/cb6-small-spaces.html', weburl='https://bkcb6.app/park/cb6-small-spaces.html',
             lat=sum(p['lat'] for p in sp) / len(sp), lng=sum(p['lon'] for p in sp) / len(sp),
             logo='place-sign-cb6-small-spaces.png', going=[],
             desc='The smallest pieces of NYC Parks land in CB6.')
    q['intro'] = ['The Parks Department counts every piece of land it holds as a park, including slivers left over where streets meet or highways were built. '
                  f'These {len(sp)} are in CB6. Each is a few thousand square feet or less of planting, paving or empty lot, with no playground, courts or fields: '
                  'not what most people picture when they hear "park." They still count toward the district\'s park acreage.',
                  'For scale: an acre is 43,560 square feet. The smallest here, 0.03 acres, is about 1,300 square feet.']
    kv = []
    for p in sp:
        nm = p['n'] if p['n'] != 'Park' else 'Unnamed lot'
        about = ' '.join(S.P.get(p['id'], {}).get('about', []))
        kv.append([nm, f'{p["loc"].rstrip(".")}. {p["acres"]} acres, about {round(p["acres"] * 43560, -1):,.0f} square feet. Parks ID {p["id"]}.' + (f' {about}' if about else '')])
    q['kv'] = kv + [['Run by', 'NYC Parks'], ['Community board', 'Brooklyn Community Board 6'], ['Source', 'NYC Parks properties and park pages']]
    q['links'] = [['Full page', 'https://bkcb6.app/park/cb6-small-spaces.html'], ['Park rules', 'https://bkcb6.app/park/rules.html']]
    return q

if __name__ == '__main__':
    main()
