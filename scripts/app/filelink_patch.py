"""FileLink: a file-driven button (strip tiles, block card buttons and pills) takes the tap. Its label had allowsHitTesting(false),
which in SwiftUI makes a plain-style Button or NavigationLink untappable; the label keeps its shape instead.
Usage: python3 filelink_patch.py <project dir>  (idempotent)"""
import sys
T = sys.argv[1].rstrip('/') + '/BKCB6/App/Views/Tools.swift'
t = open(T).read()
n = t.count('content().allowsHitTesting(false)')
t = t.replace('content().allowsHitTesting(false)', 'content().contentShape(Rectangle())')
open(T, 'w').write(t)
print('FileLink labels fixed:', n)
