import SwiftUI
import MapKit

// A map described in a file: a node {"type": "map", ...} anywhere a node goes, or a whole screen (screens.json "nodes"
// {"<name>": {...}} opened by "node:<name>", or put in place of any screen with "replace": {"<screen>": "node:<name>"}).
//
// map:    "height" (points, or "full"), "center" [lat, lon], "distance" (meters), "fit" (a layer id or "all"), "style" (muted,
//         standard, hybrid, imagery), "pois" (true shows Apple's places), "search" (true: an address box, offline, every NYC block),
//         "searchScope" ("city", a borough digit, or a board cd), "toggles" (true: a chip per layer with a "title"), "legend" (true),
//         "layers": [layer], "tapEmpty" (a node shown before anything is tapped), "corner".
// layer:  "id", "title", "on" (default true), "toggle" (default true), "file" (a GeoJSON path in the pack) or "data" (rows, as
//         nodes take them, with "lat"/"lon" fields named by "latKey"/"lonKey"), "where" {prop: value | [values]} on features,
//         "stroke", "width", "dash" [on, off], "fill", "fillOpacity", "colorBy" {"prop", "map": {value: color}, "stops": [[number, color]],
//         "default"} (fill; "strokeBy" the same for lines and outlines), "pin" {"style": dot | marker | image | text, "color",
//         "symbol", "image" (pack path, may use {prop}), "size", "text"}, "label" ("{prop}" at each shape's center), "labelSize",
//         "labelColor", "minDistance"/"maxDistance" (meters: shown only when the camera is that far or closer), "tap" (a node drawn
//         in the card when a shape or pin is tapped, filled from its properties; or "dest" to open a screen straight away),
//         "pick" {"fill", "stroke", "width"} (how a tapped shape looks), "legend" [[color, label], ...].

final class FMLayer {
    struct Feat { let props: [String: Any]; let polys: [MKPolygon]; let lines: [[CLLocationCoordinate2D]]; let points: [CLLocationCoordinate2D]; let center: CLLocationCoordinate2D?; let rect: MKMapRect }
    let feats: [Feat]
    let rect: MKMapRect
    init(_ feats: [Feat]) { self.feats = feats; self.rect = feats.reduce(MKMapRect.null) { $0.union($1.rect) } }
}

enum FM {
    private static var cache: [String: FMLayer] = [:]
    private static let watch: Any = NotificationCenter.default.addObserver(forName: DataPack.notification, object: nil, queue: .main) { _ in FM.cache = [:] }

    static func coords(_ a: Any?) -> [CLLocationCoordinate2D] {
        (a as? [Any] ?? []).compactMap { p in
            guard let p = p as? [Any], p.count >= 2, let x = DK.num(p[0]), let y = DK.num(p[1]) else { return nil }
            return CLLocationCoordinate2D(latitude: y, longitude: x)
        }
    }
    static func polygon(_ rings: Any?) -> MKPolygon? {
        let rs = (rings as? [Any] ?? []).map(coords)
        guard let outer = rs.first, outer.count > 2 else { return nil }
        let holes = rs.dropFirst().filter { $0.count > 2 }.map { MKPolygon(coordinates: $0, count: $0.count) }
        return MKPolygon(coordinates: outer, count: outer.count, interiorPolygons: holes)
    }
    static func rectOf(_ cs: [CLLocationCoordinate2D]) -> MKMapRect {
        cs.reduce(MKMapRect.null) { r, c in let p = MKMapPoint(c); return r.union(MKMapRect(x: p.x, y: p.y, width: 0.1, height: 0.1)) }
    }

    @MainActor static func layer(_ l: [String: Any], ctx: [String: Any], store: DataStore) -> FMLayer {
        _ = watch
        let key = (try? JSONSerialization.data(withJSONObject: l, options: [.sortedKeys])).map { String(decoding: $0, as: UTF8.self) } ?? UUID().uuidString
        let dataKey = l["data"] != nil ? key + FN.board : key
        if let hit = cache[dataKey] { return hit }
        var feats: [FMLayer.Feat] = []
        if let spec = l["data"] as? [String: Any] {
            let la = DK.str(l["latKey"]).isEmpty ? "lat" : DK.str(l["latKey"]), lo = DK.str(l["lonKey"]).isEmpty ? "lon" : DK.str(l["lonKey"])
            for r in FN.rows(spec, ctx, store: store) {
                guard let y = DK.num(r[la]), let x = DK.num(r[lo]) else { continue }
                let c = CLLocationCoordinate2D(latitude: y, longitude: x)
                feats.append(.init(props: r, polys: [], lines: [], points: [c], center: c, rect: rectOf([c])))
            }
        } else if let gj = FN.json(FN.fill(DK.str(l["file"]), ctx)) as? [String: Any] {
            let list = (gj["features"] as? [[String: Any]]) ?? (gj["type"] as? String == "Feature" ? [gj] : [["type": "Feature", "properties": [:], "geometry": gj]])
            for f in list {
                let props = f["properties"] as? [String: Any] ?? [:]
                guard let g = f["geometry"] as? [String: Any] else { continue }
                var polys: [MKPolygon] = [], lines: [[CLLocationCoordinate2D]] = [], pts: [CLLocationCoordinate2D] = []
                let c = g["coordinates"]
                switch DK.str(g["type"]) {
                case "Polygon": if let p = polygon(c) { polys.append(p) }
                case "MultiPolygon": polys = (c as? [Any] ?? []).compactMap(polygon)
                case "LineString": lines = [coords(c)]
                case "MultiLineString": lines = (c as? [Any] ?? []).map(coords)
                case "Point": pts = coords([c as Any])
                case "MultiPoint": pts = coords(c)
                default: break
                }
                var rect = MKMapRect.null
                polys.forEach { rect = rect.union($0.boundingMapRect) }
                lines.forEach { rect = rect.union(rectOf($0)) }
                if !pts.isEmpty { rect = rect.union(rectOf(pts)) }
                let biggest = polys.max { $0.boundingMapRect.width * $0.boundingMapRect.height < $1.boundingMapRect.width * $1.boundingMapRect.height }
                let center = labelPoint(props) ?? biggest.map { $0.coordinate } ?? lines.first.flatMap { $0.isEmpty ? nil : $0[$0.count / 2] } ?? pts.first
                feats.append(.init(props: props, polys: polys, lines: lines, points: pts, center: center, rect: rect))
            }
        }
        if let w = l["where"] as? [String: Any] {
            feats = feats.filter { f in w.allSatisfy { k, want in
                let have = FN.string(f.props[k])
                if let list = want as? [Any] { return list.contains { FN.fill(DK.str($0), ctx) == have } }
                return FN.fill(DK.str(want), ctx) == have
            } }
        }
        let out = FMLayer(feats)
        cache[dataKey] = out
        return out
    }
    /// A label point the file gives ("c": [lat, lon] or "lat"/"lon" in the properties).
    static func labelPoint(_ p: [String: Any]) -> CLLocationCoordinate2D? {
        if let c = p["c"] as? [Any], c.count == 2, let y = DK.num(c[0]), let x = DK.num(c[1]) { return .init(latitude: y, longitude: x) }
        if let y = DK.num(p["lat"]), let x = DK.num(p["lon"]) { return .init(latitude: y, longitude: x) }
        return nil
    }

    static func inside(_ c: CLLocationCoordinate2D, _ p: MKPolygon) -> Bool {
        let m = MKMapPoint(c)
        guard p.boundingMapRect.contains(m) else { return false }
        func ring(_ q: MKPolygon) -> Bool {
            let pts = q.points(); let n = q.pointCount; var inside = false; var j = n - 1
            for i in 0..<n {
                let a = pts[i], b = pts[j]
                if (a.y > m.y) != (b.y > m.y), m.x < (b.x - a.x) * (m.y - a.y) / (b.y - a.y) + a.x { inside.toggle() }
                j = i
            }
            return inside
        }
        guard ring(p) else { return false }
        return !(p.interiorPolygons ?? []).contains { ring($0) }
    }

    static func styled(_ l: [String: Any], _ key: String, _ by: String, _ f: FMLayer.Feat, _ ctx: [String: Any], _ fallback: Color) -> Color {
        if let cb = l[by] as? [String: Any] {
            let v = FN.lookup(DK.str(cb["prop"]), f.props)
            if let m = cb["map"] as? [String: Any], let c = m[FN.string(v)] { return FN.color(c, ctx, fallback) }
            if let stops = cb["stops"] as? [[Any]], let x = DK.num(v) {
                var pick: Any? = nil
                for s in stops where s.count == 2 { if let t = DK.num(s[0]), x >= t { pick = s[1] } }
                if let pick { return FN.color(pick, ctx, fallback) }
            }
            if let d = cb["default"] { return FN.color(d, ctx, fallback) }
        }
        var c = ctx; f.props.forEach { c[$0.key] = $0.value }
        return FN.color(l[key], c, fallback)
    }
}

struct FileMap: View {
    let spec: [String: Any]
    let ctx: [String: Any]
    @EnvironmentObject var store: DataStore
    @State private var position: MapCameraPosition = .automatic
    @State private var distance: Double = 30000
    @State private var on: [String: Bool] = [:]
    @State private var picked: (layer: Int, feat: Int)? = nil
    @State private var query = ""
    @State private var found: AddressMatch? = nil
    @State private var started = false

    private var layerSpecs: [[String: Any]] { spec["layers"] as? [[String: Any]] ?? [] }
    private func id(_ i: Int) -> String { let s = DK.str(layerSpecs[i]["id"]); return s.isEmpty ? "layer\(i)" : s }
    private func isOn(_ i: Int) -> Bool { on[id(i)] ?? (layerSpecs[i]["on"] as? Bool ?? true) }
    private func shown(_ i: Int) -> Bool {
        let l = layerSpecs[i]
        if !isOn(i) || !FN.shows(l["when"], ctx) { return false }
        if let mx = DK.num(l["maxDistance"]), distance > mx { return false }
        if let mn = DK.num(l["minDistance"]), distance < mn { return false }
        return true
    }

    var body: some View {
        let layers = layerSpecs.map { FM.layer($0, ctx: ctx, store: store) }
        let corner = CGFloat(DK.num(spec["corner"]) ?? 16)
        let full = DK.str(spec["height"]) == "full"
        VStack(alignment: .leading, spacing: 8) {
            if spec["search"] as? Bool ?? false { searchBox }
            ZStack(alignment: .bottom) {
                MapReader { proxy in
                    Map(position: $position) { content(layers) }
                        .mapStyle(mapStyle)
                        .onMapCameraChange(frequency: .onEnd) { c in distance = c.camera.distance }
                        .onTapGesture { pt in
                            guard let c = proxy.convert(pt, from: .local) else { return }
                            picked = hit(c, layers)
                            if let p = picked, let d = tapDest(p), !d.isEmpty { pendingDest = d }
                        }
                }
                card(layers)
            }
            .frame(height: full ? nil : CGFloat(DK.num(spec["height"]) ?? 420))
            .frame(maxHeight: full ? .infinity : nil)
            .clipShape(RoundedRectangle(cornerRadius: full ? 0 : corner, style: .continuous))
            if spec["toggles"] as? Bool ?? false { toggles }
            if spec["legend"] as? Bool ?? false { legend }
        }
        .onAppear {
            if !started { started = true; position = initial(layers) }
            // Test hooks: "-mapPick lat,lon" taps that point; "-mapSearch text" types into the address box.
            if let p = Hook.value("-mapPick")?.split(separator: ",").compactMap({ Double($0) }), p.count == 2 { picked = hit(.init(latitude: p[0], longitude: p[1]), layers) }
            if let q = Hook.value("-mapSearch") { query = q }
        }
        .navigationDestination(isPresented: Binding(get: { pendingDest != nil }, set: { if !$0 { pendingDest = nil } })) {
            FileNodeDest(dest: pendingDest ?? "")
        }
    }
    @State private var pendingDest: String? = nil
    private func merged(_ f: FMLayer.Feat) -> [String: Any] { var c = ctx; f.props.forEach { c[$0.key] = $0.value }; return c }

    private func tapDest(_ p: (layer: Int, feat: Int)) -> String? {
        let l = layerSpecs[p.layer]
        guard l["tap"] == nil, let d = l["dest"] as? String else { return nil }
        let f = FM.layer(l, ctx: ctx, store: store).feats[p.feat]
        var c = ctx; f.props.forEach { c[$0.key] = $0.value }
        return FN.fill(d, c)
    }

    private var mapStyle: MapKit.MapStyle {
        let pois: PointOfInterestCategories = (spec["pois"] as? Bool ?? false) ? .all : .excludingAll
        switch DK.str(spec["style"]) {
        case "standard": return .standard(elevation: .flat, pointsOfInterest: pois)
        case "hybrid": return .hybrid(elevation: .flat, pointsOfInterest: pois)
        case "imagery": return .imagery(elevation: .flat)
        default: return .standard(elevation: .flat, emphasis: .muted, pointsOfInterest: pois)
        }
    }

    private func initial(_ layers: [FMLayer]) -> MapCameraPosition {
        let fit = DK.str(spec["fit"])
        if !fit.isEmpty {
            var r = MKMapRect.null
            for (i, l) in layers.enumerated() where fit == "all" || id(i) == fit { r = r.union(l.rect) }
            if !r.isNull, r.width > 0 {
                let pad = max(r.width, r.height) * 0.08
                return .rect(r.insetBy(dx: -pad, dy: -pad))
            }
        }
        if let c = spec["center"] as? [Any], c.count == 2, let y = DK.num(c[0]), let x = DK.num(c[1]) {
            return .camera(MapCamera(centerCoordinate: .init(latitude: y, longitude: x), distance: DK.num(spec["distance"]) ?? 12000))
        }
        return .camera(MapCamera(centerCoordinate: .init(latitude: 40.676, longitude: -73.995), distance: DK.num(spec["distance"]) ?? 12000))
    }

    @MapContentBuilder private func content(_ layers: [FMLayer]) -> some MapContent {
        ForEach(Array(layers.indices), id: \.self) { i in
            if shown(i) { layerContent(i, layers[i]) }
        }
        if let p = picked, layers.indices.contains(p.layer), layers[p.layer].feats.indices.contains(p.feat) {
            let l = layerSpecs[p.layer], f = layers[p.layer].feats[p.feat], pk = l["pick"] as? [String: Any] ?? [:]
            ForEach(Array(f.polys.indices), id: \.self) { k in
                MapPolygon(f.polys[k]).foregroundStyle(FN.color(pk["fill"] ?? "#ffd400", ctx, .yellow).opacity(DK.num(pk["fillOpacity"]) ?? 0.6))
                    .stroke(FN.color(pk["stroke"] ?? "navy", ctx, .cb6Navy), lineWidth: CGFloat(DK.num(pk["width"]) ?? 4))
            }
        }
        if let a = found { Marker(a.label, coordinate: a.coord).tint(Color.cb6Orange) }
    }

    @MapContentBuilder private func layerContent(_ i: Int, _ layer: FMLayer) -> some MapContent {
        let l = layerSpecs[i]
        let width = CGFloat(DK.num(l["width"]) ?? 1.5)
        let dash = (l["dash"] as? [Any])?.compactMap { DK.num($0).map { CGFloat($0) } } ?? []
        let op = DK.num(l["fillOpacity"]) ?? 0.25
        let pin = l["pin"] as? [String: Any]
        let label = DK.str(l["label"])
        ForEach(Array(layer.feats.indices), id: \.self) { k in
            let f = layer.feats[k]
            let stroke = FM.styled(l, "stroke", "strokeBy", f, ctx, .cb6Navy)
            let fill = FM.styled(l, "fill", "colorBy", f, ctx, .clear)
            ForEach(Array(f.polys.indices), id: \.self) { j in
                MapPolygon(f.polys[j]).foregroundStyle(fill.opacity(l["fill"] == nil && l["colorBy"] == nil ? 0 : op))
                    .stroke(stroke, style: StrokeStyle(lineWidth: width, dash: dash))
            }
            ForEach(Array(f.lines.indices), id: \.self) { j in
                MapPolyline(coordinates: f.lines[j]).stroke(stroke, style: StrokeStyle(lineWidth: width, lineCap: .round, lineJoin: .round, dash: dash))
            }
            if let pin {
                ForEach(Array(f.points.indices), id: \.self) { j in
                    Annotation("", coordinate: f.points[j], anchor: DK.str(pin["style"]) == "marker" ? .bottom : .center) {
                        Button { picked = (i, k); if let d = tapDest((i, k)), !d.isEmpty { pendingDest = d } } label: { pinView(pin, f, fill: fill) }.buttonStyle(.plain)
                    }
                }
            }
            if !label.isEmpty, let c = f.center {
                Annotation("", coordinate: c, anchor: .center) {
                    Text(text(label, f)).font(DM.sans(CGFloat(DK.num(l["labelSize"]) ?? 11), .bold))
                        .foregroundStyle(FN.color(l["labelColor"], ctx, .cb6Navy)).shadow(color: .white, radius: 2)
                        .allowsHitTesting(false)
                }
            }
        }
    }

    private func text(_ t: String, _ f: FMLayer.Feat) -> String { var c = ctx; f.props.forEach { c[$0.key] = $0.value }; return FN.fill(t, c) }

    @ViewBuilder private func pinView(_ pin: [String: Any], _ f: FMLayer.Feat, fill: Color) -> some View {
        let size = CGFloat(DK.num(pin["size"]) ?? 22)
        let color = FN.color(pin["color"], ctx, fill == .clear ? .cb6Orange : fill)
        switch DK.str(pin["style"]) {
        case "image":
            if let ui = FN.image(text(DK.str(pin["image"]), f)) {
                Image(uiImage: ui).resizable().scaledToFit().frame(width: size, height: size)
                    .clipShape(RoundedRectangle(cornerRadius: CGFloat(DK.num(pin["corner"]) ?? size / 2)))
            } else { Circle().fill(color).frame(width: size * 0.6, height: size * 0.6).overlay(Circle().stroke(.white, lineWidth: 2)) }
        case "text":
            Text(text(DK.str(pin["text"]), f)).font(DM.sans(CGFloat(DK.num(pin["textSize"]) ?? 11), .bold)).foregroundStyle(.white)
                .padding(.horizontal, 7).padding(.vertical, 3).background(color, in: Capsule()).overlay(Capsule().stroke(.white, lineWidth: 1))
        case "marker":
            VStack(spacing: 0) {
                Image(systemName: DK.str(pin["symbol"]).isEmpty ? "mappin" : DK.str(pin["symbol"])).font(.system(size: size * 0.5, weight: .bold)).foregroundStyle(.white)
                    .frame(width: size, height: size).background(color, in: Circle()).overlay(Circle().stroke(.white, lineWidth: 2))
                Triangle().fill(color).frame(width: size * 0.4, height: size * 0.3)
            }
        default:
            if DK.str(pin["symbol"]).isEmpty {
                Circle().fill(color).frame(width: size * 0.6, height: size * 0.6).overlay(Circle().stroke(.white, lineWidth: 2))
            } else {
                Image(systemName: DK.str(pin["symbol"])).font(.system(size: size * 0.5, weight: .bold)).foregroundStyle(.white)
                    .frame(width: size, height: size).background(color, in: Circle()).overlay(Circle().stroke(.white, lineWidth: 2))
            }
        }
    }

    private func hit(_ c: CLLocationCoordinate2D, _ layers: [FMLayer]) -> (layer: Int, feat: Int)? {
        for i in layers.indices.reversed() where shown(i) {
            for (k, f) in layers[i].feats.enumerated() where f.rect.contains(MKMapPoint(c)) {
                if f.polys.contains(where: { FM.inside(c, $0) }) { return (i, k) }
            }
        }
        return nil
    }

    @ViewBuilder private func card(_ layers: [FMLayer]) -> some View {
        if let p = picked, layers.indices.contains(p.layer), layers[p.layer].feats.indices.contains(p.feat) {
            let l = layerSpecs[p.layer], f = layers[p.layer].feats[p.feat]
            let c = merged(f)
            if let node = l["tap"] as? [String: Any] {
                ZStack(alignment: .topTrailing) {
                    FileNode(node, ctx: c).frame(maxWidth: .infinity, alignment: .leading)
                        .padding(14).background(.white, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                        .shadow(color: .black.opacity(0.18), radius: 8, y: 2)
                    Button { picked = nil } label: { Image(systemName: "xmark.circle.fill").font(.system(size: 20)).foregroundStyle(Color.cb6Muted) }.padding(8)
                }
                .padding(10)
            }
        } else if let e = spec["tapEmpty"] as? [String: Any] {
            FileNode(e, ctx: ctx).padding(10)
        }
    }

    private var searchBox: some View {
        let scope: FindScope = {
            let s = DK.str(spec["searchScope"])
            if s.count == 3 { return .district(s) }
            if s.count == 1 { return .borough(s) }
            return .city
        }()
        let results = query.count > 2 && found?.label != query ? Array(AddressIndex.search(query, scope: scope).prefix(6)) : []
        return VStack(alignment: .leading, spacing: 0) {
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass").foregroundStyle(Color.cb6Muted)
                TextField(FN.fill(DK.str(spec["searchPrompt"]).isEmpty ? "Address, e.g. 250 Baltic Street" : DK.str(spec["searchPrompt"]), ctx), text: $query)
                    .font(DM.sans(16)).textInputAutocapitalization(.words).autocorrectionDisabled()
                if !query.isEmpty { Button { query = ""; found = nil } label: { Image(systemName: "xmark.circle.fill").foregroundStyle(Color.cb6Muted) } }
            }
            .padding(12).background(Color.white, in: RoundedRectangle(cornerRadius: 12)).overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.cb6Rule))
            ForEach(results, id: \.self) { m in
                Button {
                    found = m; query = m.label
                    position = .camera(MapCamera(centerCoordinate: m.coord, distance: DK.num(spec["searchDistance"]) ?? 900))
                    let layers = layerSpecs.map { FM.layer($0, ctx: ctx, store: store) }
                    picked = hit(m.coord, layers)
                } label: {
                    Text(m.label).font(DM.sans(15)).foregroundStyle(Color.cb6Ink).frame(maxWidth: .infinity, alignment: .leading).padding(.vertical, 10).padding(.horizontal, 12)
                }
                .buttonStyle(.plain)
                Divider()
            }
        }
    }

    private var toggles: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(Array(layerSpecs.indices), id: \.self) { i in
                    let l = layerSpecs[i], t = FN.fill(DK.str(l["title"]), ctx)
                    if !t.isEmpty, l["toggle"] as? Bool ?? true, FN.shows(l["when"], ctx) {
                        let c = FN.color(l["chip"] ?? l["stroke"] ?? l["fill"], ctx, .cb6Navy)
                        Button { on[id(i)] = !isOn(i) } label: {
                            HStack(spacing: 6) {
                                Circle().fill(isOn(i) ? c : .clear).overlay(Circle().stroke(c, lineWidth: 2)).frame(width: 12, height: 12)
                                Text(t).font(DM.sans(13, .bold)).foregroundStyle(Color.cb6Navy)
                            }
                            .padding(.horizontal, 12).padding(.vertical, 8)
                            .background(isOn(i) ? Color.white : Color.cb6Paper, in: Capsule()).overlay(Capsule().stroke(isOn(i) ? c : Color.cb6Rule, lineWidth: 1.5))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }

    private var legend: some View {
        let rows: [(Color, String)] = layerSpecs.indices.filter { isOn($0) }.flatMap { i -> [(Color, String)] in
            (layerSpecs[i]["legend"] as? [[Any]] ?? []).compactMap { r in r.count == 2 ? (FN.color(r[0], ctx, .cb6Navy), FN.fill(DK.str(r[1]), ctx)) : nil }
        }
        return LazyVGrid(columns: [GridItem(.adaptive(minimum: 140), alignment: .leading)], alignment: .leading, spacing: 6) {
            ForEach(Array(rows.enumerated()), id: \.offset) { _, r in
                HStack(spacing: 6) { RoundedRectangle(cornerRadius: 3).fill(r.0).frame(width: 14, height: 14); Text(r.1).font(DM.sans(12)).foregroundStyle(Color.cb6Ink) }
            }
        }
    }
}

private struct Triangle: Shape {
    func path(in r: CGRect) -> Path { var p = Path(); p.move(to: CGPoint(x: r.minX, y: r.minY)); p.addLine(to: CGPoint(x: r.maxX, y: r.minY)); p.addLine(to: CGPoint(x: r.midX, y: r.maxY)); p.closeSubpath(); return p }
}

/// Where a tap goes, as a pushed screen: the same destinations as FileLink.
struct FileNodeDest: View {
    let dest: String
    var body: some View {
        let d = dest
        if d.hasPrefix("web:") { SitePageView(path: String(d.dropFirst(4))) }
        else if d.hasPrefix("dk:") { DKRoute(spec: String(d.dropFirst(3))).view }
        else { ScreenRouter.view(d.hasPrefix("screen:") ? String(d.dropFirst(7)) : d) }
    }
}

/// A whole screen from screens.json "nodes": {"<name>": node}; "node:<name>" opens it, "replace" can put it in place of any screen.
struct FileNodeScreen: View {
    let name: String
    @ObservedObject private var ui = UIConfig.shared
    var body: some View {
        let n = ((ui.file("screens")["nodes"] as? [String: Any])?[name] as? [String: Any]) ?? [:]
        let title = FN.fill(DK.str(n["title"]), [:])
        Group {
            if n["scroll"] as? Bool ?? true {
                ScrollView { FileNode(n).padding(.horizontal, CGFloat(DK.num(n["side"]) ?? 16)).padding(.vertical, 12) }
            } else {
                FileNode(n)
            }
        }
        .background(Color.cb6Paper.ignoresSafeArea())
        .navigationTitle(title)
        .navigationBarTitleDisplayMode(.inline)
    }
}
