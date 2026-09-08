"""Chat — 1:1 and group chats, messages, search."""

from __future__ import annotations

from ._common import graph, graph_tool, require_write, run_sync, to_query


@graph_tool("chat", "GET", "/me/chats", delegated=["Chat.Read"])
def list_chats(top: int = None, filter: str = None):
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        return run_sync(graph().get_all("/me/chats", params=params))
    return go()


@graph_tool("chat", "GET", "/me/chats/{id}", delegated=["Chat.Read"])
def get_chat(chat_id: str):
    def go():
        return run_sync(graph().get(f"/me/chats/{chat_id}"))
    return go()


@graph_tool("chat", "GET", "/chats/{id}/messages", delegated=["ChatMessage.Read"])
def list_chat_messages(chat_id: str, top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all(f"/chats/{chat_id}/messages", params=params))
    return go()


@graph_tool("chat", "GET", "/chats/{id}/members", delegated=["ChatMember.Read"])
def list_chat_members(chat_id: str):
    def go():
        return run_sync(graph().get_all(f"/chats/{chat_id}/members"))
    return go()


@graph_tool("chat", "POST", "/chats/{id}/messages", delegated=["ChatMessage.Send"])
def send_chat_message(chat_id: str, content: str, content_type: str = "text"):
    """Send a message to a chat. content_type: 'text' or 'html'."""
    def go():
        require_write()
        body = {"body": {"contentType": content_type, "content": content}}
        return run_sync(graph().post(f"/chats/{chat_id}/messages", json=body))
    return go()


@graph_tool("chat", "POST", "/chats", delegated=["Chat.Create"])
def create_chat(chat_type: str, topic: str = None, members: str = None):
    """Create a chat. chat_type: 'group' or 'oneOnOne'. members: semicolon-separated UPNs."""
    def go():
        require_write()
        body: dict = {"chatType": chat_type}
        if topic:
            body["topic"] = topic
        if members:
            body["members"] = [
                {"odataType": "#microsoft.graph.aadUserConversationMember",
                 "roles": ["owner"] if i == 0 else [],
                 "user@odata.bind": f"https://graph.microsoft.com/v1.0/users/{m.strip()}"}
                for i, m in enumerate(members.split(";"))
            ]
        return run_sync(graph().post("/chats", json=body))
    return go()


@graph_tool("chat", "GET", "/search", delegated=["Chat.Read", "ChatMessage.Read"])
def search_messages(query: str, top: int = 20):
    """Search Teams messages using Microsoft Search KQL."""
    def go():
        body = {
            "requests": [
                {
                    "entityTypes": ["chatMessage"],
                    "query": {"queryString": query},
                    "from": 0,
                    "size": top,
                }
            ]
        }
        return run_sync(graph().post("/search/query", json=body))
    return go()
