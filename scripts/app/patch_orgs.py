import re,sys,os,hashlib,json
H='/Users/user301938'
app=sys.argv[1]; fn=f'{H}/{app}/BKCB6/App/Views/OrgsTabView.swift'
s=open(fn).read(); o=s
reg={}
def ct(text):
    k='OrgsTabView.'+hashlib.sha1(text.encode()).hexdigest()[:8]; reg[k]=text
    return f'Copy.t("{k}", "{text}")'
def cf(text,*args):
    k='OrgsTabView.'+hashlib.sha1(text.encode()).hexdigest()[:8]; reg[k]=text
    return f'Copy.f("{k}", "{text}", {", ".join(args)})'

# 1. the model: group, topic and sort on profiles and calendar organizations
s=s.replace('''    let cal: String?
    var going: [OrgGoing] = []

    var id: String { slug }
    var coordinate: CLLocationCoordinate2D''','''    let cal: String?
    var going: [OrgGoing] = []
    /// Where it sits in the Organizations tab, from the file: the heading, the subsection, and the order under the heading.
    var group: String = ""
    var topic: String = ""
    var sort: Int = 0

    var id: String { slug }
    var coordinate: CLLocationCoordinate2D''')
assert 'var group: String = ""' in s, 'profile model'
s=s.replace('''    let cal: String?
    let count: Int
    var id: String { slug }
    static func == (a: CalOrg, b: CalOrg) -> Bool''','''    let cal: String?
    let count: Int
    var group: String = ""
    var topic: String = ""
    var sort: Int = 0
    var id: String { slug }
    static func == (a: CalOrg, b: CalOrg) -> Bool''')
assert s.count('var group: String = ""')==2, 'calorg model'

# 2. the loader
i=s.index('                profiles.append(OrgProfile(')
j=s.index('            for o in root["orgs"]')
block=s[i:j]
end=block.rindex('}))')
block=block[:end].replace('                profiles.append(OrgProfile(','                var pr = OrgProfile(',1)+'''})
                pr.group = s("group"); pr.topic = s("topic"); pr.sort = (p["sort"] as? NSNumber)?.intValue ?? 0
                profiles.append(pr)
            }
'''
s=s[:i]+block+s[j:]
assert 'profiles.append(pr)' in s, 'loader profiles'
s=s.replace('''            for o in root["orgs"] as? [[String: Any]] ?? [] {
                orgs.append(CalOrg(slug: (o["slug"] as? String) ?? "", name: (o["name"] as? String) ?? "",
                                   logo: OrgTopics.logoFix[(o["slug"] as? String) ?? ""] ?? o["logo"] as? String, site: (o["site"] as? String).flatMap(URL.init(string:)),
                                   cal: o["cal"] as? String, count: (o["n"] as? NSNumber)?.intValue ?? 0))
            }''','''            for o in root["orgs"] as? [[String: Any]] ?? [] {
                var co = CalOrg(slug: (o["slug"] as? String) ?? "", name: (o["name"] as? String) ?? "",
                                logo: OrgTopics.logoFix[(o["slug"] as? String) ?? ""] ?? o["logo"] as? String, site: (o["site"] as? String).flatMap(URL.init(string:)),
                                cal: o["cal"] as? String, count: (o["n"] as? NSNumber)?.intValue ?? 0)
                co.group = (o["group"] as? String) ?? ""; co.topic = (o["topic"] as? String) ?? ""; co.sort = (o["sort"] as? NSNumber)?.intValue ?? 0
                orgs.append(co)
            }
            groups = (root["groups"] as? [[String: Any]] ?? []).compactMap { g in
                guard let n = g["name"] as? String else { return nil }
                return OrgGroup(name: n, topics: (g["topics"] as? [String]) ?? [])
            }''')
assert 'orgs.append(co)' in s, 'loader orgs'
s=s.replace('enum OrgsData {','/// A heading of the Organizations tab and the order of its subsections.\nstruct OrgGroup: Identifiable { let name: String; let topics: [String]; var id: String { name } }\n\nenum OrgsData {',1)
s=s.replace('''    private static var cache: (profiles: [OrgProfile], orgs: [CalOrg])?
    static func reset() { cache = nil }''','''    private static var cache: (profiles: [OrgProfile], orgs: [CalOrg])?
    /// The headings of the Organizations tab and the order of their subsections, from the file.
    static var groups: [OrgGroup] = []
    static let defaultGroups: [OrgGroup] = [
        OrgGroup(name: "Community groups", topics: []), OrgGroup(name: "Local businesses", topics: []), OrgGroup(name: "Elected officials", topics: []), OrgGroup(name: "Government agencies", topics: [])]
    static func reset() { cache = nil; groups = [] }''')
assert 'static var groups' in s, 'groups'

# 3. OrgTopics: a heading for anything the file does not place
s=s.replace('''    static func topic(_ slug: String, kind: String) -> String {
        if let t = bySlug[slug] { return t }''','''    static func group(_ slug: String, kind: String) -> String {
        switch kind {
        case "official": return "Elected officials"
        case "agency": return "Government agencies"
        default: return bySlug[slug] == "Local shops and restaurants" ? "Local businesses" : "Community groups"
        }
    }
    static func topic(_ slug: String, kind: String) -> String {
        if let t = bySlug[slug] { return t }''')
assert 'static func group(_ slug' in s, 'orgtopics group'

# 4. OrgItem carries the heading and the order
s=s.replace('''struct OrgItem: Identifiable {
    let id: String
    let name: String
    let topic: String''','''struct OrgItem: Identifiable {
    let id: String
    let name: String
    let group: String
    let topic: String
    var sort: Int = 0''')
assert 'let group: String\n    let topic: String' in s, 'orgitem'

# 5. items, results and the list
i=s.index('    private var items: [OrgItem] {'); j=s.index('    var body: some View {', i)
s=s[:i]+'''    private var groups: [OrgGroup] { OrgsData.groups.isEmpty ? OrgsData.defaultGroups : OrgsData.groups }

    private var items: [OrgItem] {
        var out = data.profiles.map { p in
            OrgItem(id: "p-" + p.slug, name: p.name, group: p.group.isEmpty ? OrgTopics.group(p.slug, kind: p.kind) : p.group,
                    topic: p.topic.isEmpty ? OrgTopics.topic(p.slug, kind: p.kind) : p.topic, sort: p.sort, subtitle: p.seat,
                    logo: OrgTopics.logoFix[p.slug] ?? p.logo, profile: p, calOrg: data.orgs.first { $0.slug == p.type })
        }
        for o in data.orgs where profileFor(o) == nil && Self.officialFor[o.slug] == nil {
            out.append(OrgItem(id: "c-" + o.slug, name: o.name, group: o.group.isEmpty ? OrgTopics.group(o.slug, kind: "org") : o.group,
                               topic: o.topic.isEmpty ? OrgTopics.topic(o.slug, kind: "org") : o.topic, sort: o.sort, subtitle: ''' + ct("On the CB6 community calendar") + ''',
                               logo: OrgTopics.logoFix[o.slug] ?? o.logo, profile: nil, calOrg: o))
        }
        return out.sorted { ($0.sort, $0.sortKey) < ($1.sort, $1.sortKey) }
    }

    private var results: [OrgItem] {
        let q = query.trimmingCharacters(in: .whitespaces).lowercased()
        return items.filter { i in
            (topic.isEmpty || i.group == topic) &&
            (q.isEmpty || i.name.lowercased().contains(q) || i.topic.lowercased().contains(q) || i.group.lowercased().contains(q) || i.subtitle.lowercased().contains(q)
             || (i.profile?.desc.lowercased().contains(q) ?? false) || (i.profile?.addr.lowercased().contains(q) ?? false))
        }
    }

    /// The subsections of a heading, in the file's order, then any the file does not list.
    private func topics(in group: String, of list: [OrgItem]) -> [String] {
        let listed = groups.first { $0.name == group }?.topics ?? []
        let present = list.filter { $0.group == group }.map(\\.topic)
        var extra: [String] = []
        for t in present where !listed.contains(t) && !t.isEmpty && !extra.contains(t) { extra.append(t) }
        return listed.filter { present.contains($0) } + extra
    }

'''+s[j:]
assert 'private func topics(in group' in s, 'items'

# the chips and the sections
i=s.index('                    ScrollView(.horizontal, showsIndicators: false) {')
j=s.index('                    if r.isEmpty {', i)
s=s[:i]+'''                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            DKChip(text: ''' + cf("All {0}", "all.count") + ''', color: Color.cb6Navy, on: topic.isEmpty) { topic = "" }
                            ForEach(groups) { g in
                                let n = all.filter { $0.group == g.name }.count
                                if n > 0 { DKChip(text: "\\(g.name) \\(n)", color: Color.cb6Navy, on: topic == g.name) { topic = topic == g.name ? "" : g.name } }
                            }
                        }
                        .padding(.vertical, 2)
                    }
                    ForEach(groups) { g in
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
                    }
'''+s[j:]
assert 'let subs = topics(in: g.name, of: inGroup)' in s, 'sections'

# 6. the page subtitle
old_sub='Search by name or topic: community groups, officials and agencies'
new_sub='Search by name or topic: community groups, local businesses, elected officials and government agencies'
m=re.search(r'Copy\.t\("OrgsTabView\.[0-9a-f]{8}", "'+re.escape(old_sub)+'"\)', s)
if m: s=s.replace(m.group(0), ct(new_sub))
else:
    assert f'"{old_sub}"' in s, 'subtitle'
    s=s.replace(f'"{old_sub}"', ct(new_sub))
open(fn,'w').write(s)
json.dump(reg,open(f'{H}/copy-orgs-{app}.json','w'))
print(app,'OrgsTabView patched; new copy keys', list(reg))
