import SwiftUI

/// Rows a file node can take from the app itself ("data": {"source": "<name>"}), for what no file holds.
@MainActor
enum FileNodeSources {
    static func rows(_ name: String, spec: [String: Any], ctx: [String: Any], store: DataStore) -> [[String: Any]] {
        let cd = FN.board
        switch name {
        case "nextmeeting":
            if cd == "306" { return store.nextBoardMeeting.map { [row($0)] } ?? [] }
            // Only full board meetings: a board's own meeting, never a committee or a community event in its district.
            let hidden = CalHidden.current
            guard let e = CalData.merged(.city, meetings: store.meetings).first(where: { e in
                let c = e.cd ?? ""
                guard !c.isEmpty, cd.isEmpty || c == cd, !hidden.contains(CalHidden.key(e)), e.key != "committee" else { return false }
                return e.key == "board" || e.type == "cbmeeting" || e.label.range(of: "full board|general meeting|board meeting", options: [.regularExpression, .caseInsensitive]) != nil
            }) else { return [] }
            let b = cd.isEmpty ? (e.cd ?? "") : cd
            return [["date": e.day, "time": e.time ?? "", "title": e.label, "board": BKBoards.board(b)?.short ?? FN.boardShort(b), "cd": b]]
        case "meetings":
            return cd == "306" ? store.upcomingBoardMeetings.map(row) : []
        default:
            return []
        }
    }
    static func row(_ m: Meeting) -> [String: Any] {
        ["date": m.start, "time": m.allDay ? "" : Fmt.time.string(from: m.start), "title": m.isFullBoard ? Copy.t("HomeView.71c4ae61", "Full Board") : m.body,
         "fullBoard": m.isFullBoard, "board": "CB6", "cd": "306"]
    }
}

/// A named piece of the app's own code inside a file node ("type": "part", "name": "meeting").
struct FileNodePart: View {
    let name: String
    @EnvironmentObject var store: DataStore
    var body: some View {
        switch name {
        case "meeting":
            if FN.board == "306" { MeetingSquare(meeting: store.nextBoardMeeting) } else { BoardMeetingSquare(cd: FN.board) }
        default: EmptyView()
        }
    }
}
