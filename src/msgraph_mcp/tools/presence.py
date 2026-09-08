"""Presence — user presence, batch presence."""

from __future__ import annotations

from ._common import graph, graph_tool, require_write, run_sync


@graph_tool("presence", "GET", "/me/presence", delegated=["Presence.Read"])
def get_my_presence():
    def go():
        return run_sync(graph().get("/me/presence"))
    return go()


@graph_tool("presence", "GET", "/users/{id}/presence", delegated=["Presence.Read.All"])
def get_user_presence(user_id: str):
    def go():
        return run_sync(graph().get(f"/users/{user_id}/presence"))
    return go()


@graph_tool("presence", "POST", "/communications/getPresencesByUserId", delegated=["Presence.Read.All"])
def get_presences_by_user_id(user_ids: str):
    """Get presence for multiple users. user_ids: comma-separated GUIDs."""
    def go():
        ids = [u.strip() for u in user_ids.split(",")]
        return run_sync(graph().post("/communications/getPresencesByUserId", json={"ids": ids}))
    return go()


@graph_tool("presence", "POST", "/users/{id}/presence/setPresence", delegated=["Presence.ReadWrite"])
def set_user_presence(user_id: str, session_id: str, availability: str, activity: str, expiration_duration: str = "PT1H"):
    """Set presence. availability/activity: e.g. 'Available'/'Available', 'Busy'/'InACall'."""
    def go():
        require_write()
        body = {
            "sessionId": session_id,
            "availability": availability,
            "activity": activity,
            "expirationDuration": expiration_duration,
        }
        return run_sync(graph().post(f"/users/{user_id}/presence/setPresence", json=body))
    return go()
