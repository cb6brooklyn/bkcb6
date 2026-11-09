"""A downloaded pack file that the new build already ships: DataPack dropped the stale download without telling the
screens, so the old screens stayed up until the app was reopened. Dropping it now counts as a change, so the
screens read the shipped file at once. fix_packstale.py <app dir>"""
import sys, os
p = os.path.join(sys.argv[1], 'BKCB6/App/Services/DataPack.swift'); s = open(p).read()
a = '''            if FileManager.default.fileExists(atPath: dest.path) { try? FileManager.default.removeItem(at: dest) }
            return true'''
b = '''            if FileManager.default.fileExists(atPath: dest.path) { try? FileManager.default.removeItem(at: dest); changed += 1 }
            return true'''
c = '''            try? FileManager.default.removeItem(at: dest)
            have[rel] = "b:" + sha'''
d = '''            if FileManager.default.fileExists(atPath: dest.path) { try? FileManager.default.removeItem(at: dest); changed += 1 }
            have[rel] = "b:" + sha'''
if b not in s:
    assert s.count(a) == 1 and s.count(c) == 1, 'DataPack anchors'
    s = s.replace(a, b).replace(c, d); open(p, 'w').write(s)
print('packstale ok')
