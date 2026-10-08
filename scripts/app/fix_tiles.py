"""Anything on any screen can be made tappable from the file, and the day's strip is a list from the file:
- screens.json parts take "dest": {"id": "<part>", "dest": "<screen key> | web:<site path> | dk:<route> | https://..."} makes that
  part a button to there, whatever it was. FileLink is the wrapper (FileAction uses it too).
- lists.json "HomeStatus.tiles": the strip's tiles in order, each {"id": today|parking|sanitation|schools|subway|weather, "dest"};
  a tile left out is not drawn; the subway tile goes to the Weather screen (its MTA service card) by default, the weather tile too.
fix_tiles.py <app dir>"""
import sys, os, re
R = sys.argv[1]
# 1. FileLink, and FilePart's "dest"
tp = os.path.join(R, 'App/Views/Tools.swift'); t = open(tp).read()
if 'struct FileLink' not in t:
    t = t.rstrip('\n') + '''

/// Anything, as a link: "feeds", "card", "web:<site path>", "dk:<route>", "screen:<key>" or any screen key, or an https link; "hide" draws nothing.
struct FileLink<Content: View>: View {
    let dest: String
    @ViewBuilder let content: () -> Content
    init(_ dest: String, @ViewBuilder content: @escaping () -> Content) { self.dest = dest; self.content = content }
    var body: some View {
        let d = dest
        if d.isEmpty { content() }
        else if d == "hide" { EmptyView() }
        else if d == "feeds", let c = MyPlace.current?.coord { NavigationLink { FeedsView(startPin: c) } label: { content().allowsHitTesting(false) }.buttonStyle(.plain) }
        else if d == "card", let p = MyPlace.current { NavigationLink { SiteCardView(address: p.label) } label: { content().allowsHitTesting(false) }.buttonStyle(.plain) }
        else if d.hasPrefix("http"), let u = URL(string: d) { Link(destination: u) { content().allowsHitTesting(false) } }
        else if d.hasPrefix("dk:") { NavigationLink { DKRoute(spec: String(d.dropFirst(3))).view } label: { content().allowsHitTesting(false) }.buttonStyle(.plain) }
        else { NavigationLink { ScreenRouter.view(d.hasPrefix("screen:") ? String(d.dropFirst(7)) : d) } label: { content().allowsHitTesting(false) }.buttonStyle(.plain) }
    }
}
'''
    # FilePart: a part with "dest" is a link
    old = '''        default:
            content(DK.str(p["id"]))
        }
    }
}'''
    new = '''        default:
            FileLink(DK.str(p["dest"])) { content(DK.str(p["id"])) }
        }
    }
}'''
    assert old in t, 'FilePart default'
    t = t.replace(old, new, 1)
    open(tp, 'w').write(t)
print('FileLink ok')
# 2. the strip's tiles from the file
hp = os.path.join(R, 'App/Views/HomeStatus.swift'); s = open(hp).read()
if 'HomeStatus.tiles' in s: print('tiles already'); sys.exit()
a = s.index('            HStack(spacing: 8) {\n')
b = s.index('            .padding(.horizontal, 10).padding(.vertical, 8)\n', a)
body = s[a:b]
# the pieces as they stand
today = re.search(r'(                VStack\(alignment: \.leading, spacing: 1\) \{\n.*?\n                \.background\(Color\.cb6Navy, in: RoundedRectangle\(cornerRadius: 10, style: \.continuous\)\)\n)', body, re.S).group(1)
def line(prefix):
    m = re.search(r'\n( *)(' + re.escape(prefix) + r'[^\n]*\n(?:                     [^\n]*\n)?)', body)
    assert m, prefix
    return m.group(2).rstrip('\n')
parking = line('tile(.mark(DKMarks.parkingSign)')
sanitation = line('tile(.mark(DKMarks.collection(')
schools = line('tile(.mark("blk-school-nycps")')
subway = line('tile(.org("mta.png")')
weather = line('tile(.symbol(code >= 0')
newbody = '''            // The strip's tiles, in the file's order (lists.json "HomeStatus.tiles": [{"id", "dest"}]); a tile with a "dest" is a button to it.
            let tiles: [(String, AnyView)] = [
                ("today", AnyView(
''' + today.rstrip('\n') + '''
                )),
                ("parking", AnyView(''' + parking.strip() + ''')),
                ("sanitation", AnyView(''' + sanitation.strip() + ''')),
                ("schools", AnyView(''' + schools.strip() + ''')),
                ("subway", AnyView(''' + subway.strip() + ''')),
                ("weather", AnyView(''' + weather.strip().replace('.id("weather")', '') + '''.id("weather")))
            ]
            HStack(spacing: 8) {
                ForEach(Array(Lists.objects("HomeStatus.tiles", Self.defaultTiles).enumerated()), id: \\.offset) { _, o in
                    if let t = tiles.first(where: { $0.0 == DK.str(o["id"]) }) {
                        FileLink(DK.str(o["dest"])) { t.1 }
                    }
                }
            }
'''
s = s[:a] + newbody + s[b:]
# the defaults
s = s.replace('    private enum Icon { case mark(String), org(String), symbol(String) }\n',
              '    /// The strip as the code draws it: the subway and weather tiles open the Weather screen, where the MTA service card is.\n    static let defaultTiles: [[String: Any]] = [["id": "today"], ["id": "parking"], ["id": "sanitation"], ["id": "schools"], ["id": "subway", "dest": "weather"], ["id": "weather", "dest": "weather"]]\n\n    private enum Icon { case mark(String), org(String), symbol(String) }\n', 1)
assert 'defaultTiles' in s
open(hp, 'w').write(s)
print('tiles ok')
