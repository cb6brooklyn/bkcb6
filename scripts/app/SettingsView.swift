import SwiftUI
import CoreLocation

// Settings: what a person chooses for themselves, kept on the phone. Their block and address (the one Home, the map and
// the calendar use), which parts of the Your block card show, and what the calendar shows and how it opens.
// Every title and label here can be changed in civic/copy.json like the rest of the app.

enum Prefs {
    static let blockOffKey = "prefs.block.off"      // ids of the block card's parts that are off, comma-separated
    static let calHiddenKey = "prefs.cal.hidden"    // calendar organization keys that are off, comma-separated
    static let calViewKey = "prefs.cal.view"        // "list" or "grid": how the calendar opens
    static let calCatKey = "prefs.cal.cat"          // the category the calendar opens on ("" for all)
    static let calAddKey = "prefs.cal.add"          // "council", "hearing": the added calendars on from the start

    static func parse(_ raw: String) -> Set<String> { Set(raw.split(separator: ",").map { String($0) }.filter { !$0.isEmpty }) }
    static func raw(_ s: Set<String>) -> String { s.sorted().joined(separator: ",") }

    static var blockOff: Set<String> { parse(UserDefaults.standard.string(forKey: blockOffKey) ?? "") }
    static func blockOn(_ id: String) -> Bool { !blockOff.contains(id) }
    static var calHidden: Set<String> { parse(UserDefaults.standard.string(forKey: calHiddenKey) ?? "") }
    static var calView: String { UserDefaults.standard.string(forKey: calViewKey) ?? "list" }
    static var calCat: String { UserDefaults.standard.string(forKey: calCatKey) ?? "" }
    static var calAdd: Set<String> { parse(UserDefaults.standard.string(forKey: calAddKey) ?? "") }

    /// The parts of the Your block card a person can turn off, in the order the card draws them.
    static var blockParts: [(id: String, title: String)] { [
        ("today", Copy.t("SettingsView.9c2f6dfc", "Today and tomorrow: parking, pickup and voting alerts")),
        ("news", Copy.t("SettingsView.735db633", "Next 30 days on your block: events, film shoots, street work")),
        ("filings", Copy.t("SettingsView.f25d14d1", "New building filings on your tax block")),
        ("trash", Copy.t("SettingsView.9c5a6eb4", "Trash and recycling")),
        ("parking", Copy.t("SettingsView.966c2cc9", "Alternate side parking")),
        ("polls", Copy.t("SettingsView.baf24b83", "Election Day poll site")),
        ("precinct", Copy.t("SettingsView.bde603b2", "Police precinct")),
        ("subway", Copy.t("SettingsView.a8ce893a", "Nearest subway")),
        ("reps", Copy.t("SettingsView.9e73a044", "Who represents you")),
        ("ballot", Copy.t("SettingsView.f277c586", "On your ballot")),
        ("park", Copy.t("SettingsView.2c877ae9", "Nearest park")),
        ("nearby", Copy.t("SettingsView.91863f09", "311 complaints and permits within 150 m")),
        ("buttons", Copy.t("SettingsView.af063483", "Buttons: full block card, address card, 311 and permits nearby"))
    ] }

    static func reset() {
        for k in [blockOffKey, calHiddenKey, calViewKey, calCatKey, calAddKey] { UserDefaults.standard.removeObject(forKey: k) }
    }
}

/// The Settings screen.
struct SettingsView: View {
    @EnvironmentObject var store: DataStore
    @AppStorage(MyPlaceKeys.label) private var label = ""
    @AppStorage(MyPlaceKeys.lat) private var lat = 0.0
    @AppStorage(MyPlaceKeys.lon) private var lon = 0.0
    @AppStorage(Prefs.blockOffKey) private var blockOffRaw = ""
    @AppStorage(Prefs.calHiddenKey) private var calHiddenRaw = ""
    @AppStorage(Prefs.calViewKey) private var calView = "list"
    @AppStorage(Prefs.calCatKey) private var calCat = ""
    @AppStorage(Prefs.calAddKey) private var calAddRaw = ""
    @State private var editing = false
    @State private var confirmReset = false

    private var blockOff: Set<String> { Prefs.parse(blockOffRaw) }
    private var calHidden: Set<String> { Prefs.parse(calHiddenRaw) }
    private var calAdd: Set<String> { Prefs.parse(calAddRaw) }
    private var types: [String: CalType] { CalData.load(.cb6).types }

    /// Every organization with something on the calendar, CB6 first, then by name.
    private var orgs: [(key: String, name: String, count: Int)] {
        var n: [String: Int] = [:]
        for e in CalData.merged(.cb6, meetings: store.meetings) { n[e.isCB6 ? "__cb6" : e.type, default: 0] += 1 }
        return n.map { ($0.key, $0.key == "__cb6" ? Copy.t("SettingsView.1f6cb944", "Brooklyn Community Board 6") : (types[$0.key]?.name ?? $0.key), $0.value) }
            .sorted { $0.key == "__cb6" ? true : ($1.key == "__cb6" ? false : $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending) }
    }

    var body: some View {
        ScrollViewReader { proxy in
        ScrollView {
            FileParts("settings", ["address", "blockcard", "calendar", "organizations", "reset"], alignment: .leading, spacing: 0) { part in
                switch part {
                case "address": AnyView(Group { SectionHeader(text: Copy.t("SettingsView.522464d1", "Your block and address")).id("address"); addressCard })
                case "blockcard": AnyView(Group { SectionHeader(text: Copy.t("SettingsView.498f3558", "Your block card on Home")).id("blockcard"); blockCard })
                case "calendar": AnyView(Group { SectionHeader(text: Copy.t("SettingsView.adab5090", "Calendar")).id("calendar"); calendarCard })
                case "organizations": AnyView(Group { SectionHeader(text: Copy.t("SettingsView.d6a97f77", "Organizations on the calendar")).id("organizations"); orgsCard })
                case "reset": AnyView(Group { resetRow.id("reset") })
                default: AnyView(EmptyView())
                }
            }
            .padding(.horizontal, Sz("SettingsView.z.8c9d4dc5", 16)).padding(.bottom, Sz("SettingsView.z.8c2561b2", 28))
        }
        .background(Color.cb6Paper)
        .cb6Page(Copy.t("SettingsView.c7f73bb5", "Settings"), Copy.t("SettingsView.1f6cb944", "Brooklyn Community Board 6"))
        .onAppear {
            // Screenshot hook only: `-settingsEdit` opens the address entry.
            if Hook.flag("-settingsEdit") { editing = true }
            if let a = Hook.value("-scrollTo") { DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { proxy.scrollTo(a, anchor: .top) } }
        }
        }
    }

    // MARK: Your block and address

    private var addressCard: some View {
        Card {
            if lat != 0, !editing {
                Text(LocalizedStringKey(Copy.t("SettingsView.6967306f", "YOUR BLOCK"))).font(DM.mono(Sz("SettingsView.z.6d6ea3d7", 11), .medium)).tracking(1.1).foregroundStyle(Color.cb6Orange)
                Text(label).font(DM.sans(Sz("SettingsView.z.689bccbd", 19), .bold)).foregroundStyle(Color.cb6Navy).fixedSize(horizontal: false, vertical: true)
                Text(LocalizedStringKey(Copy.t("SettingsView.bbf15187", "Home shows this block: trash days, parking, the poll site, who represents it and what is happening on it. The map opens on it too.")))
                    .font(DM.sans(Sz("SettingsView.z.40ec06c7", 13))).foregroundStyle(Color.cb6Muted).fixedSize(horizontal: false, vertical: true)
                HStack(spacing: Sz("SettingsView.z.5d02206a", 10)) {
                    FileAction("SettingsView.64fbd995") {
                    Button { editing = true } label: { pill(Copy.t("SettingsView.64fbd995", "Change"), filled: true) }.buttonStyle(.plain)
                    }
                    FileAction("SettingsView.a0c3d8b2") {
                    Button { MyPlace.clear(); editing = false } label: { pill(Copy.t("SettingsView.e963907d", "Remove"), filled: false) }.buttonStyle(.plain)
                    }
                }
                Text(LocalizedStringKey(Copy.t("SettingsView.8e7cb391", "The address is saved on this phone only."))).font(DM.sans(Sz("SettingsView.z.0d70a1ff", 11))).foregroundStyle(Color.cb6Muted)
            } else {
                if lat == 0 {
                    Text(LocalizedStringKey(Copy.t("SettingsView.30ed6361", "No address saved yet."))).font(DM.sans(Sz("SettingsView.z.894243a7", 17), .bold)).foregroundStyle(Color.cb6Navy)
                    Text(LocalizedStringKey(Copy.t("SettingsView.b92b7ce2", "Enter an address for trash days, parking, the poll site, who represents it and what is happening nearby"))).font(DM.sans(Sz("SettingsView.z.40ec06c7", 13))).foregroundStyle(Color.cb6Muted)
                        .fixedSize(horizontal: false, vertical: true)
                }
                AddressPicker(cancel: lat == 0 ? nil : { editing = false }) { name, c in
                    let d = UserDefaults.standard
                    d.set(name, forKey: MyPlaceKeys.label); d.set(c.latitude, forKey: MyPlaceKeys.lat); d.set(c.longitude, forKey: MyPlaceKeys.lon)
                    NotificationCenter.default.post(name: MyPlace.changed, object: nil)
                    editing = false
                }
            }
        }
    }

    // MARK: The block card

    private var blockCard: some View {
        Card {
            Text(LocalizedStringKey(Copy.t("SettingsView.b795b65f", "Choose what the Your block card shows. Everything is on until you turn it off.")))
                .font(DM.sans(Sz("SettingsView.z.40ec06c7", 13))).foregroundStyle(Color.cb6Muted).fixedSize(horizontal: false, vertical: true)
            ForEach(Prefs.blockParts, id: \.id) { p in
                Toggle(isOn: Binding(get: { !blockOff.contains(p.id) }, set: { on in
                    var s = blockOff; if on { s.remove(p.id) } else { s.insert(p.id) }; blockOffRaw = Prefs.raw(s)
                })) {
                    Text(p.title).font(DM.sans(Sz("SettingsView.z.3f479b6d", 15))).foregroundStyle(Color.cb6Ink).fixedSize(horizontal: false, vertical: true)
                }
                .tint(Color.cb6Orange)
            }
        }
    }

    // MARK: The calendar

    private static var cats: [(String, String)] { Lists.pairs("BKCalendar.cats", [("", "All"), ("cb6", "CB6"), ("arts", "Arts"), ("food", "Food & Markets"),
                                                   ("civic", Copy.t("BKCalendar.60a6e5ba", "Civic")), ("parks", Copy.t("BKCalendar.2e1a43ff", "Parks")), ("community", Copy.t("BKCalendar.bfd58ee3", "Community"))]) }

    private var calendarCard: some View {
        Card {
            Text(LocalizedStringKey(Copy.t("SettingsView.5a8f860b", "Opens as"))).font(DM.sans(Sz("SettingsView.z.abe5af47", 12), .bold)).foregroundStyle(Color.cb6Muted)
            Picker("", selection: $calView) {
                Text(LocalizedStringKey(Copy.t("SettingsView.a1fffaaa", "List"))).tag("list")
                Text(LocalizedStringKey(Copy.t("SettingsView.adab5090", "Calendar"))).tag("grid")
            }
            .pickerStyle(.segmented)
            Text(LocalizedStringKey(Copy.t("SettingsView.6d888f78", "Starts on"))).font(DM.sans(Sz("SettingsView.z.abe5af47", 12), .bold)).foregroundStyle(Color.cb6Muted).padding(.top, Sz("SettingsView.z.e38fef99", 6))
            CalFlow(spacing: 6) {
                ForEach(Self.cats, id: \.0) { k, name in
                    let on = calCat == k
                    Button { calCat = k } label: {
                        Text(name).font(DM.sans(Sz("SettingsView.z.a07f9fcb", 14), .medium))
                            .foregroundStyle(on ? .white : Color.cb6Navy)
                            .padding(.horizontal, Sz("SettingsView.z.00b9f117", 14)).padding(.vertical, Sz("SettingsView.z.21bae8fc", 7))
                            .background(on ? Color.cb6Navy : Color.white, in: Capsule())
                            .overlay(Capsule().stroke(on ? Color.cb6Navy : Color.cb6Rule, lineWidth: 1))
                    }
                    .buttonStyle(.plain)
                }
            }
            Text(LocalizedStringKey(Copy.t("SettingsView.cab2787d", "Added calendars"))).font(DM.sans(Sz("SettingsView.z.abe5af47", 12), .bold)).foregroundStyle(Color.cb6Muted).padding(.top, Sz("SettingsView.z.e38fef99", 6))
            ForEach([("council", Copy.t("SettingsView.e991ad82", "City Council")), ("hearing", Copy.t("SettingsView.db7c2511", "Public hearings"))], id: \.0) { k, name in
                Toggle(isOn: Binding(get: { calAdd.contains(k) }, set: { on in
                    var s = calAdd; if on { s.insert(k) } else { s.remove(k) }; calAddRaw = Prefs.raw(s)
                })) {
                    Text(name).font(DM.sans(Sz("SettingsView.z.3f479b6d", 15))).foregroundStyle(Color.cb6Ink)
                }
                .tint(Color.cb6Orange)
            }
        }
    }

    private var orgsCard: some View {
        Card {
            Text(LocalizedStringKey(Copy.t("SettingsView.5f2564ff", "Turn an organization off to keep its meetings and events off the calendar.")))
                .font(DM.sans(Sz("SettingsView.z.40ec06c7", 13))).foregroundStyle(Color.cb6Muted).fixedSize(horizontal: false, vertical: true)
            ForEach(orgs, id: \.key) { o in
                Toggle(isOn: Binding(get: { !calHidden.contains(o.key) }, set: { on in
                    var s = calHidden; if on { s.remove(o.key) } else { s.insert(o.key) }; calHiddenRaw = Prefs.raw(s)
                })) {
                    HStack(spacing: Sz("SettingsView.z.86845d35", 8)) {
                        orgIcon(o.key, 24)
                        Text(o.name).font(DM.sans(Sz("SettingsView.z.3f479b6d", 15))).foregroundStyle(Color.cb6Ink).lineLimit(2)
                        Text("\(o.count)").font(DM.mono(Sz("SettingsView.z.4c7ad421", 11))).foregroundStyle(Color.cb6Muted)
                    }
                }
                .tint(Color.cb6Orange)
            }
            if !calHidden.isEmpty {
                FileAction("SettingsView.6a720856") {
                Button { calHiddenRaw = "" } label: { pill(Copy.t("SettingsView.b9505121", "Turn them all on"), filled: false) }.buttonStyle(.plain)
                }
            }
        }
    }

    @ViewBuilder private func orgIcon(_ key: String, _ s: CGFloat) -> some View {
        if key == "__cb6" {
            LogoImage(name: Copy.t("SettingsView.900333f1", "CB6_540"), size: s)
        } else if let icon = types[key]?.icon, let ui = CalData.image("icons", icon) {
            Image(uiImage: ui).resizable().scaledToFit().frame(width: s, height: s)
                .clipShape(RoundedRectangle(cornerRadius: 4, style: .continuous))
        } else {
            Text(types[key]?.emoji ?? "•").font(.system(size: s * 0.5))
                .frame(width: s, height: s).background(types[key]?.bg ?? Color.cb6Navy, in: RoundedRectangle(cornerRadius: 4, style: .continuous))
        }
    }

    // MARK: Reset

    private var resetRow: some View {
        VStack(alignment: .leading, spacing: Sz("SettingsView.z.c2bb79ea", 8)) {
            FileAction("SettingsView.3d4e5f60") {
            Button { confirmReset = true } label: {
                Text(LocalizedStringKey(Copy.t("SettingsView.0d30736d", "Reset these settings"))).font(DM.sans(Sz("SettingsView.z.c3cbe6a4", 13), .medium)).foregroundStyle(Color.cb6Muted).underline()
            }
            .buttonStyle(.plain)
            }
            .confirmationDialog(Copy.t("SettingsView.4ebe86b7", "Turn every part of the block card and every organization back on, and open the calendar as a list? Your address stays."), isPresented: $confirmReset, titleVisibility: .visible) {
                Button(Copy.t("SettingsView.0d30736d", "Reset these settings"), role: .destructive) { Prefs.reset() }
                Button(Copy.t("SettingsView.77dfd213", "Cancel"), role: .cancel) {}
            }
        }
        .padding(.top, Sz("SettingsView.z.8ac0e82b", 16))
    }

    private func pill(_ t: String, filled: Bool) -> some View {
        Text(t).font(DM.sans(Sz("SettingsView.z.b8c76286", 14), .bold)).foregroundStyle(filled ? .white : Color.cb6Navy)
            .padding(.horizontal, Sz("SettingsView.z.927f142e", 14)).padding(.vertical, Sz("SettingsView.z.c76c7fab", 9))
            .background(filled ? Color.cb6Navy : Color.white, in: Capsule())
            .overlay(Capsule().stroke(Color.cb6Navy, lineWidth: 1.5))
    }
}

/// Type an address or use the phone's location; the same search Home's Your block card uses, from the bundled address index.
struct AddressPicker: View {
    var cancel: (() -> Void)?
    let pick: (String, CLLocationCoordinate2D) -> Void
    @State private var query = ""
    @StateObject private var locator = OneShotLocation()

    private var hits: [AddressMatch] {
        let q = query.trimmingCharacters(in: .whitespaces)
        guard q.count > 3 else { return [] }
        let exact = AddressIndex.points(q, scope: .city)
        return exact.isEmpty ? AddressIndex.search(q, scope: .city) : exact
    }

    var body: some View {
        VStack(alignment: .leading, spacing: Sz("SettingsView.z.feb8be5f", 10)) {
            HStack(spacing: Sz("SettingsView.z.68f72b3f", 8)) {
                Image(systemName: MapStyle.symbol("SettingsView.s.8709f7f6", "magnifyingglass")).foregroundStyle(Color.cb6Muted)
                TextField(Copy.t("SettingsView.cfd709ff", "Address, e.g. 250 Baltic Street"), text: $query).font(DM.sans(Sz("SettingsView.z.7ca1c7ef", 15))).autocorrectionDisabled()
            }
            .padding(.horizontal, Sz("SettingsView.z.1dc39bb2", 12)).padding(.vertical, Sz("SettingsView.z.dca45bf2", 10))
            .background(Color.cb6Paper, in: RoundedRectangle(cornerRadius: 10, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 10, style: .continuous).stroke(Color.cb6Rule, lineWidth: 1))
            ForEach(Array(hits.prefix(5).enumerated()), id: \.offset) { _, h in
                Button { pick(h.label.replacingOccurrences(of: ", Brooklyn", with: ""), h.coord); query = "" } label: {
                    HStack(spacing: Sz("SettingsView.z.c4ee0716", 8)) {
                        Image(systemName: MapStyle.symbol("SettingsView.s.f90dd65b", "mappin.circle.fill")).foregroundStyle(Color.cb6Orange)
                        Text(h.label).font(DM.sans(Sz("SettingsView.z.ef5166ce", 14))).foregroundStyle(Color.cb6Ink).multilineTextAlignment(.leading)
                        Spacer(minLength: 0)
                    }
                }
                .buttonStyle(.plain)
            }
            HStack(spacing: Sz("SettingsView.z.5d02206a", 10)) {
                FileAction("SettingsView.0132375d") {
                Button { locator.request() } label: {
                    Label(Copy.t("SettingsView.0132375d", "Use my location"), systemImage: MapStyle.symbol("SettingsView.s.3915084d", "location.fill")).font(DM.sans(Sz("SettingsView.z.b8c76286", 14), .bold)).foregroundStyle(.white)
                        .padding(.horizontal, Sz("SettingsView.z.927f142e", 14)).padding(.vertical, Sz("SettingsView.z.c76c7fab", 9)).background(Color.cb6Navy, in: Capsule())
                }
                .buttonStyle(.plain)
                }
                if let cancel {
                    FileAction("SettingsView.77dfd213") {
                    Button { query = ""; cancel() } label: {
                        Text(LocalizedStringKey(Copy.t("SettingsView.77dfd213", "Cancel"))).font(DM.sans(Sz("SettingsView.z.8c6e48d2", 14), .medium)).foregroundStyle(Color.cb6Muted)
                    }
                    .buttonStyle(.plain)
                    }
                }
            }
            if locator.denied {
                Text(LocalizedStringKey(Copy.t("SettingsView.7f3917c4", "Location is turned off for BKCB6. Type your address instead, or allow it in Settings."))).font(DM.sans(Sz("SettingsView.z.38058a6c", 12))).foregroundStyle(Color.cb6Muted)
            }
            Text(LocalizedStringKey(Copy.t("SettingsView.8e7cb391", "The address is saved on this phone only."))).font(DM.sans(Sz("SettingsView.z.0d70a1ff", 11))).foregroundStyle(Color.cb6Muted)
        }
        .onReceive(locator.$coordinate) { c in
            if let c { pick(Copy.t("SettingsView.37e3a3f3", "Your location"), c) }
        }
    }
}

/// Home's way into Settings: one card saying what is set, and a button.
struct SettingsHomeCard: View {
    var open: () -> Void
    @AppStorage(MyPlaceKeys.label) private var label = ""
    @AppStorage(Prefs.blockOffKey) private var blockOffRaw = ""
    @AppStorage(Prefs.calHiddenKey) private var calHiddenRaw = ""
    @AppStorage(Prefs.calViewKey) private var calView = "list"

    private var summary: String {
        let off = Prefs.parse(blockOffRaw).count, hidden = Prefs.parse(calHiddenRaw).count
        let block = off == 0 ? Copy.t("SettingsView.c1ae41ef", "the whole block card") : Copy.f("SettingsView.8e4e9f90", "{0} parts of the block card off", off)
        let cal = hidden == 0 ? (calView == "grid" ? Copy.t("SettingsView.07ec2466", "the calendar as a month") : Copy.t("SettingsView.ca62ce0f", "the calendar as a list"))
                              : Copy.f("SettingsView.97d9f84a", "{0} organizations off the calendar", hidden)
        return (label.isEmpty ? Copy.t("SettingsView.9e765533", "No address saved") : label) + " · " + block + " · " + cal
    }

    var body: some View {
        FileAction("SettingsView.f4f70727") {
        Button(action: open) {
            HStack(spacing: Sz("SettingsView.z.3e9d8d05", 12)) {
                Image(systemName: MapStyle.symbol("SettingsView.s.1a2b3c4d", "gearshape.fill")).font(.system(size: Sz("SettingsView.z.693d2735", 26), weight: .semibold)).foregroundStyle(Color.cb6Orange)
                VStack(alignment: .leading, spacing: Sz("SettingsView.z.b2922efa", 2)) {
                    Text(T("home.settings.title", Copy.t("SettingsView.c7f73bb5", "Settings"))).font(DM.sans(Sz("SettingsView.z.dc930bb1", 17), .bold)).foregroundStyle(Color.cb6Navy)
                    Text(T("home.settings.sub", Copy.t("SettingsView.f3b87984", "Your block and address, what the block card shows, what the calendar shows"))).font(DM.sans(Sz("SettingsView.z.3af68c51", 13))).foregroundStyle(Color.cb6Muted)
                        .fixedSize(horizontal: false, vertical: true)
                    Text(summary).font(DM.mono(Sz("SettingsView.z.03053c2b", 11))).foregroundStyle(Color.cb6Muted).fixedSize(horizontal: false, vertical: true)
                }
                Spacer(minLength: 0)
                Image(systemName: MapStyle.symbol("SettingsView.s.0d427863", "chevron.right")).font(.system(size: Sz("SettingsView.z.e36ae9a0", 14), weight: .bold)).foregroundStyle(Color.cb6Orange)
            }
            .padding(Sz("SettingsView.z.e73a7b83", 14))
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.white, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).stroke(Color.cb6Rule, lineWidth: 1))
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        }
        .padding(.top, Sz("SettingsView.z.8ac0e82b", 8))
    }
}
