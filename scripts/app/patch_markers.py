import sys,os,re
H='/Users/user301938'
app=sys.argv[1]; V=f'{H}/{app}/BKCB6/App/Views/'
def rw(fn, f):
    p=V+fn
    if not os.path.exists(p): return False
    s=open(p).read(); s2=f(s)
    if s2!=s: open(p,'w').write(s2)
    return s2!=s
MARKERS='''

// MARK: - Markers from a file

/// Icon layers from civic/markers.json, so a set of badges lands on any map without a build. Each layer:
/// {"id": "...", "screens": ["cb6map", "profile", "boards"], "with": "parks", "icon": "mi:nyc-parks-logo.png",
///  "color": "#16a34a", "size": 26, "points": [[lat, lng, "title", "subtitle"], ...]}
/// with names the overlay or topic the layer rides with (empty: always). icon is "mi:<file>" (civic/mapicons),
/// "img:<file>" (civic/img), a logo file name, or "sf:<symbol>#<hex>" for an SF Symbol on a disc.
enum DKMarkers {
    struct Layer { let id: String; let screens: [String]; let with: String; let color: UIColor; let dots: [DKDot] }
    private static var cache: [Layer]?
    private static let lock = NSLock()
    private static var observing = false
    static func icon(_ s: String) -> DKIcon? {
        if s.isEmpty { return nil }
        if s.hasPrefix("sf:") {
            let parts = String(s.dropFirst(3)).split(separator: "#", maxSplits: 1).map(String.init)
            return .symbol(parts[0], parts.count > 1 ? "#" + parts[1] : "#0d1b4b")
        }
        return .image(s)
    }
    static func all() -> [Layer] {
        lock.lock(); defer { lock.unlock() }
        if !observing {
            observing = true
            NotificationCenter.default.addObserver(forName: DataPack.notification, object: nil, queue: nil) { _ in
                lock.lock(); cache = nil; lock.unlock()
            }
        }
        if let c = cache { return c }
        let root = DK.json("markers") as? [String: Any]
        let out: [Layer] = (root?["layers"] as? [[String: Any]] ?? []).compactMap { l in
            guard let id = l["id"] as? String else { return nil }
            let color = DK.uiHex((l["color"] as? String) ?? "#0d1b4b")
            let size = CGFloat((l["size"] as? NSNumber)?.doubleValue ?? 26)
            let ic = icon((l["icon"] as? String) ?? "")
            let dense = (l["dense"] as? Bool) ?? true
            let dots: [DKDot] = (l["points"] as? [[Any]] ?? []).compactMap { p in
                guard p.count >= 2, let la = (p[0] as? NSNumber)?.doubleValue, let ln = (p[1] as? NSNumber)?.doubleValue else { return nil }
                return DKDot(coord: CLLocationCoordinate2D(latitude: la, longitude: ln), title: p.count > 2 ? (p[2] as? String ?? "") : "",
                             subtitle: p.count > 3 ? (p[3] as? String ?? "") : "", color: color, size: size, icon: ic, dense: dense)
            }
            return Layer(id: id, screens: l["screens"] as? [String] ?? [], with: (l["with"] as? String) ?? "", color: color, dots: dots)
        }
        cache = out
        return out
    }
    /// The file's layers for a screen, given which overlays or topics are on.
    static func layers(screen: String, on: Set<String>) -> [DKLayer] {
        all().filter { ($0.screens.isEmpty || $0.screens.contains(screen)) && ($0.with.isEmpty || on.contains($0.with)) }
            .map { DKLayer(id: "markers-" + $0.id, dots: $0.dots, color: $0.color) }
    }
    /// The same, as one layer, for maps that list their layers in one literal.
    static func merged(screen: String, on: Set<String>) -> DKLayer {
        DKLayer(id: "markers-" + screen, dots: layers(screen: screen, on: on).flatMap(\\.dots))
    }
}
'''
n=0
def a(s):
    if 'enum DKMarkers' in s: return s
    assert 'enum DKParkIcons' in s, 'park icons first'
    # the park badge image is file-overridable too
    s=s.replace('out.append(DKDot(coord: c, title: p.name, subtitle: p.type.isEmpty ? "NYC Parks" : p.type, color: color, size: size, icon: .image(image), dense: true))',
                'out.append(DKDot(coord: c, title: p.name, subtitle: p.type.isEmpty ? "NYC Parks" : p.type, color: color, size: size, icon: MapStyle.icon("parks-icons", .image(image)), dense: true))')
    return s.replace('\nenum DKIconRenderer {', MARKERS + '\nenum DKIconRenderer {', 1)
n+=rw('MapIcons.swift', a)
def b(s):
    if 'static func icon(_ key: String, _ fallback: DKIcon?)' in s: return s
    old='    static func number(_ key: String, _ fallback: CGFloat) -> CGFloat { CGFloat(number(key, Double(fallback))) }\n'
    assert old in s, 'mapstyle number'
    return s.replace(old, old+'''    /// A point layer's icon by key ("cb6map:schools", or the layer's own id): "mi:<file>", "img:<file>", a logo file, or "sf:<symbol>#<hex>".
    static func icon(_ key: String, _ fallback: DKIcon?) -> DKIcon? {
        let icons = section("icons")
        let bare = key.split(separator: ":").last.map(String.init) ?? key
        guard let s = (icons[key] as? String) ?? (icons[bare] as? String) else { return fallback }
        return DKMarkers.icon(s)
    }
''',1)
n+=rw('DistrictKit.swift', b)
def c(s):
    if 'DKMarkers.layers(screen: "cb6map"' in s: return s
    old='        // CB6 stays on top of everything.\n        out.append(DKLayer(id: "outline", lines: outline, color: UIColor(Color.cb6Orange), width: 3.5))\n'
    assert old in s, 'cb6map outline'
    s=s.replace(old, '        out += DKMarkers.layers(screen: "cb6map", on: Set(overlays.map { "\\($0)" }))\n'+old, 1)
    s=s.replace('size: 26, icon: DKIcon.school($0.name), dense: true)', 'size: 26, icon: MapStyle.icon("cb6map:schools", DKIcon.school($0.name)), dense: true)')
    s=s.replace('size: 24, icon: .image("mi:nyc-child-care-logo.png"), dense: true)', 'size: 24, icon: MapStyle.icon("cb6map:childcare", .image("mi:nyc-child-care-logo.png")), dense: true)')
    s=s.replace('size: 26, icon: .image("mi:brooklyn-public-library-logo.webp"))', 'size: 26, icon: MapStyle.icon("cb6map:libraries", .image("mi:brooklyn-public-library-logo.webp")))')
    return s
n+=rw('CB6MapView.swift', c)
def d(s):
    if 'DKMarkers.layers(screen: "profile"' in s: return s
    old='            out.append(DKLayer(id: "parks", polys: cds.flatMap { DKParks.parks($0).flatMap(\\.rings) }, color: UIColor(Color.parksGreen), width: 1, fill: 0.5))\n'
    assert old in s, 'profile parks'
    s=s.replace(old, old+'            out.append(DKLayer(id: "parks-icons", dots: DKParkIcons.dots(cds.flatMap { DKParks.parks($0) }.map { (name: $0.name, type: $0.type, rings: $0.rings) }, color: UIColor(Color.parksGreen))))\n', 1)
    # the file's layers, before the first return of this builder
    i=s.index(old); j=s.index('        return out\n', i)
    s=s[:j]+'        out += DKMarkers.layers(screen: "profile", on: Set(layers))\n'+s[j:]
    return s
n+=rw('ProfileMap.swift', d)
def e(s):
    if 'DKMarkers.merged(screen: "boards"' in s: return s
    m=re.search(r'^( *)DKLayer\(id: "parks-icons", dots: DKParkIcons\.dots\(parks\.map[^\n]*\n', s, re.M)
    assert m, 'boardparks icons'
    return s[:m.end()]+m.group(1)+'DKMarkers.merged(screen: "boards", on: ["parks"]),\n'+s[m.end():]
n+=rw('DistrictKit.swift', e)
print(app, 'files changed', n)
