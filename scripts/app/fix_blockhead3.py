"""Home's block card: the block ("Baltic Street between Clinton Street and Court Street") is the headline, the address
typed sits under it. fix_blockhead3.py <app dir>"""
import sys, os, re
p = os.path.join(sys.argv[1], 'App/Views/ExploreViews.swift'); s = open(p).read()
if 'blockHeadline' in s: print('already'); sys.exit()
OLD = re.compile(r'''( *)Text\(label == "Your location" \? \(summary\?\.address\.map \{ "Near \\\(\$0\)" \} \?\? label\) : label\)\.font\(DM\.sans\(19, \.bold\)\)\.foregroundStyle\(Color\.cb6Navy\)\.fixedSize\(horizontal: false, vertical: true\)\n'''
                 r''' *if let card = summary\?\.card \{\n *Text\(verbatim: (Copy\.f\("ExploreViews\.5b670a8a", "[^"]*", card\.street, card\.from, card\.to\))\)\.font\(DM\.sans\(13\)\)\.foregroundStyle\(Color\.cb6Muted\)\n *\}\n''')
m = OLD.search(s)
assert m, 'headline block not found'
ind, tmpl = m.group(1), m.group(2)
NEW = (f'{ind}// The block is the headline; the address typed sits under it.\n'
       f'{ind}let blockHeadline: String? = summary?.card.map {{ card in {tmpl} }}\n'
       f'{ind}Text(blockHeadline ?? (label == "Your location" ? (summary?.address.map {{ "Near \\($0)" }} ?? label) : label)).font(DM.sans(19, .bold)).foregroundStyle(Color.cb6Navy).fixedSize(horizontal: false, vertical: true)\n'
       f'{ind}if blockHeadline != nil {{\n'
       f'{ind}    Text(label == "Your location" ? (summary?.address.map {{ "Near \\($0)" }} ?? label) : label).font(DM.sans(13)).foregroundStyle(Color.cb6Muted)\n'
       f'{ind}}}\n')
s = s[:m.start()] + NEW + s[m.end():]
open(p, 'w').write(s); print('patched', '| braces', s.count('{') - s.count('}'))
