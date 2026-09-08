"""Directory tools — organization, directory roles, admin units, org contacts."""

from __future__ import annotations

from ._common import graph, graph_tool, run_sync, to_query


@graph_tool("directory", "GET", "/organization", delegated=["Organization.Read.All"], application=["Organization.Read.All"])
def get_organization():
    def go():
        return run_sync(graph().get("/organization"))
    return go()


@graph_tool("directory", "GET", "/directoryRoles", delegated=["Directory.Read.All"], application=["Directory.Read.All"])
def list_directory_roles():
    def go():
        return run_sync(graph().get_all("/directoryRoles"))
    return go()


@graph_tool("directory", "GET", "/directoryRoles/{id}/members", delegated=["Directory.Read.All"], application=["Directory.Read.All"])
def list_directory_role_members(role_id: str):
    def go():
        return run_sync(graph().get_all(f"/directoryRoles/{role_id}/members"))
    return go()


@graph_tool("directory", "GET", "/directory/administrativeUnits", delegated=["AdministrativeUnit.Read.All"], application=["AdministrativeUnit.Read.All"])
def list_administrative_units(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/directory/administrativeUnits", params=params))
    return go()


@graph_tool("directory", "GET", "/directory/administrativeUnits/{id}", delegated=["AdministrativeUnit.Read.All"], application=["AdministrativeUnit.Read.All"])
def get_administrative_unit(unit_id: str):
    def go():
        return run_sync(graph().get(f"/directory/administrativeUnits/{unit_id}"))
    return go()


@graph_tool("directory", "GET", "/directory/administrativeUnits/{id}/members", delegated=["AdministrativeUnit.Read.All"], application=["AdministrativeUnit.Read.All"])
def list_administrative_unit_members(unit_id: str):
    def go():
        return run_sync(graph().get_all(f"/directory/administrativeUnits/{unit_id}/members"))
    return go()


@graph_tool("directory", "GET", "/contacts", delegated=["OrgContact.Read.All"], application=["OrgContact.Read.All"])
def list_org_contacts(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/contacts", params=params))
    return go()


@graph_tool("directory", "GET", "/contacts/{id}", delegated=["OrgContact.Read.All"], application=["OrgContact.Read.All"])
def get_org_contact(contact_id: str):
    def go():
        return run_sync(graph().get(f"/contacts/{contact_id}"))
    return go()


@graph_tool("directory", "POST", "/directoryObjects/getByIds", delegated=["Directory.Read.All"], application=["Directory.Read.All"])
def get_objects_by_ids(ids: str, types: str = None):
    """Resolve multiple object IDs in one call. ids: comma-separated GUIDs."""
    def go():
        id_list = [i.strip() for i in ids.split(",")]
        body: dict = {"ids": id_list}
        if types:
            body["types"] = [t.strip() for t in types.split(",")]
        return run_sync(graph().post("/directoryObjects/getByIds", json=body))
    return go()
