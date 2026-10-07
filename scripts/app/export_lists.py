#!/usr/bin/env python3
"""export_lists.py <app dir> <out.json>: every table the code reads from civic/lists.json, with the value the code
falls back to, so the file can start from what the app shows today. Reads the patched Swift (Lists.<fn>("key", [..]) and
Lists.rows("key")?... ?? [..] forms) and parses the fallback literal."""
import re, sys, os, glob, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import patch_tables2 as T

root = sys.argv[1]; out_path = sys.argv[2]
files = sorted(glob.glob(root + '/App/Views/*.swift') + glob.glob(root + '/App/Services/*.swift') + glob.glob(root + '/Shared/*.swift'))
PAT = re.compile(r'Lists\.(?P<fn>[A-Za-z0-9]+)\("(?P<key>[A-Za-z0-9_.]+)"(?P<tail>\)\?[^\n]*?\?\? |, )\[')
reg = {}; bad = []
for fn in files:
    s = open(fn).read()
    for m in PAT.finditer(s):
        key = m.group('key')
        if key in reg: continue
        start = m.end() - 1
        try:
            end = T.literal_end(s, start); lit = s[start:end]
            v = T.parse_literal(lit)
        except Exception as e:
            bad.append((key, str(e)[:60])); continue
        # tuple rows with a UInt32 column export as "#rrggbb"
        decl = s[max(0, m.start() - 200):m.start()]
        dm = re.search(r'var \w+: (\[\(.*?\)\]) \{\s*$', decl)
        if dm:
            cols = [ty for _, ty in T.tuple_parts(dm.group(1)[1:-1])]
            if 'UInt32' in cols and isinstance(v, list):
                v = [[('#%06x' % c if cols[j] == 'UInt32' and isinstance(c, int) else c) for j, c in enumerate(row)] if isinstance(row, list) else row for row in v]
        def clean(x):
            if isinstance(x, dict): return {str(k): clean(y) for k, y in x.items() if k != '__type'}
            if isinstance(x, list): return [clean(y) for y in x]
            return x
        reg[key] = clean(v)
json.dump(reg, open(out_path, 'w'), ensure_ascii=False, indent=1)
print(os.path.basename(root), 'tables exported', len(reg), '| unparsed', bad)
