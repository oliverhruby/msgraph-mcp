"""SharePoint — sites, lists, list items, columns, content types, site pages.

This is the largest gap in most community MCP servers. Graph exposes:
- sites: READ-ONLY (cannot create a site via Graph)
- lists & listItems: read-write
- driveItem: read-write (covered in files.py)
"""

from __future__ import annotations

from ._common import fail, graph, graph_tool, require_write, run_sync, to_query


@graph_tool("sharepoint", "GET", "/sites", delegated=["Sites.Read.All"], application=["Sites.Read.All"])
def search_sites(query: str):
    """Search SharePoint sites by name/description."""
    def go():
        return run_sync(graph().get_all("/sites", params={"search": query}))
    return go()


@graph_tool("sharepoint", "GET", "/sites/root", delegated=["Sites.Read.All"], application=["Sites.Read.All"])
def get_root_site():
    def go():
        return run_sync(graph().get("/sites/root"))
    return go()


@graph_tool("sharepoint", "GET", "/sites/{hostname}:/{path}", delegated=["Sites.Read.All"], application=["Sites.Read.All"])
def get_site_by_path(hostname: str, path: str):
    """Get a site by its full path. hostname: e.g. 'contoso.sharepoint.com'. path: e.g. 'sites/marketing' or '' for root."""
    def go():
        return run_sync(graph().get(f"/sites/{hostname}:/{path}"))
    return go()


@graph_tool("sharepoint", "GET", "/sites/{id}", delegated=["Sites.Read.All"], application=["Sites.Read.All"])
def get_site(site_id: str):
    def go():
        return run_sync(graph().get(f"/sites/{site_id}"))
    return go()


@graph_tool("sharepoint", "GET", "/sites/{id}/sites", delegated=["Sites.Read.All"], application=["Sites.Read.All"])
def list_sub_sites(site_id: str):
    def go():
        return run_sync(graph().get_all(f"/sites/{site_id}/sites"))
    return go()


@graph_tool("sharepoint", "GET", "/sites/{id}/drives", delegated=["Sites.Read.All"], application=["Sites.Read.All"])
def list_site_drives(site_id: str):
    """List document libraries (drives) on a site."""
    def go():
        return run_sync(graph().get_all(f"/sites/{site_id}/drives"))
    return go()


@graph_tool("sharepoint", "GET", "/sites/{id}/lists", delegated=["Sites.Read.All"], application=["Sites.Read.All"])
def list_lists(site_id: str, top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all(f"/sites/{site_id}/lists", params=params))
    return go()


@graph_tool("sharepoint", "GET", "/sites/{id}/lists/{listId}", delegated=["Sites.Read.All"], application=["Sites.Read.All"])
def get_list(site_id: str, list_id: str):
    def go():
        return run_sync(graph().get(f"/sites/{site_id}/lists/{list_id}"))
    return go()


@graph_tool("sharepoint", "GET", "/sites/{id}/lists/{listId}/items", delegated=["Sites.Read.All"], application=["Sites.Read.All"])
def list_list_items(site_id: str, list_id: str, top: int = None, filter: str = None):
    """List items in a SharePoint list. Use expand_fields=true to get column values."""
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        return run_sync(graph().get_all(
            f"/sites/{site_id}/lists/{list_id}/items",
            params=params,
        ))
    return go()


@graph_tool("sharepoint", "GET", "/sites/{id}/lists/{listId}/items?expand=fields", delegated=["Sites.Read.All"], application=["Sites.Read.All"])
def list_list_items_with_fields(site_id: str, list_id: str, top: int = None, filter: str = None):
    """List SharePoint list items with all column values expanded."""
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        params["$expand"] = "fields"
        return run_sync(graph().get_all(
            f"/sites/{site_id}/lists/{list_id}/items",
            params=params,
        ))
    return go()


@graph_tool("sharepoint", "GET", "/sites/{id}/lists/{listId}/items/{itemId}", delegated=["Sites.Read.All"], application=["Sites.Read.All"])
def get_list_item(site_id: str, list_id: str, item_id: str, expand_fields: bool = False):
    def go():
        params = {"$expand": "fields"} if expand_fields else None
        return run_sync(graph().get(f"/sites/{site_id}/lists/{list_id}/items/{item_id}", params=params))
    return go()


@graph_tool("sharepoint", "POST", "/sites/{id}/lists/{listId}/items", delegated=["Sites.ReadWrite.All"], application=["Sites.ReadWrite.All"])
def create_list_item(site_id: str, list_id: str, fields_json: str):
    """Create a list item. fields_json: JSON object of {columnName: value}."""
    def go():
        require_write()
        import json as _json
        try:
            fields = _json.loads(fields_json)
        except Exception:
            return fail("fields_json must be a valid JSON object")
        return run_sync(graph().post(f"/sites/{site_id}/lists/{list_id}/items", json={"fields": fields}))
    return go()


@graph_tool("sharepoint", "PATCH", "/sites/{id}/lists/{listId}/items/{itemId}/fields", delegated=["Sites.ReadWrite.All"], application=["Sites.ReadWrite.All"])
def update_list_item(site_id: str, list_id: str, item_id: str, fields_json: str):
    """Update list item fields. fields_json: JSON object of {columnName: value}."""
    def go():
        require_write()
        import json as _json
        try:
            fields = _json.loads(fields_json)
        except Exception:
            return fail("fields_json must be a valid JSON object")
        return run_sync(graph().patch(f"/sites/{site_id}/lists/{list_id}/items/{item_id}/fields", json=fields))
    return go()


@graph_tool("sharepoint", "DELETE", "/sites/{id}/lists/{listId}/items/{itemId}", delegated=["Sites.ReadWrite.All"], application=["Sites.ReadWrite.All"])
def delete_list_item(site_id: str, list_id: str, item_id: str):
    def go():
        require_write()
        return run_sync(graph().delete(f"/sites/{site_id}/lists/{list_id}/items/{item_id}"))
    return go()


@graph_tool("sharepoint", "GET", "/sites/{id}/lists/{listId}/columns", delegated=["Sites.Read.All"], application=["Sites.Read.All"])
def list_columns(site_id: str, list_id: str):
    """List column schema of a SharePoint list."""
    def go():
        return run_sync(graph().get_all(f"/sites/{site_id}/lists/{list_id}/columns"))
    return go()


@graph_tool("sharepoint", "GET", "/sites/{id}/lists/{listId}/contentTypes", delegated=["Sites.Read.All"], application=["Sites.Read.All"])
def list_content_types(site_id: str, list_id: str):
    def go():
        return run_sync(graph().get_all(f"/sites/{site_id}/lists/{list_id}/contentTypes"))
    return go()


@graph_tool("sharepoint", "GET", "/sites/{id}/pages", delegated=["Sites.Read.All"], application=["Sites.Read.All"])
def list_site_pages(site_id: str):
    def go():
        return run_sync(graph().get_all(f"/sites/{site_id}/pages"))
    return go()
