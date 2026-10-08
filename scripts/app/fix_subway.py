"""The strip's subway tile opens the MTA's alerts for the lines it watches: each active delay, suspension or change with its
headline and details, from the feed the tile already fetches, kept on the phone for when there is no connection. The tile
is a button the file can re-aim (screens.json buttons "HomeStatus.subway"). fix_subway.py <app dir>"""
import sys, os
p = os.path.join(sys.argv[1], 'App/Views/HomeStatus.swift'); s = open(p).read()
if 'SubwayAlertsView' in s: print('already'); sys.exit()
# 1. the tile is a link
# BKCB and CBNYC pass the title and routes in; BKCB6's strip is CB6's
old = '                tile(.org("mta.png"), subwayTitle, transit.isEmpty ? Copy.t("HomeStatus.97876b83", "Checking") : transit, transit == "Good service")\n'
old6 = '                tile(.org("mta.png"), Copy.t("HomeStatus.318e719c", "Subway in CB6"), transit.isEmpty ? Copy.t("HomeStatus.97876b83", "Checking") : transit, transit == "Good service")\n'
def link(title, routes):
    return f'''                FileAction("HomeStatus.subway") {{
                NavigationLink {{ SubwayAlertsView(routes: {routes}, title: {title}) }} label: {{
                    tile(.org("mta.png"), {title}, transit.isEmpty ? Copy.t("HomeStatus.97876b83", "Checking") : transit, transit == "Good service")
                }}
                .buttonStyle(.plain)
                }}
'''
if old in s: s = s.replace(old, link('subwayTitle', 'routes'), 1)
elif old6 in s: s = s.replace(old6, link('Copy.t("HomeStatus.318e719c", "Subway in CB6")', 'CityStatus.cb6Routes'), 1)
else: raise SystemExit('tile NOT FOUND')
# 2. the feed is kept for the alerts screen
old2 = '''           let summary = await Task.detached(priority: .utility, operation: { Self.summarize(d, routes: routes) }).value {
            transit = summary
        }'''
new2 = '''           let summary = await Task.detached(priority: .utility, operation: { Self.summarize(d, routes: routes) }).value {
            transit = summary
            try? d.write(to: SubwayAlertsView.cacheURL)
        }'''
if old2 in s: s = s.replace(old2, new2, 1)
else:
    old3 = old2.replace('Self.summarize(d, routes: routes)', 'Self.summarize(d)'); new3 = new2.replace('Self.summarize(d, routes: routes)', 'Self.summarize(d)')
    assert old3 in s, 'refresh'; s = s.replace(old3, new3, 1)
# 3. the alerts screen
s = s.rstrip('\n') + '''

/// The MTA's current alerts for the lines the strip watches: delays, suspensions and service changes, with their details.
/// Reads the feed the strip last fetched (kept on the phone), so it opens without a connection.
struct SubwayAlertsView: View {
    let routes: [String]
    var title: String = ""
    @State private var alerts: [Alert] = []
    @State private var loaded = false
    static let cacheURL = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0].appendingPathComponent("subway-alerts.json")

    struct Alert: Identifiable {
        let id: String
        let routes: [String]
        let kind: String
        let headline: String
        let details: String
        let active: Bool
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                if !loaded {
                    HStack(spacing: 8) { ProgressView(); Text(LocalizedStringKey(Copy.t("HomeStatus.sa.loading", "Reading the MTA's alerts"))).font(DM.sans(13)).foregroundStyle(Color.cb6Muted) }
                } else if alerts.isEmpty {
                    Card { Text(LocalizedStringKey(Copy.t("HomeStatus.sa.none", "No delays, suspensions or service changes are posted for these lines right now."))).font(DM.sans(14)).foregroundStyle(Color.cb6Ink) }
                } else {
                    Text(LocalizedStringKey(Copy.f("HomeStatus.sa.count", "{0} alert{1} on {2}", alerts.count, alerts.count == 1 ? "" : "s", routes.joined(separator: " ")))).font(DM.mono(11, .medium)).tracking(1).foregroundStyle(Color.cb6Muted)
                    ForEach(alerts) { a in
                        VStack(alignment: .leading, spacing: 6) {
                            HStack(spacing: 6) {
                                ForEach(a.routes, id: \\.self) { r in
                                    Text(r).font(DM.sans(12, .bold)).foregroundStyle(.white).frame(width: 24, height: 24).background(Color.cb6Navy, in: Circle())
                                }
                                Text(a.kind.uppercased()).font(DM.mono(9, .medium)).tracking(0.8).foregroundStyle(a.active ? MapStyle.color("HomeStatus.c.1ea96404", Color(red: 0.75, green: 0.18, blue: 0.2)) : Color.cb6Muted)
                                Spacer(minLength: 0)
                            }
                            Text(a.headline).font(DM.sans(15, .bold)).foregroundStyle(Color.cb6Ink).fixedSize(horizontal: false, vertical: true)
                            if !a.details.isEmpty { Text(a.details).font(DM.sans(13)).foregroundStyle(Color.cb6Ink).fixedSize(horizontal: false, vertical: true) }
                        }
                        .padding(12).frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.white, in: RoundedRectangle(cornerRadius: 12, style: .continuous))
                        .overlay(RoundedRectangle(cornerRadius: 12, style: .continuous).stroke(Color.cb6Rule, lineWidth: 1))
                    }
                }
                Text(LocalizedStringKey(Copy.t("HomeStatus.sa.source", "From the MTA's service alerts, refreshed when the app has a connection."))).font(DM.sans(12)).foregroundStyle(Color.cb6Muted)
            }
            .padding(.horizontal, 16).padding(.vertical, 14)
        }
        .background(Color.cb6Paper)
        .cb6Page(title.isEmpty ? Copy.t("HomeStatus.sa.title", "Subway alerts") : title, Copy.t("HomeStatus.sa.sub", "Delays, suspensions and service changes on your lines"), logo: DK.logo)
        .task { await load() }
    }

    private func load() async {
        var data = try? Data(contentsOf: Self.cacheURL)
        if let u = URL(string: "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts.json"), let (d, _) = try? await URLSession.shared.data(from: u) {
            data = d; try? d.write(to: Self.cacheURL)
        }
        let routes = self.routes
        if let d = data { alerts = await Task.detached(priority: .utility, operation: { Self.parse(d, routes: routes) }).value }
        loaded = true
    }

    /// Every alert on these lines that is active now or starts within the day: the first translation of its headline and details.
    nonisolated static func parse(_ d: Data, routes: [String]) -> [Alert] {
        guard let o = (try? JSONSerialization.jsonObject(with: d)) as? [String: Any], let ents = o["entity"] as? [[String: Any]] else { return [] }
        let now = Date().timeIntervalSince1970
        func text(_ t: Any?) -> String {
            let tr = (t as? [String: Any])?["translation"] as? [[String: Any]] ?? []
            return (tr.first(where: { ($0["language"] as? String ?? "en") == "en" }) ?? tr.first).flatMap { $0["text"] as? String } ?? ""
        }
        var out: [Alert] = []
        for e in ents {
            guard let a = e["alert"] as? [String: Any] else { continue }
            let mine = (a["informed_entity"] as? [[String: Any]] ?? []).compactMap { $0["route_id"] as? String }.filter(routes.contains)
            guard !mine.isEmpty else { continue }
            let periods = a["active_period"] as? [[String: Any]] ?? []
            var active = periods.isEmpty, soon = false
            for p in periods {
                let s = (p["start"] as? NSNumber)?.doubleValue ?? 0
                let en = (p["end"] as? NSNumber)?.doubleValue ?? .greatestFiniteMagnitude
                if s <= now && now <= (en == 0 ? .greatestFiniteMagnitude : en) { active = true }
                if s > now && s - now < 86400 { soon = true }
            }
            guard active || soon else { continue }
            let m = a["transit_realtime.mercury_alert"] as? [String: Any] ?? [:]
            let kind = (m["alert_type"] as? String ?? "").replacingOccurrences(of: "_", with: " ")
            let headline = text(a["header_text"]); let details = text(a["description_text"])
            guard !headline.isEmpty else { continue }
            out.append(Alert(id: (e["id"] as? String) ?? headline, routes: routes.filter(mine.contains), kind: kind.isEmpty ? Copy.t("HomeStatus.sa.change", "service change") : kind, headline: headline, details: details, active: active))
        }
        return out.sorted { ($0.active ? 0 : 1, $0.routes.first ?? "") < ($1.active ? 0 : 1, $1.routes.first ?? "") }
    }
}
'''
open(p, 'w').write(s)
print('subway ok')
