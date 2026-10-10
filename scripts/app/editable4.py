"""The main sections of NYCHA, the election screen and the block card from screens.json; the inner parts the first pass
picked get their own names. editable4.py <app dir> <registry>"""
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

def fileparts(screen, ids, stmts, ind, fp=''):
    cases = ''.join(f'{ind}    case "{pid}": AnyView(Group {{\n{st}\n{ind}    }})\n' for pid, st in zip(ids, stmts))
    reg[screen] = [{'id': i} for i in ids]
    return f'FileParts("{screen}", {json.dumps(ids)}{fp}) {{ part in\n{ind}    switch part {{\n{cases}{ind}    default: AnyView(EmptyView())\n{ind}    }}\n{ind}}}'
done = []
def rename(f, old, new):
    p = os.path.join(V, f); s = rd(p)
    if f'FileParts("{old}"' in s:
        s = s.replace(f'FileParts("{old}"', f'FileParts("{new}"', 1); wr(p, s)
        if old in reg: reg[new] = reg.pop(old)
        done.append(f'{old}->{new}')
# the earlier pass picked inner stacks for these: give those their own names
rename('NYCHAView.swift', 'nycha', 'nycha-apply')
rename('November2026View.swift', 'november2026', 'november2026-source')
rename('UseOfLand.swift', 'use-of-land-hub', 'use-of-land-row')
rename('BlockCards.swift', 'block-card', 'block-place')
# the main sections of NYCHA and the election screen
def ifloaded(f, screen, names, ids):
    p = os.path.join(V, f); s = rd(p)
    lines = ''.join(f'                    {n}\n' for n in names)
    old = '                if model.loaded {\n' + lines + '                } else {'
    if old not in s: done.append(f'{screen}: not found'); return
    ind = ' ' * 20
    body = fileparts(screen, ids, [ind + n for n in names], ind)
    s = s.replace(old, '                if model.loaded {\n' + ind + body + '\n                } else {', 1); wr(p, s); done.append(screen)
ifloaded('NYCHAView.swift', 'nycha', ['mapSection', 'directorySection', 'applySection', 'sourceNote'], ['map', 'directory', 'apply', 'source'])
ifloaded('November2026View.swift', 'november2026', ['intro', 'whoWhatWhereWhy', 'countdownRow', 'pollSiteSection', 'ballotSection', 'questionsSection', 'registerSection', 'datesSection', 'sourceSection'],
         ['intro', 'who-what-where-why', 'countdown', 'poll-site', 'ballot', 'questions', 'register', 'dates', 'source'])
# the block card's sections
p = os.path.join(V, 'BlockCards.swift'); s = rd(p)
k = '    @ViewBuilder private func cardBody(_ c: BlockCard) -> some View {\n'
if k in s and 'FileParts("block-card"' not in s:
    b = s.index(k) + len(k) - 2; close = match_brace(s, b)
    stmts = statements(s[b + 2:close])
    used = set(); ids = [part_id(x, used) for x in stmts]
    body = fileparts('block-card', ids, stmts, ' ' * 8, ', alignment: .leading, spacing: 0')
    s = s[:b + 2] + '        ' + body + '\n    ' + s[close:]; wr(p, s); done.append(f'block-card: {len(ids)} parts')
json.dump(reg, open(OUT, 'w'), indent=1, sort_keys=True)
print('done:', done)
