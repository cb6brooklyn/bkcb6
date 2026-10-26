"""Parse The Comprehensive Plan for Brooklyn (October 2023) into plan2023.json.
Source PDF: https://www.brooklynbp.nyc.gov/wp-content/uploads/2025/03/Comprehensive_Plan-1.pdf
Page numbers in the output are PDF page numbers, which equal the printed page numbers in this plan."""
import pymupdf, json, re, collections

import sys, os
DOC = pymupdf.open(sys.argv[1] if len(sys.argv) > 1 else 'cp2023.pdf')
if len(sys.argv) > 2: os.chdir(sys.argv[2])
NP = len(DOC)

# ---------- lines with fonts, superscript note markers dropped ----------
def page_lines(pn):
    pg = DOC[pn - 1]
    out = []
    for b in pg.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            sp = [s for s in l['spans'] if s['text'].strip()]
            if not sp:
                continue
            main = max(sp, key=lambda s: len(s['text'].strip()))
            sz = main['size']
            txt = ''
            for s in l['spans']:
                t = s['text']
                if s['size'] < sz * 0.8 and re.fullmatch(r'\s*[\d,*†]+\s*', t) and s is not l['spans'][0]:
                    continue  # superscript note marker
                if s['size'] < sz * 0.8 and re.fullmatch(r'\s*2\.5\s*', t):
                    t = '2.5'  # PM2.5 subscript
                txt += t
            txt = re.sub(r'\s+', ' ', txt).strip()
            f0 = sp[0]
            out.append(dict(p=pn, x0=l['bbox'][0], y0=l['bbox'][1], x1=l['bbox'][2], y1=l['bbox'][3],
                            font=f0['font'], size=round(f0['size'], 1), color=f0['color'], t=txt))
    return out

ALL = {p: page_lines(p) for p in range(1, NP + 1)}
FULLTEXT = ' '.join(l['t'] for p in ALL for l in ALL[p])
HYPH = set(m.lower() for m in re.findall(r'\b[A-Za-z]+-[A-Za-z]+\b', FULLTEXT))

def ordered(lines, split=300):
    left = [l for l in lines if l['x0'] < split]
    right = [l for l in lines if l['x0'] >= split]
    left.sort(key=lambda l: (round(l['y0']), l['x0']))
    right.sort(key=lambda l: (round(l['y0']), l['x0']))
    return left + right

def join(a, b):
    if not a:
        return b
    if a.endswith('-'):
        w1 = re.findall(r'([A-Za-z]+)-$', a)
        w2 = re.findall(r'^([A-Za-z]+)', b)
        if w1 and w2 and (w1[0] + '-' + w2[0]).lower() in HYPH:
            return a + b
        if b[:1].islower():
            return a[:-1] + b
        return a + b
    if a.endswith('—') or a.endswith('/'):
        return a + b
    return a + ' ' + b

def is_body(l):
    return l['font'].startswith('Garamond') or l['font'].startswith('Wingdings') or (l['font'].startswith('Graphik-Light') and l['size'] == 8.0) or (l['font'] == 'Graphik-Regular' and l['size'] == 10.0 and l['color'] == 0x221f1f)

BUL = re.compile(r'^(?:[••\u0083]|\x83)\s*')

def paras(lines, pn_of=None):
    """Body lines -> [[type,text,page]] paragraphs. Breaks on vertical gaps, column changes and bullets."""
    out = []
    cur = None
    prev = None
    for l in lines:
        t = l['t']
        bullet = bool(BUL.match(t)) or l['font'].startswith('Wingdings')
        t = BUL.sub('', t).strip()
        if not t:
            continue
        gap = prev is None or l['p'] != prev['p'] and False or (l['p'] == prev['p'] and (l['y0'] - prev['y1'] > 8 or l['y0'] < prev['y0'] - 2))
        if prev is not None and l['p'] == prev['p'] and (l['x0'] >= 300) != (prev['x0'] >= 300):
            gap = bool(re.search(r'[.:!?”"]$', prev['t']))
        if prev is not None and l['p'] != prev['p']:
            # new page: continue the paragraph only if the previous one did not end a sentence
            gap = bool(re.search(r'[.:!?”"]$', prev['t']))
        if l['font'] == 'GaramondPremrPro-Bd' and len(t) < 45 and not bullet and (cur is None or gap or t.endswith(':')):
            if cur:
                out.append(cur)
            out.append(['h', t.rstrip(':'), l['p']])
            cur = None
            prev = l
            continue
        if cur is None or gap or bullet:
            if cur:
                out.append(cur)
            cur = ['li' if bullet else 'p', t, l['p']]
        else:
            cur[1] = join(cur[1], t)
        prev = l
    if cur:
        out.append(cur)
    for c in out:
        c[1] = re.sub(r'\s+', ' ', c[1]).strip()
    return out

FOOTER_Y = 745

def keep(l):
    if l['y0'] > FOOTER_Y:
        return False
    if l['font'].startswith('GraphikCond'):
        return False  # footnotes
    return True

# ---------- front matter ----------
def simple(p0, p1, title):
    lines = []
    lede = []
    for p in range(p0, p1 + 1):
        for l in ordered([x for x in ALL[p] if keep(x)]):
            if l['font'] == 'Graphik-Regular' and l['size'] == 12.0:
                lede.append(l)
            elif is_body(l):
                lines.append(l)
    b = []
    if lede:
        lt = ''
        for x in lede:
            lt = join(lt, x['t'])
        b.append(['lede', lt, lede[0]['p']])
    b += paras(lines)
    return {'t': title, 'p': p0, 'b': b}

front = []
letter = simple(4, 4, 'Letter from the Borough President')
front.append(letter)
# executive summary: body uses Graphik-Medium 9 run-in heads + Garamond
ex = []
for p in range(5, 11):
    for l in ordered([x for x in ALL[p] if keep(x)]):
        if is_body(l) or (l['font'] == 'Graphik-Medium' and l['size'] == 9.0):
            ex.append(l)
front.append({'t': 'Executive Summary', 'p': 5, 'b': paras(ex)})
front.append(simple(11, 11, 'Introduction'))
front.append(simple(12, 13, 'Methodology'))

# ---------- existing conditions ----------
EC = [('History of Planning in NYC', 15, 15), ('A Focus on Housing and Health', 16, 17), ('Demographic', 18, 24),
      ('Socioeconomic', 25, 34), ('Health', 35, 52), ('Land Use and Built Form', 53, 64), ('Housing', 65, 80),
      ('Transportation and Utilities', 81, 99), ('Environmental', 100, 111), ('Neighborhood Conditions', 112, 123)]
OCR = {int(k): v for k, v in json.load(open('ocr.json')).items()}

def norm(s):
    return re.sub(r'[^a-z0-9 ]', ' ', s.lower()).split()

MAPT = {19: ('Race and Ethnicity', 'Race and Ethnicity'), 20: ('Median Age', 'Median Age'), 21: ('Sex Ratio', 'Sex Ratio'),
 22: ('Limited English Proficiency', 'English Proficiency'), 23: ('Educational Attainment', 'Educational Attainment'), 24: ('Foreign-Born Population', 'Foreign Born Population'),
 26: ('Total Number of Jobs Added by Neighborhood: 2010 - 2019', None), 28: ('Median Household Income', 'Median Income'), 29: ('Poverty', 'Poverty'),
 30: ('Service Occupations', 'Service Occupations'), 31: ('Healthcare Workers', 'Healthcare Support Occupations'), 32: ('Work Destination', 'Work Destination, Brooklyn Residents'),
 33: ('Cash Public Assistance', 'Cash Public Assistance'), 34: ('Population Vulnerability to Displacement', 'Population Vulnerabilities to Displacement'),
 38: ('Life Expectancy', 'Life Expectancy'), 39: ('Premature Mortality', 'Premature Mortality'), 40: ('Asthma Hospitalizations (Adults)', 'Asthma Hospitalizations (Adults)'),
 41: ('Asthma Hospitalizations (Children)', 'Asthma Hospitalizations (Children)'), 42: ('Adult Cancer', 'Adult Cancer'), 43: ('Coronary Heart Disease', 'Coronary Heart Disease'),
 44: ('Adult Diabetes', 'Adult Diabetes'), 45: ('Adult Obesity', 'Adult Obesity'), 46: ('Mental Health', 'Mental Health'), 47: ('No Health Insurance', 'No Health Insurance'),
 48: ('Self-Reported Health', 'Self-Reported Health'), 49: ('Low Birth Weight at Full Term', 'Low Birth Weight at Full Term'), 50: ('Avoidable Adult Hospitalizations', 'Avoidable Adult Hospitalizations'),
 51: ('Food Insecurity', 'Food Insecurity'), 52: ('Unhealthy Food Access', 'Unhealthy Food Access'),
 55: ('Land Use', 'Land Use'), 56: ('Land Use by Type', 'Land Use'), 57: ('Zoning Districts', 'Zoning Districts'), 58: ('Residential Allowable Density', 'Residential Floor Area Ratio'),
 59: ('Zoning Changes', 'Zoning Changes'), 60: ('Landmarks and Historic Districts', 'Historic and Individual Landmarks'), 61: ('Transit Zones', 'Transit Zones'),
 62: ('Business and Industrial Areas', 'Business and Industrial Areas'), 63: ('"FRESH" Food Program', 'FRESH Zones'), 64: ('Improvement and Land Values', 'Improvement Land Value Ratios'),
 68: ('Housing Growth', 'Housing Growth'), 69: ('Housing Unit Change', 'Housing Unit Change 2010 - 2020'), 70: ('Income Restricted Housing', 'Income-restricted Housing & Zoning'),
 71: ('Residential Units per Acre', 'Residential Units per Acre'), 72: ('Median Rent', 'Median Rent'), 73: ('Housing Tenure', 'Housing Tenure: Renters'), 74: ('Rent Burden', 'Rent Burden'),
 75: ('Overcrowded Households', 'Overcrowded Households'), 76: ('Population Change 2010-2020', 'Population Change 2010 - 2020'), 77: ('Public Housing', 'Public Housing'),
 78: ('Shelters and Transitional Housing', 'Shelters and Transitional Housing'), 79: ('Market Pressure', 'Market Pressure'), 80: ('Displacement Risk', 'Displacement Risk'),
 84: ('Walking Distance to Subway', 'Walking Distance to Subway'), 85: ('Proposed Interborough Express (IBX) Route', 'Interborough Express (IBX)'),
 86: ('Bus Network (titled “Bicycle Routes” on the page)', 'Bus Network'), 87: ('Bicycle Routes', 'Bicycle Network'), 88: ('Citi Bike Availability', 'Bicycle Network'),
 89: ('Monthly Bicycle Use', 'Monthly Bicycle Use'), 90: ('Street Types by Use', 'Street Types by Use'), 91: ('Commute to Work by Transit', 'Commute to Work by Transit'),
 92: ('Commute to Work by Driving', 'Commute to Work by Driving'), 93: ('Vehicle Miles Traveled', 'Vehicle Miles Traveled'), 94: ('Households with No Vehicles', 'Households with No Vehicles'),
 95: ('Pedestrian Safety', 'Pedestrian Safety'), 96: ('Cycling Safety', 'Cyclist Safety'), 97: ('Truck Routes', 'Truck Routes'), 98: ('Broadband Adoption', 'Broadband Adoption'),
 99: ('Sewersheds', 'Wastewater Infrastructure'), 102: ('Future Floodplain', 'Future Coastal Flooding'), 103: ('Stormwater Flooding', 'Stormwater Flooding'),
 104: ('Air Pollution - PM2.5', 'Air Pollution – PM 2.5'), 105: ('Air Pollution - Nitrogen Dioxide', 'Air Pollution – Nitrogen Dioxide'), 106: ('Indoor Air Quality', 'Indoor Air Quality Complaints'),
 107: ('Tree Cover Canopy', 'Tree Canopy Coverage'), 108: ('Tree Cover Canopy Change', 'Tree Canopy Change 2010-2017'), 109: ('Heat Vulnerability', 'Heat Vulnerability'),
 110: ('Walking Access to Parks', 'Park Access'), 111: ('Waterfront Access', 'Waterfront Access'), 114: ('Hospitals and Health Facilities', 'Hospitals and Health Facilities'),
 115: ('Hospital Patient Satisfaction', 'Hospital Patient Satisfaction'), 116: ('School Accessibility', 'School Accessibility'), 117: ('Public Assembly', 'Public Assembly'),
 118: ('Total Number of School Seats Needed', 'Overcrowding and Schools'), 119: ('School Locations', 'School Locations'), 120: ('Day Care and Pre-Kindergarten', 'Daycare and Pre-Kindergarten'),
 121: ('Libraries and Cultural Programs', 'Libraries and Cultural Programs'), 122: ('7 Major Felony Crimes Committed 2022', 'Neighborhood Safety: Major Felony Crimes'),
 123: ('Perception of Neighborhood Safety', 'Neighborhood Safety: Perception')}
secs = []
for title, p0, p1 in EC:
    sec = {'t': title, 'p': p0, 'lede': '', 'b': [], 'topics': [], 'fb': None, 'maps': []}
    cur_lines = []
    mode = 'intro'
    topic = None
    fb_lines = []
    lede = []
    for p in range(p0, p1 + 1):
        ls = [x for x in ALL[p] if keep(x)]
        nbody = sum(1 for x in ls if x['font'].startswith('Garamond'))
        if p not in (15,) and nbody <= 3:
            sec['maps'].append({'p': p})
            continue
        for l in ordered(ls):
            if l['font'] == 'Graphik-Regular' and l['size'] == 12.0:
                lede.append(l); continue
            if l['font'] == 'Graphik-Medium' and l['size'] == 12.0:
                mode = 'fb'; continue
            if l['font'] == 'Graphik-Bold' and l['size'] == 11.0 and mode != 'fb':
                if topic and topic['_l']:
                    pass
                topic = {'t': l['t'], 'p': p, '_l': []}
                sec['topics'].append(topic)
                mode = 'topic'
                continue
            if not is_body(l):
                continue
            if mode == 'fb':
                fb_lines.append(l)
            elif mode == 'topic' and topic is not None:
                topic['_l'].append(l)
            else:
                cur_lines.append(l)
    lt = ''
    for x in lede:
        lt = join(lt, x['t'])
    sec['lede'] = lt
    sec['b'] = paras(cur_lines)
    for t in sec['topics']:
        t['b'] = paras(t.pop('_l'))
    if fb_lines:
        # "What we heard:" / "Updates:" run-in heads are bold Garamond at the start of a line
        sec['fb'] = {'p': fb_lines[0]['p'], 'b': paras(fb_lines)}
    for m in sec['maps']:
        t, tp = MAPT[m['p']]
        m['t'] = t
        if m['p'] == 26:
            m['chart'] = True  # bar charts, not a map
        if tp:
            assert tp in [x['t'] for x in sec['topics']], (tp, sec['t'])
            m['topic'] = tp
    secs.append(sec)

ec_intro = []
for l in ordered([x for x in ALL[14] if keep(x)]):
    if l['font'] == 'Graphik-Regular' and l['size'] == 10.0:
        ec_intro.append(l)

# ---------- powers of the BP (p.125) ----------
powers = {'p': 125, 'intro': '', 'k': []}
_cur = None
_buf = []
for l in ordered([x for x in ALL[125] if keep(x)]):
    if l['font'] == 'Graphik-Regular' and l['size'] == 10.0:
        powers['intro'] = join(powers['intro'], l['t'])
    elif l['font'] == 'Graphik-Medium' and l['size'] == 12.0:
        if _cur: _cur['b'] = paras(_buf); _buf = []
        _cur = {'k': l['t'].title(), 'sub': '', 'b': []}
        powers['k'].append(_cur)
    elif l['font'] == 'Graphik-Medium' and l['size'] == 9.0 and _cur:
        _cur['sub'] = join(_cur['sub'], l['t'])
    elif is_body(l):
        _buf.append(l)
if _cur: _cur['b'] = paras(_buf)

# ---------- recommendations ----------
def icon_clusters(pn):
    pg = DOC[pn - 1]
    out = []
    for dr in pg.get_drawings():
        r = dr['rect']
        if r.width > 22 or r.height > 22 or r.y0 > 725:
            continue
        n = len(dr['items'])
        kind = {85: 'Advocacy', 26: 'Budget', 14: 'Outreach', 28: 'Land Use'}.get(n) if dr['type'] == 'f' else None
        if kind:
            dx, dy = (5.5, 2.5) if kind == 'Land Use' else (0, 0)  # the land use glyph's distinctive piece sits at its lower right
            out.append({'k': kind, 'x': r.x0 - dx, 'y': r.y0 - dy, 'y1': r.y1, 'x1': r.x1})
    return out

FWS = ['Housing Growth & Parking Demand Management', 'Health & Wellness Economy', 'Healthy Streets & Environment', 'Resilient Infrastructure & Jobs']
REC = re.compile(r'^(\d+\.\d+\.\d+)\s*(.*)$')
SUB = re.compile(r'^([a-z])\s?\)\s*(.*)$')
OBJ = re.compile(r'^Objective (\d+\.\d+):\s*(.*)$')

goals = []
G = O = R = S = None
starts = []  # (page, col, y, x, target)
pend_goal = None
for p in range(126, 149):
    ls = [x for x in ALL[p] if keep(x)]
    figt = None
    for l in ordered(ls):
        t = l['t']
        f = l['font']
        if f == 'Graphik-Medium' and l['size'] == 12.0 and l['color'] == 0x2c496f:
            m = re.match(r'GOAL\s*\d*:\s*(.*)', t)
            if m:
                G = {'n': len(goals) + 1, 't': m.group(1).title().replace(' And ', ' and '), 'goal': '', 'p': p, 'obj': []}
                goals.append(G); O = R = S = None
            elif G is not None:
                G['goal'] = join(G['goal'], t)
            continue
        if f == 'Graphik-Medium' and l['size'] >= 12.0 and G is not None and not G['obj'] and G['p'] == p:
            G['goal'] = join(G['goal'], t)
            continue
        if f == 'Graphik-Bold' and l['size'] == 11.0:
            m = OBJ.match(t)
            if m:
                O = {'n': m.group(1), 't': m.group(2), 'p': p, 'fw': [], 'recs': [], 'figs': [], 'notes': []}
                G['obj'].append(O); R = S = None
                O['_y'] = (p, l['y1'], l['x0'])
            elif O is not None and O.get('_y') and O['_y'][0] == p and abs(l['y0'] - O['_y'][1]) < 6:
                O['t'] = join(O['t'], t); O['_y'] = (p, l['y1'], l['x0'])
            continue
        if f == 'Graphik-RegularItalic' and l['size'] == 10.0 and l['color'] == 0xffffff:
            for fw in FWS:
                if t and (t in fw) and O is not None:
                    key = fw
                    if key not in O['fw'] and (len(t) > 12 or t.startswith('Housing')):
                        O['fw'].append(key)
            continue
        if t == 'Recommendations:':
            continue
        if f == 'Graphik-Medium' and l['size'] == 10.0:
            if O is not None:
                if figt and figt['p'] == p and abs(l['y0'] - figt['_y']) < 14:
                    figt['t'] = join(figt['t'], t); figt['_y'] = l['y1']
                else:
                    figt = {'t': t, 'p': p, 'cap': '', '_y': l['y1']}
                    O['figs'].append(figt)
            continue
        if f == 'Graphik-RegularItalic' and l['size'] == 6.5:
            if O is not None and O['figs']:
                # attach caption to the nearest figure title on this page
                cands = [x for x in O['figs'] if x['p'] == p]
                if cands:
                    c = cands[-1]
                    c['cap'] = join(c['cap'], t)
            continue
        if f == 'Graphik-Regular' and l['size'] == 10.0 and l['color'] == 0x123d66:
            if O is not None:
                if O['notes'] and O['notes'][-1][2] == p and l['y0'] - O['_ny'] < 18:
                    O['notes'][-1][1] = join(O['notes'][-1][1], t)
                else:
                    O['notes'].append(['note', t, p])
                O['_ny'] = l['y1']
            continue
        if not f.startswith('Garamond') and not (f == 'Graphik-Black' and l['size'] == 9.5):
            continue
        if O is None:
            continue
        m = REC.match(t)
        if m:
            R = {'n': m.group(1), 't': m.group(2), 'p': p, 'cats': [], 'subs': []}
            O['recs'].append(R); S = None
            starts.append((p, l['x0'] >= 300, l['y0'], l['x0'], R))
            continue
        m = SUB.match(t)
        if m and R is not None:
            S = {'l': m.group(1), 't': m.group(2), 'p': p, 'cats': []}
            R['subs'].append(S)
            starts.append((p, l['x0'] >= 300, l['y0'], l['x0'], S))
            continue
        tgt = S or R
        if tgt is not None:
            tgt['t'] = join(tgt['t'], t)

# icons -> categories: icons stacked beside one recommendation form a stack; the stack belongs to the
# recommendation (or lettered sub-item) whose first line is nearest the top of the stack
unassigned = 0
for p in range(126, 149):
    for ic in icon_clusters(p):
        col = ic['x'] >= 300
        c = [s for s in starts if s[0] == p and s[1] == col and s[2] - 12 <= ic['y']]
        if not c:
            unassigned += 1
            print('unassigned icon', p, round(ic['x']), round(ic['y']), ic['k'])
            continue
        tgt = max(c, key=lambda s: s[2])[4]
        if ic['k'] not in tgt['cats']:
            tgt['cats'].append(ic['k'])
ORDER = ['Advocacy', 'Land Use', 'Budget', 'Outreach']
for g in goals:
    for o in g['obj']:
        o.pop('_y', None); o.pop('_ny', None)
        for f in o['figs']:
            f.pop('_y', None)
        for r in o['recs']:
            r['cats'].sort(key=ORDER.index)
            for s in r['subs']:
                s['cats'].sort(key=ORDER.index)
                for k in s['cats']:
                    if k not in r['cats']:
                        pass
            r['t'] = re.sub(r'\s+', ' ', r['t']).strip()

# ---------- land use frameworks (149-158) ----------
fws = []
cur = None
for p in range(149, 158):
    ls = [x for x in ALL[p] if keep(x)]
    heads = [x for x in ls if x['font'] == 'Graphik-Light' and x['size'] >= 30]
    if heads:
        name = re.sub(r'\s+', ' ', ' '.join(x['t'] for x in sorted(heads, key=lambda x: x['y0']))).rstrip(':').strip()
        cur = {'t': name, 'p': p, '_l': [], 'maps': []}
        fws.append(cur)
    body = [x for x in ordered(ls) if is_body(x)]
    if cur is None:
        continue
    if len([x for x in ls if x['font'].startswith('Garamond')]) <= 3:
        cur['maps'].append(p)
    cur['_l'] += body
fw_intro = paras([x for x in ordered([y for y in ALL[149] if keep(y)]) if is_body(x)])
for f in fws:
    f['b'] = paras(f.pop('_l'))

nxt = simple(159, 159, 'Next Steps'); nxt['p'] = 158

# ---------- appendix 1: data sources table ----------
sources = []
for p in range(161, 164):
    rows = collections.defaultdict(list)
    for w in DOC[p - 1].get_text('words'):
        if (56 if p == 161 else 30) < w[1] < 745:
            rows[round(w[1])].append(w)
    for y in sorted(rows):
        cols = ['', '', '', '']
        for w in sorted(rows[y], key=lambda w: w[0]):
            i = 0 if w[0] < 210 else 1 if w[0] < 375 else 2 if w[0] < 425 else 3
            cols[i] = (cols[i] + ' ' + w[4]).strip()
        if cols[0] == 'Map' or re.match(r'^\d+ Comprehensive', ' '.join(cols)):
            continue
        if sources and not any(sources[-1][1:]) and sources[-1][0] != 'Frameworks' and cols[0] and any(cols[1:]):
            sources[-1] = [sources[-1][0] + ' ' + cols[0]] + cols[1:]
            continue
        if not cols[0] and sources:
            for i in range(4):
                if cols[i]:
                    sources[-1][i] = (sources[-1][i] + ' ' + cols[i]).strip()
            continue
        sources.append(cols)
# glossary: Graphik-Medium 9 terms, Garamond definitions
gloss = []
for p in range(165, 170):
    for l in ordered([x for x in ALL[p] if keep(x)]):
        if l['font'] == 'Graphik-Medium' and l['size'] == 9.0:
            if gloss and gloss[-1]['_t'] and gloss[-1]['p'] == p and l['y0'] - gloss[-1]['_y'] < 6:
                gloss[-1]['t'] = join(gloss[-1]['t'], l['t']); gloss[-1]['_y'] = l['y1']
            else:
                gloss.append({'t': l['t'], 'd': '', 'p': p, '_t': True, '_y': l['y1']})
        elif is_body(l) and gloss:
            gloss[-1]['d'] = join(gloss[-1]['d'], l['t']); gloss[-1]['_t'] = False
for g in gloss:
    g.pop('_t'); g.pop('_y')

def headed(p0, p1):
    out = []
    buf = []
    for p in range(p0, p1 + 1):
        for l in ordered([x for x in ALL[p] if keep(x)]):
            if l['size'] >= 30:
                continue
            head = (l['font'].startswith('Graphik-Bold') and l['size'] >= 9) or (l['font'] == 'Graphik-Medium' and l['size'] == 9.0) or l['font'] == 'GaramondPremrPro-Bd'
            if head:
                if buf:
                    out += paras(buf); buf = []
                if out and out[-1][0] == 'h' and out[-1][2] == p and l['y0'] - out[-1][3] < 6:
                    out[-1][1] = join(out[-1][1], l['t']); out[-1][3] = l['y1']
                else:
                    out.append(['h', l['t'], p, l['y1']])
            elif is_body(l):
                buf.append(l)
    if buf:
        out += paras(buf)
    return [x[:3] for x in out]

apps = [{'t': 'Appendix 3: Draft Existing Conditions Feedback Synthesis', 'p': 170, 'b': headed(171, 175)},
        {'t': 'Appendix 4: Draft Recommendations and Survey', 'p': 176, 'b': headed(177, 181)},
        {'t': 'Appendix 5: Draft Recommendations Feedback and Synthesis', 'p': 182, 'b': headed(183, 199)}]

# each existing conditions map's row in Appendix 1 (Data Sources): exact or near-exact name, or a row named for the same map
import difflib
SRCX = {24: 'Share of Foreign Born Population', 26: 'Total Number of Jobs Added by Neighborhood', 32: 'Work Destination, Brooklyn Residents',
        58: 'Residentual Floor Area Ratio', 62: 'BIDs and IBZs', 63: 'FRESH Food', 70: 'Income Restricted Housing and Zoning',
        71: 'Residentual Units per Acre by Community District', 85: 'Proposed IBX Route', 86: 'Bus Network by Ridership',
        94: 'Households With No Vehicles Available', 108: 'Tree Canopy Change', 120: 'Daycare and Pre-k', 122: 'Median Number of 7 Major Felony Crimes'}
def _n(x): return re.sub(r'[^a-z0-9]', '', x.lower())
for sec in secs:
    for m in sec['maps']:
        row = None
        if m['p'] in SRCX:
            row = next(r for r in sources if r[0].startswith(SRCX[m['p']]))
        else:
            best = max(sources, key=lambda r: difflib.SequenceMatcher(None, _n(m['t']), _n(r[0])).ratio())
            if difflib.SequenceMatcher(None, _n(m['t']), _n(best[0])).ratio() >= 0.9:
                row = best
        if row:
            m['src'] = row

out = {
    'title': 'The Comprehensive Plan for Brooklyn', 'date': 'October 2023', 'pages': NP,
    'pdf': 'https://www.brooklynbp.nyc.gov/wp-content/uploads/2025/03/Comprehensive_Plan-1.pdf',
    'front': front,
    'ec': {'p': 14, 'b': paras(ec_intro), 'secs': secs},
    'powers': powers,
    'goals': goals,
    'fw_intro': {'p': 149, 'b': fw_intro},
    'fws': fws, 'next': nxt, 'sources': sources, 'gloss': gloss, 'apps': apps,
}
json.dump(out, open('plan2023.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('icons unassigned', unassigned)
print('goals', [(g['t'], len(g['obj']), sum(len(o['recs']) for o in g['obj'])) for g in goals])
print('fws', [(f['t'], f['p'], f['maps']) for f in fws])
print('sources', len(sources))
