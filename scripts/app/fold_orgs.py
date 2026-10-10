"""Orgs tab: every heading and subsection a fold, open or closed from civic/ui/<app>/screens.json "open":
{"orgs.<heading>": true|false, "orgs.<heading>/<subsection>": true|false, "orgs.*": true|false}; closed when the file says nothing.
A search or a chosen heading chip opens what matches. fold_orgs.py <app dir>"""
import sys, os
R = sys.argv[1]
t = os.path.join(R, 'BKCB6/App/Views/Tools.swift'); s = open(t).read()
if 'func isOpen(_ screen: String' not in s:
    a = '    func tab(_ id: String) -> [String: Any]? { tabs()?.first { DK.str($0["id"]) == id } }\n'
    assert a in s, 'Tools anchor'
    s = s.replace(a, a + '''    /// Open or closed, from screens.json "open": {"<screen>.<key>": Bool, "<screen>.*": Bool}; else the fallback.
    func isOpen(_ screen: String, _ key: String, _ fallback: Bool) -> Bool {
        let o = file("screens")["open"] as? [String: Any] ?? [:]
        if let b = o[screen + "." + key] as? Bool { return b }
        if let b = o[screen + ".*"] as? Bool { return b }
        return fallback
    }
''', 1)
    open(t, 'w').write(s)
o = os.path.join(R, 'BKCB6/App/Views/OrgsTabView.swift'); s = open(o).read()
old = '''                    ForEach(groups) { g in
                        let inGroup = r.filter { $0.group == g.name }
                        if !inGroup.isEmpty {
                            SectionHeader(text: "\\(g.name) · \\(inGroup.count)").id(g.name == "Elected officials" ? "officials" : g.name)
                            let subs = topics(in: g.name, of: inGroup)
                            if subs.isEmpty {
                                ForEach(inGroup) { i in link(i) }
                            } else {
                                ForEach(subs, id: \\.self) { t in
                                    Text(t.uppercased()).font(DM.mono(10, .medium)).tracking(1).foregroundStyle(Color.cb6Muted).padding(.top, 6)
                                    ForEach(inGroup.filter { $0.topic == t }) { i in link(i) }
                                }
                                ForEach(inGroup.filter { $0.topic.isEmpty }) { i in link(i) }
                            }
                        }
                    }'''
new = '''                    // Every heading and subsection is a fold, open or closed as screens.json "open" says (closed when it says nothing);
                    // a search or a chosen heading opens what matches.
                    let searching = !query.trimmingCharacters(in: .whitespaces).isEmpty
                    ForEach(groups) { g in
                        let inGroup = r.filter { $0.group == g.name }
                        if !inGroup.isEmpty {
                            let forced = searching || topic == g.name
                            let subs = topics(in: g.name, of: inGroup)
                            HomeFold(title: "\\(g.name) · \\(inGroup.count)", id: "orgs." + g.name, open: forced || UIConfig.shared.isOpen("orgs", g.name, false)) {
                                VStack(alignment: .leading, spacing: 10) {
                                    if subs.isEmpty {
                                        ForEach(inGroup) { i in link(i) }
                                    } else {
                                        ForEach(subs, id: \\.self) { t in
                                            let inSub = inGroup.filter { $0.topic == t }
                                            HomeFold(title: "\\(t) · \\(inSub.count)", id: "orgs." + g.name + "/" + t, open: forced || UIConfig.shared.isOpen("orgs", g.name + "/" + t, false)) {
                                                VStack(alignment: .leading, spacing: 10) { ForEach(inSub) { i in link(i) } }
                                            }
                                            .id("\\(g.name)/\\(t)/\\(forced)/\\(UIConfig.shared.version)")
                                        }
                                        ForEach(inGroup.filter { $0.topic.isEmpty }) { i in link(i) }
                                    }
                                }
                            }
                            .id((g.name == "Elected officials" ? "officials" : g.name) + "/\\(forced)/\\(UIConfig.shared.version)")
                        }
                    }'''
if 'UIConfig.shared.isOpen("orgs"' not in s:
    assert old in s, 'Orgs groups block'
    s = s.replace(old, new, 1)
    open(o, 'w').write(s)
print('orgs folds ok')
