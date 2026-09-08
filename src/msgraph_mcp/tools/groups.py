"""Group management — CRUD, members, owners, transitive membership."""

from __future__ import annotations

from ._common import graph, graph_tool, require_write, run_sync, to_query


@graph_tool("groups", "GET", "/groups", delegated=["Group.Read.All"], application=["Group.Read.All"])
def list_groups(
    search: str = None,
    top: int = None,
    select: str = None,
    filter: str = None,
    order_by: str = None,
):
    def go():
        params = to_query(**{
            "$search": search,
            "$top": top,
            "$select": select,
            "$filter": filter,
            "$orderby": order_by,
        })
        return run_sync(graph().get_all("/groups", params=params))
    return go()


@graph_tool("groups", "GET", "/groups/{id}", delegated=["Group.Read.All"], application=["Group.Read.All"])
def get_group(group_id: str, select: str = None, expand: str = None):
    def go():
        params = to_query(**{"$select": select, "$expand": expand})
        return run_sync(graph().get(f"/groups/{group_id}", params=params))
    return go()


@graph_tool("groups", "GET", "/groups/{id}/members", delegated=["Group.Read.All"], application=["Group.Read.All"])
def list_group_members(group_id: str, top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all(f"/groups/{group_id}/members", params=params))
    return go()


@graph_tool("groups", "GET", "/groups/{id}/owners", delegated=["Group.Read.All"], application=["Group.Read.All"])
def list_group_owners(group_id: str):
    def go():
        return run_sync(graph().get_all(f"/groups/{group_id}/owners"))
    return go()


@graph_tool("groups", "GET", "/groups/{id}/transitiveMembers", delegated=["Group.Read.All"], application=["Group.Read.All"])
def list_transitive_members(group_id: str):
    def go():
        return run_sync(graph().get_all(f"/groups/{group_id}/transitiveMembers"))
    return go()


@graph_tool("groups", "POST", "/groups", delegated=["Group.ReadWrite.All"], application=["Group.Create"])
def create_group(display_name: str, mail_enabled: bool = False, security_enabled: bool = True, group_types: str = None):
    def go():
        require_write()
        body = {
            "displayName": display_name,
            "mailEnabled": mail_enabled,
            "securityEnabled": security_enabled,
        }
        if group_types:
            body["groupTypes"] = group_types.split(",")
        return run_sync(graph().post("/groups", json=body))
    return go()


@graph_tool("groups", "POST", "/groups/{id}/members/$ref", delegated=["Group.ReadWrite.All"], application=["Group.Member.ReadWrite.All"])
def add_member(group_id: str, user_id: str):
    def go():
        require_write()
        return run_sync(graph().post(
            f"/groups/{group_id}/members/$ref",
            json={"@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}"},
        ))
    return go()


@graph_tool("groups", "DELETE", "/groups/{id}/members/{id}/$ref", delegated=["Group.ReadWrite.All"], application=["Group.Member.ReadWrite.All"])
def remove_member(group_id: str, user_id: str):
    def go():
        require_write()
        return run_sync(graph().delete(f"/groups/{group_id}/members/{user_id}/$ref"))
    return go()


@graph_tool("groups", "DELETE", "/groups/{id}", delegated=["Group.ReadWrite.All"], application=["Group.ReadWrite.All"])
def delete_group(group_id: str):
    def go():
        require_write()
        return run_sync(graph().delete(f"/groups/{group_id}"))
    return go()
