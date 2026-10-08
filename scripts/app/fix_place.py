"""Site pages inside the app know the saved address: a page path in home.json, tools.json or a route can carry
{ADDRESS} {LAT} {LON} {SLUG} {CD} {BBL} {NUMBER}, filled from the saved place when the page loads (so
"page": "app/ballot.html?slug={SLUG}" shows that block's page), and every in-app site page gets
window.__bkcbPlace = {label, lat, lon, slug, cd, bbl, number} (null with no address) before its own scripts run.
When the address changes, open pages reload with the new one. fix_place.py <app dir>"""
import sys, os
R = sys.argv[1]
p = os.path.join(R, 'App/Views/SiteCard.swift'); s = open(p).read()
if '__bkcbPlace' in s: print('already'); sys.exit()
# 1. the web view: placeholders in the path, the place in the page, a reload on change
old = '''struct SitePageWeb: UIViewRepresentable {
    let path: String
    func makeCoordinator() -> Coord { Coord() }
    func makeUIView(context: Context) -> WKWebView {
        let cfg = WKWebViewConfiguration()
        cfg.setURLSchemeHandler(SiteScheme(), forURLScheme: SiteScheme.scheme)
        cfg.userContentController.addUserScript(WKUserScript(source: "window.__bkcbOffline=\\(NetWatch.useBundledMap ? "true" : "false");", injectionTime: .atDocumentStart, forMainFrameOnly: false))
        cfg.userContentController.addUserScript(WKUserScript(source: SiteScheme.shim, injectionTime: .atDocumentStart, forMainFrameOnly: false))
        cfg.userContentController.add(context.coordinator, name: "card")
        cfg.websiteDataStore = .nonPersistent()
        let w = WKWebView(frame: .zero, configuration: cfg)
        w.navigationDelegate = context.coordinator
        w.uiDelegate = context.coordinator
        w.isOpaque = false
        w.backgroundColor = UIColor(Color.cb6Paper)
        w.scrollView.backgroundColor = UIColor(Color.cb6Paper)
        if #available(iOS 16.4, *) { w.isInspectable = Hook.flag("-inspect") }
        let rel = path.hasPrefix("/") ? String(path.dropFirst()) : path
        if let u = URL(string: "\\(SiteScheme.scheme)://site/\\(rel)") { w.load(URLRequest(url: u)) }
        return w
    }
    func updateUIView(_ w: WKWebView, context: Context) {}
    final class Coord: NSObject, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler {
'''
new = '''struct SitePageWeb: UIViewRepresentable {
    let path: String
    func makeCoordinator() -> Coord { Coord() }

    /// The saved place as the pages see it: window.__bkcbPlace, null with no address.
    static func placeJSON() -> String {
        guard let p = MyPlace.current else { return "null" }
        let o: [String: Any] = ["label": p.label, "lat": p.coord.latitude, "lon": p.coord.longitude, "slug": p.slug, "cd": p.cd, "bbl": p.bbl, "number": p.number]
        return (try? JSONSerialization.data(withJSONObject: o)).flatMap { String(data: $0, encoding: .utf8) } ?? "null"
    }
    /// {ADDRESS} {LAT} {LON} {SLUG} {CD} {BBL} {NUMBER} in a page path, filled from the saved place (blank with none).
    static func fill(_ path: String) -> String {
        let p = MyPlace.current
        func q(_ s: String) -> String { s.addingPercentEncoding(withAllowedCharacters: .alphanumerics) ?? s }
        return path.replacingOccurrences(of: "{ADDRESS}", with: q(p?.label ?? "")).replacingOccurrences(of: "{LAT}", with: p.map { String($0.coord.latitude) } ?? "")
            .replacingOccurrences(of: "{LON}", with: p.map { String($0.coord.longitude) } ?? "").replacingOccurrences(of: "{SLUG}", with: q(p?.slug ?? ""))
            .replacingOccurrences(of: "{CD}", with: p.map { String($0.cd) } ?? "").replacingOccurrences(of: "{BBL}", with: p?.bbl ?? "")
            .replacingOccurrences(of: "{NUMBER}", with: p.map { String($0.number) } ?? "")
    }
    private static func scripts(_ c: WKUserContentController) {
        c.removeAllUserScripts()
        c.addUserScript(WKUserScript(source: "window.__bkcbOffline=\\(NetWatch.useBundledMap ? "true" : "false");window.__bkcbPlace=\\(placeJSON());", injectionTime: .atDocumentStart, forMainFrameOnly: false))
        c.addUserScript(WKUserScript(source: SiteScheme.shim, injectionTime: .atDocumentStart, forMainFrameOnly: false))
    }
    func makeUIView(context: Context) -> WKWebView {
        let cfg = WKWebViewConfiguration()
        cfg.setURLSchemeHandler(SiteScheme(), forURLScheme: SiteScheme.scheme)
        Self.scripts(cfg.userContentController)
        cfg.userContentController.add(context.coordinator, name: "card")
        cfg.websiteDataStore = .nonPersistent()
        let w = WKWebView(frame: .zero, configuration: cfg)
        w.navigationDelegate = context.coordinator
        w.uiDelegate = context.coordinator
        w.isOpaque = false
        w.backgroundColor = UIColor(Color.cb6Paper)
        w.scrollView.backgroundColor = UIColor(Color.cb6Paper)
        if #available(iOS 16.4, *) { w.isInspectable = Hook.flag("-inspect") }
        load(w, context)
        return w
    }
    private func load(_ w: WKWebView, _ context: Context) {
        let filled = Self.fill(path)
        let rel = filled.hasPrefix("/") ? String(filled.dropFirst()) : filled
        context.coordinator.loaded = filled + "|" + Self.placeJSON()
        if let u = URL(string: "\\(SiteScheme.scheme)://site/\\(rel)") { w.load(URLRequest(url: u)) }
    }
    /// The address changed since the page loaded: the page loads again with the new one.
    func updateUIView(_ w: WKWebView, context: Context) {
        let now = Self.fill(path) + "|" + Self.placeJSON()
        if now != context.coordinator.loaded {
            Self.scripts(w.configuration.userContentController)
            load(w, context)
        }
    }
    final class Coord: NSObject, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler {
        var loaded = ""
'''
assert old in s, 'SitePageWeb'
s = s.replace(old, new, 1)
# 2. the page screen and the Home card draw again when the address changes
old2 = '''struct SitePageView: View {
    let path: String
    var title: String = ""
    var body: some View {
        SitePageWeb(path: path)'''
new2 = '''struct SitePageView: View {
    let path: String
    var title: String = ""
    @AppStorage(MyPlaceKeys.label) private var placeLabel = ""
    var body: some View {
        let _ = placeLabel
        SitePageWeb(path: path)'''
assert old2 in s, 'SitePageView'; s = s.replace(old2, new2, 1)
old3 = '''struct SiteHomeCard: View {
    let section: UIConfig.Section
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {'''
new3 = '''struct SiteHomeCard: View {
    let section: UIConfig.Section
    @AppStorage(MyPlaceKeys.label) private var placeLabel = ""
    var body: some View {
        let _ = placeLabel
        VStack(alignment: .leading, spacing: 0) {'''
assert old3 in s, 'SiteHomeCard'; s = s.replace(old3, new3, 1)
open(p, 'w').write(s)
print('place ok')
