import XCTest

final class StripUITests: XCTestCase {
    let dir = "/Users/user301938/uit-shots"
    func shot(_ app: XCUIApplication, _ name: String) {
        try? app.screenshot().pngRepresentation.write(to: URL(fileURLWithPath: "\(dir)/\(name).png"))
    }
    func note(_ s: String) {
        let u = URL(fileURLWithPath: "\(dir)/log.txt")
        let line = (s + "\n").data(using: .utf8)!
        if let h = try? FileHandle(forWritingTo: u) { h.seekToEndOfFile(); h.write(line); h.closeFile() } else { try? line.write(to: u) }
    }
    func bars(_ app: XCUIApplication) -> String { "navbars=\(app.navigationBars.allElementsBoundByIndex.map { $0.identifier }) back=\(app.navigationBars.buttons.count) homeTitle=\(app.staticTexts["Brooklyn Community Board 6"].exists)" }
    func testTiles() throws {
        let app = XCUIApplication()
        app.launch()
        sleep(12)
        let tb = app.buttons["ALTERNATE SIDE PARKING ›, In effect"].firstMatch
        guard tb.waitForExistence(timeout: 20) else { note("tile button not found"); return }
        note("tile button at \(tb.frame) hittable=\(tb.isHittable) enabled=\(tb.isEnabled)")
        tb.tap(); sleep(3)
        note("after tile tap: \(bars(app))"); shot(app, "4-tilebutton")
        if app.navigationBars.buttons.count > 0 { app.navigationBars.buttons.element(boundBy: 0).tap(); sleep(2) }
        let c = tb.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5))
        c.tap(); sleep(3)
        note("after coord tap: \(bars(app))"); shot(app, "5-coord")
        if app.navigationBars.buttons.count > 0 { app.navigationBars.buttons.element(boundBy: 0).tap(); sleep(2) }
        c.press(forDuration: 0.1); sleep(3)
        note("after press: \(bars(app))"); shot(app, "6-press")
        // What sits at that point?
        let hits = app.descendants(matching: .any).allElementsBoundByIndex.filter { $0.frame.contains(CGPoint(x: 280, y: 236)) && $0.frame.width < 900 }
        note("elements at (280,236): \(hits.map { "\($0.elementType.rawValue):\($0.label.prefix(30)):\($0.frame)" })")
        // A view-destination NavigationLink in the block card (vertical layout), scrolled clear of the tab bar.
        app.swipeUp(); sleep(1)
        for name in ["Full address card", "City records for the lot", "Full block card"] {
            let p = app.buttons[name].firstMatch
            if p.waitForExistence(timeout: 3) {
                note("\(name) at \(p.frame) hittable=\(p.isHittable)")
                if p.isHittable && p.frame.maxY < 760 {
                    p.tap(); sleep(3); note("after \(name) tap: \(bars(app))"); shot(app, "8-\(name.prefix(4))")
                    if app.navigationBars.buttons.count > 0 { app.navigationBars.buttons.element(boundBy: 0).tap(); sleep(2) }
                    break
                }
            }
        }
        // The squares: a Button with path.append.
        let e = app.buttons.matching(NSPredicate(format: "label BEGINSWITH 'ELECTION DAY'")).firstMatch
        if e.waitForExistence(timeout: 5) { note("election square at \(e.frame) hittable=\(e.isHittable)"); e.tap(); sleep(3); note("after election tap: \(bars(app))"); shot(app, "7-election") }
    }
}
