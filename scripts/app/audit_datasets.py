"""Every NYC Open Data dataset the code names ("xxxx-xxxx") reads from the file first: Lists.string("<File>.ds.<id>", "xxxx-xxxx"),
with lists.json {"<File>.ds.<id>": "yyyy-yyyy"} pointing that screen at another dataset. Adds Lists.string. Writes
datasets-<app>.json, the registry of keys with the ids the code uses. audit_datasets.py <app dir> <registry>"""
import re, sys, os, glob, json
R = sys.argv[1]; OUT = sys.argv[2]
V = os.path.join(R, 'App/Views')
reg = json.load(open(OUT)) if os.path.exists(OUT) else {}
PAT = re.compile(r'"([a-z0-9]{4}-[a-z0-9]{4})"')
NOT = {'show-more', 'full-text', 'read-more', 'show-less', 'load-more', 'home-view', 'site-card', 'base-map', 'show-list'}
n = 0
for f in sorted(glob.glob(os.path.join(V, '*.swift'))):
    name = os.path.splitext(os.path.basename(f))[0]
    s = open(f).read(); o = s
    def rep(m):
        global n
        lit = m.group(1)
        if lit in NOT or not any(ch.isdigit() for ch in lit): return m.group(0)
        before = s[max(0, m.start() - 40):m.start()]
        if 'Lists.string("' in before or 'Copy.' in before[-20:] or 'case ' in before[-12:] or '== ' in before[-4:]: return m.group(0)
        k = f'{name}.ds.{lit}'; reg[k] = lit; n += 1
        return f'Lists.string("{k}", "{lit}")'
    s = PAT.sub(rep, s)
    if s != o: open(f, 'w').write(s)
dk = os.path.join(V, 'DistrictKit.swift'); d = open(dk).read()
if 'static func string(_ key: String, _ fallback: String)' not in d:
    anchor = '    static func strings(_ key: String, _ fallback: [String]) -> [String] { (entry(key) as? [String]) ?? fallback }\n'
    assert anchor in d, 'Lists.strings'
    d = d.replace(anchor, anchor + '    /// One string from the file (a dataset id, a slug), the code\'s when the file has none.\n    static func string(_ key: String, _ fallback: String) -> String { (entry(key) as? String) ?? fallback }\n', 1)
    open(dk, 'w').write(d)
json.dump(reg, open(OUT, 'w'), indent=1, sort_keys=True)
print('datasets', n, 'wrapped,', len(reg), 'keys')
