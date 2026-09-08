"""Unified search — KQL across messages, events, files, sites, lists, people."""

from __future__ import annotations

from ._common import graph, graph_tool, run_sync


def _split_entity_types(s: str):
    return [e.strip() for e in s.split(",")]


@graph_tool("search", "POST", "/search/query", delegated=["Mail.Read", "Files.Read.All", "Sites.Read.All", "People.Read"])
def search_query(
    query: str,
    entity_types: str = "message,driveItem,site,listItem,person,event",
    size: int = 25,
):
    """Unified Microsoft Search (KQL). entity_types: comma-separated (message, driveItem, site, listItem, person, event)."""
    def go():
        types = _split_entity_types(entity_types)
        body = {
            "requests": [
                {
                    "entityTypes": types,
                    "query": {"queryString": query},
                    "from": 0,
                    "size": size,
                }
            ]
        }
        return run_sync(graph().post("/search/query", json=body))
    return go()


@graph_tool("search", "POST", "/search/query", delegated=["ExternalItem.Read.All"])
def search_external(query: str, connection_id: str, size: int = 25):
    """Search a specific Microsoft Graph connector (externalItem)."""
    def go():
        body = {
            "requests": [
                {
                    "entityTypes": ["externalItem"],
                    "query": {"queryString": query},
                    "from": 0,
                    "size": size,
                    "sharePointOneDriveOptions": {"includeContent": "sharedAndPrivate"},
                    "trimDuplicates": False,
                    "searchTerms": [query],
                    "contentSources": [f"external/{connection_id}"],
                }
            ]
        }
        return run_sync(graph().post("/search/query", json=body))
    return go()
