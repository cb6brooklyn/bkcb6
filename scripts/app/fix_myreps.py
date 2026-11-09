"""Your reps and following (Nov 2026 builds).

Home section {"kind": "myreps"} (home.json "<screen>@4", read before "@3" so older builds keep their Home): a row of the
officials who represent the saved address, in civic/myreps.json's order (Council Member, Borough President, Assembly,
State Senate, Congress, DA, Comptroller, Public Advocate, Mayor, AG, State Comptroller, Governor, US senators), then the
officials the person follows. Each logo opens that official's profile. A dot on a logo means an event today or tomorrow.
Follow: a button on every official's profile and a picker from the row; the follows are kept on the phone
(UserDefaults "my.reps.follow"), and the morning of each followed official's calendar event the phone gets an alert.
Profile banners take "links" (one per image) in banners.json, so two images can open two places.
fix_myreps.py <app dir>"""
import sys, os
R = sys.argv[1]
V = os.path.join(R, 'BKCB6/App/Views')
S = os.path.join(R, 'BKCB6/App/Services')
def rd(p): return open(p).read()
def wr(p, s): open(p, 'w').write(s)
def rep(p, old, new, n=1):
    s = rd(p)
    if new in s: return
    assert s.count(old) == n, (p, old[:80], s.count(old))
    wr(p, s.replace(old, new))

# 1. Home reads "@4" first
rep(os.path.join(S, 'UIConfig.swift'), '(file("home")[screen + "@3"] ?? ', '(file("home")[screen + "@4"] ?? file("home")[screen + "@3"] ?? ')

# 2. the Home section
hv = os.path.join(V, 'HomeView.swift')
a = '                            case "about": AboutBoardsCard().padding(.top, Sz("HomeView.z.844f630f", 14)).id("about")\n'
rep(hv, a, '                            case "myreps": MyRepsRow().padding(.top, 14).id("myreps")\n' + a)
bk = os.path.join(V, 'BKHome.swift')
if os.path.exists(bk):
    a = '                            case "pickboard": if sel.cd.isEmpty { PickBoardCard().padding(.top, Sz("BKHome.z.5f715429", 14)) }\n'
    rep(bk, a, '                            case "myreps": MyRepsRow().padding(.top, 14).id("myreps")\n' + a)

# 3. Follow on every official's profile
dk = os.path.join(V, 'DistrictKit.swift')
a = '                if !o.boro.isEmpty { DKPill(text: o.boro, fg: .white, bg: .white.opacity(0.18)) }\n            }\n'
rep(dk, a, a + '            FollowRepButton(slug: o.slug)\n')

# 3b. the row at the top of the Directory tab, for the apps civic/myreps.json lists under "directory"
ot = os.path.join(V, 'OrgsTabView.swift')
import re
t = rd(ot)
if 'MyRepsRow(' not in t:
    m = re.search(r'\n( *)searchField\.padding\(\.top, Sz\("OrgsTabView\.z\.[0-9a-f]+", 12\)\)\n', t)
    assert m, 'OrgsTabView searchField'
    ind = m.group(1)
    t = t[:m.start()] + '\n' + ind + 'if MyReps.inDirectory { MyRepsRow(open: { hookOfficial = $0 }).padding(.top, 12) }' + t[m.start():m.end()] + ind + 'RepsForAddress(query: query, open: { hookOfficial = $0 })\n' + t[m.end():]
    t = t.replace('"Search a name or a topic, like housing or arts"', '"Search a name, a topic or your address"')
    wr(ot, t)

# 4. banners with one link per image
uc = os.path.join(S, 'UIConfig.swift')
rep(uc, 'struct Banner { let images: [String]; let url: URL; let label: String }',
    'struct Banner { let images: [String]; let url: URL; let label: String; var links: [URL] = [] }')
rep(uc, r'''return Banner(images: images, url: u, label: b["label"] as? String ?? Copy.t("UIConfig.27a65e8a", "Open \u{2197}"))''',
    r'''return Banner(images: images, url: u, label: b["label"] as? String ?? Copy.t("UIConfig.27a65e8a", "Open \u{2197}"), links: (b["links"] as? [String] ?? []).compactMap { URL(string: $0) })''')
pm = os.path.join(V, 'ProfileMap.swift')
a = '        if let b = UIConfig.shared.banner(slug) ?? Self.defaultBanners[slug] {\n'
rep(pm, a, '''        if let b = UIConfig.shared.banner(slug), !b.links.isEmpty, b.links.count == b.images.count {
            // One link per image: each image opens its own place (a podcast on Apple Podcasts and on Spotify).
            VStack(alignment: .leading, spacing: 8) {
                Text(b.label).font(DM.sans(14, .bold)).foregroundStyle(Color.cb6Navy).fixedSize(horizontal: false, vertical: true)
                HStack(spacing: 8) {
                    ForEach(Array(b.images.enumerated()), id: \\.offset) { i, name in
                        Link(destination: b.links[i]) {
                            Group {
                                if let u = DataPack.url("Logos/\\(name).jpg") ?? DataPack.url("Logos/\\(name).png"), let ui = UIImage(contentsOfFile: u.path) {
                                    Image(uiImage: ui).resizable().scaledToFit()
                                } else { Color.cb6Rule }
                            }
                            .frame(maxWidth: .infinity).frame(height: 46)
                            .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .padding(10)
            .background(Color.white, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).stroke(Color.cb6Rule, lineWidth: 1))
            .padding(.top, 14)
        } else ''' + a.lstrip())

# 5. the code
tl = os.path.join(V, 'Tools.swift')
s = rd(tl)
if 'enum MyReps' not in s:
    if 'import UserNotifications' not in s: s = 'import UserNotifications\nimport CoreLocation\n' + s
    s = s.rstrip('\n') + '''


// MARK: - Your reps
//
// civic/myreps.json: "order" (the offices in the row's order: district seats by type, citywide and statewide offices by
// slug), "prefix" (the short title before a last name, by the same keys), "labels" (a whole label for one official),
// "title", "follow", "following", "add", "noBlock", "pickTitle", "done", "alertHour" (when the alert comes on an event's day).

enum MyReps {
    static let followKey = "my.reps.follow"
    static let changed = Notification.Name("myreps.changed")
    static var cfg: [String: Any] { DK.json("myreps") as? [String: Any] ?? [:] }
    static func t(_ k: String, _ d: String) -> String { (cfg[k] as? String) ?? d }
    /// Apps whose Directory tab opens with the row ("directory": ["cb6"]).
    static var inDirectory: Bool { (cfg["directory"] as? [String])?.contains(UIConfig.app) ?? false }
    /// With no saved block: the officials the file lists for this app ("fallback": {"cb6": [slugs]}), under "fallbackTitle".
    static var fallback: [Official] {
        let ord = order
        return ((cfg["fallback"] as? [String: Any])?[UIConfig.app] as? [String] ?? []).compactMap { DKOfficials.bySlug[$0] }
            .sorted { (rank($0, ord), $0.district ?? 0) < (rank($1, ord), $1.district ?? 0) }
    }
    static var follows: [String] { (UserDefaults.standard.string(forKey: followKey) ?? "").split(separator: ",").map(String.init).filter { !$0.isEmpty } }
    static func isFollowing(_ s: String) -> Bool { follows.contains(s) }
    static func toggle(_ s: String) {
        var f = follows
        if let i = f.firstIndex(of: s) { f.remove(at: i) } else { f.append(s) }
        UserDefaults.standard.set(f.joined(separator: ","), forKey: followKey)
        NotificationCenter.default.post(name: changed, object: nil)
    }
    static let defaultOrder = ["council", "bp", "assembly", "senate", "congress", "da", "comptroller", "publicadvocate", "mayor",
                               "attorneygeneral", "statecomptroller", "governor", "ussenate"]
    static var order: [String] { cfg["order"] as? [String] ?? defaultOrder }
    /// What an official sorts by: the type for district seats, the slug for the citywide and statewide offices.
    static func key(_ o: Official) -> String { (o.type == "citywide" || o.type == "statewide") ? o.slug : o.type }
    static func rank(_ o: Official, _ ord: [String]) -> Int { ord.firstIndex(of: key(o)) ?? 999 }
    static func label(_ o: Official, _ c: [String: Any]) -> String {
        if let l = (c["labels"] as? [String: String])?[o.slug] { return l }
        let pre = (c["prefix"] as? [String: String])?[key(o)] ?? ""
        let last = o.name.split(separator: " ").last.map(String.init) ?? o.name
        return pre.isEmpty ? last : "\\(pre) \\(last)"
    }
    static let boros = ["1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"]
    /// Everyone who represents the saved address, in the row's order.
    static func mine() -> [Official] {
        guard let p = MyPlace.current else { return [] }
        return mine(at: p.coord, cd: p.cd)
    }
    /// Everyone who represents a point.
    static func mine(at c: CLLocationCoordinate2D, cd pcd: Int = 0) -> [Official] {
        let ord = order
        var slugs: [String] = []
        for k in CivicLookup.kinds {
            if let hit = DK.shapes.keys.filter({ $0.hasPrefix("\\(k.key)-") }).first(where: { DK.contains(DK.shapes[$0] ?? [], c) }) {
                let n = Int(hit.split(separator: "-").last.map(String.init) ?? "") ?? 0
                if let o = DKOfficials.all.first(where: { $0.type == k.type && $0.district == n }) { slugs.append(o.slug) }
            }
        }
        let cd = CivicLookup.boards(.city).first { DK.contains(DK.shapes["cb-\\($0)"] ?? [], c) } ?? (pcd > 0 ? String(pcd) : "")
        let boro = boros[String(cd.prefix(1))] ?? ""
        for o in DKOfficials.all {
            if (o.type == "bp" || o.type == "da"), !boro.isEmpty, o.boro == boro { slugs.append(o.slug) }
            if o.type == "ussenate" || o.type == "citywide" || o.type == "statewide" { slugs.append(o.slug) }
        }
        var seen = Set<String>()
        return slugs.filter { seen.insert($0).inserted }.compactMap { DKOfficials.bySlug[$0] }
            .filter { ord.contains(key($0)) }.sorted { rank($0, ord) < rank($1, ord) }
    }
    static func nyDay() -> Calendar { var c = Calendar(identifier: .gregorian); c.timeZone = CalData.tz; return c }
    /// Officials with a calendar event today or tomorrow.
    static func soon(_ list: [Official], meetings: [Meeting]) -> Set<String> {
        let c = nyDay(), start = c.startOfDay(for: Date())
        guard let end = c.date(byAdding: .day, value: 2, to: start) else { return [] }
        return Set(list.filter { o in DKOfficials.events(for: o, meetings: meetings).contains { $0.day >= start && $0.day < end } }.map(\\.slug))
    }
    static func ask() async {
        _ = try? await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge])
        await MainActor.run { NotificationCenter.default.post(name: changed, object: nil) }
    }
    /// An alert the morning of each calendar event of everyone followed.
    static func schedule(meetings: [Meeting]) async {
        let center = UNUserNotificationCenter.current()
        let old = await center.pendingNotificationRequests().map(\\.identifier).filter { $0.hasPrefix("rep-") }
        center.removePendingNotificationRequests(withIdentifiers: old)
        let followed = follows.compactMap { DKOfficials.bySlug[$0] }
        guard !followed.isEmpty else { return }
        let st = await center.notificationSettings().authorizationStatus
        guard st == .authorized || st == .provisional else { return }
        let c = nyDay(), hour = (cfg["alertHour"] as? NSNumber)?.intValue ?? 9
        var n = 0
        for o in followed {
            for e in DKOfficials.events(for: o, meetings: meetings).sorted(by: { $0.day < $1.day }) {
                if n >= 50 { return }
                var comps = c.dateComponents([.year, .month, .day], from: e.day)
                comps.hour = hour; comps.minute = 0; comps.timeZone = CalData.tz
                guard let fire = c.date(from: comps), fire > Date() else { continue }
                let content = UNMutableNotificationContent()
                content.title = o.name
                var body = e.label
                if let t = e.time, !t.isEmpty { body += ", \\(t)" }
                if let l = e.location, !l.isEmpty { body += " \\u{00B7} \\(l)" }
                content.body = body
                content.sound = .default
                let req = UNNotificationRequest(identifier: "rep-\\(o.slug)-\\(e.id)", content: content,
                                                trigger: UNCalendarNotificationTrigger(dateMatching: comps, repeats: false))
                try? await center.add(req)
                n += 1
            }
        }
    }
}

/// Home: the officials for the saved address, then the ones followed. Each opens its profile.
struct MyRepsRow: View {
    /// Set where the screen opens a profile itself (the Directory tab); otherwise the row links to "official:<slug>".
    var open: ((String) -> Void)? = nil
    @State private var usingFallback = false
    @EnvironmentObject var store: DataStore
    @AppStorage(MyPlaceKeys.label) private var placeLabel = ""
    @AppStorage(MyReps.followKey) private var followRaw = ""
    @State private var mine: [Official] = []
    @State private var more: [Official] = []
    @State private var soon: Set<String> = []
    @State private var picking = false
    @State private var tick = 0
    var body: some View {
        let c = MyReps.cfg
        VStack(alignment: .leading, spacing: 8) {
            Text((usingFallback ? ((c["fallbackTitle"] as? [String: String])?[UIConfig.app] ?? MyReps.t("title", "Your reps")) : MyReps.t("title", "Your reps")).uppercased()).font(DM.mono(10, .medium)).tracking(1).foregroundStyle(Color.cb6Orange)
                .padding(.horizontal, 14)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(alignment: .top, spacing: 8) {
                    ForEach(mine + more, id: \\.slug) { o in
                        let t = tile(o, label: MyReps.label(o, c), followed: followRaw.split(separator: ",").contains(Substring(o.slug)))
                        if let open { Button { open(o.slug) } label: { t }.buttonStyle(.plain) }
                        else { NavigationLink(value: "official:\\(o.slug)") { t }.buttonStyle(.plain) }
                    }
                    Button { picking = true } label: {
                        Text(MyReps.t("add", "Follow\\nmore")).font(DM.sans(11, .bold)).multilineTextAlignment(.center).foregroundStyle(Color.cb6Navy)
                            .frame(width: 54, height: 54)
                            .background(Color.cb6Orange, in: RoundedRectangle(cornerRadius: 10, style: .continuous))
                    }
                    .buttonStyle(.plain)
                }
                .padding(.horizontal, 14)
            }
            if MyPlace.current == nil {
                Text(MyReps.t("noBlock", "Save your block to see who represents it")).font(DM.sans(12)).foregroundStyle(.white.opacity(0.85))
                    .padding(.horizontal, 14)
            }
        }
        .padding(.vertical, 12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.cb6Navy, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        .task(id: "\\(placeLabel)|\\(followRaw)|\\(tick)|\\(store.meetings.count)") {
            var m = MyReps.mine()
            usingFallback = m.isEmpty && !MyReps.fallback.isEmpty
            if m.isEmpty { m = MyReps.fallback }
            mine = m
            let have = Set(mine.map(\\.slug))
            more = MyReps.follows.filter { !have.contains($0) }.compactMap { DKOfficials.bySlug[$0] }
            soon = MyReps.soon(mine + more, meetings: store.meetings)
            await MyReps.schedule(meetings: store.meetings)
        }
        .onReceive(NotificationCenter.default.publisher(for: MyReps.changed)) { _ in tick += 1 }
        .sheet(isPresented: $picking) { MyRepsPicker() }
    }
    private func tile(_ o: Official, label: String, followed: Bool) -> some View {
        VStack(spacing: 4) {
            ZStack(alignment: .topTrailing) {
                OfficialIcon(slug: o.slug, size: 46)
                    .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
                    .padding(4)
                    .background(Color.white, in: RoundedRectangle(cornerRadius: 10, style: .continuous))
                if soon.contains(o.slug) {
                    Circle().fill(Color.cb6Orange).frame(width: 13, height: 13).overlay(Circle().stroke(Color.white, lineWidth: 2)).offset(x: 4, y: -4)
                } else if followed {
                    Image(systemName: "star.fill").font(.system(size: 9, weight: .bold)).foregroundStyle(Color.cb6Orange)
                        .padding(3).background(Circle().fill(Color.white)).offset(x: 4, y: -4)
                }
            }
            Text(label).font(DM.mono(9, .medium)).foregroundStyle(.white.opacity(0.92)).lineLimit(2).multilineTextAlignment(.center)
                .frame(width: 66)
        }
    }
}

/// In the Directory's search: an address typed there shows who represents it.
struct RepsForAddress: View {
    let query: String
    var open: (String) -> Void
    @AppStorage(MyPlaceKeys.label) private var placeLabel = ""
    @State private var hit: AddressMatch?
    @State private var reps: [Official] = []
    var body: some View {
        let c = MyReps.cfg
        Group {
            if let h = hit, !reps.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text(MyReps.t("addressTitle", "Who represents").uppercased()).font(DM.mono(10, .medium)).tracking(1).foregroundStyle(Color.cb6Orange)
                    Text(h.label).font(DM.sans(16, .bold)).foregroundStyle(.white)
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(alignment: .top, spacing: 8) {
                            ForEach(reps, id: \\.slug) { o in
                                Button { open(o.slug) } label: {
                                    VStack(spacing: 4) {
                                        OfficialIcon(slug: o.slug, size: 46).clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
                                            .padding(4).background(Color.white, in: RoundedRectangle(cornerRadius: 10, style: .continuous))
                                        Text(MyReps.label(o, c)).font(DM.mono(9, .medium)).foregroundStyle(.white.opacity(0.92)).lineLimit(2).multilineTextAlignment(.center).frame(width: 66)
                                    }
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }
                    if placeLabel != h.label {
                        Button {
                            MyPlace.save(MyPlace.Saved(label: h.label, coord: h.coord, slug: h.slug, cd: h.cd, bbl: "", number: Int(h.label.split(separator: " ").first.map { $0.filter(\\.isNumber) } ?? "") ?? 0))
                            NotificationCenter.default.post(name: MyReps.changed, object: nil)
                        } label: {
                            Text(MyReps.t("saveBlock", "Save as my block")).font(DM.sans(13, .bold)).foregroundStyle(Color.cb6Navy)
                                .padding(.horizontal, 14).padding(.vertical, 7).background(Color.cb6Orange, in: Capsule())
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(14)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.cb6Navy, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
            }
        }
        .task(id: query) {
            let q = query.trimmingCharacters(in: .whitespaces)
            guard q.count > 3, q.first?.isNumber == true else { hit = nil; reps = []; return }
            try? await Task.sleep(nanoseconds: 250_000_000)
            if Task.isCancelled { return }
            let exact = AddressIndex.points(q, scope: .city)
            let h = exact.first ?? AddressIndex.search(q, scope: .city).first
            hit = h
            reps = h.map { MyReps.mine(at: $0.coord, cd: $0.cd) } ?? []
        }
    }
}

/// Every official, searchable, with a star to follow.
struct MyRepsPicker: View {
    @Environment(\\.dismiss) private var dismiss
    @AppStorage(MyReps.followKey) private var followRaw = ""
    @State private var q = ""
    private var list: [Official] {
        let ord = MyReps.order
        let all = DKOfficials.all.filter { ord.contains(MyReps.key($0)) }
            .sorted { (MyReps.rank($0, ord), $0.district ?? 0, $0.name) < (MyReps.rank($1, ord), $1.district ?? 0, $1.name) }
        let s = q.trimmingCharacters(in: .whitespaces).lowercased()
        return s.isEmpty ? all : all.filter { "\\($0.name) \\($0.seat) \\($0.boro)".lowercased().contains(s) }
    }
    var body: some View {
        NavigationStack {
            List(list, id: \\.slug) { o in
                let on = followRaw.split(separator: ",").contains(Substring(o.slug))
                Button {
                    MyReps.toggle(o.slug)
                    if !on { Task { await MyReps.ask() } }
                } label: {
                    HStack(spacing: 10) {
                        OfficialIcon(slug: o.slug, size: 38).clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
                        VStack(alignment: .leading, spacing: 2) {
                            Text(o.name).font(DM.sans(15, .bold)).foregroundStyle(Color.cb6Navy)
                            Text(o.seat).font(DM.sans(12)).foregroundStyle(Color.cb6Muted).lineLimit(2)
                        }
                        Spacer()
                        Image(systemName: on ? "star.fill" : "star").font(.system(size: 18, weight: .bold)).foregroundStyle(Color.cb6Orange)
                    }
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
            }
            .listStyle(.plain)
            .searchable(text: $q)
            .navigationTitle(MyReps.t("pickTitle", "Follow officials"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button(MyReps.t("done", "Done")) { dismiss() } } }
        }
    }
}

/// On an official's profile: follow for alerts of their events and a place in the Home row.
struct FollowRepButton: View {
    let slug: String
    @AppStorage(MyReps.followKey) private var followRaw = ""
    var body: some View {
        let on = followRaw.split(separator: ",").contains(Substring(slug))
        Button {
            MyReps.toggle(slug)
            if !on { Task { await MyReps.ask() } }
        } label: {
            Label(on ? MyReps.t("following", "Following") : MyReps.t("follow", "Follow"), systemImage: on ? "star.fill" : "star")
                .font(DM.sans(14, .bold)).foregroundStyle(on ? Color.cb6Navy : Color.white)
                .padding(.horizontal, 16).padding(.vertical, 8)
                .background(on ? Color.cb6Orange : Color.white.opacity(0.18), in: Capsule())
        }
        .buttonStyle(.plain)
    }
}
'''
    wr(tl, s)
print('myreps ok', R)
