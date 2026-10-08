"""A board's next meeting is a meeting: the civic calendar's "cb6" group marks events from the CB6 community calendar
(any organization), so it no longer counts as a board meeting for another board. fix_boardmeeting.py <app dir>"""
import sys, os
p = os.path.join(sys.argv[1], 'App/Views/BKBoards.swift')
if not os.path.exists(p): print('no BKBoards'); sys.exit()
s = open(p).read()
old = 'e.type == "cbmeeting" || e.type.hasPrefix("brooklyn-community-board") || e.key == "board" || e.key == "committee" || e.group == "cb6"'
new = 'e.type == "cbmeeting" || e.type.hasPrefix("brooklyn-community-board") || e.key == "board" || e.key == "committee"'
if old in s: open(p, 'w').write(s.replace(old, new, 1)); print('board meeting ok')
else: print('already' if new in s else 'NOT FOUND')
