"""Native file nodes (builds from Nov 2026 read home.json "<screen>@3" first, so older builds keep "@2"): a Home section {"kind": "node", "node": {...}} and a screen part {"kind": "node", "node": {...}} draw whatever
the node describes (FileNode.swift). Copies FileNode.swift and the app's FileNodeSources into App/Views and wires them in.
fix_node.py <app dir> <cb6|bk>"""
import sys, os, shutil
R, V = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
views = os.path.join(R, 'BKCB6/App/Views')
shutil.copy(os.path.join(here, 'FileNode.swift'), os.path.join(views, 'FileNode.swift'))
shutil.copy(os.path.join(here, f'FileNodeSources-{V}.swift'), os.path.join(views, 'FileNodeSources.swift'))
uc = os.path.join(R, 'BKCB6/App/Services/UIConfig.swift'); s = open(uc).read()
if 'var raw: [String: Any]' not in s:
    o = '        var height: Double = 0\n    }'
    assert s.count(o) == 1, 'Section height'
    s = s.replace(o, '        var height: Double = 0\n        /// The section as the file wrote it, for kinds that read their own settings ("node").\n        var raw: [String: Any] = [:]\n    }')
    o = 'height: (r["height"] as? NSNumber)?.doubleValue ?? 0)'
    assert s.count(o) == 1, 'sections() height'
    s = s.replace(o, 'height: (r["height"] as? NSNumber)?.doubleValue ?? 0, raw: r)')
    o = '            if s.kind == "fold" {'
    assert s.count(o) == 1, 'HomeSections fold'
    s = s.replace(o, '''            if s.kind == "node" {
                let node = (s.raw["node"] as? [String: Any]) ?? s.raw
                if s.fold || s.pinned {
                    HomeFold(title: titleFor(s), id: s.id, open: s.open || s.pinned || Hook.flag("-openAll"), pinned: s.pinned, icon: s.icon) { FileNode(node) }
                } else {
                    FileNode(node).padding(.top, CGFloat(DK.num(s.raw["top"]) ?? 14)).id(s.id)
                }
            } else if s.kind == "fold" {''')
    o = '(file("home")[screen + "@2"] ?? file("home")[screen])'
    assert s.count(o) == 1, 'sections @2'
    s = s.replace(o, '(file("home")[screen + "@3"] ?? file("home")[screen + "@2"] ?? file("home")[screen])')
    open(uc, 'w').write(s)
tl = os.path.join(views, 'Tools.swift'); s = open(tl).read()
if 'case "node":' not in s:
    o = '        case "header":\n            SectionHeader(text: title)'
    assert s.count(o) == 1, 'FilePart header'
    s = s.replace(o, '        case "node":\n            FileNode((p["node"] as? [String: Any]) ?? p)\n' + o)
    open(tl, 'w').write(s)
print('node ok', R)
