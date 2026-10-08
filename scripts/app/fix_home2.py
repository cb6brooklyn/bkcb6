"""Builds from 114 / 49 / 46 read the section list under "<screen>@2" when home.json has one, else "<screen>", so the
installed builds keep their order while the new builds get theirs. fix_home2.py <app dir>"""
import sys, os
p = os.path.join(sys.argv[1], 'App/Services/UIConfig.swift'); s = open(p).read()
old = '        guard let rows = file("home")[screen] as? [[String: Any]] else { return nil }\n'
new = '        // "<screen>@2" when the file carries one (the order for these builds), else "<screen>" (the order older builds draw).\n        guard let rows = (file("home")[screen + "@2"] ?? file("home")[screen]) as? [[String: Any]] else { return nil }\n'
if new in s: print('already'); sys.exit()
assert old in s, 'sections'
s = s.replace(old, new, 1); open(p, 'w').write(s); print('home@2 ok')
