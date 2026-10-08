"""A fold header can carry an icon from home.json ("icon": "map.fill" for an SF symbol, "logo:CB6_540" for a logo),
and the "What is a community board?" card drops its seal when copy.json blanks the logo name. fix_foldicon.py <app dir>"""
import sys, os
R = sys.argv[1]
# 1. the section model and the generic folds
p = os.path.join(R, 'App/Services/UIConfig.swift'); s = open(p).read()
if 'var icon: String = ""' not in s:
    s = s.replace('        var pinned: Bool = false\n    }\n', '        var pinned: Bool = false\n        /// An icon on the fold header: an SF symbol name, or "logo:<name>" for a logo under Logos/.\n        var icon: String = ""\n    }\n', 1)
    s = s.replace('pinned: r["pinned"] as? Bool ?? false)', 'pinned: r["pinned"] as? Bool ?? false, icon: r["icon"] as? String ?? "")', 1)
    s = s.replace('HomeFold(title: titleFor(s), id: s.id, open: s.open || s.pinned || Hook.flag("-openAll") || (s.id == "myblock" && MyPlace.current != nil), pinned: s.pinned)',
                  'HomeFold(title: titleFor(s), id: s.id, open: s.open || s.pinned || Hook.flag("-openAll") || (s.id == "myblock" && MyPlace.current != nil), pinned: s.pinned, icon: s.icon)', 1)
    s = s.replace('HomeFold(title: titleFor(s), id: s.id, open: s.open || Hook.flag("-openAll")) { fixed(s) }',
                  'HomeFold(title: titleFor(s), id: s.id, open: s.open || Hook.flag("-openAll"), icon: s.icon) { fixed(s) }', 1)
    assert s.count('icon: s.icon') == 2 and 'icon: r["icon"]' in s, 'UIConfig'
    open(p, 'w').write(s)
print('UIConfig icon ok')
# 2. the fold view
hv = os.path.join(R, 'App/Views/HomeView.swift'); s = open(hv).read()
if 'let icon: String' not in s:
    old = '''    let pinned: Bool
    @State var open: Bool
    @ViewBuilder var content: Content
    init(title: String, id: String, open: Bool = false, pinned: Bool = false, @ViewBuilder content: () -> Content) {
        self.title = title; self.id = id; self.pinned = pinned; _open = State(initialValue: open || pinned); self.content = content()
    }'''
    new = '''    let pinned: Bool
    /// An SF symbol name, or "logo:<name>" for a logo under Logos/; nothing for none.
    let icon: String
    @State var open: Bool
    @ViewBuilder var content: Content
    init(title: String, id: String, open: Bool = false, pinned: Bool = false, icon: String = "", @ViewBuilder content: () -> Content) {
        self.title = title; self.id = id; self.pinned = pinned; self.icon = icon; _open = State(initialValue: open || pinned); self.content = content()
    }'''
    assert old in s, 'HomeFold init'; s = s.replace(old, new, 1)
    old2 = '''                HStack {
                    Text(title).font(DM.sans(16, .bold)).foregroundStyle(Color.cb6Navy)
                    Spacer()
                    if !pinned {'''
    new2 = '''                HStack(spacing: 10) {
                    if icon.hasPrefix("logo:") { LogoImage(name: String(icon.dropFirst(5)), size: 30) }
                    else if !icon.isEmpty { Image(systemName: icon).font(.system(size: 18, weight: .semibold)).foregroundStyle(Color.cb6Orange).frame(width: 26) }
                    Text(title).font(DM.sans(16, .bold)).foregroundStyle(Color.cb6Navy)
                    Spacer()
                    if !pinned {'''
    assert old2 in s, 'HomeFold header'; s = s.replace(old2, new2, 1)
    # the map's own fold header takes the icon too
    s = s.replace('HomeFold(title: s.title.isEmpty ? Copy.t("HomeView.ad87f8e3", "The map") : s.title, id: s.id, open: s.open || Hook.flag("-openAll")) {',
                  'HomeFold(title: s.title.isEmpty ? Copy.t("HomeView.ad87f8e3", "The map") : s.title, id: s.id, open: s.open || Hook.flag("-openAll"), icon: s.icon) {', 1)
    open(hv, 'w').write(s)
print('HomeFold icon ok')
bk = os.path.join(R, 'App/Views/BKHome.swift')
if os.path.exists(bk):
    s = open(bk).read()
    s2 = s.replace('HomeFold(title: s.title.isEmpty ? Copy.t("BKHome.ad87f8e3", "The map") : s.title, id: s.id, open: s.open || Hook.flag("-openAll")) { mapOnly.padding(.top, 8) }',
                   'HomeFold(title: s.title.isEmpty ? Copy.t("BKHome.ad87f8e3", "The map") : s.title, id: s.id, open: s.open || Hook.flag("-openAll"), icon: s.icon) { mapOnly.padding(.top, 8) }', 1)
    if s2 != s: open(bk, 'w').write(s2)
    print('BKHome icon', 'icon: s.icon' in s2)
# 3. the community board card: no seal when the logo name is blank
ev = os.path.join(R, 'App/Views/ExploreViews.swift'); s = open(ev).read()
import re
m = re.search(r'( *)LogoImage\(name: (Copy\.t\("ExploreViews\.[0-9a-f]{8}", "[^"]*"\)), size: 40\)\n', s)
if m and 'aboutLogo' not in s:
    s = s[:m.start()] + f'{m.group(1)}let aboutLogo = {m.group(2)}\n{m.group(1)}if !aboutLogo.isEmpty {{ LogoImage(name: aboutLogo, size: 40) }}\n' + s[m.end():]
    open(ev, 'w').write(s)
print('about card logo', 'aboutLogo' in s)
