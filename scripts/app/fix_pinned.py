"""A fold home.json marks "pinned": true stays open with no toggle: its header and content are always on screen (the
address entry under Your block). Runs after fix_mapfold.py. fix_pinned.py <app dir>"""
import sys, os
R = sys.argv[1]
p = os.path.join(R, 'App/Services/UIConfig.swift'); s = open(p).read()
if 'var pinned: Bool = false' not in s:
    s = s.replace('        var fold: Bool = false\n    }\n', '        var fold: Bool = false\n        /// A fold that stays open with no toggle ("pinned": true), so what is inside is never scrolled past.\n        var pinned: Bool = false\n    }\n', 1)
    s = s.replace('fold: r["fold"] as? Bool ?? false)', 'fold: r["fold"] as? Bool ?? false, pinned: r["pinned"] as? Bool ?? false)', 1)
    old = 'HomeFold(title: titleFor(s), id: s.id, open: s.open || Hook.flag("-openAll") || (s.id == "myblock" && MyPlace.current != nil)) { fold(s) }'
    new = 'HomeFold(title: titleFor(s), id: s.id, open: s.open || s.pinned || Hook.flag("-openAll") || (s.id == "myblock" && MyPlace.current != nil), pinned: s.pinned) { fold(s) }'
    assert old in s and 'var pinned: Bool = false' in s and 'pinned: r["pinned"]' in s, 'UIConfig'
    s = s.replace(old, new, 1); open(p, 'w').write(s)
print('UIConfig pinned ok')
for name in ('HomeView',):
    hv = os.path.join(R, 'App/Views', name + '.swift'); s = open(hv).read()
    if 'let pinned: Bool' in s: print('HomeFold already'); continue
    old = '''struct HomeFold<Content: View>: View {
    let title: String
    let id: String
    @State var open: Bool
    @ViewBuilder var content: Content
    init(title: String, id: String, open: Bool = false, @ViewBuilder content: () -> Content) {
        self.title = title; self.id = id; _open = State(initialValue: open); self.content = content()
    }
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Button { withAnimation(.easeInOut(duration: 0.15)) { open.toggle() } } label: {
                HStack {
                    Text(title).font(DM.sans(16, .bold)).foregroundStyle(Color.cb6Navy)
                    Spacer()
                    Image(systemName: open ? "chevron.up" : "chevron.down").font(.system(size: 13, weight: .bold)).foregroundStyle(Color.cb6Orange)
                }
                .padding(.horizontal, 14).padding(.vertical, 13)
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            if open { content.padding(.horizontal, 10).padding(.bottom, 10) }'''
    new = '''struct HomeFold<Content: View>: View {
    let title: String
    let id: String
    /// Always open, no toggle: the header is a label and the content is always on screen.
    let pinned: Bool
    @State var open: Bool
    @ViewBuilder var content: Content
    init(title: String, id: String, open: Bool = false, pinned: Bool = false, @ViewBuilder content: () -> Content) {
        self.title = title; self.id = id; self.pinned = pinned; _open = State(initialValue: open || pinned); self.content = content()
    }
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Button { if !pinned { withAnimation(.easeInOut(duration: 0.15)) { open.toggle() } } } label: {
                HStack {
                    Text(title).font(DM.sans(16, .bold)).foregroundStyle(Color.cb6Navy)
                    Spacer()
                    if !pinned { Image(systemName: open ? "chevron.up" : "chevron.down").font(.system(size: 13, weight: .bold)).foregroundStyle(Color.cb6Orange) }
                }
                .padding(.horizontal, 14).padding(.vertical, 13)
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            if open || pinned { content.padding(.horizontal, 10).padding(.bottom, 10) }'''
    assert old in s, 'HomeFold'
    s = s.replace(old, new, 1); open(hv, 'w').write(s); print('HomeFold pinned ok')
