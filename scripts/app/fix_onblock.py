"""The block card counts a permit, event, shoot or closure as on the block only when both its cross streets are the
block's; the rest of the street goes under "more on <street>, off your block". fix_onblock.py <app dir>"""
import sys, os
p = os.path.join(sys.argv[1], 'App/Views/MyBlock.swift'); s = open(p).read()
if 'func sameBlock(' in s: print('already'); sys.exit()
old = '''        func onBlock(_ segs: [(on: String, a: String, b: String)]) -> Bool? {
            let mine = segs.filter { $0.on == street }
            if mine.isEmpty { return nil }
            return mine.contains { !cross.isDisjoint(with: [$0.a, $0.b]) }
        }'''
new = '''        /// The block itself: both cross streets named are the block's (one shared corner is the next block over).
        func sameBlock(_ a: String, _ b: String) -> Bool {
            let pair = Set([a, b].filter { !$0.isEmpty })
            return cross.count == 2 ? pair == cross : !cross.isDisjoint(with: pair)
        }
        func onBlock(_ segs: [(on: String, a: String, b: String)]) -> Bool? {
            let mine = segs.filter { $0.on == street }
            if mine.isEmpty { return nil }
            return mine.contains { sameBlock($0.a, $0.b) }
        }'''
assert old in s, 'onBlock'; s = s.replace(old, new, 1)
old2 = 'let hit = mine.contains { !cross.isDisjoint(with: [norm(DK.str($0["from"])), norm(DK.str($0["to"]))]) }'
new2 = 'let hit = mine.contains { sameBlock(norm(DK.str($0["from"])), norm(DK.str($0["to"]))) }'
assert old2 in s, 'film'; s = s.replace(old2, new2, 1)
old3 = 'start: LotRecords.date(DK.str(r["work_start_date"])), end: LotRecords.date(DK.str(r["work_end_date"])), onBlock: !cross.isDisjoint(with: [a, b])))'
new3 = 'start: LotRecords.date(DK.str(r["work_start_date"])), end: LotRecords.date(DK.str(r["work_end_date"])), onBlock: sameBlock(a, b)))'
assert old3 in s, 'closures'; s = s.replace(old3, new3, 1)
old4 = '''                let pair: Set<String> = [g.a, g.b].filter { !$0.isEmpty }.reduce(into: []) { $0.insert($1) }
                let onBlock = cross.count == 2 ? pair == cross : !cross.isDisjoint(with: pair)
'''
new4 = '''                let onBlock = sameBlock(g.a, g.b)
'''
assert old4 in s, 'permits'; s = s.replace(old4, new4, 1)
open(p, 'w').write(s); print('on-block rule ok')
