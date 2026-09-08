"""Files — OneDrive + SharePoint drives: items, upload, versions, permissions, sharing."""

from __future__ import annotations

import base64

from ._common import fail, graph, graph_tool, require_write, run_sync, to_query


@graph_tool("files", "GET", "/me/drive/recent", delegated=["Files.Read"])
def list_recent_files(top: int = 20):
    def go():
        return run_sync(graph().get("/me/drive/recent"))
    return go()


@graph_tool("files", "GET", "/me/drive/sharedWithMe", delegated=["Files.Read"])
def list_shared_with_me(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get("/me/drive/sharedWithMe", params=params))
    return go()


@graph_tool("files", "GET", "/me/drive/root/children", delegated=["Files.Read"])
def list_root_files(top: int = None, select: str = None, order_by: str = None):
    def go():
        params = to_query(**{"$top": top, "$select": select, "$orderby": order_by})
        return run_sync(graph().get_all("/me/drive/root/children", params=params))
    return go()


@graph_tool("files", "GET", "/me/drive/items/{id}", delegated=["Files.Read"])
def get_file(file_id: str, select: str = None):
    def go():
        params = to_query(**{"$select": select})
        return run_sync(graph().get(f"/me/drive/items/{file_id}", params=params))
    return go()


@graph_tool("files", "GET", "/me/drive/items/{id}/content", delegated=["Files.Read"])
def get_file_content(file_id: str):
    """Get file content (returns base64-encoded)."""
    def go():
        return run_sync(graph().get(f"/me/drive/items/{file_id}/content"))
    return go()


@graph_tool("files", "GET", "/me/drive/items/{id}/children", delegated=["Files.Read"])
def list_folder_children(file_id: str, top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all(f"/me/drive/items/{file_id}/children", params=params))
    return go()


@graph_tool("files", "GET", "/me/drive/items/{id}/versions", delegated=["Files.ReadWrite"])
def list_file_versions(file_id: str):
    def go():
        return run_sync(graph().get_all(f"/me/drive/items/{file_id}/versions"))
    return go()


@graph_tool("files", "GET", "/me/drive/items/{id}/permissions", delegated=["Files.ReadWrite"])
def list_permissions(file_id: str):
    def go():
        return run_sync(graph().get_all(f"/me/drive/items/{file_id}/permissions"))
    return go()


@graph_tool("files", "GET", "/me/drive/search(q='{query}')", delegated=["Files.Read.All"])
def search_files(query: str, top: int = None):
    def go():
        params = to_query(**{"$top": top})
        path = f"/me/drive/search(q='{query}')"
        return run_sync(graph().get_all(path, params=params))
    return go()


@graph_tool("files", "POST", "/me/drive/items/{id}/children", delegated=["Files.ReadWrite"])
def create_folder(parent_id: str, name: str):
    def go():
        require_write()
        body = {"name": name, "folder": {}, "@microsoft.graph.conflictBehavior": "rename"}
        return run_sync(graph().post(f"/me/drive/items/{parent_id}/children", json=body))
    return go()


@graph_tool("files", "PUT", "/me/drive/items/{id}/content", delegated=["Files.ReadWrite"])
def upload_file(parent_id: str, name: str, content_base64: str, content_type: str = "text/plain"):
    """Upload a file. content_base64: base64-encoded file content."""
    def go():
        require_write()
        raw = base64.b64decode(content_base64)
        # For small files, use simple upload
        import httpx

        from ..auth import AuthManager
        auth = AuthManager()
        token = auth.acquire_token()
        url = f"{auth.base_url}/v1.0/me/drive/items/{parent_id}:/{name}:/content"
        resp = httpx.put(url, content=raw, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
        })
        if resp.status_code in (200, 201):
            return resp.json()
        return fail(f"Upload failed: {resp.status_code} {resp.text}")
    return go()


@graph_tool("files", "POST", "/me/drive/items/{id}/createUploadSession", delegated=["Files.ReadWrite"])
def create_upload_session(parent_id: str, name: str, file_size: int):
    """Create an upload session for large files (>4MB). Returns upload URL."""
    def go():
        require_write()
        body = {
            "item": {"@microsoft.graph.conflictBehavior": "rename", "name": name},
            "fileSize": file_size,
        }
        return run_sync(graph().post(f"/me/drive/items/{parent_id}:/createUploadSession", json=body))
    return go()


@graph_tool("files", "PATCH", "/me/drive/items/{id}", delegated=["Files.ReadWrite"])
def update_file(file_id: str, name: str = None, description: str = None):
    def go():
        require_write()
        body = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if not body:
            return fail("No fields to update")
        return run_sync(graph().patch(f"/me/drive/items/{file_id}", json=body))
    return go()


@graph_tool("files", "DELETE", "/me/drive/items/{id}", delegated=["Files.ReadWrite"])
def delete_file(file_id: str):
    def go():
        require_write()
        return run_sync(graph().delete(f"/me/drive/items/{file_id}"))
    return go()


@graph_tool("files", "POST", "/me/drive/items/{id}/copy", delegated=["Files.ReadWrite"])
def copy_file(file_id: str, name: str, parent_id: str = None):
    def go():
        require_write()
        body: dict = {"name": name}
        if parent_id:
            body["parentReference"] = {"id": parent_id}
        return run_sync(graph().post(f"/me/drive/items/{file_id}/copy", json=body))
    return go()


@graph_tool("files", "POST", "/me/drive/items/{id}/move", delegated=["Files.ReadWrite"])
def move_file(file_id: str, parent_id: str):
    def go():
        require_write()
        return run_sync(graph().patch(f"/me/drive/items/{file_id}", json={"parentReference": {"id": parent_id}}))
    return go()


@graph_tool("files", "POST", "/me/drive/items/{id}/createLink", delegated=["Files.ReadWrite"])
def create_sharing_link(file_id: str, link_type: str = "view", scope: str = "organization"):
    """Create a sharing link. link_type: 'view', 'edit', 'embed'. scope: 'anonymous', 'organization', 'users'."""
    def go():
        require_write()
        body = {
            "type": link_type,
            "scope": scope,
        }
        return run_sync(graph().post(f"/me/drive/items/{file_id}/createLink", json=body))
    return go()


@graph_tool("files", "DELETE", "/me/drive/items/{id}/permissions/{permId}", delegated=["Files.ReadWrite.All"])
def revoke_sharing_link(file_id: str, permission_id: str):
    def go():
        require_write()
        return run_sync(graph().delete(f"/me/drive/items/{file_id}/permissions/{permission_id}"))
    return go()


@graph_tool("files", "GET", "/groups/{groupId}/drive/root/children", delegated=["Files.Read.All"])
def list_group_drive_files(group_id: str, top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all(f"/groups/{group_id}/drive/root/children", params=params))
    return go()
