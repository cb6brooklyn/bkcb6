"""BKCB's Home with no board picked: the next meeting or event in Brooklyn, from the Brooklyn calendar, any board or
organization, under "NEXT MEETING OR EVENT" (copy.json BKBoards.ae541759). A picked board keeps its own next meeting.
fix_bknext.py <app dir>"""
import sys, os
p = os.path.join(sys.argv[1], 'App/Views/BKBoards.swift')
if not os.path.exists(p): print('no BKBoards'); sys.exit()
s = open(p).read()
old = '        if cd.isEmpty { return all.first { ($0.cd ?? "").hasPrefix("3") && isBoardMeeting($0) && !hidden.contains(CalHidden.key($0)) } }\n'
new = '        // Brooklyn as a whole: the next meeting or event on the Brooklyn calendar, whoever holds it.\n        if cd.isEmpty { return CalData.merged(.cb6, meetings: store.meetings).first { !hidden.contains(CalHidden.key($0)) } }\n'
if old in s: s = s.replace(old, new, 1)
elif new not in s: print('not BKCB, skipped'); sys.exit()
old2 = 'Copy.f("BKBoards.ae541759", "NEXT MEETING: {0}", e.cd.flatMap { BKBoards.board($0)?.short } ?? "BROOKLYN")'
new2 = 'Copy.t("BKBoards.ae541759", "NEXT MEETING OR EVENT")'
if old2 in s: s = s.replace(old2, new2, 1)
elif new2 not in s: print('NOT FOUND label'); sys.exit(1)
open(p, 'w').write(s); print('bk next ok')
