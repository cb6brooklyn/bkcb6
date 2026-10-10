"""The last screens: the community organizations directory, Vision Zero, the page viewer, Votes, every hub screen and the
map's layer list read their sections (order, hidden, folds, inserts) or their entries (order, hidden) from screens.json.
editable3.py <app dir> <registry>"""
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
# FileOrder: entries in the file's order, dropping the ones it leaves out
t = os.path.join(V, 'Tools.swift'); s = rd(t)
if 'enum FileOrder' not in s:
    s += '''
/// Entries (hub sections, map layers, list sections) in the order screens.json "screens"[<screen>] lists their ids; ones it leaves out are not shown.
enum FileOrder {
    static func apply<T>(_ screen: String, _ items: [T], id: (T) -> String) -> [T] {
        guard let parts = UIConfig.shared.parts(screen) else { return items }
        return parts.compactMap { p in items.first { id($0) == DK.str(p["id"]) } }
    }
    static func ids(_ screen: String, _ defaults: [String]) -> [String] {
        guard let parts = UIConfig.shared.parts(screen) else { return defaults }
        return parts.map { DK.str($0["id"]) }.filter { defaults.contains($0) }
    }
}
'''
    wr(t, s); done.append('FileOrder')
# the community organizations directory
p = os.path.join(V, 'BidsOrgsView.swift'); s = rd(p)
old = '''                if model.loaded {
                    OrgLogoGroups()
                    SectionHeader(text: Copy.t("BidsOrgsView.234a6721", "In the city's community organization directory"))
                    directoryNote
                    directoryCards
                    sourceNote
                } else {'''
if old in s:
    ind = ' ' * 20
    body = fileparts('orgs-directory', ['logo-groups', 'heading', 'note', 'cards', 'source'],
                     [ind + 'OrgLogoGroups()', ind + 'SectionHeader(text: Copy.t("BidsOrgsView.234a6721", "In the city\'s community organization directory"))', ind + 'directoryNote', ind + 'directoryCards', ind + 'sourceNote'], ind, ', alignment: .leading, spacing: 16')
    s = s.replace(old, '                if model.loaded {\n' + ind + body + '\n                } else {', 1); wr(p, s); done.append('orgs-directory')
# Vision Zero
p = os.path.join(V, 'VisionZeroView.swift'); s = rd(p)
m = re.search(r'(private struct VZLoaded: View \{\n    let data: VZData\n\n    var body: some View \{\n        )VStack\(alignment: \.leading, spacing: (Sz\("[^"]+", 0\))\) \{\n            masthead\n            foldsTop\n            foldsBottom\n            tail\n        \}', s)
if m:
    ind = ' ' * 8
    body = fileparts('vision-zero', ['masthead', 'folds-top', 'folds-bottom', 'tail'], [ind + '    masthead', ind + '    foldsTop', ind + '    foldsBottom', ind + '    tail'], ind, f', alignment: .leading, spacing: {m.group(2)}')
    s = s[:m.start()] + m.group(1) + body + s[m.end():]; wr(p, s); done.append('vision-zero')
# the page viewer: header, pages, controls
p = os.path.join(V, 'FHGSView.swift'); s = rd(p)
i = s.find('struct FHPageViewer: View {')
if i >= 0 and 'FileParts("fh-page-viewer"' not in s:
    j = s.index('    var body: some View {\n', i) + len('    var body: some View {\n')
    m = re.match(r'        VStack\(spacing: (Sz\("[^"]+", 0\))\) \{\n', s[j:]); assert m, 'FH vstack'
    vb = j + m.end() - 2; close = match_brace(s, vb)
    parts = [x for x in statements(s[j + m.end():close])]
    assert len(parts) == 3, len(parts)
    body = fileparts('fh-page-viewer', ['header', 'pages', 'controls'], parts, ' ' * 8, f', alignment: .center, spacing: {m.group(1)}')
    s = s[:j] + '        ' + body + s[close + 1:]; wr(p, s); done.append('fh-page-viewer')
# Votes: its list sections in the file's order
p = os.path.join(V, 'VotesView.swift'); s = rd(p)
if 'FileOrder.ids("votes"' not in s:
    j = s.index('        List {\n'); lb = j + len('        List'); close = match_brace(s, s.index('{', lb))
    parts = statements(s[s.index('{', lb) + 2:close])
    secs = [x for x in parts if x.strip().startswith('Section')]
    assert len(secs) == len(parts) == 2, [x[:40] for x in parts]
    ids = ['filters', 'votes']
    cases = ''.join(f'                case "{k}":\n{x}\n' for k, x in zip(ids, secs))
    s = s[:s.index('{', lb) + 2] + f'            ForEach(FileOrder.ids("votes", {json.dumps(ids)}), id: \\.self) {{ part in\n                switch part {{\n{cases}                default: EmptyView()\n                }}\n            }}\n' + s[close:]
    reg['votes'] = [{'id': i} for i in ids]; wr(p, s); done.append('votes')
# every hub screen: its sections in the file's order ("hub.<title>")
p = os.path.join(V, 'Hub.swift'); s = rd(p)
if 'FileOrder.apply("hub.' not in s:
    old = '        self.title = title; self.subtitle = subtitle; self.sections = sections; self.color = color\n'
    assert old in s, 'hub init'
    s = s.replace(old, '        self.title = title; self.subtitle = subtitle; self.color = color\n        // the sections in screens.json "screens"["hub.<title>"] order, ones it leaves out hidden\n        self.sections = FileOrder.apply("hub." + title.lowercased().replacingOccurrences(of: " ", with: "-"), sections, id: { $0.id })\n', 1)
    wr(p, s); done.append('hubs')
# the map's layer list
p = os.path.join(V, 'CivicMap.swift'); s = rd(p)
if 'FileOrder.apply("map-layers"' not in s:
    i = s.index('struct LayerToggles: View {'); k = s.index('                ForEach(layers) { l in', i)
    s = s[:k] + '                ForEach(FileOrder.apply("map-layers", layers, id: { $0.id })) { l in' + s[k + len('                ForEach(layers) { l in'):]
    wr(p, s); done.append('map-layers')
json.dump(reg, open(OUT, 'w'), indent=1, sort_keys=True)
print('done:', done)
