"""Home's block card lists the DOT street construction permits on the block (the permits the 311, Crime, Tickets &
Permits page maps as "Street work (DOT)"), one row per permit set, as a permit to use the street for work and not as a
closure; only the block itself counts as on the block (both cross streets). fix_blockwork.py <app dir>; re-runnable."""
import sys, os, hashlib, re
p = os.path.join(sys.argv[1], 'App/Views/MyBlock.swift'); s = open(p).read()
def key(t): return 'MyBlock.' + hashlib.sha1(t.encode()).hexdigest()[:8]
ANCHOR = '        // New DOB NOW job filings on the tax block in the last 30 days.\n'
START = '        // DOT street construction permits on the block: the same permits the 311, Crime, Tickets & Permits page maps.\n'
# the earlier version of this block, if present, goes
if START in s and 'case permit' not in s:
    i = s.find(START); j = s.find(ANCHOR, i); assert j > i, 'old block'
    s = s[:i] + s[j:]
if 'tqtj-sjs8' in s: print('already'); sys.exit()
assert s.count(ANCHOR) == 1, 'anchor'
NEW = '''        // DOT street construction permits on the block: the same permits the 311, Crime, Tickets & Permits page maps.
        // One row per permit set (same place, dates and status), named as what it is: a permit to use the street or
        // sidewalk for work, not a closure. The block itself (both cross streets) is on the block; the rest of the street is not.
        if let rows = await LotRecords.all("tqtj-sjs8", where: "boroughname='\\(boro.uppercased())' AND upper(onstreetname) like '%\\(like)%' AND issuedworkenddate >= '\\(today)' AND issuedworkstartdate <= '\\(until)'",
                                           select: "permitnumber,onstreetname,fromstreetname,tostreetname,issuedworkstartdate,issuedworkenddate,permittypedesc,permitstatusshortdesc") {
            anyOK = true
            var sets: [String: (where: String, a: String, b: String, start: String, end: String, status: String, types: [String], numbers: [String])] = [:]
            var order: [String] = []
            for r in rows where norm(DK.str(r["onstreetname"])) == street {
                let a = norm(DK.str(r["fromstreetname"])), b = norm(DK.str(r["tostreetname"]))
                let start = String(DK.str(r["issuedworkstartdate"]).prefix(10)), end = String(DK.str(r["issuedworkenddate"]).prefix(10))
                let status = DK.str(r["permitstatusshortdesc"]).capitalized
                let k = [a, b, start, end, status].joined(separator: "|")
                if sets[k] == nil {
                    sets[k] = (Copy.f("MyBlock.5b670a8a", "{0} between {1} and {2}", ref.street, DK.str(r["fromstreetname"]).capitalized, DK.str(r["tostreetname"]).capitalized), a, b, start, end, status, [], [])
                    order.append(k)
                }
                let t = DK.str(r["permittypedesc"]).lowercased().trimmingCharacters(in: .whitespaces)
                if !t.isEmpty, !(sets[k]!.types.contains(t)) { sets[k]!.types.append(t) }
                let n = DK.str(r["permitnumber"]); if !n.isEmpty { sets[k]!.numbers.append(n) }
            }
            for k in order {
                let g = sets[k]!
                let pair: Set<String> = [g.a, g.b].filter { !$0.isEmpty }.reduce(into: []) { $0.insert($1) }
                let onBlock = cross.count == 2 ? pair == cross : !cross.isDisjoint(with: pair)
                let what = g.types.joined(separator: ", ")
                let nums = g.numbers.count > 1 ? Copy.f("MyBlock.c1e2d3f4", "permits {0} to {1}", g.numbers.first!, g.numbers.last!) : (g.numbers.first.map { Copy.f("KEY_PERMIT", "permit {0}", $0) } ?? "")
                out.append(BlockNews(kind: .permit, title: Copy.f("KEY_TITLE", "DOT construction permit: {0}", what),
                                     detail: [g.where, g.status, nums, Copy.t("KEY_NOTE", "A permit to use the street or sidewalk for work, not a closure.")].filter { !$0.isEmpty }.joined(separator: " \\u{00B7} "),
                                     start: LotRecords.date(g.start), end: LotRecords.date(g.end), onBlock: onBlock))
            }
        }
'''.replace('KEY_TITLE', key('DOT construction permit: {0}')).replace('KEY_PERMIT', key('permit {0}')).replace('KEY_NOTE', key('A permit to use the street or sidewalk for work, not a closure.')).replace('MyBlock.c1e2d3f4', key('permits {0} to {1}'))
s = s.replace(ANCHOR, NEW + ANCHOR, 1)
# the kind: a plain wrench, never the red alert
s = s.replace('    enum Kind { case event, film, closure, filing }', '    enum Kind { case event, film, closure, filing, permit }', 1)
s = s.replace('case .closure: return "cone.fill"; case .filing: return "doc.text.fill" }', 'case .closure: return "cone.fill"; case .filing: return "doc.text.fill"; case .permit: return "wrench.and.screwdriver.fill" }', 1)
s = s.replace('let soon = n.kind != .filing && (n.start.map', 'let soon = n.kind != .filing && n.kind != .permit && (n.start.map', 1)
assert 'case permit' in s or 'filing, permit' in s, 'kind'
assert 'wrench.and.screwdriver.fill' in s and 'n.kind != .permit' in s, 'render'
open(p, 'w').write(s); print('patched', key('DOT construction permit: {0}'))
