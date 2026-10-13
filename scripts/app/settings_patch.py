"""Settings: wires the block card and the calendar to what the person chose in Settings, and puts Settings on Home.
Usage: python3 settings_patch.py <project dir>   (idempotent; prints what it changed)"""
import sys, os, re
P = sys.argv[1].rstrip('/')
V = f'{P}/BKCB6/App/Views'
changed = []

KEY = re.compile(r'((?:Sz|Copy\.t|Copy\.f|MapStyle\.symbol|MapStyle\.color)\(")([^"]+)(")')

def pattern(old):
    """The block as a regex: the copy and size keys, and FeedsView's arguments, may differ from app to app."""
    out, pos = '', 0
    for m in re.finditer(KEY.pattern + r'|FeedsView\([^)]*\)', old):
        out += re.escape(old[pos:m.start()])
        out += (re.escape(m.group(1)) + r'[^"]+' + re.escape(m.group(3))) if m.group(1) else r'FeedsView\([^)]*\)'
        pos = m.end()
    return out + re.escape(old[pos:])

def adapt(old, new, got):
    """The replacement with this app's own keys and FeedsView call."""
    ko = [m.group(2) for m in KEY.finditer(old)]; kg = [m.group(2) for m in KEY.finditer(got)]
    for a, b in zip(ko, kg):
        if a != b: new = new.replace('"' + a + '"', '"' + b + '"')
    fo = re.findall(r'FeedsView\([^)]*\)', old); fg = re.findall(r'FeedsView\([^)]*\)', got)
    for a, b in zip(fo, fg): new = new.replace(a, b)
    return new

def edit(path, pairs, must=True):
    s = open(path).read(); orig = s
    for old, new in pairs:
        if re.search(pattern(new), s): continue   # already applied
        m = re.search(pattern(old), s)
        if not m:
            if must: raise SystemExit(f'NOT FOUND in {path}:\n{old[:200]}')
            print('skipped in', os.path.basename(path), ':', old.strip().splitlines()[0][:80]); continue
        s = s[:m.start()] + adapt(old, new, m.group(0)) + s[m.end():]
    if s != orig: open(path, 'w').write(s); changed.append(os.path.basename(path))

# 1. The block card's rows, pills and chips: off when Settings turns them off.
edit(f'{V}/ExploreViews.swift', [
    ("""    @StateObject private var locator = OneShotLocation()

    private var coord: CLLocationCoordinate2D? { lat == 0 ? nil : CLLocationCoordinate2D(latitude: lat, longitude: lon) }
""", """    @StateObject private var locator = OneShotLocation()
    /// The parts of the card turned off in Settings.
    @AppStorage(Prefs.blockOffKey) private var blockOffRaw = ""
    private var blockOff: Set<String> { Prefs.parse(blockOffRaw) }

    private var coord: CLLocationCoordinate2D? { lat == 0 ? nil : CLLocationCoordinate2D(latitude: lat, longitude: lon) }
"""),
    ("""                rows(s)
                HStack(spacing: Sz("ExploreViews.z.942bc8f4", 8)) {
                    if let b = s.block {""", """                rows(s)
                if !blockOff.contains("buttons") {
                HStack(spacing: Sz("ExploreViews.z.942bc8f4", 8)) {
                    if let b = s.block {"""),
    ("""                        NavigationLink { FeedsView(startPin: c) } label: { pill(Copy.t("ExploreViews.09eee297", "311, crime and permits nearby")) }.buttonStyle(.plain)
                        }
                    }
                }
            } else {""", """                        NavigationLink { FeedsView(startPin: c) } label: { pill(Copy.t("ExploreViews.09eee297", "311, crime and permits nearby")) }.buttonStyle(.plain)
                        }
                    }
                }
                }
            } else {"""),
    ("""        ForEach(Array(Lists.objects("MyBlock.rows", Self.defaultRows).enumerated()), id: \\.offset) { _, r in
            let id = DK.str(r["id"]), icon = DK.str(r["icon"]), color = DK.str(r["color"]), title = DK.str(r["title"])
            if id == "button" {""", """        ForEach(Array(Lists.objects("MyBlock.rows", Self.defaultRows).enumerated()), id: \\.offset) { _, r in
            let id = DK.str(r["id"]), icon = DK.str(r["icon"]), color = DK.str(r["color"]), title = DK.str(r["title"])
            if blockOff.contains(id) {
                EmptyView()   // turned off in Settings
            } else if id == "button" {"""),
])

# 2. Today's alerts, the next 30 days, filings and the chips: off when Settings turns them off.
edit(f'{V}/MyBlock.swift', [
    ("""    @State private var showAll = UIConfig.shared.isOpen("MyBlock", "showAll", false)
""", """    @State private var showAll = UIConfig.shared.isOpen("MyBlock", "showAll", false)
    /// The parts of the card turned off in Settings.
    @AppStorage(Prefs.blockOffKey) private var blockOffRaw = ""
    private var blockOff: Set<String> { Prefs.parse(blockOffRaw) }
"""),
    ("""            ForEach(Array(todayLines().enumerated()), id: \\.offset) { _, l in line(l.0, l.1, l.2, l.3) }
            newsSection
            HStack(spacing: Sz("MyBlock.z.04531f7e", 8)) {""", """            if !blockOff.contains("today") { ForEach(Array(todayLines().enumerated()), id: \\.offset) { _, l in line(l.0, l.1, l.2, l.3) } }
            if !blockOff.contains("news") { newsSection }
            if !blockOff.contains("buttons") {
            HStack(spacing: Sz("MyBlock.z.04531f7e", 8)) {"""),
    ("""                    NavigationLink { LotRecordsView(bbl: b, label: place.label) } label: { chip(Copy.t("MyBlock.12a94ac2", "City records for the lot"), MapStyle.symbol("MyBlock.s.7f2f02af", "building.columns.fill")) }.buttonStyle(.plain)
                    }
                }
            }
        }""", """                    NavigationLink { LotRecordsView(bbl: b, label: place.label) } label: { chip(Copy.t("MyBlock.12a94ac2", "City records for the lot"), MapStyle.symbol("MyBlock.s.7f2f02af", "building.columns.fill")) }.buttonStyle(.plain)
                    }
                }
            }
            }
        }"""),
    ("""            if !hide.contains("filings"), !filings.isEmpty {""", """            if !hide.contains("filings"), !blockOff.contains("filings"), !filings.isEmpty {"""),
])

# 3. The calendar: organizations turned off stay off; it opens the way Settings says.
edit(f'{V}/BKCalendar.swift', [
    ("""    @State private var addOn: Set<String> = []
""", """    @State private var addOn: Set<String> = []
    /// Settings: organizations turned off, and how the calendar opens (applied once, when the screen first appears).
    @AppStorage(Prefs.calHiddenKey) private var hiddenRaw = ""
    private var hidden: Set<String> { Prefs.parse(hiddenRaw) }
    @State private var prefsApplied = false
"""),
    ("""    private func passes(_ e: CalEvent) -> Bool {
        if !added(e) { return false }
""", """    private func passes(_ e: CalEvent) -> Bool {
        if !added(e) { return false }
        if hidden.contains(orgKey(e)) { return false }
"""),
    ("""    private var today: [CalEvent] { events.filter { $0.dateKey == todayKey && added($0) } }
    private var orgs: [(key: String, name: String, count: Int)] {
        var n: [String: Int] = [:]
        for e in events where added(e) { n[orgKey(e), default: 0] += 1 }""", """    private var today: [CalEvent] { events.filter { $0.dateKey == todayKey && added($0) && !hidden.contains(orgKey($0)) } }
    private var orgs: [(key: String, name: String, count: Int)] {
        var n: [String: Int] = [:]
        for e in events where added(e) && !hidden.contains(orgKey(e)) { n[orgKey(e), default: 0] += 1 }"""),
    ("""        .onAppear {
            reload()
            if Hook.value("-calview") == "grid" { mode = .grid }""", """        .onAppear {
            reload()
            if !prefsApplied {
                prefsApplied = true
                mode = Prefs.calView == "grid" ? .grid : .list
                cat = Prefs.calCat
                addOn = Prefs.calAdd
            }
            if Hook.value("-calview") == "grid" { mode = .grid }"""),
])

# 4. Home: the Settings card (home.json kind "settings") and the screen ("settings").
edit(f'{V}/HomeView.swift', [
    ("""                            case "reading": NavigationLink(value: "reading") { ReadingButton() }.buttonStyle(.plain).padding(.top, Sz("HomeView.z.48492519", 16))
                            default: EmptyView()""", """                            case "reading": NavigationLink(value: "reading") { ReadingButton() }.buttonStyle(.plain).padding(.top, Sz("HomeView.z.48492519", 16))
                            case "settings": SettingsHomeCard { path.append("settings") }.id("settings")
                            default: EmptyView()"""),
    ("""        case "help": AnyView(HelpView())
        case "faq": AnyView(FAQView())""", """        case "help": AnyView(HelpView())
        case "settings": AnyView(SettingsView())
        case "faq": AnyView(FAQView())"""),
], must=False)

print('changed:', changed)
