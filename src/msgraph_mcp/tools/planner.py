"""Planner — plans, buckets, tasks, task details, assignments."""

from __future__ import annotations

from ._common import fail, graph, graph_tool, require_write, run_sync


@graph_tool("planner", "GET", "/me/planner/plans", delegated=["Group.Read.All", "Tasks.Read"])
def list_my_planner_plans():
    def go():
        return run_sync(graph().get_all("/me/planner/plans"))
    return go()


@graph_tool("planner", "GET", "/groups/{group_id}/planner/plans", delegated=["Group.Read.All", "Tasks.Read"])
def list_group_plans(group_id: str):
    def go():
        return run_sync(graph().get_all(f"/groups/{group_id}/planner/plans"))
    return go()


@graph_tool("planner", "GET", "/groups/{group_id}/planner/plans/{planId}/buckets", delegated=["Tasks.Read"])
def list_buckets(group_id: str, plan_id: str):
    def go():
        return run_sync(graph().get_all(f"/groups/{group_id}/planner/plans/{plan_id}/buckets"))
    return go()


@graph_tool("planner", "GET", "/groups/{group_id}/planner/plans/{planId}/tasks", delegated=["Tasks.Read"])
def list_planner_tasks(group_id: str, plan_id: str):
    def go():
        return run_sync(graph().get_all(f"/groups/{group_id}/planner/plans/{plan_id}/tasks"))
    return go()


@graph_tool("planner", "GET", "/me/planner/tasks", delegated=["Tasks.Read"])
def list_my_tasks():
    def go():
        return run_sync(graph().get_all("/me/planner/tasks"))
    return go()


@graph_tool("planner", "GET", "/planner/tasks/{id}/details", delegated=["Tasks.Read"])
def get_task_details(task_id: str):
    def go():
        return run_sync(graph().get(f"/planner/tasks/{task_id}/details"))
    return go()


@graph_tool("planner", "POST", "/planner/tasks", delegated=["Tasks.ReadWrite"])
def create_planner_task(
    plan_id: str,
    bucket_id: str,
    title: str,
    due_datetime: str = None,
    percent_complete: int = None,
    assignments: str = None,
):
    """Create a planner task. assignments: comma-separated user IDs to assign."""
    def go():
        require_write()
        body: dict = {
            "planId": plan_id,
            "bucketId": bucket_id,
            "title": title,
        }
        if due_datetime:
            body["dueDateTime"] = due_datetime
        if percent_complete is not None:
            body["percentComplete"] = percent_complete
        if assignments:
            body["assignments"] = {u.strip(): {"@odata.type": "#microsoft.graph.plannerAssignment", "orderHint": " !"} for u in assignments.split(",")}
        result = run_sync(graph().post("/planner/tasks", json=body))
        return result
    return go()


@graph_tool("planner", "PATCH", "/planner/tasks/{id}", delegated=["Tasks.ReadWrite"])
def update_planner_task(
    task_id: str,
    title: str = None,
    percent_complete: int = None,
    due_datetime: str = None,
    if_match: str = None,
):
    """Update a planner task. Requires If-Match header (use etag from the task)."""
    def go():
        require_write()
        body = {}
        if title is not None:
            body["title"] = title
        if percent_complete is not None:
            body["percentComplete"] = percent_complete
        if due_datetime is not None:
            body["dueDateTime"] = due_datetime
        if not body:
            return fail("No fields to update")
        headers = {}
        if if_match:
            headers["If-Match"] = if_match
        return run_sync(graph().patch(f"/planner/tasks/{task_id}", json=body, headers=headers))
    return go()


@graph_tool("planner", "POST", "/planner/plans", delegated=["Group.ReadWrite.All", "Tasks.ReadWrite"])
def create_planner_plan(group_id: str, title: str):
    def go():
        require_write()
        return run_sync(graph().post("/planner/plans", json={
            "owner": f"https://graph.microsoft.com/v1.0/groups/{group_id}",
            "title": title,
        }))
    return go()


@graph_tool("planner", "POST", "/planner/buckets", delegated=["Tasks.ReadWrite"])
def create_planner_bucket(plan_id: str, name: str):
    def go():
        require_write()
        return run_sync(graph().post("/planner/buckets", json={
            "planId": plan_id,
            "name": name,
        }))
    return go()


@graph_tool("planner", "DELETE", "/planner/tasks/{id}", delegated=["Tasks.ReadWrite"])
def delete_planner_task(task_id: str, if_match: str = None):
    def go():
        require_write()
        headers = {}
        if if_match:
            headers["If-Match"] = if_match
        return run_sync(graph().delete(f"/planner/tasks/{task_id}", headers=headers))
    return go()
