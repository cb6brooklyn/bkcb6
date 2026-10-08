"""Home's block card shows the next 30 days the way the Permits tab does: the block on a small map with one dot per
permit, event or shoot, colored by kind, a count under it, and the rows under a "Details" toggle, shut by default.
Runs after fix_blockwork.py and fix_onblock.py. fix_blockmap.py <app dir>"""
import sys, os, hashlib
p = os.path.join(sys.argv[1], 'App/Views/MyBlock.swift'); s = open(p).read()
if 'struct BlockNewsMap' in s: print('already'); sys.exit()
def key(t): return 'MyBlock.' + hashlib.sha1(t.encode()).hexdigest()[:8]
old = '''            } else {
                Text(LocalizedStringKey(Copy.t("MyBlock.040aadd3", "NEXT 30 DAYS ON YOUR BLOCK"))).font(DM.mono(10, .medium)).tracking(1).foregroundStyle(Color.cb6Orange).padding(.top, 2)
                ForEach(mine) { item($0) }
            }
'''
new = '''            } else {
                Text(LocalizedStringKey(Copy.t("MyBlock.040aadd3", "NEXT 30 DAYS ON YOUR BLOCK"))).font(DM.mono(10, .medium)).tracking(1).foregroundStyle(Color.cb6Orange).padding(.top, 2)
                // The block on a map with a dot per item, the way the Permits tab shows them, then the count; the rows wait under Details.
                if let r = ref { BlockNewsMap(ref: r, items: mine) }
                Text(verbatim: BlockNewsMap.summary(mine)).font(DM.sans(13)).foregroundStyle(Color.cb6Ink).fixedSize(horizontal: false, vertical: true)
                Button { withAnimation { showDetails.toggle() } } label: {
                    HStack {
                        Text(LocalizedStringKey(Copy.t("KEY_DETAILS", "Details"))).font(DM.sans(13, .bold)).foregroundStyle(Color.cb6Navy)
                        Spacer(); Image(systemName: showDetails ? "chevron.up" : "chevron.down").font(.system(size: 11, weight: .bold)).foregroundStyle(Color.cb6Muted)
                    }
                }
                .buttonStyle(.plain)
                if showDetails { ForEach(mine) { item($0) } }
            }
'''.replace('KEY_DETAILS', key('Details'))
assert old in s, 'news section'; s = s.replace(old, new, 1)
old2 = '    @State private var news: [BlockNews]?\n'
new2 = '    @State private var news: [BlockNews]?\n    @State private var showDetails = false\n'
assert old2 in s, 'state'; s = s.replace(old2, new2, 1)
MAP = '''

/// The block with one dot per permit, event, shoot or closure in the next 30 days, colored as the Permits tab colors
/// its kinds; dots spread along the block since the records name the block, not a point on it.
struct BlockNewsMap: View {
    let ref: BlockRef
    let items: [BlockNews]
    static func color(_ k: BlockNews.Kind) -> Color {
        switch k {
        case .permit: return MapStyle.color("myblock.dot.permit", Color(red: 0.93, green: 0.55, blue: 0.13))
        case .closure: return MapStyle.color("myblock.dot.closure", Color(red: 0.82, green: 0.19, blue: 0.18))
        case .film: return MapStyle.color("myblock.dot.film", Color(red: 0.55, green: 0.25, blue: 0.75))
        case .event: return MapStyle.color("myblock.dot.event", Color(red: 0.0, green: 0.55, blue: 0.55))
        case .filing: return MapStyle.color("myblock.dot.filing", Color(red: 0.12, green: 0.44, blue: 0.92))
        }
    }
    static func noun(_ k: BlockNews.Kind, _ n: Int) -> String {
        switch k {
        case .permit: return n == 1 ? Copy.t("KEY_N_PERMIT1", "DOT construction permit") : Copy.t("KEY_N_PERMIT", "DOT construction permits")
        case .closure: return n == 1 ? Copy.t("KEY_N_CLOSURE1", "street closure") : Copy.t("KEY_N_CLOSURE", "street closures")
        case .film: return n == 1 ? Copy.t("KEY_N_FILM1", "film shoot") : Copy.t("KEY_N_FILM", "film shoots")
        case .event: return n == 1 ? Copy.t("KEY_N_EVENT1", "permitted event") : Copy.t("KEY_N_EVENT", "permitted events")
        case .filing: return n == 1 ? Copy.t("KEY_N_FILING1", "building filing") : Copy.t("KEY_N_FILING", "building filings")
        }
    }
    /// "3 on this block: 1 DOT construction permit, 2 permitted events"
    static func summary(_ items: [BlockNews]) -> String {
        let order: [BlockNews.Kind] = [.event, .film, .closure, .permit, .filing]
        let parts = order.compactMap { k -> String? in
            let n = items.filter { $0.kind == k }.count
            return n == 0 ? nil : "\\(n) \\(noun(k, n))"
        }
        return Copy.f("KEY_SUMMARY", "{0} on this block: {1}", items.count, parts.joined(separator: ", "))
    }
    var body: some View {
        let n = max(items.count, 1)
        let dots: [DKDot] = items.enumerated().map { i, it in
            let t = (Double(i) + 1) / (Double(n) + 1)
            let c = CLLocationCoordinate2D(latitude: ref.a.latitude + (ref.b.latitude - ref.a.latitude) * t, longitude: ref.a.longitude + (ref.b.longitude - ref.a.longitude) * t)
            return DKDot(coord: c, title: it.title, subtitle: it.detail, color: UIColor(Self.color(it.kind)), size: 12)
        }
        DKLayerMap(layers: [DKLayer(id: "block", lines: [[ref.a, ref.b]], color: UIColor(Color.cb6Navy), width: 6), DKLayer(id: "news", dots: dots)],
                   style: "myblock", signature: "myblock-\\(ref.slug)-\\(items.count)", fit: [[ref.a, ref.b]])
            .dkMapFrame(MapStyle.number("myblock.mapHeight", 170))
            .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
    }
}
'''
for k, t in (('KEY_N_PERMIT1', 'DOT construction permit'), ('KEY_N_PERMIT', 'DOT construction permits'), ('KEY_N_CLOSURE1', 'street closure'), ('KEY_N_CLOSURE', 'street closures'),
             ('KEY_N_FILM1', 'film shoot'), ('KEY_N_FILM', 'film shoots'), ('KEY_N_EVENT1', 'permitted event'), ('KEY_N_EVENT', 'permitted events'),
             ('KEY_N_FILING1', 'building filing'), ('KEY_N_FILING', 'building filings'), ('KEY_SUMMARY', '{0} on this block: {1}')):
    MAP = MAP.replace(k, key(t))
s = s.rstrip('\n') + '\n' + MAP
open(p, 'w').write(s); print('block map ok')
