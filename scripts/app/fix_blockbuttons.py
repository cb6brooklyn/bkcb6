"""The block card's buttons and rows from the file (lists.json): "MyBlock.buttons" is a list of
{title, dest, when} pills under the next-30-days section (dest: "feeds" = 311, crime and permits on the address,
"web:<site path>", "screen:<route key>", "dk:<DK route>"; when: "cb6" or "always"), and "MyBlock.hide" names rows to
leave out ("offblock", "filings", "map", "details"). Replaces the code-only button of fix_nearby.py. fix_blockbuttons.py <app dir>"""
import sys, os
p = os.path.join(sys.argv[1], 'App/Views/MyBlock.swift'); s = open(p).read()
if 'MyBlock.buttons' in s: print('already'); sys.exit()
old = '''            if place.cd == 306 {
                // CB6: the Permits tab on this address, every kind within a radius, in place of the off-block list.
                NavigationLink { FeedsView(startPin: place.coord) } label: {
                    Text(Copy.t("ExploreViews.09eee297", "311, crime and permits nearby")).font(DM.sans(13, .bold)).foregroundStyle(.white).lineLimit(1).minimumScaleFactor(0.8)
                        .padding(.horizontal, 12).padding(.vertical, 9).frame(maxWidth: .infinity).background(Color.cb6Navy, in: Capsule())
                }
                .buttonStyle(.plain)
            } else if !street.isEmpty, let r = ref {'''
new = '''            // Buttons from the file (lists.json MyBlock.buttons), the code's one when the file has none.
            let hide = Set(Lists.strings("MyBlock.hide", ["offblock"]))
            let buttons = Lists.objects("MyBlock.buttons", [["title": "311, crime and permits nearby", "dest": "feeds", "when": "cb6"]])
                .filter { b in (DK.str(b["when"]).isEmpty || DK.str(b["when"]) == "always" || (DK.str(b["when"]) == "cb6" && place.cd == 306)) }
            if !buttons.isEmpty {
                HStack(spacing: 8) {
                    ForEach(Array(buttons.enumerated()), id: \\.offset) { _, b in blockButton(DK.str(b["title"]), DK.str(b["dest"])) }
                }
            }
            if !hide.contains("offblock"), !street.isEmpty, let r = ref {'''
assert s.count(old) == 1, 'nearby block'
s = s.replace(old, new, 1)
old2 = '''    private func loadNews() async {'''
new2 = '''    /// One pill of the block card: where it goes is a word in the file.
    @ViewBuilder private func blockButton(_ title: String, _ dest: String) -> some View {
        let label = Text(title).font(DM.sans(13, .bold)).foregroundStyle(.white).lineLimit(1).minimumScaleFactor(0.8)
            .padding(.horizontal, 12).padding(.vertical, 9).frame(maxWidth: .infinity).background(Color.cb6Navy, in: Capsule())
        if dest == "feeds" { NavigationLink { FeedsView(startPin: place.coord) } label: { label }.buttonStyle(.plain) }
        else if dest.hasPrefix("web:") { NavigationLink { SitePageView(path: String(dest.dropFirst(4))) } label: { label }.buttonStyle(.plain) }
        else if dest.hasPrefix("dk:") { NavigationLink { DKRoute(spec: String(dest.dropFirst(3))).view } label: { label }.buttonStyle(.plain) }
        else if dest.hasPrefix("screen:") { NavigationLink(value: String(dest.dropFirst(7))) { label }.buttonStyle(.plain) }
        else { label }
    }

    private func loadNews() async {'''
assert s.count(old2) == 1, 'loadNews'
s = s.replace(old2, new2, 1)
# the filings, map and details rows answer to the file too
s = s.replace('            if !filings.isEmpty {\n                Text(LocalizedStringKey(Copy.t("MyBlock.b81ef81f"', '            if !hide.contains("filings"), !filings.isEmpty {\n                Text(LocalizedStringKey(Copy.t("MyBlock.b81ef81f"', 1)
s = s.replace('                if let r = ref { BlockNewsMap(ref: r, items: mine) }\n', '                if !Set(Lists.strings("MyBlock.hide", ["offblock"])).contains("map"), let r = ref { BlockNewsMap(ref: r, items: mine) }\n', 1)
open(p, 'w').write(s); print('block buttons ok')
