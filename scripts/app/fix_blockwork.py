"""Home's block card lists the DOT street construction permits on the block (the permits the 311, Crime, Tickets &
Permits page maps as "Street work (DOT)"), not only DOT's full closures, so the two screens agree. fix_blockwork.py <app dir>"""
import sys, os, hashlib
p = os.path.join(sys.argv[1], 'App/Views/MyBlock.swift'); s = open(p).read()
if 'tqtj-sjs8' in s: print('already'); sys.exit()
ANCHOR = '        // New DOB NOW job filings on the tax block in the last 30 days.\n'
assert s.count(ANCHOR) == 1, 'anchor'
k = 'MyBlock.' + hashlib.sha1('Street work permit: {0}'.encode()).hexdigest()[:8]
NEW = '''        // DOT street construction permits on the block: the same permits the 311, Crime, Tickets & Permits page maps.
        if let rows = await LotRecords.all("tqtj-sjs8", where: "boroughname='\\(boro.uppercased())' AND upper(onstreetname) like '%\\(like)%' AND issuedworkenddate >= '\\(today)' AND issuedworkstartdate <= '\\(until)'",
                                           select: "permitnumber,onstreetname,fromstreetname,tostreetname,issuedworkstartdate,issuedworkenddate,permittypedesc,permitstatusshortdesc") {
            anyOK = true
            var seen = Set<String>()
            for r in rows where norm(DK.str(r["onstreetname"])) == street {
                let a = norm(DK.str(r["fromstreetname"])), b = norm(DK.str(r["tostreetname"]))
                let what = DK.str(r["permittypedesc"]).capitalized
                let key = [what, a, b, String(DK.str(r["issuedworkstartdate"]).prefix(10)), String(DK.str(r["issuedworkenddate"]).prefix(10))].joined(separator: "|")
                guard seen.insert(key).inserted else { continue }
                let status = DK.str(r["permitstatusshortdesc"]).capitalized
                out.append(BlockNews(kind: .closure, title: Copy.f("KEY_TITLE", "Street work permit: {0}", what),
                                     detail: [Copy.f("MyBlock.5b670a8a", "{0} between {1} and {2}", ref.street, DK.str(r["fromstreetname"]).capitalized, DK.str(r["tostreetname"]).capitalized), status, Copy.f("KEY_PERMIT", "DOT permit {0}", DK.str(r["permitnumber"]))].filter { !$0.isEmpty }.joined(separator: " \\u{00B7} "),
                                     start: LotRecords.date(DK.str(r["issuedworkstartdate"])), end: LotRecords.date(DK.str(r["issuedworkenddate"])), onBlock: !cross.isDisjoint(with: [a, b])))
            }
        }
'''.replace('KEY_TITLE', k).replace('KEY_PERMIT', 'MyBlock.' + hashlib.sha1('DOT permit {0}'.encode()).hexdigest()[:8])
s = s.replace(ANCHOR, NEW + ANCHOR, 1)
open(p, 'w').write(s); print('patched', os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(p)))), k)
