"""User management tools — profiles, photos, direct reports, licenses."""

from __future__ import annotations

from ._common import fail, graph, graph_tool, run_sync, to_query


@graph_tool("users", "GET", "/me", delegated=["User.Read"])
def get_my_profile():
    def go():
        return run_sync(graph().get("/me"))
    return go()


@graph_tool("users", "GET", "/users/{id}", delegated=["User.Read.All"], application=["User.Read.All"])
def get_user(user_id: str):
    def go():
        return run_sync(graph().get(f"/users/{user_id}"))
    return go()


@graph_tool("users", "GET", "/users", delegated=["User.ReadBasic.All"], application=["User.Read.All"])
def list_users(
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
        return run_sync(graph().get_all("/users", params=params))
    return go()


@graph_tool("users", "GET", "/users/{id}/photo/$value", delegated=["User.Read.All"], application=["User.Read.All"])
def get_user_photo(user_id: str):
    """Get user profile photo (returns metadata, not bytes)."""
    def go():
        return run_sync(graph().get(f"/users/{user_id}/photo"))
    return go()


@graph_tool("users", "GET", "/users/{id}/directReports", delegated=["User.Read.All"], application=["User.Read.All"])
def get_direct_reports(user_id: str):
    def go():
        return run_sync(graph().get(f"/users/{user_id}/directReports"))
    return go()


@graph_tool("users", "GET", "/users/{id}/manager", delegated=["User.Read.All"], application=["User.Read.All"])
def get_user_manager(user_id: str):
    def go():
        return run_sync(graph().get(f"/users/{user_id}/manager"))
    return go()


@graph_tool("users", "GET", "/users/{id}/transitiveMemberOf", delegated=["User.Read.All"], application=["User.Read.All"])
def get_transitive_member_of(user_id: str):
    def go():
        return run_sync(graph().get_all(f"/users/{user_id}/transitiveMemberOf"))
    return go()


@graph_tool("users", "GET", "/users/{id}/licenseDetails", delegated=["User.Read.All"], application=["User.Read.All"])
def get_user_licenses(user_id: str):
    def go():
        return run_sync(graph().get_all(f"/users/{user_id}/licenseDetails"))
    return go()


@graph_tool("users", "GET", "/users/{id}/checkMemberGroups", delegated=["User.Read.All"], application=["User.Read.All"])
def check_member_groups(user_id: str, group_ids: str):
    """Check if user belongs to groups. group_ids: comma-separated GUIDs."""
    def go():
        ids = [g.strip() for g in group_ids.split(",")]
        return run_sync(graph().post(f"/users/{user_id}/checkMemberGroups", json={"groupIds": ids}))
    return go()


@graph_tool("users", "PATCH", "/users/{id}", delegated=["User.ReadWrite.All"], application=["User.ReadWrite.All"])
def update_user(user_id: str, display_name: str = None, mail: str = None, about_me: str = None):
    def go():
        from ..tools._common import require_write
        require_write()
        body = {}
        if display_name is not None:
            body["displayName"] = display_name
        if mail is not None:
            body["mail"] = mail
        if about_me is not None:
            body["aboutMe"] = about_me
        if not body:
            return fail("No fields to update")
        return run_sync(graph().patch(f"/users/{user_id}", json=body))
    return go()


@graph_tool("users", "GET", "/me/manager", delegated=["User.Read"])
def get_my_manager():
    def go():
        return run_sync(graph().get("/me/manager"))
    return go()


@graph_tool("users", "GET", "/me/memberOf", delegated=["User.Read.All"])
def get_my_groups():
    def go():
        return run_sync(graph().get_all("/me/memberOf"))
    return go()
