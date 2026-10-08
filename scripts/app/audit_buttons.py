"""Every button the code draws can be re-aimed or hidden from the file: each Button, NavigationLink or Link statement whose
label carries a copy key is wrapped in FileAction("<File>.<id>") { ... }; screens.json "buttons": {"<File>.<id>": "<dest>"}
sends it to that screen key, "web:<site path>", "dk:<route>" or an https link instead, and "hide" drops it. Buttons inside
alerts, menus, toolbars, swipe actions and dialogs are left alone (those must stay plain buttons). Writes buttons-<app>.json,
the registry of keys with the label text. audit_buttons.py <app dir> <registry>"""
import re, sys, os, glob, json
R = sys.argv[1]; OUT = sys.argv[2]
V = os.path.join(R, 'App/Views')
reg = json.load(open(OUT)) if os.path.exists(OUT) else {}
START = re.compile(r'^([ \t]*)(Button(?: ?\{|\(|\s*\{)|NavigationLink(?: ?\{|\()|Link\(destination:)', re.M)
CONTEXT = ('.alert(', '.confirmationDialog(', 'Menu {', 'Menu(', '.contextMenu', '.toolbar', 'ToolbarItem', '.swipeActions', '.sheet(', 'label: {', 'ShareLink', 'Picker')
KEY = re.compile(r'Copy\.[tf]\("([A-Za-z0-9]+\.[0-9a-f]{8})", "([^"]*)"')

def end_of_statement(s, i):
    """From the start of a statement: the index just past it, including trailing modifier lines."""
    n = len(s); j = i; depth = 0
    while j < n:
        c = s[j]
        if c == '"':
            if s.startswith('"""', j): j = s.find('"""', j + 3) + 3; continue
            j += 1
            while j < n and s[j] != '"':
                if s[j] == '\\': j += 1
                j += 1
            j += 1; continue
        if s.startswith('//', j): j = s.find('\n', j); continue
        if c in '([{': depth += 1
        elif c in ')]}': depth -= 1
        elif c == '\n' and depth == 0:
            # the statement continues when the next non-blank line starts with a modifier or an else
            k = j + 1
            while k < n and s[k] in ' \t': k += 1
            if s.startswith('.', k) or s.startswith('else', k): j = k; continue
            return j
        j += 1
    return n

def enclosed(s, i):
    """The lines that open the two innermost braces around i, checked for contexts that need a plain Button."""
    depth = 0; j = i - 1; found = 0
    while j >= 0 and found < 2:
        c = s[j]
        if c == '"':
            j -= 1
            while j >= 0 and not (s[j] == '"' and s[j - 1] != '\\'): j -= 1
            j -= 1; continue
        if c in ')]}': depth += 1
        elif c in '([{':
            if depth == 0:
                if c == '{':
                    ls = s.rfind('\n', 0, j) + 1
                    line = s[ls:j]
                    if any(t in line for t in CONTEXT): return True
                    found += 1
            else: depth -= 1
        j -= 1
    return False

n = 0
for f in sorted(glob.glob(os.path.join(V, '*.swift'))):
    s = open(f).read(); o = s; pos = 0; out = []
    last = 0
    for m in START.finditer(s):
        if m.start() < last: continue
        if 'FileAction(' in s[max(0, m.start() - 60):m.start()]: continue
        # inside a label closure, a menu, an alert, a toolbar...: those need a plain Button; look at the two enclosing braces
        if enclosed(s, m.start()): continue
        e = end_of_statement(s, m.start())
        stmt = s[m.start():e]
        km = KEY.search(stmt)
        if not km: continue
        key = km.group(1)
        if key in reg and reg[key] != km.group(2): key = key + '-' + str(sum(1 for k in reg if k.startswith(km.group(1))))
        reg[key] = km.group(2); n += 1
        ind = m.group(1)
        wrapped = f'{ind}FileAction("{key}") {{\n{stmt}\n{ind}}}'
        out.append(s[last:m.start()]); out.append(wrapped); last = e
    out.append(s[last:])
    s = ''.join(out)
    if s != o: open(f, 'w').write(s)
# the view
tp = os.path.join(V, 'Tools.swift'); t = open(tp).read()
if 'struct FileAction' not in t:
    t = t.rstrip('\n') + '''

/// A button of the code, re-aimed by the file: screens.json "buttons": {"<File>.<id>": "<screen key> | web:<site path> | dk:<route> | https://... | hide"}
/// sends that button there instead (or hides it); the button keeps its look.
struct FileAction<Content: View>: View {
    let key: String
    @ViewBuilder let content: () -> Content
    init(_ key: String, @ViewBuilder content: @escaping () -> Content) { self.key = key; self.content = content }
    var body: some View {
        let d = ((UIConfig.shared.file("screens")["buttons"] as? [String: Any])?[key] as? String) ?? ""
        if d.isEmpty { content() }
        else if d == "hide" { EmptyView() }
        else if d.hasPrefix("http"), let u = URL(string: d) { Link(destination: u) { content().allowsHitTesting(false) } }
        else if d.hasPrefix("dk:") { NavigationLink { DKRoute(spec: String(d.dropFirst(3))).view } label: { content().allowsHitTesting(false) }.buttonStyle(.plain) }
        else { NavigationLink { ScreenRouter.view(d.hasPrefix("screen:") ? String(d.dropFirst(7)) : d) } label: { content().allowsHitTesting(false) }.buttonStyle(.plain) }
    }
}
'''
    open(tp, 'w').write(t)
json.dump(reg, open(OUT, 'w'), indent=1, sort_keys=True)
print('buttons', n, 'wrapped,', len(reg), 'keys')
