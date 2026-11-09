#!/usr/bin/env python3
"""ballotmeasures/areas.json: the policy area of every ballot measure in ballotmeasures/data.json, by id. Each measure
gets one area, from its title: the first rule below that matches, or the id's entry in FIX. A measure no rule matches
stops the script, so none is left out. Usage: python3 scripts/ballot_areas.py"""
import json, os, re, sys, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = json.load(open(os.path.join(ROOT, 'ballotmeasures/data.json')))['measures']
RULES = [
 ('Constitutional conventions and new constitutions', r'constitutional convention|revised constitution|proposed new constitution|constitutional changes amendment|new constitution'),
 ('Housing', r'hous|slum|\brent\b|tenement|urban renewal'),
 ('Parks, forests, water and the environment', r'forest|adirondack|catskill|\bparks?\b|palisades|open lands|sewer|environment|clean (water|air)|sewage|pure water|ski |ski-|bobsled|reservoir|conservation|land bank|mount van hoevenberg|recreation|wildlife|camp |timber|water supply|pollution|climate|olympic'),
 ('Transportation', r'canal|highway|grade crossing|railroad|transit|transportation|barge|bridge|road|thruway|parkway|airport|subway|street'),
 ('Courts and judges', r'court|judge|justice|judicia|surrogate|jury|juror|appellate|grand jur|indictment|bail|district attorney'),
 ('Elections and voting', r'vot|election|ballot|registration|suffrage|absentee|apportion|redistrict|proportional representation|literacy|primary|ranked|term limits|campaign finance'),
 ('Gambling', r'gambl|lotter|bingo|pari-mutuel|games of chance|casino|racing|wager'),
 ('Veterans', r'veteran|soldier|bonus|military|war '),
 ('Education', r'education|school|universit|college|scholarship|student|regents'),
 ('Health and social welfare', r'health|hospital|mental|welfare|relief|aged|aging|child|disab|social|nursing|blind|unemploy|care '),
 ('Workers, pensions and civil service', r'labor|worker|pension|retire|civil service|employ|wage|compensation of work|workmen'),
 ('Police, prisons and public safety', r'prison|correction|police|civilian (complaint|review)|public safety|gun|crime|inmate'),
 ('Debt, taxes and budgets', r'debt|indebted|tax|budget|bond|borrow|fiscal|sinking fund|financ|appropriation|rainy day|procurement|cost of|capital planning'),
 ('Business, banks and jobs', r'job|economic|business|industr|commerce|development'),
 ('Pay and terms of elected officials', r'salar|terms?\b|term limits'),
 ('Land use and property', r'private property|eminent domain|public use|condemnation|annexation|land use|ulurp|city map|public space|permitting|street project'),
 ('Local government and home rule', r'home rule|\bcit(y|ies)\b|count(y|ies)|\btowns?\b|village|local|municipal|supervisor|sheriff|charter|board of estimate|community board|consolidation'),
 ('State government and ethics', r'legislat|governor|senator|assembly|lieutenant|comptroller|attorney general|department|officer|official|government|succession|ethics|office|civic engagement|agenc|commission|laws|publishing|public corporation|emergency|bills'),
]
G, C, CT, B, E, D, R, O, EL, GA, CV = ('State government and ethics', 'Constitutional conventions and new constitutions', 'Courts and judges', 'Business, banks and jobs',
    'Parks, forests, water and the environment', 'Debt, taxes and budgets', 'Rights and equal protection', 'Other', 'Elections and voting', 'Gambling', 'Constitutional conventions and new constitutions')
# titles the rules cannot place, placed by hand; "Other" is for titles that do not say what the measure did
L, LU, PT, T, H, W, BJ = 'Local government and home rule', 'Land use and property', 'Pay and terms of elected officials', 'Transportation', 'Health and social welfare', 'Workers, pensions and civil service', 'Business, banks and jobs'
FIX = {'1913-state-amendment-2': O, '1919-state-amendment-1': E, '1921-state-amendment-4': L, '1927-state-amendment-1': O, '1927-state-amendment-8': LU,
       '1935-state-amendment-3': B, '1937-state-amendment-3': CT, '1939-state-amendment-1': GA, '1941-state-amendment-3': CV, '1959-state-amendment-8': D,
       '1959-state-amendment-9': L, '1961-state-amendment-1': CT, '1961-state-amendment-4': O, '1962-state-amendment-2': O, '1962-state-amendment-4': EL,
       '1963-state-amendment-3': G, '1969-state-amendment-3': E, '1972-state-amendment-2': CV, '1973-state-amendment-2': CT, '1973-state-amendment-3': G,
       '1973-state-amendment-6': CT, '1975-state-amendment-1': R, '1983-state-amendment-3': B, '1983-state-amendment-8': D, '1989-state-amendment-1': L,
       '2001-state-amendment-1': R, '2013-state-proposal-5': E, '2014-state-proposal-2': G, '2024-state-proposal-1': R}
# titles a rule places in the wrong area, by title
BYTITLE = [(r'^city purchasing$', D), (r'^government administration$', L), (r'energy conservation transportation', T), (r'pensions for the department of street cleaning', W), (r'^cleaning public property', L),
           (r'^community boards: term limits', L), (r'more notice and time before votes', L), (r'^charter revision \(2001\)', L),
           (r'institutions of wards of the state', H), (r'measure the true cost of living', H),
           (r'industrial and manufacturing plants|job development authority|state debt for economic development|private sector job support', BJ),
           (r'creation of assembly and senate districts', EL), (r'statement of values|racial equity', R),
           (r'saranac lake for refuse|exchange of land in hamilton county|town of arietta|cemetery for the town of keene|township 40', E),
           (r'^changes to street project approval', LU), (r'succession of governor-elect|filling vacancies of the governor|election of the governor|joint election of governor', G),
           (r'increase in term limits of the governor', PT), (r'changing the term lengths for district attorneys', CT)]
out = {}; miss = []
for m in M:
    t = (m['title'] + ' ').lower(); a = FIX.get(m['id'])
    if not a:
        for rx, name in BYTITLE:
            if re.search(rx, t): a = name; break
    if not a:
        for name, rx in RULES:
            if re.search(rx, t): a = name; break
    if not a: miss.append((m['id'], m['title']))
    out[m['id']] = a
if miss:
    for x in miss: print('NO AREA', x)
    sys.exit(1)
json.dump({'areas': [r[0] for r in RULES] + ['Rights and equal protection', 'Other'], 'by': out}, open(os.path.join(ROOT, 'ballotmeasures/areas.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
c = collections.Counter(out.values()); print(len(out), dict(c))
if '-v' in sys.argv:
    for name in [r[0] for r in RULES] + ['Rights and equal protection', 'Other']:
        print('\n##', name)
        for m in M:
            if out[m['id']] == name: print('  ', m['year'], m['level'][0], m['title'][:95])
