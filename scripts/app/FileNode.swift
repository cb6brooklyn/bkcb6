import SwiftUI
import UIKit

// Anything on a screen, described in a file. A node is a JSON object with a "type" and its own settings; nodes nest.
// Home (home.json, a section {"kind": "node", "node": {...}}) and every screen (screens.json, a part {"kind": "node", "node": {...}})
// draw them natively, so a new card, button, row, list or layout is a file change, never a build.
//
// types   v | h | z (stacks; "children", "spacing", "align"), text ("text"), image ("src": a pack path or https URL, or "tile": a tile
//         image name), symbol ("name"), spacer ("min"), divider, grid ("columns", "children"), web ("page", "height"),
//         tools ("list"), button ("text", "dest"), each ("data", "item": the node drawn once per row), part (a named piece of the
//         app's own code, see FileNodePart).
// every node: "when" (show only if), "data" (rows from a file or a source; the first row fills {fields}), "dest" (tap target:
//         any screen key, "web:<path>", "dk:<route>", "https://..."), "pad", "bg" (color or [top, bottom] gradient), "fg", "corner",
//         "border", "borderWidth", "width", "height", "minHeight", "maxWidth" ("full"), "align", "opacity", "shadow", "top" (space above).
// text:   "size", "weight" (regular, medium, bold), "mono", "color", "lines", "tracking", "upper", "textAlign", "scale" (shrink to fit).
// {...}:  {field}, {field|date:MMM d}, {field|weekday}, {field|time}, {field|days} (days until), {field|upper}, {field|default:x},
//         {@today|date:EEEE}, {@board}, {@boardShort}, {@place.label}, {@place.cd}, {@app}.
// "when": {"before": "2026-11-04"}, {"after": "..."}, {"app": "cb6"|[...]}, {"board": "306"|[...]}, {"notBoard": ...},
//         {"place": true|false}, {"has": "field"}, {"empty": "field"}, {"weekday": [1..7]}; a list means all of them.
// "data": {"file": "civic/cal/calendar-bk.json", "at": "events", "where": {"k": "board", "cd": "@board"}, "match": {"l": "regex"},
//         "upcoming": "d", "sort": "d" | "-d", "limit": 1} or {"source": "nextmeeting"} (FileNodeSources); no rows hides the node
//         unless it has "empty": a node to draw instead.

enum FN {
    private static var cache: [String: Any] = [:]
    private static let lock = NSLock()
    private static let watch: Any = NotificationCenter.default.addObserver(forName: DataPack.notification, object: nil, queue: .main) { _ in
        FN.lock.lock(); FN.cache = [:]; FN.lock.unlock()
    }
    static func json(_ rel: String) -> Any? {
        _ = watch
        lock.lock(); if let c = cache[rel] { lock.unlock(); return c is NSNull ? nil : c }; lock.unlock()
        var out: Any? = nil
        for u in [DataPack.url(rel), DataPack.bundled(rel)].compactMap({ $0 }) {
            if let d = try? Data(contentsOf: u), let o = try? JSONSerialization.jsonObject(with: d) { out = o; break }
        }
        lock.lock(); cache[rel] = out ?? NSNull(); lock.unlock()
        return out
    }
    static func image(_ rel: String) -> UIImage? {
        for u in [DataPack.url(rel), DataPack.bundled(rel)].compactMap({ $0 }) { if let i = UIImage(contentsOfFile: u.path) { return i } }
        return nil
    }

    // MARK: context

    static var board: String {
        let b = Hook.value("-board") ?? UserDefaults.standard.string(forKey: "bk.board") ?? ""
        return b.isEmpty && UIConfig.app == "cb6" ? "306" : b
    }
    static var nyc: TimeZone { TimeZone(identifier: "America/New_York") ?? .current }
    static var cal: Calendar { var c = Calendar(identifier: .gregorian); c.timeZone = nyc; return c }
    static var today: Date { cal.startOfDay(for: Date()) }

    static func special(_ key: String) -> Any? {
        switch key {
        case "@today": return Date()
        case "@board": return board
        case "@boardShort": return board == "306" ? "CB6" : boardShort(board)
        case "@app": return UIConfig.app
        case "@place.label": return MyPlace.current?.label ?? ""
        case "@place.cd": return MyPlace.current.map { String($0.cd) } ?? ""
        case "@place.slug": return MyPlace.current?.slug ?? ""
        default: return nil
        }
    }
    static func boardShort(_ cd: String) -> String {
        guard cd.count == 3, let n = Int(cd.suffix(2)) else { return cd }
        let b = ["1": "MN", "2": "BX", "3": "BK", "4": "QN", "5": "SI"][String(cd.prefix(1))] ?? ""
        return "\(b)CB\(n)"
    }

    static func lookup(_ key: String, _ ctx: [String: Any]) -> Any? {
        if key.hasPrefix("@") { return special(key) }
        var node: Any? = ctx
        for part in key.split(separator: ".") {
            if let d = node as? [String: Any] { node = d[String(part)] }
            else if let a = node as? [Any], let i = Int(part), a.indices.contains(i) { node = a[i] }
            else { return nil }
        }
        return node
    }

    static func date(_ v: Any?) -> Date? {
        if let d = v as? Date { return d }
        let s = DK.str(v); guard s.count >= 10 else { return nil }
        let f = DateFormatter(); f.locale = Locale(identifier: "en_US_POSIX"); f.timeZone = nyc
        for fmt in ["yyyy-MM-dd'T'HH:mm:ssXXXXX", "yyyy-MM-dd'T'HH:mm:ss", "yyyy-MM-dd'T'HH:mm", "yyyy-MM-dd"] {
            f.dateFormat = fmt
            if let d = f.date(from: fmt == "yyyy-MM-dd" ? String(s.prefix(10)) : s) { return d }
        }
        return nil
    }

    static func string(_ v: Any?) -> String {
        if let d = v as? Date { let f = DateFormatter(); f.timeZone = nyc; f.dateFormat = "yyyy-MM-dd"; return f.string(from: d) }
        return DK.str(v)
    }

    /// "{field|filter:arg|filter}" filled from the row and the app's context.
    static func fill(_ s: String, _ ctx: [String: Any]) -> String {
        guard s.contains("{") else { return s }
        var out = ""; var i = s.startIndex
        while i < s.endIndex {
            if s[i] == "{", let j = s[i...].firstIndex(of: "}") {
                let expr = String(s[s.index(after: i)..<j])
                out += apply(expr, ctx)
                i = s.index(after: j)
            } else { out.append(s[i]); i = s.index(after: i) }
        }
        return out
    }
    static func apply(_ expr: String, _ ctx: [String: Any]) -> String {
        let parts = expr.split(separator: "|", omittingEmptySubsequences: false).map(String.init)
        var v: Any? = lookup(parts[0].trimmingCharacters(in: .whitespaces), ctx)
        for p in parts.dropFirst() {
            let (name, arg): (String, String) = {
                if let c = p.firstIndex(of: ":") { return (String(p[..<c]), String(p[p.index(after: c)...])) }
                return (p, "")
            }()
            switch name {
            case "date":
                if let d = date(v) { let f = DateFormatter(); f.locale = Locale(identifier: "en_US"); f.timeZone = nyc; f.dateFormat = arg.isEmpty ? "MMM d" : arg; v = f.string(from: d) }
            case "weekday":
                if let d = date(v) { let f = DateFormatter(); f.locale = Locale(identifier: "en_US"); f.timeZone = nyc; f.dateFormat = "EEEE"; v = f.string(from: d) }
            case "days":
                if let d = date(v) { v = String(max(0, cal.dateComponents([.day], from: today, to: cal.startOfDay(for: d)).day ?? 0)) }
            case "time":
                let t = string(v).trimmingCharacters(in: .whitespaces)
                if let m = t.range(of: #"(\d{1,2})(:(\d\d))?\s*([ap])\.?m\.?"#, options: [.regularExpression, .caseInsensitive]) {
                    let raw = String(t[m]).lowercased().replacingOccurrences(of: ".", with: "").replacingOccurrences(of: " ", with: "")
                    let ap = raw.hasSuffix("pm") ? "PM" : "AM"
                    let hm = raw.dropLast(2); v = hm.contains(":") ? "\(hm) \(ap)" : "\(hm):00 \(ap)"
                } else { v = t }
            case "upper": v = string(v).uppercased()
            case "lower": v = string(v).lowercased()
            case "default": if string(v).isEmpty { v = arg }
            case "first": v = string(v).components(separatedBy: arg.isEmpty ? " " : arg).first ?? ""
            default: break
            }
        }
        return string(v)
    }

    // MARK: rows

    @MainActor static func rows(_ spec: [String: Any], _ ctx: [String: Any], store: DataStore) -> [[String: Any]] {
        var rows: [[String: Any]]
        if let src = spec["source"] as? String {
            rows = FileNodeSources.rows(src, spec: spec, ctx: ctx, store: store)
        } else {
            var node: Any? = json(fill(DK.str(spec["file"]), ctx))
            let at = DK.str(spec["at"])
            if !at.isEmpty { for p in at.split(separator: ".") { node = (node as? [String: Any])?[String(p)] } }
            if let a = node as? [[String: Any]] { rows = a }
            else if let d = node as? [String: Any] { rows = d.keys.sorted().compactMap { k in (d[k] as? [String: Any]).map { var r = $0; r["@key"] = k; return r } } }
            else { rows = [] }
        }
        if let w = spec["where"] as? [String: Any] {
            rows = rows.filter { r in w.allSatisfy { k, want in
                let have = string(r[k])
                if let list = want as? [Any] { return list.contains { fill(DK.str($0), ctx) == have } }
                return fill(DK.str(want), ctx) == have
            } }
        }
        if let m = spec["match"] as? [String: Any] {
            rows = rows.filter { r in m.allSatisfy { k, pat in string(r[k]).range(of: DK.str(pat), options: [.regularExpression, .caseInsensitive]) != nil } }
        }
        let up = DK.str(spec["upcoming"])
        if !up.isEmpty { rows = rows.filter { (date($0[up]).map { cal.startOfDay(for: $0) } ?? .distantPast) >= today } }
        let past = DK.str(spec["past"])
        if !past.isEmpty { rows = rows.filter { (date($0[past]) ?? .distantFuture) < today } }
        var sort = DK.str(spec["sort"])
        if !sort.isEmpty {
            let desc = sort.hasPrefix("-"); if desc { sort.removeFirst() }
            rows.sort { a, b in
                let x = string(a[sort]), y = string(b[sort])
                if let p = Double(x), let q = Double(y) { return desc ? p > q : p < q }
                return desc ? x > y : x < y
            }
        }
        if let n = DK.num(spec["limit"]), n >= 0 { rows = Array(rows.prefix(Int(n))) }
        return rows
    }

    // MARK: when

    static func shows(_ when: Any?, _ ctx: [String: Any]) -> Bool {
        if let list = when as? [Any] { return list.allSatisfy { shows($0, ctx) } }
        guard let w = when as? [String: Any] else { return true }
        func any(_ v: Any?, _ x: String) -> Bool { (v as? [Any])?.contains { fill(DK.str($0), ctx) == x } ?? (fill(DK.str(v), ctx) == x) }
        for (k, v) in w {
            switch k {
            case "before": if let d = date(fill(DK.str(v), ctx)), Date() >= d { return false }
            case "after": if let d = date(fill(DK.str(v), ctx)), Date() < d { return false }
            case "app": if !any(v, UIConfig.app) { return false }
            case "board": if !any(v, board) { return false }
            case "notBoard": if any(v, board) { return false }
            case "place": if (v as? Bool ?? true) != (MyPlace.current != nil) { return false }
            case "has": if apply(DK.str(v), ctx).isEmpty { return false }
            case "empty": if !apply(DK.str(v), ctx).isEmpty { return false }
            case "weekday": let wd = cal.component(.weekday, from: Date()); if !((v as? [Any])?.contains { Int(DK.str($0)) == wd } ?? (Int(DK.str(v)) == wd)) { return false }
            default: break
            }
        }
        return true
    }

    // MARK: style

    static func color(_ v: Any?, _ ctx: [String: Any], _ fallback: Color) -> Color {
        let s = fill(DK.str(v), ctx)
        switch s {
        case "": return fallback
        case "navy": return .cb6Navy
        case "navyDeep": return .cb6NavyDeep
        case "orange": return .cb6Orange
        case "paper": return .cb6Paper
        case "ink": return .cb6Ink
        case "muted": return .cb6Muted
        case "rule": return .cb6Rule
        case "white": return .white
        case "clear": return .clear
        default:
            if s.hasPrefix("theme.") { return MapStyle.color(s, fallback) }
            return DK.hex(s)
        }
    }
    static func edges(_ v: Any?) -> EdgeInsets? {
        if let n = DK.num(v) { let c = CGFloat(n); return EdgeInsets(top: c, leading: c, bottom: c, trailing: c) }
        guard let a = v as? [Any] else { return nil }
        let n = a.compactMap { DK.num($0) }.map { CGFloat($0) }
        if n.count == 2 { return EdgeInsets(top: n[0], leading: n[1], bottom: n[0], trailing: n[1]) }
        if n.count == 4 { return EdgeInsets(top: n[0], leading: n[1], bottom: n[2], trailing: n[3]) }
        return nil
    }
    static func hAlign(_ s: String) -> HorizontalAlignment { s == "center" ? .center : s == "trailing" ? .trailing : .leading }
    static func vAlign(_ s: String) -> VerticalAlignment { s == "top" ? .top : s == "bottom" ? .bottom : s == "baseline" ? .firstTextBaseline : .center }
    static func frameAlign(_ s: String) -> Alignment {
        switch s {
        case "center": return .center
        case "trailing": return .trailing
        case "top": return .top
        case "bottom": return .bottom
        case "topTrailing": return .topTrailing
        case "bottomLeading": return .bottomLeading
        case "bottomTrailing": return .bottomTrailing
        case "leading": return .leading
        default: return .topLeading
        }
    }
    static func weight(_ s: String) -> Font.Weight { s == "bold" ? .bold : s == "medium" ? .medium : s == "semibold" ? .semibold : .regular }
}

/// One node from a file, with its rows and context.
struct FileNode: View {
    let n: [String: Any]
    var ctx: [String: Any] = [:]
    @EnvironmentObject var store: DataStore
    @ObservedObject private var ui = UIConfig.shared

    init(_ n: [String: Any], ctx: [String: Any] = [:]) { self.n = n; self.ctx = ctx }

    var body: some View {
        _ = ui.version
        return resolved
    }

    private var resolved: AnyView {
        if !FN.shows(n["when"], ctx) { return AnyView(EmptyView()) }
        if let spec = n["data"] as? [String: Any], DK.str(n["type"]) != "each" {
            let rows = FN.rows(spec, ctx, store: store)
            if let first = rows.first {
                var c = ctx; first.forEach { c[$0.key] = $0.value }; c["@rows"] = rows; c["@count"] = rows.count
                return AnyView(FileNode(strip(n), ctx: c))
            }
            if let e = n["empty"] as? [String: Any] { return AnyView(FileNode(e, ctx: ctx)) }
            return AnyView(EmptyView())
        }
        return AnyView(styled(content))
    }

    private func strip(_ n: [String: Any]) -> [String: Any] { var m = n; m["data"] = nil; m["when"] = nil; return m }
    private func s(_ k: String) -> String { FN.fill(DK.str(n[k]), ctx) }
    private func f(_ k: String) -> CGFloat? { DK.num(FN.fill(DK.str(n[k]), ctx)).map { CGFloat($0) } }
    private var kids: [[String: Any]] { n["children"] as? [[String: Any]] ?? [] }

    @ViewBuilder private var content: some View {
        let type = DK.str(n["type"])
        switch type {
        case "h":
            HStack(alignment: FN.vAlign(s("align")), spacing: f("spacing") ?? 8) { ForEach(Array(kids.enumerated()), id: \.offset) { _, k in FileNode(k, ctx: ctx) } }
        case "z":
            ZStack(alignment: FN.frameAlign(s("align"))) { ForEach(Array(kids.enumerated()), id: \.offset) { _, k in FileNode(k, ctx: ctx) } }
        case "text":
            text(s("text"))
        case "button":
            text(s("text"))
                .padding(.horizontal, 16).padding(.vertical, 10)
                .frame(maxWidth: s("maxWidth") == "full" ? .infinity : nil)
                .background(FN.color(n["bg"], ctx, .cb6Navy), in: Capsule())
                .overlay(Capsule().stroke(FN.color(n["border"], ctx, .clear), lineWidth: f("borderWidth") ?? 2))
        case "image":
            image
        case "symbol":
            Image(systemName: s("name").isEmpty ? "circle" : s("name"))
                .font(.system(size: f("size") ?? 16, weight: FN.weight(s("weight").isEmpty ? "bold" : s("weight"))))
                .foregroundStyle(FN.color(n["color"], ctx, .cb6Navy))
        case "spacer":
            Spacer(minLength: f("min") ?? 0)
        case "divider":
            Rectangle().fill(FN.color(n["color"], ctx, .cb6Rule)).frame(height: f("thickness") ?? 1)
        case "grid":
            let cols = max(1, Int(f("columns") ?? 2))
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: f("spacing") ?? 10, alignment: .top), count: cols), alignment: .leading, spacing: f("spacing") ?? 10) {
                ForEach(Array(kids.enumerated()), id: \.offset) { _, k in FileNode(k, ctx: ctx) }
            }
        case "each":
            let rows = (n["data"] as? [String: Any]).map { FN.rows($0, ctx, store: store) } ?? []
            let item = n["item"] as? [String: Any] ?? [:]
            let cols = Int(f("columns") ?? 0)
            if rows.isEmpty, let e = n["empty"] as? [String: Any] { FileNode(e, ctx: ctx) }
            else if cols > 0 {
                LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: f("spacing") ?? 10, alignment: .top), count: cols), alignment: .leading, spacing: f("spacing") ?? 10) {
                    ForEach(Array(rows.enumerated()), id: \.offset) { i, r in FileNode(item, ctx: merge(r, i)) }
                }
            } else if s("axis") == "h" {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(alignment: .top, spacing: f("spacing") ?? 10) { ForEach(Array(rows.enumerated()), id: \.offset) { i, r in FileNode(item, ctx: merge(r, i)) } }
                }
            } else {
                VStack(alignment: FN.hAlign(s("align")), spacing: f("spacing") ?? 8) { ForEach(Array(rows.enumerated()), id: \.offset) { i, r in FileNode(item, ctx: merge(r, i)) } }
            }
        case "web":
            SitePageWeb(path: s("page")).frame(height: f("height") ?? 320)
        case "tools":
            ToolGrid(title: s("title"), tools: Tools.list(s("list")), tap: { _ in }, link: ScreenRouter.tool)
        case "part":
            FileNodePart(name: s("name"))
        default:
            VStack(alignment: FN.hAlign(s("align")), spacing: f("spacing") ?? 6) { ForEach(Array(kids.enumerated()), id: \.offset) { _, k in FileNode(k, ctx: ctx) } }
        }
    }

    private func merge(_ r: [String: Any], _ i: Int) -> [String: Any] { var c = ctx; r.forEach { c[$0.key] = $0.value }; c["@index"] = i; c["@n"] = i + 1; return c }

    private func text(_ t: String) -> some View {
        let size = f("size") ?? 15, w = FN.weight(s("weight"))
        let shown = (n["upper"] as? Bool ?? false) ? t.uppercased() : t
        let align: TextAlignment = s("textAlign") == "center" ? .center : s("textAlign") == "trailing" ? .trailing : .leading
        return Text(shown)
            .font((n["mono"] as? Bool ?? false) ? DM.mono(size, w == .regular ? .regular : .medium) : DM.sans(size, w))
            .tracking(f("tracking") ?? 0)
            .foregroundStyle(FN.color(n["color"] ?? n["fg"], ctx, .cb6Ink))
            .multilineTextAlignment(align)
            .lineLimit(f("lines").map { Int($0) })
            .minimumScaleFactor(f("scale") ?? 1)
            .fixedSize(horizontal: false, vertical: f("lines") == nil)
    }

    @ViewBuilder private var image: some View {
        let src = s("src"), tile = s("tile")
        let fit = s("fit") == "fill" ? ContentMode.fill : ContentMode.fit
        Group {
            if !tile.isEmpty, let ui = FN.image("civic/icons/\(tile).png") ?? FN.image("civic/icons/\(tile).jpg") {
                Image(uiImage: ui).resizable().aspectRatio(contentMode: fit)
            } else if src.hasPrefix("http"), let u = URL(string: src) {
                AsyncImage(url: u) { i in i.resizable().aspectRatio(contentMode: fit) } placeholder: { Color.cb6Rule.opacity(0.3) }
            } else if let ui = FN.image(src) {
                Image(uiImage: ui).resizable().aspectRatio(contentMode: fit)
            } else {
                Color.clear
            }
        }
        .frame(width: f("width"), height: f("height"))
        .clipped()
    }

    @ViewBuilder private func styled<V: View>(_ v: V) -> some View {
        let corner = f("corner") ?? 0
        let shape = RoundedRectangle(cornerRadius: corner, style: .continuous)
        let core = v
            .padding(FN.edges(n["pad"]) ?? EdgeInsets())
            .frame(minHeight: f("minHeight"))
            .frame(maxWidth: s("maxWidth") == "full" || s("width") == "full" ? .infinity : nil, alignment: FN.frameAlign(s("align").isEmpty ? "topLeading" : s("align")))
            .frame(width: s("width") == "full" ? nil : f("width"), height: DK.str(n["type"]) == "image" ? nil : f("height"))
            .background(background, in: shape)
            .overlay(shape.stroke(FN.color(n["border"], ctx, .clear), lineWidth: n["border"] == nil ? 0 : (f("borderWidth") ?? 2)))
            .clipShape(shape)
            .shadow(color: .black.opacity((n["shadow"] as? Bool ?? false) ? 0.12 : 0), radius: 6, y: 2)
            .opacity(f("opacity") ?? 1)
            .padding(.top, f("top") ?? 0)
        let dest = s("dest")
        if dest.isEmpty { core } else { FileLink(dest) { core } }
    }

    private var background: AnyShapeStyle {
        if let a = n["bg"] as? [Any], a.count >= 2 {
            return AnyShapeStyle(LinearGradient(colors: a.map { FN.color($0, ctx, .clear) }, startPoint: .topLeading, endPoint: .bottomTrailing))
        }
        if DK.str(n["type"]) == "button" { return AnyShapeStyle(Color.clear) }
        return AnyShapeStyle(FN.color(n["bg"], ctx, .clear))
    }
}
