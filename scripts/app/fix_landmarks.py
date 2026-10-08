"""The landmark tables' fallback literal carries its tuple type, so the type checker reads (name, hex, short) rows
with Copy.t cells. fix_landmarks.py <app dir>"""
import re, sys, os
n = 0
for f in ('LandmarksSection', 'LandmarksView'):
    p = os.path.join(sys.argv[1], 'App/Views', f + '.swift')
    if not os.path.exists(p): continue
    s = open(p).read()
    if 'as [(name: String, hex: UInt32, short: String)]' in s: n += 1; continue
    m = re.search(r'(static var hdTable: \[\(name: String, hex: UInt32, short: String\)\] \{ Lists\.rows\("[^"]+"\)\?\.map \{ r in \(name: Lists\.s\(r, 0\), hex: Lists\.u32\(r, 1\), short: Lists\.s\(r, 2\)\) \} \?\? \[\n(?:.*\n)*?    \]) \}', s)
    if not m: print(f, 'table not found'); continue
    s = s[:m.start()] + m.group(1) + ' as [(name: String, hex: UInt32, short: String)] }' + s[m.end():]
    open(p, 'w').write(s); n += 1
print('landmark tables typed', n)
