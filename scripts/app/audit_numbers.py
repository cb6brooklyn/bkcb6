"""The code's tunable numbers read from the file first (mapstyle.json "numbers": {"<File>.n.<id>": value}):
list caps (.prefix(N), N >= 12, not on strings), day windows (N * 86400, byAdding: .day, value: N), the 150 m radius and the
3,000 m park limit. Writes numbers-<app>.json, the registry of keys with the code's values. audit_numbers.py <app dir> <registry>"""
import re, sys, os, glob, json, hashlib
R = sys.argv[1]; OUT = sys.argv[2]
V = os.path.join(R, 'App/Views')
reg = json.load(open(OUT)) if os.path.exists(OUT) else {}
def h8(t): return hashlib.sha1(t.encode()).hexdigest()[:8]
n = 0
for f in sorted(glob.glob(os.path.join(V, '*.swift'))):
    name = os.path.splitext(os.path.basename(f))[0]
    s = open(f).read(); o = s
    def key(label, lineno):
        k = f'{name}.n.{label}'
        if k in reg and reg[k][1] != lineno: k = f'{name}.n.{label}-{lineno}'
        return k
    out = []
    for i, line in enumerate(s.split('\n'), 1):
        if line.strip().startswith('//') or 'MapStyle.number(' in line:
            out.append(line); continue
        l = line
        # list caps
        def cap(m):
            global n
            N = int(m.group(1))
            if N < 12: return m.group(0)
            before = l[:m.start()]
            if before.rstrip().endswith('String(') or 'String(' in before[-24:] or '.count >' in l: return m.group(0)
            k = key(f'cap{N}', i); reg[k] = (N, i); n += 1
            return f'.prefix(Int(MapStyle.number("{k}", {N})))'
        l = re.sub(r'\.prefix\((\d+)\)', cap, l)
        # day windows
        def days(m):
            global n
            sign, N = m.group(1), int(m.group(2))
            k = key(f'days{N}', i); reg[k] = (N, i); n += 1
            return f'{sign}MapStyle.number("{k}", {N}) * 86400'
        l = re.sub(r'(-?)(\d+) \* 86400\b', days, l)
        def byday(m):
            global n
            sign, N = m.group(1), int(m.group(2))
            k = key(f'days{N}', i); reg[k] = (N, i); n += 1
            return f'byAdding: .day, value: {sign}Int(MapStyle.number("{k}", {N}))'
        l = re.sub(r'byAdding: \.day, value: (-?)(\d+)\b', byday, l)
        # the radius and the park limit
        if '<= 150 * 150' in l:
            k = key('radiusMeters', i); reg[k] = (150, i); n += 1
            l = l.replace('<= 150 * 150', f'<= MapStyle.number("{k}", 150) * MapStyle.number("{k}", 150)')
        if 'p.meters < 3000' in l:
            k = key('parkMeters', i); reg[k] = (3000, i); n += 1
            l = l.replace('p.meters < 3000', f'p.meters < Int(MapStyle.number("{k}", 3000))')
        out.append(l)
    s = '\n'.join(out)
    if s != o: open(f, 'w').write(s)
json.dump({k: v[0] for k, v in reg.items()}, open(OUT, 'w'), indent=1, sort_keys=True)
print('numbers', n, 'wrapped,', len(reg), 'keys')
