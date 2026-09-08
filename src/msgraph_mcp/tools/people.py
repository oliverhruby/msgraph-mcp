"""People — relevance search, insights, profile."""

from __future__ import annotations

from ._common import graph, graph_tool, run_sync


@graph_tool("people", "GET", "/me/people", delegated=["People.Read"])
def people_search(query: str, top: int = 10):
    """Search people using the relevance graph (colleagues ranked by interaction)."""
    def go():
        return run_sync(graph().get("/me/people", params={
            "$search": f'"query:{query}"',
            "$top": str(top),
            "$select": ",".join(["displayName", "givenName", "surname", "userPrincipalName", "mail", "jobTitle", "department", "mobilePhone", "officeLocation"]),
        }))
    return go()


@graph_tool("people", "GET", "/me/insights/trending", delegated=["Sites.Read.All"])
def list_trending():
    def go():
        return run_sync(graph().get_all("/me/insights/trending"))
    return go()


@graph_tool("people", "GET", "/me/insights/used", delegated=["Sites.Read.All"])
def list_used():
    def go():
        return run_sync(graph().get_all("/me/insights/used"))
    return go()


@graph_tool("people", "GET", "/me/insights/shared", delegated=["Sites.Read.All"])
def list_shared_insights():
    def go():
        return run_sync(graph().get_all("/me/insights/shared"))
    return go()


@graph_tool("people", "GET", "/me/profile", delegated=["User.Read"])
def get_my_rich_profile():
    def go():
        return run_sync(graph().get("/me/profile"))
    return go()
