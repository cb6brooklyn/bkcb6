import re, glob
H = '/Users/user301938'
COORDS = '''    static func coords(_ key: String, _ fallback: [CLLocationCoordinate2D]) -> [CLLocationCoordinate2D] {
        guard let rows = entry(key) as? [[String: NSNumber]] else { return fallback }
        return rows.compactMap { r in
            guard let la = r["latitude"], let ln = r["longitude"] else { return nil }
            return CLLocationCoordinate2D(latitude: la.doubleValue, longitude: ln.doubleValue)
        }
    }
    /// Rows of simple structs, decoded from the file's JSON; the code's table when the file has none.'''
for a in ('bkcb6app', 'bkcivics', 'cb6beyond'):
    p = f'{H}/{a}/BKCB6/App/Views/DistrictKit.swift'; s = open(p).read()
    if 'static func coords(' not in s:
        s = s.replace("    /// Rows of simple structs, decoded from the file's JSON; the code's table when the file has none.", COORDS, 1); open(p, 'w').write(s)
    print(a, 'coords', s.count('static func coords('))
    b = f'{H}/{a}/BKCB6/App/Views/BKBoards.swift'
    try:
        t = open(b).read()
        n = t.count('Lists.decode("BKBoards.labelSpots"')
        t2 = t.replace('Lists.decode("BKBoards.labelSpots"', 'Lists.coords("BKBoards.labelSpots"')
        if t2 != t: open(b, 'w').write(t2)
        print(a, 'labelSpots decode->coords', n, '| now', t2.count('Lists.coords("BKBoards.labelSpots"'))
        for m in re.finditer(r'labelSpots[^\n]{0,160}', t2): print('   ', m.group(0)[:160])
    except FileNotFoundError: pass
