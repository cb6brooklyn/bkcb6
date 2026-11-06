import SwiftUI

/// Rows a file node can take from the app itself ("data": {"source": "<name>"}), for what no file holds.
@MainActor
enum FileNodeSources {
    static func rows(_ name: String, spec: [String: Any], ctx: [String: Any], store: DataStore) -> [[String: Any]] {
        switch name {
        case "nextmeeting":
            return store.nextBoardMeeting.map { [row($0)] } ?? []
        case "meetings":
            return store.upcomingBoardMeetings.map(row)
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
        case "meeting": MeetingSquare(meeting: store.nextBoardMeeting)
        default: EmptyView()
        }
    }
}
