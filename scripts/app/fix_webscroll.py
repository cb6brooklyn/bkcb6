"""Test hook for in-app site pages: "-webScroll <y>" scrolls the page after it loads. fix_webscroll.py <app dir>"""
import sys, os
p = os.path.join(sys.argv[1], 'BKCB6/App/Views/SiteCard.swift'); s = open(p).read()
if '-webScroll' not in s:
    o = '''    final class Coord: NSObject, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler {
        var loaded = ""
'''
    assert s.count(o) == 1
    s = s.replace(o, o + '''        func webView(_ w: WKWebView, didFinish n: WKNavigation!) {
            if let y = Hook.value("-webScroll") { DispatchQueue.main.asyncAfter(deadline: .now() + 6) { w.evaluateJavaScript("window.scrollTo(0,\\(y))", completionHandler: nil) } }
        }
''')
    open(p, 'w').write(s)
print('webscroll ok')
