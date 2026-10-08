"""The block card's sources from the file: lists.json "MyBlock.sources" adds NYC Open Data sources (dataset, filter,
fields, templates) without a build, and "MyBlock.sourcesOff" switches the built-in ones off by name
(sapo, film, filmdata, closures, permits, filings). fix_blocksources.py <app dir>"""
import sys, os
p = os.path.join(sys.argv[1], 'App/Views/MyBlock.swift'); s = open(p).read()
if 'MyBlock.sources' in s: print('already'); sys.exit()
# 1. the switches on the built-in sources
reps = [
    ('        if let rows = await LotRecords.all("tvpp-9vvx"', '        if !off.contains("sapo"), let rows = await LotRecords.all("tvpp-9vvx"'),
    ('        if let u = URL(string: "https://bkcb6.app/filmingpermits/permits.json"),', '        if !off.contains("film"), let u = URL(string: "https://bkcb6.app/filmingpermits/permits.json"),'),
    ('        if let rows = await LotRecords.all("tg4x-b46p"', '        if !off.contains("filmdata"), let rows = await LotRecords.all("tg4x-b46p"'),
    ('        if let rows = await LotRecords.all("i6b5-j7bu"', '        if !off.contains("closures"), let rows = await LotRecords.all("i6b5-j7bu"'),
    ('        if let rows = await LotRecords.all("tqtj-sjs8"', '        if !off.contains("permits"), let rows = await LotRecords.all("tqtj-sjs8"'),
    ('        if place.bbl.count == 10, let blk = Int(place.bbl.dropFirst().prefix(5)) {', '        if !off.contains("filings"), place.bbl.count == 10, let blk = Int(place.bbl.dropFirst().prefix(5)) {'),
]
for a, b in reps:
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b, 1)
old = '        var out: [BlockNews] = []\n        /// The block itself'
new = '        var out: [BlockNews] = []\n        // Built-in sources the file switches off by name, and the sources the file adds (lists.json MyBlock.sourcesOff, MyBlock.sources).\n        let off = Set(Lists.strings("MyBlock.sourcesOff", []))\n        /// The block itself'
assert old in s, 'out'; s = s.replace(old, new, 1)
# 2. the file's own sources, run before the result is returned
old2 = '        guard anyOK else { return nil }\n        return out.sorted { ($0.start ?? .distantFuture) < ($1.start ?? .distantFuture) }\n    }\n}'
new2 = '''        // Sources the file adds: each a NYC Open Data dataset with a filter and field names (see lists.json "about").
        for src in Lists.dictList("MyBlock.sources", []) {
            func f(_ k: String) -> String { DK.str(src[k]) }
            let blk = place.bbl.count == 10 ? String(Int(place.bbl.dropFirst().prefix(5)) ?? 0) : ""
            let since = CityStatus.keyFmt.string(from: Date().addingTimeInterval(-30 * 86400))
            func fill(_ t: String) -> String {
                t.replacingOccurrences(of: "{BORO}", with: boro.uppercased()).replacingOccurrences(of: "{Boro}", with: boro).replacingOccurrences(of: "{BOROCODE}", with: boroCode(place.cd))
                    .replacingOccurrences(of: "{LIKE}", with: like).replacingOccurrences(of: "{TODAY}", with: today).replacingOccurrences(of: "{UNTIL}", with: until)
                    .replacingOccurrences(of: "{SINCE30}", with: since).replacingOccurrences(of: "{BLOCK}", with: blk).replacingOccurrences(of: "{BBL}", with: place.bbl)
            }
            guard !f("dataset").isEmpty, !f("where").isEmpty else { continue }
            guard let rows = await LotRecords.all(f("dataset"), where: fill(f("where")), select: f("select").isEmpty ? nil : f("select")) else { continue }
            anyOK = true
            let kind: BlockNews.Kind = ["event": .event, "film": .film, "closure": .closure, "permit": .permit, "filing": .filing][f("kind")] ?? .event
            var seen = Set<String>()
            for r in rows {
                func v(_ k: String) -> String { DK.str(r[k]) }
                func tmpl(_ t: String) -> String {
                    var o = t
                    for (k, _) in r { o = o.replacingOccurrences(of: "{\\(k)}", with: v(k)) }
                    return o
                }
                var hit = true
                if !f("location").isEmpty {
                    guard let h = onBlock(segments(v(f("location")))) else { continue }
                    hit = h
                } else if !f("street").isEmpty {
                    guard norm(v(f("street"))) == street else { continue }
                    hit = sameBlock(norm(v(f("from"))), norm(v(f("to"))))
                }
                if let g = src["group"] as? [String], !g.isEmpty {
                    let key = g.map { v($0) }.joined(separator: "|")
                    guard seen.insert(key).inserted else { continue }
                }
                out.append(BlockNews(kind: kind, title: tmpl(f("title")), detail: tmpl(f("detail")),
                                     start: LotRecords.date(v(f("start"))), end: f("end").isEmpty ? nil : LotRecords.date(v(f("end"))), onBlock: hit))
            }
        }
        guard anyOK else { return nil }
        return out.sorted { ($0.start ?? .distantFuture) < ($1.start ?? .distantFuture) }
    }
}'''
assert old2 in s, 'tail'; s = s.replace(old2, new2, 1)
open(p, 'w').write(s)
# 3. Lists.dictList: a list of dictionaries from the file
dk = os.path.join(sys.argv[1], 'App/Views/DistrictKit.swift'); d = open(dk).read()
if 'static func dictList(' not in d:
    old3 = '    static func dictRows(_ key: String) -> [String: [[Any]]]? { entry(key) as? [String: [[Any]]] }\n'
    new3 = old3 + '    /// A list of objects from the file (sources, rules), the code\'s list when the file has none.\n    static func dictList(_ key: String, _ fallback: [[String: Any]]) -> [[String: Any]] { (entry(key) as? [[String: Any]]) ?? fallback }\n'
    assert old3 in d, 'Lists'; d = d.replace(old3, new3, 1); open(dk, 'w').write(d)
print('block sources ok')
