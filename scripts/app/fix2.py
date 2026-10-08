H = '/Users/user301938'
CD = '''    static func coordDict(_ key: String, _ fallback: [String: CLLocationCoordinate2D]) -> [String: CLLocationCoordinate2D] {
        guard let d = entry(key) as? [String: [String: NSNumber]] else { return fallback }
        var out: [String: CLLocationCoordinate2D] = [:]
        for (k, r) in d { if let la = r["latitude"], let ln = r["longitude"] { out[k] = CLLocationCoordinate2D(latitude: la.doubleValue, longitude: ln.doubleValue) } }
        return out
    }
    static func coords('''
for a in ('bkcb6app', 'bkcivics', 'cb6beyond'):
    p = f'{H}/{a}/BKCB6/App/Views/DistrictKit.swift'; s = open(p).read()
    if 'static func coordDict(' not in s: s = s.replace('    static func coords(', CD, 1); open(p, 'w').write(s)
    b = f'{H}/{a}/BKCB6/App/Views/BKBoards.swift'
    try:
        t = open(b).read(); t2 = t.replace('Lists.decodeDict("BKBoards.labelSpots"', 'Lists.coordDict("BKBoards.labelSpots"')
        if t2 != t: open(b, 'w').write(t2)
        print(a, 'coordDict in kit', s.count('static func coordDict('), '| labelSpots routed', t2.count('Lists.coordDict("BKBoards.labelSpots"'))
    except FileNotFoundError: print(a, 'coordDict in kit', s.count('static func coordDict('))
