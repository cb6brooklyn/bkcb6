"""Apple maps in the site pages the apps show: Apple's MapKit JS key works only on bkcb6.app, so with a connection the
in-app pages (SitePageWeb, and the address card SiteCardWeb) load from https://bkcb6.app itself, where every map is an
Apple map; with no connection they load the app's own copy as before (Leaflet over the bundled street map).
fix_applemaps.py <app dir>"""
import sys, os
R = sys.argv[1]
p = os.path.join(R, 'BKCB6/App/Views/SiteCard.swift'); s = open(p).read()
if 'var WEB=' not in s:
    def rep(o, n, c=1):
        global s
        assert s.count(o) == c, (o[:70], s.count(o))
        s = s.replace(o, n)
    # the shim: on bkcb6.app itself nothing is rerouted through the app
    rep("      var S='bkcb://', ORIGIN='https://bkcb6.app';\n", "      var S='bkcb://', ORIGIN='https://bkcb6.app', WEB=/^https?:$/.test(location.protocol);\n")
    rep("          if(typeof u!=='string') return u;\n", "          if(WEB||typeof u!=='string') return u;\n")
    rep("        if(!window.L||!L.tileLayer||L.__bkcb) return;\n", "        if(WEB){clearInterval(hook);return;}\n        if(!window.L||!L.tileLayer||L.__bkcb) return;\n")
    # SitePageWeb: load bkcb6.app with a connection, keep its links in the page
    rep('''        if let u = URL(string: "\\(SiteScheme.scheme)://site/\\(rel)") { w.load(URLRequest(url: u)) }''',
        '''        if !NetWatch.useBundledMap, let u = URL(string: "https://bkcb6.app/\\(rel)") { w.load(URLRequest(url: u)); return }
        if let u = URL(string: "\\(SiteScheme.scheme)://site/\\(rel)") { w.load(URLRequest(url: u)) }''')
    rep('''            if u.scheme == SiteScheme.scheme || u.scheme == "about" || u.scheme == "data" || u.scheme == "blob" { decisionHandler(.allow); return }
            if u.scheme == "tel" || u.scheme == "mailto" || u.scheme == "sms" { UIApplication.shared.open(u); decisionHandler(.cancel); return }
            if let web = SiteScheme.webURL(u) { InAppWeb.open(web) } else { InAppWeb.open(u) }''',
        '''            if u.scheme == SiteScheme.scheme || u.scheme == "about" || u.scheme == "data" || u.scheme == "blob" { decisionHandler(.allow); return }
            if u.scheme == "https", u.host == "bkcb6.app" || !(a.targetFrame?.isMainFrame ?? true) { decisionHandler(.allow); return }
            if u.scheme == "tel" || u.scheme == "mailto" || u.scheme == "sms" { UIApplication.shared.open(u); decisionHandler(.cancel); return }
            if let web = SiteScheme.webURL(u) { InAppWeb.open(web) } else { InAppWeb.open(u) }''')
    # SiteCardWeb: the address card the same way
    rep('''        var q = URLComponents(string: "\\(SiteScheme.scheme)://site/citywide-search.html")!''',
        '''        var q = URLComponents(string: NetWatch.useBundledMap ? "\\(SiteScheme.scheme)://site/citywide-search.html" : "https://bkcb6.app/citywide-search.html")!''')
    rep('''            if u.scheme == "about" || u.scheme == "data" || u.scheme == "blob" { decisionHandler(.allow); return }
            if u.scheme == "tel" || u.scheme == "mailto" || u.scheme == "sms" { UIApplication.shared.open(u); decisionHandler(.cancel); return }
            if a.targetFrame?.isMainFrame ?? true { route(u, w); decisionHandler(.cancel); return }''',
        '''            if u.scheme == "about" || u.scheme == "data" || u.scheme == "blob" { decisionHandler(.allow); return }
            if u.scheme == "tel" || u.scheme == "mailto" || u.scheme == "sms" { UIApplication.shared.open(u); decisionHandler(.cancel); return }
            if u.scheme == "https", u.host == "bkcb6.app", u.path.hasSuffix("citywide-search.html") || a.navigationType != .linkActivated { decisionHandler(.allow); return }
            if a.targetFrame?.isMainFrame ?? true { route(u, w); decisionHandler(.cancel); return }''')
    open(p, 'w').write(s)
print('applemaps ok', R)
