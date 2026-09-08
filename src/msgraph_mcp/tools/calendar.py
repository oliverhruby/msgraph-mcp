"""Calendar — events, calendars, free/busy, meeting times, rooms."""

from __future__ import annotations

from ._common import fail, graph, graph_tool, require_write, run_sync, to_query


@graph_tool("calendar", "GET", "/me/calendarView", delegated=["Calendars.Read"])
def list_upcoming_events(top: int = 20):
    """List upcoming events from the user's default calendar."""
    def go():
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        # Use calendarView for expanded recurring events
        return run_sync(graph().get("/me/calendarView", params={
            "$top": str(top),
            "startDateTime": now,
            "endDateTime": (datetime.now(timezone.utc).replace(hour=23, minute=59)).isoformat(),
        }))
    return go()


@graph_tool("calendar", "GET", "/me/calendarView", delegated=["Calendars.Read"])
def list_events_in_range(start_date: str, end_date: str, top: int = None):
    """List events in a date range. Dates in ISO 8601 format."""
    def go():
        params = to_query(**{
            "startDateTime": start_date,
            "endDateTime": end_date,
            "$top": top,
        })
        return run_sync(graph().get_all("/me/calendarView", params=params))
    return go()


@graph_tool("calendar", "GET", "/me/events/{id}", delegated=["Calendars.Read"])
def get_event(event_id: str, select: str = None):
    def go():
        params = to_query(**{"$select": select})
        return run_sync(graph().get(f"/me/events/{event_id}", params=params))
    return go()


@graph_tool("calendar", "GET", "/me/events/{id}/instances", delegated=["Calendars.Read"])
def list_event_instances(event_id: str, start_date: str, end_date: str):
    """List instances of a recurring event in a date range."""
    def go():
        params = {"startDateTime": start_date, "endDateTime": end_date}
        return run_sync(graph().get_all(f"/me/events/{event_id}/instances", params=params))
    return go()


@graph_tool("calendar", "GET", "/me/events/{id}/attachments", delegated=["Calendars.Read"])
def list_event_attachments(event_id: str):
    def go():
        return run_sync(graph().get_all(f"/me/events/{event_id}/attachments"))
    return go()


@graph_tool("calendar", "GET", "/me/calendars", delegated=["Calendars.Read"])
def list_calendars():
    def go():
        return run_sync(graph().get_all("/me/calendars"))
    return go()


@graph_tool("calendar", "GET", "/me/calendarGroups/{groupId}/calendars", delegated=["Calendars.Read"])
def list_calendars_in_group(group_id: str):
    def go():
        return run_sync(graph().get_all(f"/me/calendarGroups/{group_id}/calendars"))
    return go()


@graph_tool("calendar", "GET", "/places", delegated=["Place.Read.All"], application=["Place.Read.All"])
def list_rooms():
    def go():
        return run_sync(graph().get_all("/places"))
    return go()


@graph_tool("calendar", "POST", "/me/findMeetingTimes", delegated=["Calendars.ReadWrite"])
def find_meeting_times(
    attendees: str,
    start: str,
    end: str,
    duration_minutes: int = 30,
    max_candidates: int = 5,
    is_required: bool = True,
):
    """Find meeting slots. attendees: semicolon-separated email addresses."""
    def go():
        attendee_list = [{"emailAddress": {"address": a.strip()}, "type": "Required" if is_required else "Optional"} for a in attendees.split(";")]
        payload = {
            "attendees": attendee_list,
            "timeConstraint": {
                "activityDomain": "work",
                "timeSlots": [{"start": {"dateTime": start, "timeZone": "UTC"}, "end": {"dateTime": end, "timeZone": "UTC"}}],
            },
            "duration": f"PT{duration_minutes}M",
            "maxCandidateCount": max_candidates,
        }
        return run_sync(graph().post("/me/findMeetingTimes", json=payload))
    return go()


@graph_tool("calendar", "POST", "/me/getSchedule", delegated=["Calendars.Read.Shared"])
def get_schedule(availability_views: str, start_date: str, end_date: str, interval_minutes: int = 30):
    """Get free/busy schedule. availability_views: semicolon-separated email addresses."""
    def go():
        emails = [e.strip() for e in availability_views.split(";")]
        payload = {
            "schedules": [e for e in emails],
            "startTime": {"dateTime": start_date, "timeZone": "UTC"},
            "endTime": {"dateTime": end_date, "timeZone": "UTC"},
            "availabilityViewInterval": interval_minutes,
        }
        return run_sync(graph().post("/me/getSchedule", json=payload))
    return go()


@graph_tool("calendar", "POST", "/me/events", delegated=["Calendars.ReadWrite"])
def create_event(
    subject: str,
    start_datetime: str,
    end_datetime: str,
    body: str = None,
    body_type: str = "HTML",
    attendees: str = None,
    location_display_name: str = None,
    is_all_day: bool = None,
    online_meeting: bool = None,
):
    """Create a calendar event. Dates in ISO 8601. attendees: semicolon-separated emails."""
    def go():
        require_write()
        payload: dict = {
            "subject": subject,
            "start": {"dateTime": start_datetime, "timeZone": "UTC"},
            "end": {"dateTime": end_datetime, "timeZone": "UTC"},
        }
        if body:
            payload["body"] = {"contentType": body_type, "content": body}
        if attendees:
            payload["attendees"] = [
                {"emailAddress": {"address": a.strip()}, "type": "required"}
                for a in attendees.split(";")
            ]
        if location_display_name:
            payload["location"] = {"displayName": location_display_name}
        if is_all_day is not None:
            payload["isAllDay"] = is_all_day
        if online_meeting:
            payload["isOnlineMeeting"] = True
            payload["onlineMeetingProvider"] = "teamsForBusiness"
        return run_sync(graph().post("/me/events", json=payload))
    return go()


@graph_tool("calendar", "PATCH", "/me/events/{id}", delegated=["Calendars.ReadWrite"])
def update_event(event_id: str, subject: str = None, start_datetime: str = None, end_datetime: str = None):
    def go():
        require_write()
        body = {}
        if subject is not None:
            body["subject"] = subject
        if start_datetime is not None:
            body["start"] = {"dateTime": start_datetime, "timeZone": "UTC"}
        if end_datetime is not None:
            body["end"] = {"dateTime": end_datetime, "timeZone": "UTC"}
        if not body:
            return fail("No fields to update")
        return run_sync(graph().patch(f"/me/events/{event_id}", json=body))
    return go()


@graph_tool("calendar", "DELETE", "/me/events/{id}", delegated=["Calendars.ReadWrite"])
def cancel_event(event_id: str):
    def go():
        require_write()
        return run_sync(graph().delete(f"/me/events/{event_id}"))
    return go()


@graph_tool("calendar", "POST", "/me/events/{id}/respond", delegated=["Calendars.ReadWrite"])
def respond_to_event(event_id: str, response: str, send_response: bool = True):
    """Respond to event. response: 'tentativelyAccept', 'accept', 'decline'."""
    def go():
        require_write()
        payload = {
            "comment": "",
            "sendResponse": send_response,
        }
        return run_sync(graph().post(f"/me/events/{event_id}/{response}", json=payload))
    return go()
