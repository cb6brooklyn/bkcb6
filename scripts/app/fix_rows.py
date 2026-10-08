"""The Home block card's rows come from the file: lists.json "MyBlock.rows" is the list, in order, of
{"id", "title", "icon", "color"}; ids are the built-in rows (trash, parking, polls, precinct, subway, reps, ballot, park,
nearby) or "field:<key>" for any text field of the block's data (zones, hist, school, sector, ballot29, ...), "button"
(title, dest: feeds | card | web:<site path> | dk:<route> | screen:<key> | https://...), "text" (title, text or key) and
"web" (page, height), each at its spot in the list. A title, icon (SF symbol name) or color (#hex) in the file replaces the code's. Replaces the code-only rows and the ballot row of
fix_ballot.py. fix_rows.py <app dir>"""
import sys, os
R = sys.argv[1]
p = os.path.join(R, 'App/Views/ExploreViews.swift'); s = open(p).read()
if 'MyBlock.rows' in s: print('already'); sys.exit()
old_rows = s[s.index('                if let card = s.card { facts(card) }\n'):s.index('                HStack(spacing: 8) {\n                    if let b = s.block {')]
assert 'Who represents you' in old_rows and 'Within 150 m' in old_rows, 'rows block'
s = s.replace(old_rows, '                rows(s)\n', 1)
# the old facts(card) becomes row(s, id)
i = s.index('    @ViewBuilder private func facts(_ card: BlockCard) -> some View {')
j = s.index('    private func fact(_ sym: String, _ color: Color, _ title: String, _ text: String) -> some View {')
new = '''    /// One row of the card: the icon, its color, the heading and the text.
    private struct RowSpec { let sym: String; let color: Color; let title: String; let text: String }

    /// The rows the code draws when lists.json "MyBlock.rows" has no entry, in this order.
    static let defaultRows: [[String: Any]] = [["id": "trash"], ["id": "parking"], ["id": "polls"], ["id": "precinct"], ["id": "subway"], ["id": "reps"], ["id": "ballot"], ["id": "park"], ["id": "nearby"]]

    /// The card's rows, in the file's order: lists.json "MyBlock.rows" = [{"id": "trash", "title": "...", "icon": "trash.fill", "color": "#1e9e59"}, ...].
    /// ids: trash, parking, polls, precinct, subway, reps, ballot, park, nearby, or "field:<key>" for any text field of the block's data.
    /// A title, icon or color in the file replaces the code's; a row the data has nothing for draws nothing.
    @ViewBuilder private func rows(_ s: MyBlockSummary) -> some View {
        ForEach(Array(Lists.objects("MyBlock.rows", Self.defaultRows).enumerated()), id: \\.offset) { _, r in
            let id = DK.str(r["id"]), icon = DK.str(r["icon"]), color = DK.str(r["color"]), title = DK.str(r["title"])
            if id == "button" {
                // {"id": "button", "title": "...", "dest": "feeds" | "web:<site path>" | "dk:<route>" | "screen:<key>"}: a button at this spot in the card.
                rowButton(title, DK.str(r["dest"]), color)
            } else if id == "text" {
                // {"id": "text", "title": "...", "text": "..."} or "key": a text.json key: a paragraph at this spot.
                let body = DK.str(r["key"]).isEmpty ? DK.str(r["text"]) : T(DK.str(r["key"]), "")
                if !body.isEmpty { fact(icon.isEmpty ? "text.alignleft" : icon, color.isEmpty ? Color.cb6Navy : DK.hex(color), title, body) }
            } else if id == "web" {
                // {"id": "web", "page": "<site path>", "height": 300}: a page of the site at this spot, with {ADDRESS} {SLUG}... filled in.
                SitePageWeb(path: DK.str(r["page"])).frame(height: DK.num(r["height"]) ?? 300)
                    .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            } else if let spec = row(s, id), !spec.text.isEmpty {
                fact(icon.isEmpty ? spec.sym : icon, color.isEmpty ? spec.color : DK.hex(color), title.isEmpty ? spec.title : title, spec.text)
            }
        }
    }

    /// A button from the file, anywhere in the card: the destinations the block card's buttons take.
    @ViewBuilder private func rowButton(_ title: String, _ dest: String, _ color: String) -> some View {
        let label = Text(title).font(DM.sans(13, .bold)).foregroundStyle(.white).lineLimit(1).minimumScaleFactor(0.8)
            .padding(.horizontal, 12).padding(.vertical, 9).frame(maxWidth: .infinity).background(color.isEmpty ? Color.cb6Navy : DK.hex(color), in: Capsule())
        if dest == "feeds", let c = coord { NavigationLink { FeedsView(startPin: c) } label: { label }.buttonStyle(.plain) }
        else if dest == "card", let b = summary?.block { NavigationLink { BlockCardView(block: b) } label: { label }.buttonStyle(.plain) }
        else if dest.hasPrefix("web:") { NavigationLink { SitePageView(path: String(dest.dropFirst(4))) } label: { label }.buttonStyle(.plain) }
        else if dest.hasPrefix("dk:") { NavigationLink { DKRoute(spec: String(dest.dropFirst(3))).view } label: { label }.buttonStyle(.plain) }
        else if dest.hasPrefix("screen:") { NavigationLink(value: String(dest.dropFirst(7))) { label }.buttonStyle(.plain) }
        else if dest.hasPrefix("http"), let u = URL(string: dest) { Link(destination: u) { label } }
        else { label }
    }

    private func row(_ s: MyBlockSummary, _ id: String) -> RowSpec? {
        let card = s.card
        switch id {
        case "trash":
            guard let d = card?.dsny.first else { return nil }
            return RowSpec(sym: "trash.fill", color: MapStyle.color("ExploreViews.c.9c287162", Color(red: 0.10, green: 0.62, blue: 0.35)), title: Copy.t("ExploreViews.9c5a6eb4", "Trash and recycling"),
                           text: [Copy.f("ExploreViews.1813c302", "Trash {0}", d.refuse), Copy.f("ExploreViews.14712a2b", "Recycling {0}", d.recycling), d.organics.isEmpty ? "" : Copy.f("ExploreViews.f4cb2cb9", "Compost {0}", d.organics)].filter { !$0.isEmpty && !$0.hasSuffix(" ") }.joined(separator: " · "))
        case "parking":
            guard let card, let a = card.asp.first else { return nil }
            return RowSpec(sym: "car.fill", color: MapStyle.color("ExploreViews.c.fb9aadb1", Color(red: 0.16, green: 0.40, blue: 0.85)), title: Copy.t("ExploreViews.966c2cc9", "Alternate side parking"),
                           text: card.asp.count > 1 ? Copy.f("ExploreViews.854aed59", "{0}: {1} ({2} rules on this block)", a.side, a.sched, card.asp.count) : "\\(a.side): \\(a.sched)")
        case "polls":
            guard let e = card?.eds.first, !e.site.isEmpty else { return nil }
            return RowSpec(sym: "checkmark.seal.fill", color: MapStyle.color("ExploreViews.c.069b4658", Color(red: 0.75, green: 0.13, blue: 0.24)), title: Copy.t("ExploreViews.baf24b83", "Election Day poll site"), text: e.site.joined(separator: ", "))
        case "precinct":
            guard let p = card?.precinct.first, !p.isEmpty else { return nil }
            return RowSpec(sym: "shield.fill", color: Color.cb6Navy, title: Copy.t("ExploreViews.bde603b2", "Police precinct"), text: p)
        case "subway":
            guard let t = card?.subway.first else { return nil }
            return RowSpec(sym: "tram.fill", color: MapStyle.color("ExploreViews.c.90aad496", DK.hex("#0039A6")), title: Copy.t("ExploreViews.a8ce893a", "Nearest subway"),
                           text: Copy.f("ExploreViews.ee7b3360", "{0} ({1}), {2} min walk", t.name, t.routes.joined(separator: " "), t.minutes))
        case "reps":
            guard !s.reps.isEmpty else { return nil }
            return RowSpec(sym: "person.2.fill", color: Color.cb6Orange, title: Copy.t("ExploreViews.9e73a044", "Who represents you"), text: s.reps.map { "\\($0.title): \\($0.name)" }.joined(separator: "\\n"))
        case "ballot":
            // The sample ballot for this block, the blocks file's ballot26 lines, then the statewide line (blank in copy.json drops it).
            guard let card, !card.ballot26.isEmpty else { return nil }
            let statewide = Copy.t("ExploreViews.637639ad", "Plus statewide: Governor, Lieutenant Governor, Attorney General, State Comptroller.")
            return RowSpec(sym: "checkmark.seal.fill", color: MapStyle.color("ExploreViews.c.069b4658", Color(red: 0.75, green: 0.13, blue: 0.24)), title: Copy.t("ExploreViews.b2a7c3e1", "On your ballot, Tuesday, November 3"),
                           text: (card.ballot26 + (statewide.isEmpty ? [] : [statewide])).joined(separator: "\\n"))
        case "park":
            guard let p = s.park, p.meters < 3000 else { return nil }
            return RowSpec(sym: "tree.fill", color: Color.parksGreen, title: Copy.t("ExploreViews.2c877ae9", "Nearest park"),
                           text: Copy.f("ExploreViews.51b51613", "{0}, about {1} minute{2} on foot", p.name, max(1, Int((Double(p.meters) / 80).rounded())), Int((Double(p.meters) / 80).rounded()) == 1 ? "" : "s"))
        case "nearby":
            guard s.cd == "306" else { return nil }
            return RowSpec(sym: "phone.fill", color: MapStyle.color("ExploreViews.c.81247020", Color(red: 0.93, green: 0.42, blue: 0.10)), title: Copy.t("ExploreViews.ebecdf6c", "Within 150 m"),
                           text: Copy.f("ExploreViews.049a94bb", "{0} 311 complaint{1} in the last 30 days · {2} permit{3} in effect today", s.near311, s.near311 == 1 ? "" : "s", s.nearPermits, s.nearPermits == 1 ? "" : "s"))
        default:
            // "field:<key>": any field of the block's data that is text, a number, a list of text, or a list of objects (one line each).
            guard id.hasPrefix("field:"), let v = card?.raw[String(id.dropFirst(6))] else { return nil }
            return RowSpec(sym: "doc.text.fill", color: Color.cb6Navy, title: String(id.dropFirst(6)), text: BlockCard.text(v))
        }
    }

'''
s = s[:i] + new + s[j:]
open(p, 'w').write(s)
print('rows ok')
# the card keeps its raw data for "field:" rows
b = os.path.join(R, 'App/Views/BlockCards.swift'); t = open(b).read()
if 'let raw: [String: Any]' not in t:
    t = t.replace('    let subway: [Subway]\n\n    init?(_ o: [String: Any]) {\n', '''    let subway: [Subway]
    /// The block's data as the file holds it, for rows the file names by key.
    let raw: [String: Any]

    /// A field as one text: a string, a number, a list of strings (one per line) or a list of objects (each object's values on a line).
    static func text(_ v: Any) -> String {
        if let s = v as? String { return s }
        if let n = v as? NSNumber { return n.stringValue }
        if let a = v as? [String] { return a.joined(separator: "\\n") }
        if let a = v as? [[String: Any]] {
            return a.map { o in o.keys.sorted().compactMap { k -> String? in let x = DK.str(o[k]); return x.isEmpty ? nil : x }.joined(separator: " · ") }.joined(separator: "\\n")
        }
        if let a = v as? [Any] { return a.map { DK.str($0) }.filter { !$0.isEmpty }.joined(separator: "\\n") }
        return DK.str(v)
    }

    init?(_ o: [String: Any]) {
        raw = o
''', 1)
    assert 'raw = o' in t, 'BlockCard raw'
    open(b, 'w').write(t)
print('raw ok')
