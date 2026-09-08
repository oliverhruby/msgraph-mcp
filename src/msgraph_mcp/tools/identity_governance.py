"""Identity governance — access reviews, PIM, entitlement management. App-only / admin."""

from __future__ import annotations

from ._common import graph, graph_tool, run_sync, to_query


@graph_tool("identity_governance", "GET", "/identityGovernance/accessReviews/definitions", delegated=["AccessReview.Read.All"], application=["AccessReview.Read.All"])
def list_access_reviews(top: int = None, filter: str = None):
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        return run_sync(graph().get_all("/identityGovernance/accessReviews/definitions", params=params))
    return go()


@graph_tool("identity_governance", "GET", "/identityGovernance/accessReviews/definitions/{id}", delegated=["AccessReview.Read.All"], application=["AccessReview.Read.All"])
def get_access_review(review_id: str):
    def go():
        return run_sync(graph().get(f"/identityGovernance/accessReviews/definitions/{review_id}"))
    return go()


@graph_tool("identity_governance", "GET", "/identityGovernance/entitlementManagement/accessPackages", delegated=["EntitlementManagement.Read.All"], application=["EntitlementManagement.Read.All"])
def list_access_packages(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/identityGovernance/entitlementManagement/accessPackages", params=params))
    return go()


@graph_tool("identity_governance", "GET", "/roleManagement/directory/roleAssignments", delegated=["RoleManagement.Read.Directory"], application=["RoleManagement.Read.Directory"])
def list_directory_role_assignments(top: int = None, filter: str = None):
    """List Entra ID directory role assignments (PIM-adjacent)."""
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        return run_sync(graph().get_all("/roleManagement/directory/roleAssignments", params=params))
    return go()


@graph_tool("identity_governance", "GET", "/roleManagement/directory/roleDefinitions", delegated=["RoleManagement.Read.Directory"], application=["RoleManagement.Read.Directory"])
def list_directory_role_definitions(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/roleManagement/directory/roleDefinitions", params=params))
    return go()
