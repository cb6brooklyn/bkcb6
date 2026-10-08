"""Any fixed Home section can sit under a fold header from home.json ("fold": true, "open": false, "title": ...).
The map handles its own fold: the day's strip (parking, sanitation, subway, weather) stays above the header and the
map itself folds. Build 113 ignores the "fold" key, so the file can carry it now. fix_mapfold.py <app dir>"""
import sys, os
R = sys.argv[1]
# 1. the section model and the generic fold
p = os.path.join(R, 'App/Services/UIConfig.swift'); s = open(p).read()
if 'var fold: Bool = false' not in s:
    s = s.replace('        let open: Bool\n    }\n    func sections(', '        let open: Bool\n        /// A fixed section shown under a fold header ("fold": true), open or closed by "open".\n        var fold: Bool = false\n    }\n    func sections(', 1)
    s = s.replace('when: r["when"] as? String ?? "always", open: r["open"] as? Bool ?? false)', 'when: r["when"] as? String ?? "always", open: r["open"] as? Bool ?? false, fold: r["fold"] as? Bool ?? false)', 1)
    old = '''            } else {
                fixed(s)
            }
        }
    }'''
    new = '''            } else if s.fold && s.kind != "map" {    // the map draws its own fold, keeping the day's strip above it
                HomeFold(title: titleFor(s), id: s.id, open: s.open || Hook.flag("-openAll")) { fixed(s) }
            } else {
                fixed(s)
            }
        }
    }'''
    assert old in s and 'var fold: Bool = false' in s and 'fold: r["fold"]' in s, 'UIConfig'
    s = s.replace(old, new, 1); open(p, 'w').write(s)
print('UIConfig fold', s.count('s.fold'))
# 2. BKCB6: the map card in three parts
hv = os.path.join(R, 'App/Views/HomeView.swift')
if os.path.exists(hv):
    s = open(hv).read()
    old = '                            case "map": HomePlanningMapCard().padding(.top, 14).id("homemap")\n'
    new = '''                            case "map":
                                if s.fold {
                                    // The day's strip stays in view; the map sits under the fold header, closed unless home.json opens it.
                                    HomePlanningMapCard(part: .strip).padding(.top, 14)
                                    HomeFold(title: s.title.isEmpty ? Copy.t("HomeView.ad87f8e3", "The map") : s.title, id: s.id, open: s.open || Hook.flag("-openAll")) {
                                        HomePlanningMapCard(part: .map).padding(.top, 8)
                                    }
                                    .id("homemap")
                                } else {
                                    HomePlanningMapCard().padding(.top, 14).id("homemap")
                                }
'''
    if old in s: s = s.replace(old, new, 1)
    old2 = '''struct HomePlanningMapCard: View {
    @EnvironmentObject var store: DataStore'''
    new2 = '''struct HomePlanningMapCard: View {
    enum Part { case both, strip, map }
    /// The whole card, the day's strip alone (above a fold), or the map alone (inside it).
    var part: Part = .both
    @EnvironmentObject var store: DataStore'''
    if old2 in s: s = s.replace(old2, new2, 1)
    old3 = '''        VStack(spacing: 0) {
            HomeStatusBanner()
            CB6MapView(embedded: true)
        }'''
    new3 = '''        VStack(spacing: 0) {
            if part != .map { HomeStatusBanner() }
            if part != .strip { CB6MapView(embedded: true) }
        }'''
    if old3 in s: s = s.replace(old3, new3, 1)
    assert 'part: .strip' in s and 'if part != .map' in s, 'HomeView'
    open(hv, 'w').write(s); print('HomeView map fold ok')
# 3. BKCB and CBNYC
bk = os.path.join(R, 'App/Views/BKHome.swift')
if os.path.exists(bk):
    s = open(bk).read()
    old = '                            case "map": mapCard.padding(.top, 14).id("homemap")\n'
    new = '''                            case "map":
                                if s.fold {
                                    // The day's strip stays in view; the map sits under the fold header, closed unless home.json opens it.
                                    mapStrip.padding(.top, 14)
                                    HomeFold(title: s.title.isEmpty ? Copy.t("BKHome.ad87f8e3", "The map") : s.title, id: s.id, open: s.open || Hook.flag("-openAll")) { mapOnly.padding(.top, 8) }
                                        .id("homemap")
                                } else {
                                    mapCard.padding(.top, 14).id("homemap")
                                }
'''
    if old in s: s = s.replace(old, new, 1)
    old2 = '''    @ViewBuilder private var mapCard: some View {
        VStack(spacing: 0) {
            HomeStatusBanner('''
    new2 = '''    /// The day's strip alone, above the map's fold header.
    @ViewBuilder private var mapStrip: some View {
        VStack(spacing: 0) {
            HomeStatusBanner(routes: sel.cd.isEmpty ? CityStatus.brooklynRoutes : BKBoards.routes(cd),
                             subwayTitle: sel.cd.isEmpty ? Copy.t("BKHome.62ae0cd6", "Subway in Brooklyn") : Copy.f("BKHome.699a36a5", "Subway in {0}", sel.short))
        }
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(Color.cb6Rule, lineWidth: 1))
        .shadow(color: .black.opacity(0.06), radius: 8, y: 3)
    }

    /// The map alone, inside its fold.
    @ViewBuilder private var mapOnly: some View {
        VStack(spacing: 0) {
            if sel.isCB6 { CB6MapView(embedded: true) } else { BoardHomeMap(cd: cd).id("map-\\(cd)") }
        }
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(Color.cb6Rule, lineWidth: 1))
        .shadow(color: .black.opacity(0.06), radius: 8, y: 3)
    }

    @ViewBuilder private var mapCard: some View {
        VStack(spacing: 0) {
            HomeStatusBanner('''
    if old2 in s: s = s.replace(old2, new2, 1)
    assert 'private var mapStrip' in s and 'private var mapOnly' in s and 'mapStrip.padding' in s, 'BKHome'
    open(bk, 'w').write(s); print('BKHome map fold ok')
