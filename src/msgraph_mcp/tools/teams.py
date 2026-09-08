"""Teams — teams, channels, channel messages, replies, members, tabs."""

from __future__ import annotations

from ._common import graph, graph_tool, require_write, run_sync, to_query


@graph_tool("teams", "GET", "/me/joinedTeams", delegated=["Team.ReadBasic.All"])
def list_my_teams(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/me/joinedTeams", params=params))
    return go()


@graph_tool("teams", "GET", "/teams", delegated=["Team.ReadBasic.All"], application=["Team.ReadBasic.All"])
def list_all_teams(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/teams", params=params))
    return go()


@graph_tool("teams", "GET", "/teams/{id}", delegated=["Team.ReadBasic.All"])
def get_team(team_id: str):
    def go():
        return run_sync(graph().get(f"/teams/{team_id}"))
    return go()


@graph_tool("teams", "GET", "/teams/{id}/channels", delegated=["Channel.ReadBasic.All"])
def list_channels(team_id: str, top: int = None, filter: str = None):
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        return run_sync(graph().get_all(f"/teams/{team_id}/channels", params=params))
    return go()


@graph_tool("teams", "GET", "/teams/{id}/channels/{channelId}", delegated=["Channel.ReadBasic.All"])
def get_channel(team_id: str, channel_id: str):
    def go():
        return run_sync(graph().get(f"/teams/{team_id}/channels/{channel_id}"))
    return go()


@graph_tool("teams", "GET", "/teams/{id}/channels/{channelId}/messages", delegated=["ChannelMessage.Read.All"])
def list_channel_messages(team_id: str, channel_id: str, top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all(f"/teams/{team_id}/channels/{channel_id}/messages", params=params))
    return go()


@graph_tool("teams", "GET", "/teams/{id}/channels/{channelId}/messages/{messageId}", delegated=["ChannelMessage.Read.All"])
def get_channel_message(team_id: str, channel_id: str, message_id: str):
    def go():
        return run_sync(graph().get(f"/teams/{team_id}/channels/{channel_id}/messages/{message_id}"))
    return go()


@graph_tool("teams", "GET", "/teams/{id}/channels/{channelId}/messages/{messageId}/replies", delegated=["ChannelMessage.Read.All"])
def list_message_replies(team_id: str, channel_id: str, message_id: str):
    def go():
        return run_sync(graph().get_all(f"/teams/{team_id}/channels/{channel_id}/messages/{message_id}/replies"))
    return go()


@graph_tool("teams", "POST", "/teams/{id}/channels/{channelId}/messages", delegated=["ChannelMessage.Send"])
def send_channel_message(team_id: str, channel_id: str, content: str, content_type: str = "text"):
    """Send message to a Teams channel. content_type: 'text' or 'html'."""
    def go():
        require_write()
        body = {"body": {"contentType": content_type, "content": content}}
        return run_sync(graph().post(f"/teams/{team_id}/channels/{channel_id}/messages", json=body))
    return go()


@graph_tool("teams", "GET", "/teams/{id}/members", delegated=["TeamMember.Read.All"])
def list_team_members(team_id: str):
    def go():
        return run_sync(graph().get_all(f"/teams/{team_id}/members"))
    return go()


@graph_tool("teams", "POST", "/teams/{id}/channels", delegated=["Channel.Create"])
def create_channel(team_id: str, display_name: str, description: str = None, membership_type: str = "standard"):
    """Create a channel. membership_type: 'standard' or 'private'."""
    def go():
        require_write()
        body = {"displayName": display_name, "membershipType": membership_type}
        if description:
            body["description"] = description
        return run_sync(graph().post(f"/teams/{team_id}/channels", json=body))
    return go()


@graph_tool("teams", "GET", "/teams/{id}/installedApps", delegated=["TeamsApp.Read.All"])
def list_installed_apps(team_id: str):
    def go():
        return run_sync(graph().get_all(f"/teams/{team_id}/installedApps"))
    return go()


@graph_tool("teams", "GET", "/teams/{id}/tabs", delegated=["TeamsTab.Read.All"])
def list_team_tabs(team_id: str, channel_id: str):
    def go():
        return run_sync(graph().get_all(f"/teams/{team_id}/channels/{channel_id}/tabs"))
    return go()
