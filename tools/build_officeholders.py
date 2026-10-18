#!/usr/bin/env python3
"""Every borough-wide, citywide, statewide and federal officeholder for New York City since consolidation (January 1, 1898),
by start and end date: data/districthistory/at-large.json, read by assets/rep-history.js and /electionhistory/.
Read from Wikipedia's lists (wikitext, action=raw), with the corrections below, each from the same pages.
python3 tools/build_officeholders.py <folder for the wikitext>   (downloads any page not already there)"""
import json, os, re, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from wikitable import clean, dates, person, rows, tables

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = sys.argv[1]
PAGES = ['List_of_borough_presidents_of_New_York_City', 'List_of_mayors_of_New_York_City', 'New_York_City_Council', 'New_York_City_Comptroller',
         'List_of_governors_of_New_York', 'List_of_lieutenant_governors_of_New_York', 'New_York_State_Attorney_General', 'New_York_State_Comptroller',
         'List_of_United_States_senators_from_New_York', 'List_of_presidents_of_the_United_States']


def wiki(p):
    f = os.path.join(DIR, p + '.wiki')
    if not os.path.exists(f):
        for t in range(8):
            try:
                req = urllib.request.Request('https://en.wikipedia.org/w/index.php?title=%s&action=raw' % p, headers={'User-Agent': 'bkcb6.app/1.0 (Mike@bkcb6.org)'})
                open(f, 'w').write(urllib.request.urlopen(req, timeout=30).read().decode()); break
            except Exception:
                time.sleep(20 * (t + 1))
        time.sleep(3)
    return clean(open(f).read())


def table_list(w, sec=None):
    if sec: w = w[w.find(sec):]
    best = None
    for t in tables(w):
        res = []
        for r in rows(t):
            p, d = person(r), dates(r)
            if p and re.match(r'^\d{4}', p): p = None  # a continuation row whose only link is an election year
            if p and d: res.append([p, d[0], d[1] if len(d) > 1 else None])
            elif d and res and not p: res[-1][2] = d[-1]
        if res and (best is None or len(res) > len(best)): best = res
    return best or []


def keep(L):  # since consolidation, with a start date
    return [x for x in L if x[1] and (x[2] or '9999') >= '1898-01-01' and x[1] >= '1890']


def H(L, **kw):
    return [dict({'name': n.replace('&nbsp;', ' '), 'from': max(a, '1898-01-01'), 'to': b}, **kw) for n, a, b in L]


SRC = 'https://en.wikipedia.org/wiki/'
offices = []

# ---- borough presidents ----
w = wiki('List_of_borough_presidents_of_New_York_City')
secs = re.split(r'\n==([^=].*?)==\n', w)
bp = {}
for i in range(1, len(secs), 2):
    for k, d in (('Bronx', '2'), ('Brooklyn', '3'), ('Manhattan', '1'), ('Queens', '4'), ('Staten Island', '5')):
        if k in secs[i] and 'borough presidents' in secs[i]:
            bp[d] = H(keep(table_list(secs[i + 1])))
offices.append({'key': 'bp', 'label': 'Borough President', 'scope': 'boro', 'holders': bp, 'src': SRC + 'List_of_borough_presidents_of_New_York_City'})

# ---- council members elected borough-wide (1938 to 1949 under proportional representation, and the at-large seats of 1964 to June 1983) ----
# only members with a Wikipedia article give their dates, so this list is incomplete
AT = json.load(open(os.path.join(ROOT, 'data/districthistory/council-atlarge.json')))
offices.append({'key': 'atlarge', 'label': 'Council Member elected borough-wide', 'scope': 'boro', 'multi': True, 'from': '1938-01-01', 'until': '1983-06-30', 'eras': [['1938-01-01', '1949-12-31'], ['1964-01-01', '1983-06-30']],
                'holders': AT['holders'], 'note': AT['note'], 'src': AT['src']})

# ---- mayor ----
m = H(keep(table_list(wiki('List_of_mayors_of_New_York_City'), 'Greater New York')))
for x in m:
    if x['name'] == 'Vincent R. Impellitteri': x['from'] = '1950-08-31'; x['note'] = 'acting mayor from August 31, 1950; elected in a special election and inaugurated November 14, 1950'
    if x['name'] == 'William T. Collins': x['to'] = '1925-12-31'; x['note'] = 'acting mayor for one day'
offices.append({'key': 'mayor', 'label': 'Mayor', 'scope': 'city', 'holders': m, 'src': SRC + 'List_of_mayors_of_New_York_City'})

# ---- the citywide presiding officer: President of the Council (1898 to 1901), of the Board of Aldermen (1902 to 1937),
#      of the City Council (1938 to 1993), Public Advocate (1994 on); and the Council Speaker ----
po = table_list(wiki('New_York_City_Council'), '==Presiding officers since 1898')
cut = [i for i, x in enumerate(po) if x[0] == 'Jumaane Williams'][0] + 1
pa, sp = H(po[:cut]), H(po[cut:])


def title(d):
    return 'President of the Council' if d < '1902' else 'President of the Board of Aldermen' if d < '1938' else 'President of the City Council' if d < '1994' else 'Public Advocate'


out = []
for x in pa:  # one holder across a change of title gets a row for each title
    for a, b in (('1898-01-01', '1901-12-31'), ('1902-01-01', '1937-12-31'), ('1938-01-01', '1993-12-31'), ('1994-01-01', None)):
        f, t = max(x['from'], a), min(x['to'] or '9999', b or '9999')
        if f <= t: out.append(dict(x, **{'from': f, 'to': None if t == '9999' else t, 'title': title(f)}))
for x in out:
    if x['name'] == 'Corey Johnson': x['note'] = 'acting'
offices.append({'key': 'pa', 'label': 'Public Advocate', 'labels': [['1898-01-01', 'President of the Council'], ['1902-01-01', 'President of the Board of Aldermen'], ['1938-01-01', 'President of the City Council'], ['1994-01-01', 'Public Advocate']],
                'scope': 'city', 'holders': out, 'src': SRC + 'New_York_City_Council#Presiding_officers_since_1898'})

# ---- comptroller: the list gives years only ----
w = wiki('New_York_City_Comptroller')
w = w[w.find('===Post-consolidation'):]
cm = []
for a, b, n in re.findall(r'\*\s*(\d{4})(?:[–-](\d{4}|present))?\s*\[\[(?:[^\]|]*\|)?([^\]]+)\]\]', w):
    cm.append({'name': n, 'from': a + '-01-01', 'to': None if b == 'present' else (b or a) + '-12-31', 'years': True})
offices.append({'key': 'comptroller', 'label': 'Comptroller', 'scope': 'city', 'holders': cm, 'src': SRC + 'New_York_City_Comptroller'})
offices.append({'key': 'speaker', 'label': 'Council Speaker', 'scope': 'city', 'from': sp[0]['from'], 'holders': sp, 'src': SRC + 'New_York_City_Council#Presiding_officers_since_1898'})

# ---- state ----
g = [x for x in H(keep(table_list(wiki('List_of_governors_of_New_York'), '==Governors=='))) if not x['name'].isdigit()]
for x in g:
    if x['name'] == 'Kathy Hochul': x['from'], x['to'] = '2021-08-24', None
offices.append({'key': 'governor', 'label': 'Governor', 'scope': 'state', 'holders': g, 'src': SRC + 'List_of_governors_of_New_York'})
lg = [x for x in H(keep(table_list(wiki('List_of_lieutenant_governors_of_New_York')))) if x['to'] or x['name'] in ('Antonio Delgado',)]
lg = [x for x in lg if x['name'] not in ('100px', 'Dean Skelos')]  # acting rows (a Senate leader acting as LG) are left out
for x in lg:
    if x['name'] == 'Kathy Hochul': x['from'], x['to'] = '2015-01-01', '2021-08-24'
lg.append({'name': 'Antonio Delgado', 'from': '2022-05-25', 'to': None})
offices.append({'key': 'lg', 'label': 'Lieutenant Governor', 'scope': 'state', 'holders': lg, 'src': SRC + 'List_of_lieutenant_governors_of_New_York'})
offices.append({'key': 'ag', 'label': 'Attorney General', 'scope': 'state', 'holders': H(keep(table_list(wiki('New_York_State_Attorney_General'), '===New York State (1777'))), 'src': SRC + 'Attorney_General_of_New_York'})
offices.append({'key': 'statecomp', 'label': 'State Comptroller', 'scope': 'state', 'holders': H(keep(table_list(wiki('New_York_State_Comptroller'), '==New York state comptrollers=='))), 'src': SRC + 'New_York_State_Comptroller'})

# ---- U.S. Senate: class 1 cells sit left of their dates, class 3 cells right ----
w = wiki('List_of_United_States_senators_from_New_York')
AB = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'June': 6, 'Jul': 7, 'July': 7, 'Aug': 8, 'Sep': 9, 'Sept': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
      'January': 1, 'February': 2, 'March': 3, 'April': 4, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}


def d1(s):
    if re.search(r'present|Incumbent', s, re.I): return None
    m = re.search(r'([A-Z][a-z]+)\.?\s+(\d{1,2}),\s*(\d{4})', s)
    return '%s-%02d-%02d' % (m.group(3), AB[m.group(1)], int(m.group(2))) if m else 'X'


last, left, sen = None, None, {'1': [], '3': []}
for c in re.split(r'\n\|(?!-)|\n!|\|\|', w):
    if 'nowrap' in c and '–' in c:
        a, b = c.split('|', 1)[1].split('–', 1); last = (d1(a), d1(b))
        if left: sen['1'].append([left, last[0], last[1]]); left = None
    elif re.search(r"align=left\s*\|.*'''\[\[", c): left = person(c)
    elif re.search(r"align=right\s*\|.*'''\[\[", c): sen['3'].append([person(c), last[0], last[1]])
offices.append({'key': 'ussenate', 'label': 'U.S. Senate', 'scope': 'us', 'seats': [H(keep(sen['3'])), H(keep(sen['1']))], 'src': SRC + 'List_of_United_States_senators_from_New_York'})

# ---- president: the list's rows link the number, so the names come from the number ----
PN = {25: 'William McKinley', 26: 'Theodore Roosevelt', 27: 'William Howard Taft', 28: 'Woodrow Wilson', 29: 'Warren G. Harding', 30: 'Calvin Coolidge',
      31: 'Herbert Hoover', 32: 'Franklin D. Roosevelt', 33: 'Harry S. Truman', 34: 'Dwight D. Eisenhower', 35: 'John F. Kennedy', 36: 'Lyndon B. Johnson',
      37: 'Richard Nixon', 38: 'Gerald Ford', 39: 'Jimmy Carter', 40: 'Ronald Reagan', 41: 'George H. W. Bush', 42: 'Bill Clinton', 43: 'George W. Bush',
      44: 'Barack Obama', 45: 'Donald Trump', 46: 'Joe Biden', 47: 'Donald Trump'}
pr = [x for x in table_list(wiki('List_of_presidents_of_the_United_States')) if x[0].isdigit() and int(x[0]) >= 25]
starts = {int(x[0]): x[1] for x in pr}
starts[25], starts[34] = '1897-03-04', '1953-01-20'
nums = sorted(starts)
prez = [{'name': PN[n], 'from': max(starts[n], '1898-01-01'), 'to': (starts[nums[i + 1]] if i + 1 < len(nums) else None)} for i, n in enumerate(nums)]
offices.append({'key': 'president', 'label': 'President', 'scope': 'us', 'holders': prez, 'src': SRC + 'List_of_presidents_of_the_United_States'})

for o in offices:  # each list in date order
    if o.get('seats'): o['seats'] = [sorted(x, key=lambda h: h['from']) for x in o['seats']]
    elif isinstance(o['holders'], dict): o['holders'] = {k: sorted(v, key=lambda h: h['from']) for k, v in o['holders'].items()}
    else: o['holders'] = sorted(o['holders'], key=lambda h: h['from'])
ABOUT = ('Officeholders elected borough-wide, citywide, statewide and nationwide since New York City was consolidated on January 1, 1898, '
         'by start and end date, from the Wikipedia lists named in each office. The city comptroller list gives years only. '
         'Council members elected borough-wide are only those whose own Wikipedia article gives their dates.')
json.dump({'about': ABOUT, 'since': '1898-01-01', 'sources': [o['src'] for o in offices], 'offices': offices},
          open(os.path.join(ROOT, 'data/districthistory/at-large.json'), 'w'), ensure_ascii=False, indent=0)
for o in offices:
    hs = o.get('seats') or ([v for k in o['holders'] for v in o['holders'][k]] if isinstance(o['holders'], dict) else o['holders'])
    if o.get('seats'): hs = [x for s in hs for x in s]
    print(o['key'], len(hs), hs[0]['name'], hs[0]['from'], '...', hs[-1]['name'], hs[-1]['from'], hs[-1]['to'])
