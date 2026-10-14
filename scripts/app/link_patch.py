"""Every Link in the app's views that a file could not redirect: wrap it in FileAction("Link.<File>.<n>") so screens.json "buttons"
can send it to any screen or site page instead (or hide it). The block card's street projects take their dest from lists.json:
a "screen:..."/"web:..." entry opens in the app, an https one as before.
Usage: python3 link_patch.py <project dir>  (idempotent). Prints the keys it added, for screens.json buttonsIndex."""
import sys, re, glob, os, json
root = sys.argv[1].rstrip('/') + '/BKCB6/App/Views/'
SKIP = {'Tools.swift'}  # FileAction / FileLink / FileButton themselves
keys = {}

# 1. Block card street projects: dest from the file, in-app when it is a screen or a site page.
bc = root + 'BlockCards.swift'
t = open(bc).read()
old = 'if let u = URL(string: p.url) {\n                    Link(destination: u) {'
if old in t:
    i = t.index(old)
    # closing of Link's closure, then .padding line, then closing of if
    t = t.replace(old, 'if !p.url.isEmpty {\n                    FileLink(p.url.hasPrefix("web:") ? "screen:" + p.url : p.url) {', 1)
    open(bc, 'w').write(t)
    print('BlockCards street projects: file dest')

def close_of(s, j):
    """index just past the closure that opens at the first '{' at or after j, skipping strings."""
    k = s.index('{', j); depth = 0; q = False; esc = False
    while k < len(s):
        c = s[k]
        if q:
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == '"': q = False
        else:
            if c == '"': q = True
            elif c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0: return k + 1
        k += 1
    raise ValueError('unbalanced')

for f in sorted(glob.glob(root + '*.swift')):
    name = os.path.basename(f)
    if name in SKIP: continue
    s = open(f).read(); out = []; pos = 0; n = 0
    for m in re.finditer(r'Link\(destination:', s):
        a = m.start()
        if a < pos: continue
        line_start = s.rfind('\n', 0, a) + 1
        before = s[max(0, line_start - 400):a]
        if 'FileAction(' in s[line_start:a] or re.search(r'FileAction\("[^"]+"\)\s*\{\s*$', before): continue
        if 'tel:' in s[a:a+120] or 'phone' in s[a:a+200].lower() and 'phone.fill' in s[a:a+300]: continue
        # the Link's argument list ends at the matching ')'
        depth = 0; k = s.index('(', a)
        while True:
            if s[k] == '(': depth += 1
            elif s[k] == ')':
                depth -= 1
                if depth == 0: break
            k += 1
        e = close_of(s, k)
        n += 1
        key = 'Link.%s.%d' % (name[:-6], n)
        label = re.findall(r'"([^"\\]{3,60})"\)', s[a:e])
        keys[key] = label[0] if label else name[:-6] + ' link ' + str(n)
        out.append(s[pos:a]); out.append('FileAction("%s") { ' % key + s[a:e] + ' }'); pos = e
    if n:
        out.append(s[pos:]); open(f, 'w').write(''.join(out)); print(name, n)
if keys: json.dump(keys, open(os.path.join(os.path.dirname(__file__), 'link_keys.json'), 'w'), indent=1, ensure_ascii=False)
print('keys', len(keys))
