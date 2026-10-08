"""Any page of the site, from the pack, anywhere in the app without a build: a Home section of kind "web" (home.json:
"page": "<path under site/>", "height": 420, with "fold"/"title" as any section), a screen route "web:<path>" for tool
buttons ("dest": "screen:web:<path>") and for DK routes, and a fold whose content is text from text.json
("content": "text:<key>"). fix_web.py <app dir>"""
import sys, os
R = sys.argv[1]
# 1. the page view and the inline web card, appended to SiteCard.swift
sc = os.path.join(R, 'App/Views/SiteCard.swift'); s = open(sc).read()
if 'struct SitePageView' not in s:
    s = s.rstrip('\n') + '''

// MARK: - Any page of the site, in the app

/// A page of bkcb6.app served from the pack (site/<path>), as a screen: tool buttons reach it with "screen:web:<path>".
struct SitePageView: View {
    let path: String
    var title: String = ""
    var body: some View {
        SitePageWeb(path: path)
            .background(Color.cb6Paper)
            .cb6Page(title.isEmpty ? Copy.t("SiteCard.f2a1c0e7", "bkcb6.app") : title, "", logo: DK.logo)
    }
}

/// A page of the site inside a Home card, at the height home.json gives it.
struct SiteHomeCard: View {
    let section: UIConfig.Section
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            if !section.title.isEmpty && !section.fold {
                Text(section.title).font(DM.sans(16, .bold)).foregroundStyle(Color.cb6Navy).padding(.horizontal, 14).padding(.vertical, 12)
            }
            SitePageWeb(path: section.content).frame(height: section.height > 0 ? section.height : 420)
        }
        .background(Color.white, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).stroke(Color.cb6Rule, lineWidth: 1))
    }
}

struct SitePageWeb: UIViewRepresentable {
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
        func userContentController(_ c: WKUserContentController, didReceive m: WKScriptMessage) {}
        /// Links inside the site stay in the page; the web beyond it opens in the in-app browser.
        func webView(_ w: WKWebView, decidePolicyFor a: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            guard let u = a.request.url else { decisionHandler(.cancel); return }
            if u.scheme == SiteScheme.scheme || u.scheme == "about" || u.scheme == "data" || u.scheme == "blob" { decisionHandler(.allow); return }
            if u.scheme == "tel" || u.scheme == "mailto" || u.scheme == "sms" { UIApplication.shared.open(u); decisionHandler(.cancel); return }
            if let web = SiteScheme.webURL(u) { InAppWeb.open(web) } else { InAppWeb.open(u) }
            decisionHandler(.cancel)
        }
        func webView(_ w: WKWebView, createWebViewWith c: WKWebViewConfiguration, for a: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
            if let u = a.request.url { if let web = SiteScheme.webURL(u) { InAppWeb.open(web) } else { InAppWeb.open(u) } }
            return nil
        }
        func webView(_ w: WKWebView, runJavaScriptAlertPanelWithMessage m: String, initiatedByFrame f: WKFrameInfo, completionHandler: @escaping () -> Void) { completionHandler() }
    }
}
'''
    open(sc, 'w').write(s)
print('SitePage ok')
# 2. the section model: a height for web cards
uc = os.path.join(R, 'App/Services/UIConfig.swift'); s = open(uc).read()
if 'var height: Double = 0' not in s:
    s = s.replace('        var icon: String = ""\n    }\n', '        var icon: String = ""\n        /// A web card\'s height in points ("height").\n        var height: Double = 0\n    }\n', 1)
    s = s.replace('icon: r["icon"] as? String ?? "")', 'icon: r["icon"] as? String ?? "", height: (r["height"] as? NSNumber)?.doubleValue ?? 0)', 1)
    assert 'var height: Double = 0' in s and 'height: (r["height"]' in s, 'UIConfig height'
    open(uc, 'w').write(s)
print('UIConfig height ok')
# 3. Home: the "web" kind, the "web:" route, the "text:" fold
hv = os.path.join(R, 'App/Views/HomeView.swift'); s = open(hv).read()
if 'case "web": SiteHomeCard' not in s:
    s = s.replace('                            case "about": AboutBoardsCard().padding(.top, 14).id("about")\n',
                  '                            case "about": AboutBoardsCard().padding(.top, 14).id("about")\n                            case "web": SiteHomeCard(section: s).padding(.top, 14).id(s.id)\n', 1)
    s = s.replace('                case "cb6map": AnyView(CB6MapView())\n',
                  '                case "cb6map": AnyView(CB6MapView())\n                case let k where k.hasPrefix("web:"): AnyView(SitePageView(path: String(k.dropFirst(4))))\n', 1)
    s = s.replace('        case "about": AboutBoardsCard()\n        case let c where c.hasPrefix("tools:"):',
                  '        case "about": AboutBoardsCard()\n        case let c where c.hasPrefix("text:"): HomeTextCard(key: String(c.dropFirst(5)))\n        case "web": SiteHomeCard(section: s)\n        case let c where c.hasPrefix("tools:"):', 1)
    s = s.replace('        case "cb6map": AnyView(CB6MapView())\n',
                  '        case "cb6map": AnyView(CB6MapView())\n        case let k where k.hasPrefix("web:"): AnyView(SitePageView(path: String(k.dropFirst(4))))\n', 1)
    assert 'case "web": SiteHomeCard' in s and s.count('hasPrefix("web:")') >= 1 and 'HomeTextCard' in s, 'HomeView web'
    s = s.rstrip('\n') + '''

/// Paragraphs from text.json ("text:<key>"), one blank line between them, inside a fold.
struct HomeTextCard: View {
    let key: String
    var body: some View {
        let t = T(key, "")
        VStack(alignment: .leading, spacing: 10) {
            ForEach(Array(t.components(separatedBy: "\\n\\n").enumerated()), id: \\.offset) { _, p in
                Text(p).font(DM.sans(15)).foregroundStyle(Color.cb6Ink).fixedSize(horizontal: false, vertical: true)
            }
        }
    }
}
'''
    open(hv, 'w').write(s)
print('HomeView web ok')
bk = os.path.join(R, 'App/Views/BKHome.swift')
if os.path.exists(bk):
    s = open(bk).read()
    if 'case "web": SiteHomeCard' not in s:
        s = s.replace('                            case "strip": mapStrip.padding(.top, 14).id("strip")\n',
                      '                            case "strip": mapStrip.padding(.top, 14).id("strip")\n                            case "web": SiteHomeCard(section: s).padding(.top, 14).id(s.id)\n', 1)
        s = s.replace('        case "myblock": MyBlockCard()\n        case "help": HomeHelpCard { path.append("help") }\n        case "about": AboutBoardsCard()\n',
                      '        case "myblock": MyBlockCard()\n        case "help": HomeHelpCard { path.append("help") }\n        case "about": AboutBoardsCard()\n        case let c where c.hasPrefix("text:"): HomeTextCard(key: String(c.dropFirst(5)))\n        case "web": SiteHomeCard(section: s)\n', 1)
        assert s.count('case "web": SiteHomeCard') == 2 and 'HomeTextCard' in s, 'BKHome web'
        open(bk, 'w').write(s)
    print('BKHome web ok')
# 4. DK routes
dk = os.path.join(R, 'App/Views/DistrictKit.swift'); s = open(dk).read()
if 'case "web": SitePageView' not in s:
    s = s.replace('        case "official": OfficialProfileView(slug: arg)\n',
                  '        case "official": OfficialProfileView(slug: arg)\n        case "web": SitePageView(path: parts.dropFirst().joined(separator: ":"))\n', 1)
    assert 'case "web": SitePageView' in s, 'DKRoute'
    open(dk, 'w').write(s)
print('DKRoute web ok')
