"""Every size and gap from the file: font sizes (DM.sans, DM.mono, .system(size:)), padding and stack spacing written as
numbers in the code read mapstyle.json "numbers" by key ("<File>.z.<id>"), keeping today's value when the file says nothing.
editable2.py <app dir> <registry out>"""
import re, os, sys, glob, json, hashlib
R = sys.argv[1]; REG = sys.argv[2]
reg = json.load(open(REG)) if os.path.exists(REG) else {}
def h8(t): return hashlib.sha1(t.encode()).hexdigest()[:8]
dk = glob.glob(os.path.join(R, 'BKCB6/App/Views/DistrictKit.swift'))[0]; d = open(dk).read()
if 'func Sz(' not in d:
    d += """
/// The sizes and gaps from mapstyle.json "numbers", read once and again when the pack brings new files.
enum SzFile {
    private static var nums: [String: Double]?
    private static var observing = false
    private static let lock = NSLock()
    static func get(_ k: String) -> Double? {
        lock.lock(); defer { lock.unlock() }
        if !observing {
            observing = true
            NotificationCenter.default.addObserver(forName: DataPack.notification, object: nil, queue: nil) { _ in lock.lock(); nums = nil; lock.unlock() }
        }
        if nums == nil {
            var d: [String: Double] = [:]
            for (key, v) in MapStyle.section("numbers") { if let x = DK.num(v) { d[key] = x } }
            nums = d
        }
        return nums?[k]
    }
}
/// A size or gap from mapstyle.json "numbers" by key, else the value written here.
func Sz(_ key: String, _ value: CGFloat) -> CGFloat { SzFile.get(key).map { CGFloat($0) } ?? value }
"""
    open(dk, 'w').write(d)
N = r'(\d+(?:\.\d+)?)'
PATS = [
    (re.compile(r'(DM\.(?:sans|mono)\()' + N + r'(?=[,)])'), 1, 2),
    (re.compile(r'(\.system\(size: )' + N + r'(?=[,)])'), 1, 2),
    (re.compile(r'(\.padding\()' + N + r'(?=\))'), 1, 2),
    (re.compile(r'(\.padding\(\.(?:horizontal|vertical|top|bottom|leading|trailing), )' + N + r'(?=\))'), 1, 2),
    (re.compile(r'((?:VStack|HStack|LazyVStack|LazyHStack|ZStack)\((?:alignment: [.\w]+, )?spacing: )' + N + r'(?=[,)])'), 1, 2),
]
n = 0
for p in sorted(glob.glob(os.path.join(R, 'BKCB6/App/**/*.swift'), recursive=True)):
    stem = os.path.basename(p)[:-6]; s = open(p).read(); o = s; out = []
    for i, line in enumerate(s.split('\n'), 1):
        if line.strip().startswith('//') or 'func Sz(' in line: out.append(line); continue
        col = [0]
        for rx, g1, g2 in PATS:
            def rep(m):
                global n
                col[0] += 1; k = f'{stem}.z.{h8(stem + str(i) + str(col[0]) + m.group(0))}'
                reg[k] = float(m.group(g2)); n += 1
                return f'{m.group(g1)}Sz("{k}", {m.group(g2)})'
            line = rx.sub(rep, line)
        out.append(line)
    s = '\n'.join(out)
    if s != o: open(p, 'w').write(s)
json.dump(reg, open(REG, 'w'), indent=1, sort_keys=True)
print('sizes and gaps:', n, 'now read the file')
