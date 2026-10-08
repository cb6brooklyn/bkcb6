"""BKCB / CBNYC home: the picker, the map, the district tools and the two tiles become sections the file orders
(kinds pickboard, map, glance, squares), with the code's order as the fallback."""
import re
H = '/Users/user301938'
OLD = '''                    VStack(alignment: .leading, spacing: 0) {
                        if sel.cd.isEmpty { PickBoardCard().padding(.top, 14) }
                        mapCard.padding(.top, 14).id("homemap")
                        // The district's own tools, right under its map and open the moment a board is picked.
                        if !sel.cd.isEmpty { AroundYouCard(cd: cd, short: sel.short, isCB6: sel.isCB6, open: open).id("glance") }
                        HStack(alignment: .top, spacing: 10) {
                            if sel.isCB6 { MeetingSquare(meeting: store.nextBoardMeeting) } else { BoardMeetingSquare(cd: cd).id("meeting-\\(cd)") }
                            Button { path.append("vote") } label: { ElectionSquare() }.buttonStyle(.plain)
                        }
                        .padding(.top, 12)
                        .id("squares")
                        HomeSections(screen: "home", fallback: BKHomeView.defaultSections, show: { BKHomeView.applies($0.when, cd: sel.cd) },
                                     fixed: { _ in EmptyView() }, fold: { s in foldContent(s) })'''
NEW = '''                    VStack(alignment: .leading, spacing: 0) {
                        // Every part of Home in the order home.json gives it: pickboard, map, glance, squares and the folds.
                        HomeSections(screen: "home", fallback: BKHomeView.defaultSections, show: { BKHomeView.applies($0.when, cd: sel.cd) },
                                     fixed: { s in
                            switch s.kind {
                            case "pickboard": if sel.cd.isEmpty { PickBoardCard().padding(.top, 14) }
                            case "map": mapCard.padding(.top, 14).id("homemap")
                            case "glance": if !sel.cd.isEmpty { AroundYouCard(cd: cd, short: sel.short, isCB6: sel.isCB6, open: open).id("glance") }
                            case "squares":
                                HStack(alignment: .top, spacing: 10) {
                                    if sel.isCB6 { MeetingSquare(meeting: store.nextBoardMeeting) } else { BoardMeetingSquare(cd: cd).id("meeting-\\(cd)") }
                                    Button { path.append("vote") } label: { ElectionSquare() }.buttonStyle(.plain)
                                }
                                .padding(.top, 12)
                                .id("squares")
                            default: EmptyView()
                            }
                        }, fold: { s in foldContent(s) })'''
OLD_D = '''    static let defaultSections: [UIConfig.Section] = [
        UIConfig.Section(kind: "fold", id: "myblock",'''
NEW_D = '''    static let defaultSections: [UIConfig.Section] = [
        UIConfig.Section(kind: "pickboard", id: "pickboard", title: "", content: "", when: "always", open: false),
        UIConfig.Section(kind: "map", id: "homemap", title: "", content: "", when: "always", open: false),
        UIConfig.Section(kind: "glance", id: "glance", title: "", content: "", when: "always", open: false),
        UIConfig.Section(kind: "squares", id: "squares", title: "", content: "", when: "always", open: false),
        UIConfig.Section(kind: "fold", id: "myblock",'''
for a in ('bkcivics', 'cb6beyond'):
    p = f'{H}/{a}/BKCB6/App/Views/BKHome.swift'; s = open(p).read()
    if 'case "pickboard":' in s: print(a, 'already'); continue
    start = s.find('                    VStack(alignment: .leading, spacing: 0) {\n                        if sel.cd.isEmpty { PickBoardCard()')
    endm = 'fixed: { _ in EmptyView() }, fold: { s in foldContent(s) })'
    end = s.find(endm, start)
    if start < 0 or end < 0 or OLD_D not in s: print(a, 'anchor missing', start, end, OLD_D in s); continue
    s = s[:start] + NEW + s[end + len(endm):]
    s = s.replace(OLD_D, NEW_D, 1)
    open(p, 'w').write(s); print(a, 'patched')
