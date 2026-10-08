"""Every screen from the file (civic/ui/<app>/screens.json):
  "screens": {"<screen>": [ {"id": "<part>", "fold", "open", "pinned", "title", "icon"} | {"kind": "text"|"web"|"button"|"tools"|"header", ...} ]}
     lists a screen's parts in order; a part left out is not drawn; text, site pages, buttons, tool grids and headers go anywhere.
  "replace": {"<screen key>": "web:<site path>" | "<other key>"}   shows that instead of the screen.
  "tabs": [{"id": "home", "title", "icon"}, ..., {"id": "x1", "title", "icon", "dest": "<screen key>"}]   the tab bar, with up to three extra tabs.
Adds FileScreen.swift (FileParts, FileButton, ScreenRouter, UIConfig lookups), routes every screen key through ScreenRouter,
gives ToolGrid a link mode, reads the tab bar from the file, and rewrites every ScrollView { VStack { ... } } screen as
FileParts with one named part per statement. Writes screens-<app>.json, the registry of each screen's parts.
fix_screens.py <app dir> <registry>"""
import re, sys, os, glob, json, hashlib
R = sys.argv[1]; OUT = sys.argv[2]
V = os.path.join(R, 'App/Views')
def rd(p): return open(p).read()
def wr(p, s): open(p, 'w').write(s)
bk = os.path.exists(os.path.join(V, 'BKHome.swift'))

# ---------------------------------------------------------------- 1. the routes: one function every screen key goes through
hv = os.path.join(V, 'HomeView.swift'); s = rd(hv)
if 'enum HomeRoutes' not in s:
    # BKCB6: the switch sits inside .navigationDestination; it becomes HomeRoutes.view(key) like the other apps
    m = re.search(r'            \.navigationDestination\(for: String\.self\) \{ key in\n                switch key \{\n(.*?)\n                \}\n            \}\n', s, re.S)
    assert m, 'HomeView route switch'
    body = m.group(1)
    s = s[:m.start()] + '            .navigationDestination(for: String.self) { key in ScreenRouter.view(key) }\n' + s[m.end():]
    s = s.rstrip('\n') + '\n\n/// Every screen a key opens ("permits", "web:<path>", "official:<slug>"...).\nenum HomeRoutes {\n    @ViewBuilder static func view(_ key: String) -> some View {\n        switch key {\n' + '\n'.join(l[8:] if l.startswith('        ') else l for l in body.split('\n')) + '\n        }\n    }\n}\n'
    wr(hv, s)
    tabarg = ''
else:
    tabarg = ', tab: .constant(.home)'
    for f in glob.glob(os.path.join(V, '*.swift')):
        t = rd(f); u = t.replace('.navigationDestination(for: String.self) { key in HomeRoutes.view(key, tab: $tab) }', '.navigationDestination(for: String.self) { key in ScreenRouter.view(key) }')
        if u != t: wr(f, u)
print('routes ok')

# ---------------------------------------------------------------- 2. FileScreen.swift
# appended to Tools.swift, which every project already lists (a new file would need the Xcode project regenerated)
fs = os.path.join(V, 'Tools.swift')
if 'struct FileParts' not in rd(fs):
    wr(fs, rd(fs).rstrip('\n') + '''


// MARK: - Screens from the file
//
// civic/ui/<app>/screens.json:
//   "screens": {"<screen>": [parts...]}  a screen's parts in order. A part the code draws: {"id": "<part>", "fold": true, "open": false,
//       "pinned": false, "title": "...", "icon": "..."}; inserted anywhere: {"kind": "text", "title", "text" | "key"}, {"kind": "web",
//       "page", "height"}, {"kind": "button", "title", "dest", "color"}, {"kind": "tools", "list", "title"}, {"kind": "header", "title"}.
//       A part left out is not drawn. The registry scripts/app/screens-<app>.json lists every screen's parts as the code draws them.
//   "replace": {"<screen key>": "web:<site path>" | "<other key>"}  that is shown instead of the screen.
//   "tabs": [{"id": "home", "title", "icon"}, ..., {"id": "x1", "title", "icon", "dest": "<screen key>"}]  the tab bar; x1, x2, x3 are extra tabs.

extension UIConfig {
    func parts(_ screen: String) -> [[String: Any]]? { (file("screens")["screens"] as? [String: Any])?[screen] as? [[String: Any]] }
    func replacement(_ key: String) -> String? { (file("screens")["replace"] as? [String: Any])?[key] as? String }
    func tabs() -> [[String: Any]]? { file("screens")["tabs"] as? [[String: Any]] }
    func tab(_ id: String) -> [String: Any]? { tabs()?.first { DK.str($0["id"]) == id } }
}

enum ScreenRouter {
    /// The screen a key opens, after the file's "replace" table.
    static func view(_ key: String) -> AnyView {
        if let r = UIConfig.shared.replacement(key), r != key {
            if r.hasPrefix("web:") { return AnyView(SitePageView(path: String(r.dropFirst(4)))) }
            return AnyView(HomeRoutes.view(r''' + tabarg + '''))
        }
        return AnyView(HomeRoutes.view(key''' + tabarg + '''))
    }
    /// Where a tool button goes when it is a link.
    static func tool(_ t: ToolButton) -> AnyView {
        switch t.destination {
        case .screen(let k): return view(k)
        case .district: return view("district")
        case .tab(let tab): return view(tab.rawValue)
        }
    }
}

/// A screen's parts in the file's order, each drawn by the screen's own code, with the file's folds, text, pages, buttons and tools between them.
struct FileParts: View {
    let screen: String
    let defaults: [String]
    var alignment: HorizontalAlignment = .leading
    var spacing: CGFloat? = nil
    let content: (String) -> AnyView
    init(_ screen: String, _ defaults: [String], alignment: HorizontalAlignment = .leading, spacing: CGFloat? = nil, content: @escaping (String) -> AnyView) {
        self.screen = screen; self.defaults = defaults; self.alignment = alignment; self.spacing = spacing; self.content = content
    }
    private var parts: [[String: Any]] { UIConfig.shared.parts(screen) ?? defaults.map { ["id": $0] } }
    var body: some View {
        VStack(alignment: alignment, spacing: spacing) {
            ForEach(Array(parts.enumerated()), id: \\.offset) { _, p in
                let kind = DK.str(p["kind"]), id = DK.str(p["id"]), title = DK.str(p["title"]), icon = DK.str(p["icon"])
                let fold = p["fold"] as? Bool ?? false, open = p["open"] as? Bool ?? false, pinned = p["pinned"] as? Bool ?? false
                if fold {
                    HomeFold(title: title.isEmpty ? id : title, id: screen + "." + id, open: open, pinned: pinned, icon: icon) { FilePart(p: p, title: title, content: content) }
                } else {
                    FilePart(p: p, title: title, content: content)
                }
            }
        }
    }
}

struct FilePart: View {
    let p: [String: Any]
    let title: String
    let content: (String) -> AnyView
    var body: some View {
        switch DK.str(p["kind"]) {
        case "text":
            let body = DK.str(p["key"]).isEmpty ? DK.str(p["text"]) : T(DK.str(p["key"]), "")
            VStack(alignment: .leading, spacing: 10) {
                if !title.isEmpty { Text(title).font(DM.sans(16, .bold)).foregroundStyle(Color.cb6Navy) }
                ForEach(Array(body.components(separatedBy: "\\n\\n").enumerated()), id: \\.offset) { _, para in
                    Text(para).font(DM.sans(15)).foregroundStyle(Color.cb6Ink).fixedSize(horizontal: false, vertical: true)
                }
            }
        case "web":
            SitePageWeb(path: DK.str(p["page"])).frame(height: DK.num(p["height"]) ?? 320)
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).stroke(Color.cb6Rule, lineWidth: 1))
        case "button":
            FileButton(title: title, dest: DK.str(p["dest"]), color: DK.str(p["color"]))
        case "tools":
            ToolGrid(title: title, tools: Tools.list(DK.str(p["list"])), tap: { _ in }, link: ScreenRouter.tool)
        case "header":
            SectionHeader(text: title)
        default:
            content(DK.str(p["id"]))
        }
    }
}

/// A button from the file: "feeds" (311, crime and permits at the saved address), "card" (the saved address's card), "web:<site path>",
/// "dk:<route>", "screen:<key>" or any screen key, or an https link.
struct FileButton: View {
    let title: String
    let dest: String
    var color: String = ""
    var body: some View {
        let label = Text(title).font(DM.sans(13, .bold)).foregroundStyle(.white).lineLimit(1).minimumScaleFactor(0.8)
            .padding(.horizontal, 12).padding(.vertical, 9).frame(maxWidth: .infinity).background(color.isEmpty ? Color.cb6Navy : DK.hex(color), in: Capsule())
        if dest == "feeds", let c = MyPlace.current?.coord { NavigationLink { FeedsView(startPin: c) } label: { label }.buttonStyle(.plain) }
        else if dest == "card", let p = MyPlace.current { NavigationLink { SiteCardView(address: p.label) } label: { label }.buttonStyle(.plain) }
        else if dest.hasPrefix("web:") { NavigationLink { SitePageView(path: String(dest.dropFirst(4))) } label: { label }.buttonStyle(.plain) }
        else if dest.hasPrefix("dk:") { NavigationLink { DKRoute(spec: String(dest.dropFirst(3))).view } label: { label }.buttonStyle(.plain) }
        else if dest.hasPrefix("http"), let u = URL(string: dest) { Link(destination: u) { label } }
        else if !dest.isEmpty { NavigationLink { ScreenRouter.view(dest.hasPrefix("screen:") ? String(dest.dropFirst(7)) : dest) } label: { label }.buttonStyle(.plain) }
        else { label }
    }
}
''')
print('FileScreen ok')

# ---------------------------------------------------------------- 3. ToolGrid: a link mode for grids inside other screens
tp = os.path.join(V, 'Tools.swift'); t = rd(tp)
if 'var link: ((ToolButton) -> AnyView)? = nil' not in t:
    t = t.replace('    let tap: (ToolButton) -> Void\n\n    private let columns', '    let tap: (ToolButton) -> Void\n    /// When set, each tile is a link to this view instead of a tap.\n    var link: ((ToolButton) -> AnyView)? = nil\n\n    private let columns', 1)
    a = t.index('                    Button { tap(tool) } label: {\n')
    b = t.index('                    .buttonStyle(.plain)\n', a)
    label = t[a + len('                    Button { tap(tool) } label: {\n'):b]
    assert label.rstrip().endswith('}'), 'ToolGrid label'
    label = label.rstrip()[:-1].rstrip('\n')  # drop the closing brace of the label closure
    t = t[:a] + '                    Group {\n                        if let link { NavigationLink { link(tool) } label: { tile(tool) } } else { Button { tap(tool) } label: { tile(tool) } }\n                    }\n' + t[b:]
    # the tile, as a function
    t = t.replace('    private let columns = [GridItem(.flexible(), spacing: 8), GridItem(.flexible(), spacing: 8)]\n',
                  '    private let columns = [GridItem(.flexible(), spacing: 8), GridItem(.flexible(), spacing: 8)]\n\n    @ViewBuilder private func tile(_ tool: ToolButton) -> some View {\n' + label + '\n    }\n', 1)
    assert 'func tile(_ tool: ToolButton)' in t
    wr(tp, t)
print('ToolGrid ok')

# ---------------------------------------------------------------- 4. the tab bar from the file
app = [f for f in glob.glob(os.path.join(R, 'App', '*App.swift'))]
assert len(app) == 1, app
ap = app[0]; a = rd(ap)
if 'case x1, x2, x3' not in a:
    m = re.search(r'    enum Tab: String, CaseIterable \{ case ([a-z0-9, ]+)\n', a)
    assert m, 'Tab enum'
    a = a[:m.start()] + f'    enum Tab: String, CaseIterable {{ case {m.group(1)}, x1, x2, x3\n' + a[m.end():]
    # title and symbol: the file's first
    a = re.sub(r'(        var title: String \{\n)(            switch self \{)', r'\1            if let t = UIConfig.shared.tab(rawValue)?["title"] as? String, !t.isEmpty { return t }\n\2', a, count=1)
    a = re.sub(r'(        var symbol: String \{\n)(            switch self \{)', r'\1            if let i = UIConfig.shared.tab(rawValue)?["icon"] as? String, !i.isEmpty { return i }\n\2', a, count=1)
    # the extra tabs' title and symbol defaults
    a = a.replace('case .board: return "Board"; default: return rawValue }', 'case .board: return "Board"; default: return rawValue }', 1)
    # the bar: the file's list when it has one
    m = re.search(r'        static let bar: \[Tab\] = (\[[^\]]+\])\n', a)
    assert m, 'Tab.bar'
    a = a[:m.start()] + f'        static let codeBar: [Tab] = {m.group(1)}\n        /// The file\'s tabs (screens.json "tabs"), else the code\'s.\n        static var bar: [Tab] {{ let f = (UIConfig.shared.tabs() ?? []).compactMap {{ Tab(rawValue: DK.str($0["id"])) }}; return f.isEmpty ? codeBar : f }}\n' + a[m.end():]
    # the extra tabs' screens
    m = re.search(r'(    @ViewBuilder private func screen\(_ t: Tab\) -> some View \{\n        switch t \{\n)', a)
    assert m, 'screen(t)'
    a = a[:m.end()] + '        case .x1, .x2, .x3: NavigationStack { ScreenRouter.view(DK.str(UIConfig.shared.tab(t.rawValue)?["dest"])) }\n' + a[m.end():]
    # titles and symbols for the extra tabs when switch statements are exhaustive without default
    for prop in ['title', 'symbol']:
        mm = re.search(r'        var ' + prop + r': String \{\n(.*?)\n        \}\n', a, re.S)
        body = mm.group(1)
        if 'default:' not in body:
            body2 = body.rstrip()
            assert body2.endswith('}'), prop
            body2 = body2[:-1].rstrip() + ('; default: return rawValue }' if prop == 'title' else '; default: return MapStyle.symbol("Tabs.s.extra", "square.grid.2x2.fill") }')
            a = a[:mm.start(1)] + body2 + a[mm.end(1):]
    wr(ap, a)
print('tabs ok')

# ---------------------------------------------------------------- 5. every ScrollView { VStack { ... } } screen as parts
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

HEAD = re.compile(r'(?P<indent>[ \t]*)ScrollView(?P<sargs>\([^\n]*?\))?\s*\{\s*\n[ \t]*(?:Lazy)?VStack(?P<vargs>\([^\n]*?\))?\s*\{\n')
converted = 0
for f in sorted(glob.glob(os.path.join(V, '*.swift'))):
    if os.path.basename(f) in SKIP: continue
    s = rd(f); o = s; pos = 0; did = []
    while True:
        m = HEAD.search(s, pos)
        if not m: break
        vb = m.end() - 2  # index of the VStack '{' (the match ends with the newline after it)
        close = match_brace(s, vb)
        if close < 0: pos = m.end(); continue
        body = s[m.end():close]
        # the view this belongs to
        before = s[:m.start()]
        sm = list(re.finditer(r'struct (\w+)\s*:\s*View', before))
        if not sm: pos = m.end(); continue
        view = sm[-1].group(1)
        screen = slug(re.sub(r'View$', '', view))
        if screen in reg or 'FileParts(' in body: pos = m.end(); continue
        stmts = statements(body)
        def code_start(x): return '\n'.join(l for l in x.split('\n') if not l.strip().startswith('//'))
        prelude = [x for x in stmts if re.match(r'\s*(let |var |guard |@)', code_start(x))]
        parts = [x for x in stmts if x not in prelude]
        if len(parts) < 2: pos = m.end(); continue
        used = set(); ids = [part_id(x, used) for x in parts]
        vargs = (m.group('vargs') or '')[1:-1]
        fp_args = ''
        if vargs:
            am = re.search(r'alignment: (\.\w+)', vargs); sp = re.search(r'spacing: ([^,)]+)', vargs)
            if am: fp_args += f', alignment: {am.group(1)}'
            if sp: fp_args += f', spacing: {sp.group(1)}'
        ind = m.group('indent') + '    '
        cases = ''.join(f'{ind}    case "{pid}": AnyView(Group {{\n{stmt}\n{ind}    }})\n' for pid, stmt in zip(ids, parts))
        new_body = (('\n'.join(prelude) + '\n') if prelude else '') + f'{ind}FileParts("{screen}", {json.dumps(ids)}{fp_args}) {{ part in\n{ind}    switch part {{\n{cases}{ind}    default: AnyView(EmptyView())\n{ind}    }}\n{ind}}}'
        # keep the VStack's own modifiers: they follow the closing brace on the same or next lines, and apply to FileParts the same way
        s = s[:m.end() - len(s[m.end() - 1:m.end()]) - 0] + '' if False else s
        # replace "VStack(args) {" + body + "}" with the FileParts call (its own braces)
        vs = s.rfind('VStack', m.start(), vb)
        if s[vs - 4:vs] == 'Lazy': vs -= 4
        s = s[:vs] + new_body.lstrip() + s[close + 1:]
        reg[screen] = [{'id': i} for i in ids]
        did.append(screen); converted += 1
        pos = vs + len(new_body)
    if s != o:
        wr(f, s)
json.dump(reg, open(OUT, 'w'), indent=1, sort_keys=True)
print('screens converted', converted, '->', OUT)
