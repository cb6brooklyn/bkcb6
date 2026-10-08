"""CBNYC home: boroughs, picker, map, district tools, tiles and the election banner become sections the file orders."""
H = '/Users/user301938'
p = f'{H}/cb6beyond/BKCB6/App/Views/BKHome.swift'; s = open(p).read()
start = s.find('                        // The five boroughs and the city, six buttons, first on the screen.')
endm = 'fixed: { _ in EmptyView() }, fold: { s in foldContent(s) })'
end = s.find(endm, start)
assert start > 0 and end > 0, (start, end)
NEW = '''                        // Every part of Home in the order home.json gives it: boroughs, pickboard, map, glance, squares, banner and the folds.
                        HomeSections(screen: "home", fallback: BKHomeView.defaultSections, show: { BKHomeView.applies($0.when, cd: sel.cd) },
                                     titleFor: { s in s.id == "borough" ? (sel.board.map { BKBoards.boroughName($0.boroDigit) } ?? "") : s.title },
                                     fixed: { s in
                            switch s.kind {
                            case "boroughs":
                                Text(T("home.boroughs.title", "The five boroughs and the city")).font(DM.sans(18, .bold)).foregroundStyle(Color.cb6Navy).padding(.top, 14).padding(.bottom, 8)
                                BoroughGrid().id("boroughs")
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
                            case "banner": BeyondElectionBanner().padding(.top, 12)
                            default: EmptyView()
                            }
                        }, fold: { s in foldContent(s) })'''
s = s[:start] + NEW + s[end + len(endm):]
OLD_D = '''    static let defaultSections: [UIConfig.Section] = [
        UIConfig.Section(kind: "fold", id: "myblock",'''
NEW_D = '''    static let defaultSections: [UIConfig.Section] = [
        UIConfig.Section(kind: "boroughs", id: "boroughs", title: "", content: "", when: "always", open: false),
        UIConfig.Section(kind: "pickboard", id: "pickboard", title: "", content: "", when: "always", open: false),
        UIConfig.Section(kind: "map", id: "homemap", title: "", content: "", when: "always", open: false),
        UIConfig.Section(kind: "glance", id: "glance", title: "", content: "", when: "always", open: false),
        UIConfig.Section(kind: "squares", id: "squares", title: "", content: "", when: "always", open: false),
        UIConfig.Section(kind: "banner", id: "banner", title: "", content: "", when: "always", open: false),
        UIConfig.Section(kind: "fold", id: "myblock",'''
assert OLD_D in s
s = s.replace(OLD_D, NEW_D, 1)
open(p, 'w').write(s); print('cb6beyond patched', s.count('case "pickboard":'))
