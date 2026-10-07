import sys,os,re
H='/Users/user301938'
app=sys.argv[1]; V=f'{H}/{app}/BKCB6/App/Views/'
def rw(fn, f):
    p=V+fn; s=open(p).read(); s2=f(s)
    if s2!=s: open(p,'w').write(s2)
    return s2!=s
ICONS='''

// MARK: - Park badges

/// NYC Parks badges, one per named park at the middle of its shape: the way schools and libraries carry theirs.
/// Strips, malls, parkways, undeveloped lots and unnamed properties get none.
enum DKParkIcons {
    static let skip: Set<String> = ["Strip", "Undeveloped", "Lot", "Parkway", "Mall", "Managed Sites", "Operations", "Retired N/A"]
    static let image = "mi:nyc-parks-logo.png"
    static func wanted(_ name: String, type: String) -> Bool {
        let n = name.trimmingCharacters(in: .whitespaces)
        return !n.isEmpty && n != "Park" && !skip.contains(type)
    }
    static func center(_ rings: [[CLLocationCoordinate2D]]) -> CLLocationCoordinate2D? {
        let pts = rings.flatMap { $0 }
        guard let la = pts.map(\\.latitude).min(), let lb = pts.map(\\.latitude).max(), let na = pts.map(\\.longitude).min(), let nb = pts.map(\\.longitude).max() else { return nil }
        return CLLocationCoordinate2D(latitude: (la + lb) / 2, longitude: (na + nb) / 2)
    }
    static func dots(_ parks: [(name: String, type: String, rings: [[CLLocationCoordinate2D]])], color: UIColor, size: CGFloat = 26) -> [DKDot] {
        var seen = Set<String>(); var out: [DKDot] = []
        for p in parks where wanted(p.name, type: p.type) && !seen.contains(p.name) {
            guard let c = center(p.rings) else { continue }
            seen.insert(p.name)
            out.append(DKDot(coord: c, title: p.name, subtitle: p.type.isEmpty ? "NYC Parks" : p.type, color: color, size: size, icon: .image(image), dense: true))
        }
        return out
    }
}
'''
n=0
# A. the helper
def a(s):
    if 'enum DKParkIcons' in s: return s
    return s.replace('\nenum DKIconRenderer {', ICONS + '\nenum DKIconRenderer {', 1)
n+=rw('MapIcons.swift', a)
# B. the CB6 map
def b(s):
    if 'parks-icons' in s: return s
    old='            out.append(DKLayer(id: "parks", polys: store.parkShapes.flatMap(\\.rings), color: UIColor(Overlay.parks.color), width: 1, fill: 0.6))\n'
    assert old in s, 'cb6map parks'
    return s.replace(old, old+'            out.append(DKLayer(id: "parks-icons", dots: DKParkIcons.dots(store.parkShapes.map { (name: $0.name, type: $0.subtitle, rings: $0.rings) }, color: UIColor(Overlay.parks.color))))\n',1)
n+=rw('CB6MapView.swift', b)
# C. the board parks page
def c(s):
    if 'parks-icons' in s: return s
    old='                    DKLayer(id: "parks", polys: parks.flatMap(\\.rings), color: UIColor(Color.parksGreen), fill: 0.45),\n'
    assert old in s, 'boardparks'
    return s.replace(old, old+'                    DKLayer(id: "parks-icons", dots: DKParkIcons.dots(parks.map { (name: $0.name, type: $0.type, rings: $0.rings) }, color: UIColor(Color.parksGreen))),\n',1)
n+=rw('DistrictKit.swift', c)
# C2. the Brooklyn boards map, where it draws parks
if os.path.exists(V+'BKBoards.swift'):
    def c2(s):
        if 'parks-icons' in s: return s
        m=re.search(r'^( *)out\.append\(DKLayer\(id: "parks", polys: DKParks\.parks\(scopeKey\)\.flatMap\(\\\.rings\), color: UIColor\(Color\.parksGreen\), width: 1, fill: 0\.5\)\)\n', s, re.M)
        if not m: print(app, 'BKBoards: no parks layer line; skipped'); return s
        ind=m.group(1)
        return s[:m.end()]+ind+'out.append(DKLayer(id: "parks-icons", dots: DKParkIcons.dots(DKParks.parks(scopeKey).map { (name: $0.name, type: $0.type, rings: $0.rings) }, color: UIColor(Color.parksGreen))))\n'+s[m.end():]
    n+=rw('BKBoards.swift', c2)
# D. the civic map's parks layer carries the badge on each named park
def d(s):
    if 'DKParkIcons.wanted' in s: return s
    old='MapFeature(id: p.id, title: p.name, subtitle: p.subtitle, rings: p.rings, colorKey: key(p.subtitle), fields: p.detail)'
    assert old in s, 'mapscreens parks'
    return s.replace(old, 'MapFeature(id: p.id, title: p.name, subtitle: p.subtitle, rings: p.rings, colorKey: key(p.subtitle), fields: p.detail, icon: DKParkIcons.wanted(p.name, type: p.subtitle) ? .image(DKParkIcons.image) : nil)',1)
n+=rw('MapScreens.swift', d)
# E. the civic map draws a shape's badge at its middle
def e(s):
    if 'f.icon, !f.rings.isEmpty' in s: return s
    old='                        for ring in f.rings { groups[f.colorKey]!.append(MKPolygon(coordinates: ring, count: ring.count)) }\n'
    assert old in s, 'civicmap polys'
    return s.replace(old, old+'                        if let ic = f.icon, !f.rings.isEmpty, let c = DKParkIcons.center(f.rings) {\n                            dots.append(DotAnnotation(coordinate: c, color: MapStyle.color("civicmap.\\(layer.id).\\(f.colorKey)", UIColor(layer.color(f.colorKey))), featureID: f.id, size: 26, icon: ic))\n                        }\n',1)
n+=rw('CivicMap.swift', e)
print(app, 'files changed', n)
