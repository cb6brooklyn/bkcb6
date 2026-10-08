#!/usr/bin/env python3
"""The address card's Assembly and Senate tiles open the member's profile (/amsimon/, /sengounardes/), the way the
Council and Borough President tiles do, instead of the district office's lot record. The district -> slug tables come
from app/data/civic/officials.json, so a new member is one line in that file. Re-runnable."""
import json, re, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS = os.path.join(ROOT, 'assets', 'citywide-full-profile-search.js')
officials = json.load(open(os.path.join(ROOT, 'app', 'data', 'civic', 'officials.json')))
def table(kind):
    rows = sorted((int(o['district']), o['slug']) for o in officials if o.get('type') == kind and o.get('district') and os.path.isdir(os.path.join(ROOT, o['slug'])))
    return '{' + ','.join(f"'{d}':'{s}'" for d, s in rows) + '}'
s = open(JS, encoding='utf-8').read()
tables = f"  var AM_PAGE={table('assembly')};\n  var SD_PAGE={table('senate')};\n"
if 'var AM_PAGE=' in s:
    s = re.sub(r"  var AM_PAGE=\{[^\n]*\n  var SD_PAGE=\{[^\n]*\n", tables, s, count=1)
else:
    s = s.replace("  var SD_NO_PAGE=[35,36];\n", "  var SD_NO_PAGE=[35,36];\n" + tables, 1)
old_am = "imgTile('/elected/AD'+an+'.png','Assembly '+an,'/assembly-district-'+an+'/')"
new_am = "imgTile('/elected/AD'+an+'.png','Assembly '+an,AM_PAGE[String(an)]?'/'+AM_PAGE[String(an)]+'/':'/assembly-district-'+an+'/')"
old_sd = "imgTile('/elected/SD'+stn+'.png','Senate '+stn,SD_NO_PAGE.indexOf(stn)===-1?'/senate-district-'+stn+'/':'')"
new_sd = "imgTile('/elected/SD'+stn+'.png','Senate '+stn,SD_PAGE[String(stn)]?'/'+SD_PAGE[String(stn)]+'/':(SD_NO_PAGE.indexOf(stn)===-1?'/senate-district-'+stn+'/':''))"
for a, b in ((old_am, new_am), (old_sd, new_sd)):
    if b in s: continue
    assert a in s, a[:60]
    s = s.replace(a, b, 1)
open(JS, 'w', encoding='utf-8').write(s)
print('AM_PAGE', s.count("var AM_PAGE="), 'SD_PAGE', s.count("var SD_PAGE="), '| assembly tiles -> profile:', new_am in s, '| senate tiles -> profile:', new_sd in s)
