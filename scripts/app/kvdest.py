"""Details rows that open a screen: a profile's "kvdest" ({"<row value>": "<screen key>"}, orgs-profiles.json) makes that
Details row a link, and "org:<slug>" opens that organization's profile; the BID pages' business lists use it.
kvdest.py <app dir>"""
import sys, os, re
R = sys.argv[1]; V = os.path.join(R, 'BKCB6/App/Views')
p = os.path.join(V, 'OrgsTabView.swift'); s = open(p).read()
if 'kvDest' not in s:
    s = s.replace('    var group: String = ""\n    var topic: String = ""\n', '    var group: String = ""\n    var topic: String = ""\n    /// Details rows that open a screen, by the row\'s value ("kvdest" in the file): "org:<slug>" opens that profile.\n    var kvDest: [String: String] = [:]\n', 1)
    s = s.replace('                pr.group = s("group"); pr.topic = s("topic"); pr.sort = (p["sort"] as? NSNumber)?.intValue ?? 0\n',
                  '                pr.group = s("group"); pr.topic = s("topic"); pr.sort = (p["sort"] as? NSNumber)?.intValue ?? 0\n                pr.kvDest = (p["kvdest"] as? [String: String]) ?? [:]\n', 1)
    old = '''                        ForEach(Array(profile.kv.enumerated()), id: \\.offset) { i, pair in
                            if i > 0 { Divider() }
                            row(pair.0, pair.1)
                        }'''
    new = '''                        ForEach(Array(profile.kv.enumerated()), id: \\.offset) { i, pair in
                            if i > 0 { Divider() }
                            if let dest = profile.kvDest[pair.1], !dest.isEmpty {
                                NavigationLink { ScreenRouter.view(dest) } label: {
                                    HStack(spacing: 8) { row(pair.0, pair.1, accent: true); Image(systemName: "chevron.right").font(.system(size: 12, weight: .semibold)).foregroundStyle(Color.cb6Orange) }
                                }
                                .buttonStyle(.plain)
                            } else {
                                row(pair.0, pair.1)
                            }
                        }'''
    assert old in s, 'details rows'
    s = s.replace(old, new, 1)
    assert 'kvDest' in s and 'p["kvdest"]' in s
    open(p, 'w').write(s)
# the route: "org:<slug>" opens that profile
h = os.path.join(V, 'HomeView.swift'); t = open(h).read()
if 'hasPrefix("org:")' not in t:
    anchor = 'case let k where k.hasPrefix("official:"): AnyView(OfficialProfileView(slug: String(k.dropFirst(9))))\n'
    assert anchor in t, 'official route'
    t = t.replace(anchor, anchor + 'case let k where k.hasPrefix("org:"): AnyView(OrgBySlug(slug: String(k.dropFirst(4))))\n', 1)
    t = t.rstrip('\n') + '''

/// An organization's profile by slug ("org:<slug>"), or its calendar page, or a line saying it was not found.
struct OrgBySlug: View {
    let slug: String
    var body: some View {
        let d = OrgsData.load()
        if let p = d.profiles.first(where: { $0.slug == slug || $0.type == slug }) { OrgProfileView(profile: p) }
        else if let o = d.orgs.first(where: { $0.slug == slug }) { CalOrgView(org: o) }
        else { Text(verbatim: Copy.f("HomeView.orgmissing", "No profile for {0}.", slug)).font(DM.sans(14)).foregroundStyle(Color.cb6Muted).padding() }
    }
}
'''
    open(h, 'w').write(t)
print('kvdest ok')
