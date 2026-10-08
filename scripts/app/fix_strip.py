"""The day's strip (today, parking, sanitation, subway, weather) is its own Home section, kind "strip", placed where
home.json puts it; when home.json has one, the map section draws the map alone. Runs after fix_mapfold.py.
fix_strip.py <app dir>"""
import sys, os
R = sys.argv[1]
hv = os.path.join(R, 'App/Views/HomeView.swift')
if os.path.exists(hv):
    s = open(hv).read()
    if 'case "strip":' not in s:
        old = '''                            case "map":
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
        new = '''                            case "strip": HomePlanningMapCard(part: .strip).padding(.top, 14).id("strip")
                            case "map":
                                // With a "strip" section elsewhere on Home the map comes alone; otherwise the day's strip tops it.
                                let hasStrip = (UIConfig.shared.sections("home") ?? HomeView.defaultSections).contains { $0.kind == "strip" }
                                if s.fold {
                                    // The day's strip stays in view; the map sits under the fold header, closed unless home.json opens it.
                                    if !hasStrip { HomePlanningMapCard(part: .strip).padding(.top, 14) }
                                    HomeFold(title: s.title.isEmpty ? Copy.t("HomeView.ad87f8e3", "The map") : s.title, id: s.id, open: s.open || Hook.flag("-openAll")) {
                                        HomePlanningMapCard(part: .map).padding(.top, 8)
                                    }
                                    .id("homemap")
                                } else {
                                    HomePlanningMapCard(part: hasStrip ? .map : .both).padding(.top, 14).id("homemap")
                                }
'''
        assert old in s, 'HomeView map case'
        s = s.replace(old, new, 1); open(hv, 'w').write(s)
    print('HomeView strip ok')
bk = os.path.join(R, 'App/Views/BKHome.swift')
if os.path.exists(bk):
    s = open(bk).read()
    if 'case "strip":' not in s:
        old = '''                            case "map":
                                if s.fold {
                                    // The day's strip stays in view; the map sits under the fold header, closed unless home.json opens it.
                                    mapStrip.padding(.top, 14)
                                    HomeFold(title: s.title.isEmpty ? Copy.t("BKHome.ad87f8e3", "The map") : s.title, id: s.id, open: s.open || Hook.flag("-openAll")) { mapOnly.padding(.top, 8) }
                                        .id("homemap")
                                } else {
                                    mapCard.padding(.top, 14).id("homemap")
                                }
'''
        new = '''                            case "strip": mapStrip.padding(.top, 14).id("strip")
                            case "map":
                                // With a "strip" section elsewhere on Home the map comes alone; otherwise the day's strip tops it.
                                let hasStrip = (UIConfig.shared.sections("home") ?? BKHomeView.defaultSections).contains { $0.kind == "strip" }
                                if s.fold {
                                    if !hasStrip { mapStrip.padding(.top, 14) }
                                    HomeFold(title: s.title.isEmpty ? Copy.t("BKHome.ad87f8e3", "The map") : s.title, id: s.id, open: s.open || Hook.flag("-openAll")) { mapOnly.padding(.top, 8) }
                                        .id("homemap")
                                } else if hasStrip {
                                    mapOnly.padding(.top, 14).id("homemap")
                                } else {
                                    mapCard.padding(.top, 14).id("homemap")
                                }
'''
        assert old in s, 'BKHome map case'
        s = s.replace(old, new, 1); open(bk, 'w').write(s)
    print('BKHome strip ok')
