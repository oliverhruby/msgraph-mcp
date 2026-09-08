"""Online meetings — create, transcripts, attendance, recordings."""

from __future__ import annotations

from ._common import graph, graph_tool, require_write, run_sync, to_query


@graph_tool("online_meetings", "POST", "/me/onlineMeetings", delegated=["OnlineMeetings.ReadWrite"])
def create_online_meeting(
    subject: str,
    start_datetime: str,
    end_datetime: str,
    join_meeting_settings: str = None,
    participants: str = None,
):
    """Create a Teams online meeting. participants: semicolon-separated emails (optional)."""
    def go():
        require_write()
        body: dict = {
            "subject": subject,
            "startDateTime": start_datetime,
            "endDateTime": end_datetime,
        }
        if participants:
            body["participants"] = {
                "attendees": [
                    {"upn": p.strip(), "role": "attendee"}
                    for p in participants.split(";")
                ]
            }
        return run_sync(graph().post("/me/onlineMeetings", json=body))
    return go()


@graph_tool("online_meetings", "GET", "/me/onlineMeetings", delegated=["OnlineMeetings.Read"])
def list_online_meetings(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/me/onlineMeetings", params=params))
    return go()


@graph_tool("online_meetings", "GET", "/me/onlineMeetings/{id}", delegated=["OnlineMeetings.Read"])
def get_online_meeting(meeting_id: str):
    def go():
        return run_sync(graph().get(f"/me/onlineMeetings/{meeting_id}"))
    return go()


@graph_tool("online_meetings", "GET", "/users/{id}/onlineMeetings/{meetingId}/transcripts", delegated=["OnlineMeetingTranscript.Read.All"])
def list_transcripts(user_id: str, meeting_id: str):
    def go():
        return run_sync(graph().get_all(f"/users/{user_id}/onlineMeetings/{meeting_id}/transcripts"))
    return go()


@graph_tool("online_meetings", "GET", "/users/{id}/onlineMeetings/{meetingId}/transcripts/{transcriptId}/content", delegated=["OnlineMeetingTranscript.Read.All"])
def get_transcript_content(user_id: str, meeting_id: str, transcript_id: str):
    def go():
        return run_sync(graph().get(f"/users/{user_id}/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content"))
    return go()


@graph_tool("online_meetings", "GET", "/users/{id}/onlineMeetings/{meetingId}/attendanceReports", delegated=["OnlineMeetingArtifact.Read.All"])
def list_attendance_reports(user_id: str, meeting_id: str):
    def go():
        return run_sync(graph().get_all(f"/users/{user_id}/onlineMeetings/{meeting_id}/attendanceReports"))
    return go()


@graph_tool("online_meetings", "GET", "/me/onlineMeetings/{id}/recordings", delegated=["OnlineMeetingRecording.Read.All"])
def list_meeting_recordings(meeting_id: str):
    def go():
        return run_sync(graph().get_all(f"/me/onlineMeetings/{meeting_id}/recordings"))
    return go()


@graph_tool("online_meetings", "GET", "/users/{id}/onlineMeetings/{meetingId}/transcripts/allTranscripts", delegated=["OnlineMeetingTranscript.Read.All"])
def list_all_transcripts(user_id: str, meeting_id: str):
    """List all transcripts for a meeting."""
    def go():
        return run_sync(graph().get_all(f"/users/{user_id}/onlineMeetings/{meeting_id}/transcripts/allTranscripts"))
    return go()
