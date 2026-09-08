"""OneNote — notebooks, sections, section groups, pages (CRUD + copy)."""

from __future__ import annotations

from ._common import graph, graph_tool, require_write, run_sync, to_query


@graph_tool("onenote", "GET", "/me/onenote/notebooks", delegated=["Notes.Read"])
def list_notebooks(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/me/onenote/notebooks", params=params))
    return go()


@graph_tool("onenote", "GET", "/me/onenote/sections", delegated=["Notes.Read"])
def list_sections(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/me/onenote/sections", params=params))
    return go()


@graph_tool("onenote", "GET", "/me/onenote/notebooks/{notebookId}/sections", delegated=["Notes.Read"])
def list_notebook_sections(notebook_id: str):
    def go():
        return run_sync(graph().get_all(f"/me/onenote/notebooks/{notebook_id}/sections"))
    return go()


@graph_tool("onenote", "GET", "/me/onenote/sections/{sectionId}/pages", delegated=["Notes.Read"])
def list_section_pages(section_id: str, top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all(f"/me/onenote/sections/{section_id}/pages", params=params))
    return go()


@graph_tool("onenote", "GET", "/me/onenote/sectionGroups", delegated=["Notes.Read"])
def list_section_groups():
    def go():
        return run_sync(graph().get_all("/me/onenote/sectionGroups"))
    return go()


@graph_tool("onenote", "GET", "/me/onenote/pages/{id}/content", delegated=["Notes.Read"])
def get_page_content(page_id: str):
    """Get OneNote page content as HTML."""
    def go():
        return run_sync(graph().get(f"/me/onenote/pages/{page_id}/content"))
    return go()


@graph_tool("onenote", "GET", "/me/onenote/pages/{id}", delegated=["Notes.Read"])
def get_page(page_id: str):
    def go():
        return run_sync(graph().get(f"/me/onenote/pages/{page_id}"))
    return go()


@graph_tool("onenote", "POST", "/me/onenote/sections/{sectionId}/pages", delegated=["Notes.Create"])
def create_page(section_id: str, html_content: str, title: str = None):
    """Create a OneNote page. html_content: HTML body content."""
    def go():
        require_write()
        content = html_content
        if title:
            content = f"<h1>{title}</h1>{content}"
        headers = {"Content-Type": "text/html"}
        return run_sync(graph().post(
            f"/me/onenote/sections/{section_id}/pages",
            data=content,  # type: ignore
            headers=headers,
        ))
    return go()


@graph_tool("onenote", "PATCH", "/me/onenote/pages/{id}/content", delegated=["Notes.ReadWrite"])
def update_page_content(page_id: str, html_content: str):
    def go():
        require_write()
        headers = {"Content-Type": "text/html"}
        return run_sync(graph().patch(
            f"/me/onenote/pages/{page_id}/content",
            data=html_content,  # type: ignore
            headers=headers,
        ))
    return go()


@graph_tool("onenote", "DELETE", "/me/onenote/pages/{id}", delegated=["Notes.ReadWrite"])
def delete_page(page_id: str):
    def go():
        require_write()
        return run_sync(graph().delete(f"/me/onenote/pages/{page_id}"))
    return go()


@graph_tool("onenote", "POST", "/me/onenote/sections/{sectionId}/copyToNotebook", delegated=["Notes.ReadWrite"])
def copy_section_to_notebook(section_id: str, notebook_id: str, site_collection_id: str = None, site_id: str = None):
    """Copy a section to a notebook."""
    def go():
        require_write()
        body: dict = {"id": notebook_id}
        if site_collection_id and site_id:
            body["siteCollectionId"] = site_collection_id
            body["siteId"] = site_id
        return run_sync(graph().post(f"/me/onenote/sections/{section_id}/copyToNotebook", json=body))
    return go()
