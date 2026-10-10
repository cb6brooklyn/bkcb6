"""Open or closed, the tab bar, and colors, from the files. editable1.py <app dir> <colors registry out>
- Every fold, "show all" and disclosure the code fixed reads screens.json "open" ("<File>.<name>": true|false), keeping today's state when the file says nothing.
- The tab bar: screens.json "tabs" (order, titles, icons, and up to three extra tabs x1..x3 with a "dest").
- Every color written in the code reads mapstyle.json "colors" by key ("<File>.c.<id>"), keeping today's color when the file says nothing."""
import re, os, sys, glob, json, hashlib
R = sys.argv[1]; REG = sys.argv[2]
V = os.path.join(R, 'BKCB6/App/Views')
def rd(p): return open(p).read()
def wr(p, s): open(p, 'w').write(s)
# 1. open or closed
STATES = {'CB6MapView.swift': ['showMore'], 'Complaints311View.swift': ['showAllTypes'], 'LandmarksSection.swift': ['openWhat', 'openCofA'],
          'MyBlock.swift': ['showAll', 'showDetails'], 'VisionZeroView.swift': ['expanded'], 'WeatherView.swift': ['showAllSites']}
n_open = 0
for f, names in STATES.items():
    p = os.path.join(V, f); s = rd(p); stem = f[:-6]
    for nm in names:
        pat = f'@State private var {nm} = false'
        c = s.count(pat); assert c >= 1, (f, nm)
        s = s.replace(pat, f'@State private var {nm} = UIConfig.shared.isOpen("{stem}", "{nm}", false)'); n_open += c
    wr(p, s)
p = os.path.join(V, 'UseOfLand.swift'); s = rd(p)
if '.onAppear { isOpen = open }' in s:
    s = s.replace('.onAppear { isOpen = open }', '.onAppear { isOpen = UIConfig.shared.isOpen("UseOfLand", title, open) }'); n_open += 1; wr(p, s)
# the disclosure groups with no state of their own
p = os.path.join(V, 'CompPlanView.swift'); s = rd(p)
if 'aboutElementOpen' not in s:
    old = '                        DisclosureGroup {\n                            CPParas(paras: E.b).padding(.top, 6)'
    assert old in s, 'CompPlan about'
    s = s.replace(old, '                        DisclosureGroup(isExpanded: $aboutElementOpen) {\n                            CPParas(paras: E.b).padding(.top, 6)', 1)
    # its state, next to the screen's open set
    m = re.search(r'\n(\s*)@State private var open: Set<String> = \[\]\n', s); assert m, 'CompPlan open set'
    s = s[:m.end()] + m.group(1) + '@State private var aboutElementOpen = UIConfig.shared.isOpen("CompPlanView", "about-this-element", false)\n' + s[m.end():]
    # objectives and strategies: the file's default, tapping flips it
    old = '        Binding(get: { open.contains(k) }, set: { if $0 { open.insert(k) } else { open.remove(k) } })'
    assert old in s, 'CompPlan binding'
    s = s.replace(old, '        let base = UIConfig.shared.isOpen("CompPlanView", k.contains("s") ? "strategies" : "objectives", false)\n        return Binding(get: { open.contains(k) != base }, set: { if $0 != base { open.insert(k) } else { open.remove(k) } })', 1)
    n_open += 3; wr(p, s)
p = os.path.join(V, 'LandUseView.swift'); s = rd(p)
if 'shapeFlipped' not in s:
    old = '                ForEach(shapes) { shape in\n                    DisclosureGroup {'
    assert old in s, 'LandUse shapes'
    s = s.replace(old, '                ForEach(shapes) { shape in\n                    DisclosureGroup(isExpanded: Binding(get: { shapeFlipped.contains("\\(shape.id)") != UIConfig.shared.isOpen("LandUseView", "shapes", false) },\n                                                         set: { _ in if shapeFlipped.contains("\\(shape.id)") { shapeFlipped.remove("\\(shape.id)") } else { shapeFlipped.insert("\\(shape.id)") } })) {', 1)
    m = re.search(r'struct LandUse\w*: View \{\n', s[:s.index('shapeFlipped')])
    i = s.rfind('struct ', 0, s.index('shapeFlipped')); j = s.index('{\n', i) + 2
    s = s[:j] + '    @State private var shapeFlipped: Set<String> = []\n' + s[j:]
    n_open += 1; wr(p, s)
# the Orgs tab rows (fold_orgs.py) already read "orgs.<heading>"
print('open/closed:', n_open, 'places now read the file')

# 2. the tab bar
ap = glob.glob(os.path.join(R, 'BKCB6/App/*App.swift')); assert len(ap) == 1, ap
ap = ap[0]; a = rd(ap)
if ', x1, x2, x3' not in a:
    m = re.search(r'    enum Tab: String, CaseIterable \{ case ([a-z0-9, ]+)\n', a); assert m, 'Tab enum'
    a = a[:m.start()] + f'    enum Tab: String, CaseIterable {{ case {m.group(1)}, x1, x2, x3\n' + a[m.end():]
    a = re.sub(r'(        var title: String \{\n)(            switch self \{)', r'\1            if let t = UIConfig.shared.tab(rawValue)?["title"] as? String, !t.isEmpty { return t }\n\2', a, count=1)
    a = re.sub(r'(        var symbol: String \{\n)(            switch self \{)', r'\1            if let i = UIConfig.shared.tab(rawValue)?["icon"] as? String, !i.isEmpty { return i }\n\2', a, count=1)
    m = re.search(r'        static let bar: \[Tab\] = (\[[^\]]+\])\n', a); assert m, 'Tab.bar'
    a = a[:m.start()] + f'        static let codeBar: [Tab] = {m.group(1)}\n        /// The file\'s tabs (screens.json "tabs"), else the code\'s.\n        static var bar: [Tab] {{ let f = (UIConfig.shared.tabs() ?? []).compactMap {{ Tab(rawValue: DK.str($0["id"])) }}; return f.isEmpty ? codeBar : f }}\n' + a[m.end():]
    m = re.search(r'(    @ViewBuilder private func screen\(_ t: Tab\) -> some View \{\n        switch t \{\n)', a); assert m, 'screen(t)'
    a = a[:m.end()] + '        case .x1, .x2, .x3: NavigationStack { ScreenRouter.view(DK.str(UIConfig.shared.tab(t.rawValue)?["dest"])) }\n' + a[m.end():]
    for prop in ['title', 'symbol']:
        mm = re.search(r'        var ' + prop + r': String \{\n(.*?)\n        \}\n', a, re.S); body = mm.group(1)
        if 'default:' not in body:
            b2 = body.rstrip(); assert b2.endswith('}'), prop
            b2 = b2[:-1].rstrip() + ('; default: return rawValue }' if prop == 'title' else '; default: return "square.grid.2x2.fill" }')
            a = a[:mm.start(1)] + b2 + a[mm.end(1):]
    wr(ap, a)
if '@ObservedObject private var uiFiles' not in a:
    if True:
        a = re.sub(r'(    @State private var tab: Tab = \w+\.launchTab\(\)\n)', r'    @ObservedObject private var uiFiles = UIConfig.shared   // redraws the bar when the files change\n\1', a, count=1)
        assert 'uiFiles' in a, 'ContentView tab state'
    wr(ap, a)
print('tab bar from the file')

# 3. colors
reg = json.load(open(REG)) if os.path.exists(REG) else {}
def h8(t): return hashlib.sha1(t.encode()).hexdigest()[:8]
nc = 0
for p in sorted(glob.glob(os.path.join(R, 'BKCB6/App/**/*.swift'), recursive=True)):
    s = rd(p); o = s; stem = os.path.basename(p)[:-6]
    out = []
    for i, line in enumerate(s.split('\n'), 1):
        if line.strip().startswith('//') or 'MapStyle.color(' in line or 'static func' in line:
            out.append(line); continue
        def wrap(m):
            global nc
            lit = m.group(0); k = f'{stem}.c.{h8(lit + str(i))}'; reg[k] = lit; nc += 1
            return f'MapStyle.color("{k}", {lit})'
        line = re.sub(r'Color\(red: [^()]*\)', wrap, line)
        line = re.sub(r'\bColor\.(red|black|blue|green|gray|yellow|purple|pink)\b', lambda m: wrap(m), line)
        out.append(line)
    s = '\n'.join(out)
    if s != o: wr(p, s)
json.dump(reg, open(REG, 'w'), indent=1, sort_keys=True)
print('colors:', nc, 'now read the file')
