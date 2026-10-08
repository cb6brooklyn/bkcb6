#!/usr/bin/env python3
"""Folds the apps' key registries (exported from the code on the Mac: lists-<app>.json, style-keys-<app>.json) into the
pack files the apps read, each key with the value the code falls back to, so every table, color, badge and string is
edited in place: app/data/civic/lists.json (tables), mapstyle.json colors/icons (colors, badges, theme, type scale),
copy.json (strings). Usage: merge_app_keys.py <dir with the registries>"""
import json, os, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1]
C = os.path.join(ROOT, 'app/data/civic')

# 1. tables
lp = os.path.join(C, 'lists.json')
lists = json.load(open(lp)) if os.path.exists(lp) else {}
tables = lists.get('lists', {})
n_new = 0
for f in sorted(glob.glob(os.path.join(SRC, 'lists-*.json'))):
    d = json.load(open(f))
    for k, v in (d['lists'] if 'lists' in d and 'structs' in d else d).items():
        if k not in tables: tables[k] = v; n_new += 1
lists['about'] = ("Every table the apps' code once carried, by <File>.<name>: categories, labels, aliases, route lists, colors (#hex), "
                  "lookup tables, tuples as rows of cells, structs as objects. Edit a value and the apps pick it up on their next refresh; "
                  "remove a key and the app's own table returns. Keys come from scripts/merge_app_keys.py (the Mac exports them from the code).")
lists['lists'] = dict(sorted(tables.items()))
json.dump(lists, open(lp, 'w'), ensure_ascii=False, indent=1)

# 2. colors, badges, theme, type
mp = os.path.join(C, 'mapstyle.json'); ms = json.load(open(mp))
colors = ms.setdefault('colors', {}); icons = ms.setdefault('icons', {}); numbers = ms.setdefault('numbers', {}); labels = ms.setdefault('labels', {})
where = ms.setdefault('where', {})
c_new = i_new = 0
for f in sorted(glob.glob(os.path.join(SRC, 'style-keys-*.json'))):
    d = json.load(open(f))
    for k, v in d['colors'].items():
        if k not in colors and v.get('hex'): colors[k] = v['hex']; c_new += 1
        where[k] = f"{v['file']}: {v.get('line', '')}"[:160]
    for k, v in d['icons'].items():
        lit = v['icon']
        # the code's badge as the file writes it: mi:<file> / img:<file> / sf:<symbol>#<hex> / labeled:<image>|<label>
        import re
        m = re.match(r'\.image\("([^"]*)"\)', lit); s = m.group(1) if m else ''
        m = re.match(r'\.symbol\("([^"]*)", "(#[0-9A-Fa-f]+)"\)', lit)
        if m: s = f'sf:{m.group(1)}{m.group(2)}'
        if not s or '\\(' in s: continue   # labeled badges, school logos and names built at run time and school logos keep the code's choice unless a key is added
        if k not in icons: icons[k] = s; i_new += 1
        where[k] = f"{v['file']}: {lit}"[:160]
numbers.setdefault('theme.textScale', 1)
for k, v in {'theme.font.sans': 'DMSans-Regular', 'theme.font.sansMedium': 'DMSans-Medium', 'theme.font.sansBold': 'DMSans-Bold', 'theme.font.mono': 'DMMono-Regular', 'theme.font.monoMedium': 'DMMono-Medium'}.items():
    labels.setdefault(k, v)
ms['colors'] = dict(sorted(colors.items())); ms['icons'] = dict(sorted(icons.items())); ms['where'] = dict(sorted(where.items()))
ms['about'] = ms['about'].split(' Every color written in the apps')[0].rstrip() + (
    " Every color written in the apps' code is here too, by <File>.c.<id> (where says which file and line), the theme colors as theme.<name>, "
    "every map badge by <File>.i.<id> under icons, the type scale as numbers theme.textScale and the font names as labels theme.font.*.")
json.dump(ms, open(mp, 'w'), ensure_ascii=False, indent=1)

# 3. strings
cp = os.path.join(C, 'copy.json'); copy = json.load(open(cp)); strings = copy['strings']; s_new = 0
for f in sorted(glob.glob(os.path.join(SRC, 'style-keys-*.json'))):
    for k, v in json.load(open(f))['strings'].items():
        if k not in strings: strings[k] = v; s_new += 1
# every visible literal the audit routed through the file (copy-audit-<app>.json, from scripts/app/audit_strings.py)
for f in sorted(glob.glob(os.path.join(SRC, 'copy-audit-*.json'))):
    for k, v in json.load(open(f))['strings'].items():
        if k not in strings: strings[k] = v; s_new += 1
copy['strings'] = dict(sorted(strings.items()))
json.dump(copy, open(cp, 'w'), ensure_ascii=False, indent=1)
print('tables', len(tables), f'(+{n_new})', '| colors', len(ms['colors']), f'(+{c_new})', '| icons', len(ms['icons']), f'(+{i_new})', '| strings', len(strings), f'(+{s_new})')
