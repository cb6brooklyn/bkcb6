"""The screens whose sections the file could not reorder or fold: each becomes FileParts("<screen>", [parts]) so screens.json
"screens" orders, hides and folds its parts like every other screen. Where the screen's scroll holds a single wrapper, the
wrapper's own children become the parts. fix_screens2.py <app dir> <registry>"""
import re, sys, os, glob, json, hashlib
R = sys.argv[1]; OUT = sys.argv[2]
V = os.path.join(R, 'BKCB6/App/Views')
def rd(p): return open(p).read()
def wr(p, s): open(p, 'w').write(s)
def h8(t): return hashlib.sha1(t.encode()).hexdigest()[:8]
def slug(name):
    """BQEView -> bqe, CPFinderView -> cp-finder, UOLMikeNote -> uol-mike-note, NextMeetingCard -> next-meeting-card."""
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', '-', name).lower()
SKIP = {'FileScreen.swift', 'HomeView.swift', 'BKHome.swift', 'SiteCard.swift'}
reg = json.load(open(OUT)) if os.path.exists(OUT) else {}

def match_brace(s, i):
    """i at '{': the index of its matching '}' (strings and comments skipped)."""
    d = 0; n = len(s); j = i
    while j < n:
        c = s[j]
        if c == '"':
            if s.startswith('"""', j):
                k = s.find('"""', j + 3); j = k + 3; continue
            j += 1
            while j < n and s[j] != '"':
                if s[j] == '\\': j += 1
                j += 1
            j += 1; continue
        if s.startswith('//', j): j = s.find('\n', j); continue
        if s.startswith('/*', j): j = s.find('*/', j) + 2; continue
        if c == '{': d += 1
        elif c == '}':
            d -= 1
            if d == 0: return j
        j += 1
    return -1

def statements(body):
    """Top-level statements of a ViewBuilder body, each with its leading comments."""
    lines = body.split('\n'); out = []; cur = []; depth = 0; instr = False
    def depth_after(line, depth):
        j = 0; n = len(line)
        while j < n:
            c = line[j]
            if c == '"':
                j += 1
                while j < n and line[j] != '"':
                    if line[j] == '\\': j += 1
                    j += 1
                j += 1; continue
            if line.startswith('//', j): break
            if c in '([{': depth += 1
            elif c in ')]}': depth -= 1
            j += 1
        return depth
    for ln in lines:
        st = ln.strip()
        if depth == 0 and cur and st and not st.startswith('.') and not st.startswith('else') and not st.startswith('}') and not st.startswith('catch') and not cur[-1].rstrip().endswith(','):
            # a new statement starts, unless what came before is only comments
            if any(l.strip() and not l.strip().startswith('//') for l in cur):
                out.append('\n'.join(cur)); cur = []
        cur.append(ln)
        depth = depth_after(ln, depth)
    if any(l.strip() for l in cur): out.append('\n'.join(cur))
    return out

def part_id(stmt, used):
    code = '\n'.join(l for l in stmt.split('\n') if not l.strip().startswith('//'))
    m = re.search(r'Copy\.[tf]\("[^"]+", "([^"]{2,60})"', code)
    base = None
    if m:
        base = re.sub(r'[^a-z0-9]+', '-', m.group(1).lower()).strip('-')
        base = '-'.join(base.split('-')[:4])
    if not base:
        m = re.match(r'\s*(?:if let \w+ = |if |ForEach|NavigationLink|HStack|VStack|ZStack|Group|Section)?\s*([A-Z][A-Za-z0-9]*)', code)
        if m and m.group(1) not in ('Spacer', 'Divider', 'Color', 'Text', 'HStack', 'VStack', 'ZStack', 'Group', 'ForEach', 'NavigationLink', 'Button', 'Image', 'Rectangle', 'RoundedRectangle', 'EmptyView', 'LazyVGrid', 'LazyVStack', 'Link'):
            base = slug(m.group(1)).replace('-view', '')
    if not base:
        m = re.match(r'\s*([A-Za-z]+)', code)
        base = (m.group(1).lower() if m else 'part')
        if base in ('if', 'foreach', 'navigationlink', 'hstack', 'vstack', 'zstack', 'group', 'button', 'text', 'image', 'link', 'section'): base = 'part'
    pid = base; k = 2
    while pid in used: pid = f'{base}-{k}'; k += 1
    used.add(pid); return pid

TARGETS = ["OrgsView", "BlockCardView", "CPSectionView", "OfficialProfileView", "FHPageViewer", "LotRecordListView", "NYCHAView",
           "November2026View", "ProjectPageView", "ReadingView", "SiteSearchView", "FAQView", "UseOfLandHubView", "VisionZeroView",
           "HousingReportSection", "ProductionReportSection", "HCRProjectsSection"]
STACK = re.compile(r'(?:Lazy)?VStack(\([^\n]*?\))?\s*\{\n')
def cs(x): return '\n'.join(l for l in x.split('\n') if not l.strip().startswith('//'))
def convert(s, view):
    m = re.search(r'struct ' + view + r'\b[^\n]*: View[^\n]*\{', s)
    if not m: return s, 'no struct'
    send = match_brace(s, s.index('{', m.start()))
    sv = s.find('ScrollView {', m.end(), send)
    if sv < 0: sv = s.find('ScrollView(', m.end(), send)
    if sv < 0: return s, 'no scroll'
    # the stack inside the scroll with the most sections: the one whose children are the screen's parts
    best = None; pos = sv
    while True:
        st = STACK.search(s, pos, send)
        if not st: break
        vb = st.end() - 2; close = match_brace(s, vb)
        if close < 0 or close > send: break
        body = s[st.end():close]
        if not body.strip().startswith('FileParts'):
            stmts = statements(body)
            prelude = [x for x in stmts if re.match(r'\s*(let |var |guard |@)', cs(x))]
            parts = [x for x in stmts if x not in prelude]
            score = len(parts) + 2 * sum(1 for x in parts if 'SectionHeader' in x or 'HomeFold' in x)
            if len(parts) >= 2 and (best is None or score > best[0]): best = (score, st, close, prelude, parts)
        pos = st.end()
    if not best: return s, 'single part'
    _, st, close, prelude, parts = best
    screen = slug(re.sub(r'View$', '', view))
    used = set(); ids = [part_id(x, used) for x in parts]
    vargs = (st.group(1) or '')[1:-1]; fp = ''
    am = re.search(r'alignment: (\.\w+)', vargs); sp = re.search(r'spacing: ([^,)]+)', vargs)
    if am: fp += f', alignment: {am.group(1)}'
    if sp: fp += f', spacing: {sp.group(1)}'
    ind = re.match(r'[ \t]*', s[s.rfind('\n', 0, st.start()) + 1:]).group(0) + '    '
    cases = ''.join(f'{ind}    case "{pid}": AnyView(Group {{\n{stmt}\n{ind}    }})\n' for pid, stmt in zip(ids, parts))
    nb = (('\n'.join(prelude) + '\n') if prelude else '') + f'{ind}FileParts("{screen}", {json.dumps(ids)}{fp}) {{ part in\n{ind}    switch part {{\n{cases}{ind}    default: AnyView(EmptyView())\n{ind}    }}\n{ind}}}'
    s = s[:st.start()] + nb.lstrip() + s[close + 1:]
    reg[screen] = [{'id': i} for i in ids]
    return s, f'{screen}: {len(ids)} parts'
for f in sorted(glob.glob(os.path.join(V, '*.swift'))):
    s = rd(f); o = s
    for view in TARGETS:
        if re.search(r'struct ' + view + r'\b', s):
            s, msg = convert(s, view); print(os.path.basename(f), view, '->', msg)
    if s != o: wr(f, s)
json.dump(reg, open(OUT, 'w'), indent=1, sort_keys=True)
