"""Every SF symbol the code names (Image(systemName: "x"), systemImage: "x") reads from the file first:
MapStyle.symbol("<File>.s.<id>", "x"), with mapstyle.json "symbols": {"<File>.s.<id>": "name"} overriding it.
Shared/ is left alone (the widget target). Writes symbols-<app>.json, the registry of keys and defaults.
audit_symbols.py <app dir> [registry path]"""
import re, sys, os, glob, json, hashlib
R = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(R.rstrip('/')), 'symbols-' + os.path.basename(os.path.dirname(R.rstrip('/'))) + '.json')
def h8(t): return hashlib.sha1(t.encode()).hexdigest()[:8]
reg = {}
n = 0
PAT = re.compile(r'(Image\(systemName: |systemImage: )"([a-z0-9.]+)"')
for f in sorted(glob.glob(os.path.join(R, 'App', '**', '*.swift'), recursive=True)):
    name = os.path.splitext(os.path.basename(f))[0]
    s = open(f).read()
    def rep(m):
        global n
        key = f'{name}.s.{h8(m.group(2))}'
        reg[key] = m.group(2); n += 1
        return f'{m.group(1)}MapStyle.symbol("{key}", "{m.group(2)}")'
    t = PAT.sub(rep, s)
    if t != s: open(f, 'w').write(t)
# the lookup
dk = os.path.join(R, 'App/Views/DistrictKit.swift'); d = open(dk).read()
if 'static func symbol(' not in d:
    anchor = '    static func label(_ key: String, _ fallback: String) -> String {\n'
    assert anchor in d, 'MapStyle.label'
    d = d.replace(anchor, '    /// An SF symbol name from the file ("symbols": {"<File>.s.<id>": "name"}), the code\'s when the file has none.\n    static func symbol(_ key: String, _ fallback: String) -> String { (section("symbols")[key] as? String) ?? fallback }\n' + anchor, 1)
    open(dk, 'w').write(d)
json.dump(reg, open(out, 'w'), indent=1, sort_keys=True)
print('symbols', n, 'replaced,', len(reg), 'keys ->', out)
