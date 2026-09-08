"""Change notifications — webhook subscriptions, lifecycles, and delta queries."""

from __future__ import annotations

from ._common import fail, graph, graph_tool, require_write, run_sync

SUPPORTED_RESOURCES = [
    "me/messages",
    "me/events",
    "me/contacts",
    "me/drive/root",
    "me/insights/trending",
    "groups",
    "users",
    "chats",
    "teams",
    "conversations",
    "sharePointLists",
]


@graph_tool("change_notifications", "POST", "/subscriptions", delegated=["Mail.ReadWrite", "Files.ReadWrite", "Group.Read.All"], application=["Mail.ReadWrite", "Files.ReadWrite", "Group.Read.All"])
def create_subscription(
    notification_url: str,
    resource: str,
    change_type: str = "created,updated",
    expiration_datetime: str = None,
    client_state: str = None,
):
    """Create a webhook subscription for a resource. resource: e.g. 'me/messages', 'me/events', 'me/drive/root'."""
    def go():
        require_write()
        if resource not in SUPPORTED_RESOURCES and not resource.startswith("users/") and not resource.startswith("sites/"):
            return fail(f"Unsupported resource. Supported: {', '.join(SUPPORTED_RESOURCES)} or users/..., sites/...")
        body: dict = {
            "changeType": change_type,
            "notificationUrl": notification_url,
            "resource": resource,
            "expirationDateTime": expiration_datetime or "2099-12-31T23:59:59Z",
            "clientState": client_state or "msgraph-mcp",
        }
        return run_sync(graph().post("/subscriptions", json=body))
    return go()


@graph_tool("change_notifications", "GET", "/subscriptions", delegated=["Mail.ReadWrite", "Files.ReadWrite", "Group.Read.All"])
def list_subscriptions():
    def go():
        return run_sync(graph().get_all("/subscriptions"))
    return go()


@graph_tool("change_notifications", "POST", "/subscriptions/{id}/reauthorize", delegated=["Mail.ReadWrite", "Files.ReadWrite", "Group.Read.All"])
def reauthorize_subscription(subscription_id: str):
    """Reauthorize an expiring subscription."""
    def go():
        require_write()
        return run_sync(graph().post(f"/subscriptions/{subscription_id}/reauthorize"))
    return go()


@graph_tool("change_notifications", "DELETE", "/subscriptions/{id}", delegated=["Mail.ReadWrite", "Files.ReadWrite", "Group.Read.All"])
def delete_subscription(subscription_id: str):
    def go():
        require_write()
        return run_sync(graph().delete(f"/subscriptions/{subscription_id}"))
    return go()


@graph_tool("change_notifications", "GET", "/{resource}/delta", delegated=["Mail.Read", "Files.Read", "Calendars.Read"])
def delta_query(resource: str, delta_token: str = None):
    """Execute a delta query on a resource. resource: 'me/messages', 'me/events', 'me/contacts', 'me/drive/root'."""
    def go():
        if resource not in ["me/messages", "me/events", "me/contacts", "me/drive/root"]:
            return fail("Delta supported on: me/messages, me/events, me/contacts, me/drive/root")
        if delta_token:
            return run_sync(graph().get(f"/{resource}/delta", params={"$deltatoken": delta_token}))
        return run_sync(graph().get(f"/{resource}/delta"))
    return go()
