"""The home-screen widget's words, colors and date formats come from bkcb6.app/app/data/civic/widget.json, fetched with
the meetings and kept in the widget's own cache for when there is no connection. fix_widget.py <app dir (bkcb6app)>"""
import sys, os
p = os.path.join(sys.argv[1], 'BKCB6Widget/BKCB6Widget.swift')
if not os.path.exists(p): print('no widget'); sys.exit()
s = open(p).read()
if 'WidgetText' in s: print('already'); sys.exit()
reps = [
    ('            if let live = try? await MeetingFeed.live(), !live.isEmpty { all = live }\n',
     '            if let live = try? await MeetingFeed.live(), !live.isEmpty { all = live }\n            await WidgetText.refresh()\n'),
    ('    private let navy = Color(red: 6/255, green: 2/255, blue: 77/255)\n    private let orange = Color(red: 244/255, green: 121/255, blue: 32/255)\n',
     '    private var navy: Color { WidgetText.color("navy", Color(red: 6/255, green: 2/255, blue: 77/255)) }\n    private var orange: Color { WidgetText.color("orange", Color(red: 244/255, green: 121/255, blue: 32/255)) }\n'),
    ('f.dateFormat = "EEE, MMM d"; return f', 'f.dateFormat = WidgetText.t("dayFormat", "EEE, MMM d"); return f'),
    ('f.dateFormat = "h:mm a"; return f', 'f.dateFormat = WidgetText.t("timeFormat", "h:mm a"); return f'),
    ('Text("BKCB6")', 'Text(WidgetText.t("title", "BKCB6"))'),
    ('Text("NEXT MEETING")', 'Text(WidgetText.t("heading", "NEXT MEETING"))'),
    ('Text(m.isFullBoard ? "Full Board" : m.body)', 'Text(m.isFullBoard ? WidgetText.t("fullBoard", "Full Board") : m.body)'),
    ('Text(f.isFullBoard ? "Full Board" : f.body)', 'Text(f.isFullBoard ? WidgetText.t("fullBoard", "Full Board") : f.body)'),
    ('Text("No upcoming board meeting posted.")', 'Text(WidgetText.t("none", "No upcoming board meeting posted."))'),
]
for a, b in reps:
    assert a in s, a[:50]
    s = s.replace(a, b)
s = s.rstrip('\n') + '''

/// The widget's words, colors and date formats from the site (app/data/civic/widget.json), kept in the widget's cache; the code's when the file has none.
enum WidgetText {
    static let url = URL(string: "https://bkcb6.app/app/data/civic/widget.json")!
    static let cache = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0].appendingPathComponent("widget.json")
    static var file: [String: Any] = load(try? Data(contentsOf: cache))
    static func load(_ d: Data?) -> [String: Any] { d.flatMap { (try? JSONSerialization.jsonObject(with: $0)) as? [String: Any] } ?? [:] }
    static func t(_ key: String, _ fallback: String) -> String { (file[key] as? String) ?? fallback }
    static func color(_ key: String, _ fallback: Color) -> Color {
        guard var h = file[key] as? String else { return fallback }
        if h.hasPrefix("#") { h.removeFirst() }
        guard h.count == 6, let v = UInt32(h, radix: 16) else { return fallback }
        return Color(red: Double((v >> 16) & 0xff) / 255, green: Double((v >> 8) & 0xff) / 255, blue: Double(v & 0xff) / 255)
    }
    static func refresh() async {
        var req = URLRequest(url: url); req.timeoutInterval = 6; req.cachePolicy = .reloadIgnoringLocalCacheData
        guard let (d, r) = try? await URLSession.shared.data(for: req), (r as? HTTPURLResponse)?.statusCode == 200, !load(d).isEmpty else { return }
        try? d.write(to: cache); file = load(d)
    }
}
'''
open(p, 'w').write(s)
print('widget ok')
