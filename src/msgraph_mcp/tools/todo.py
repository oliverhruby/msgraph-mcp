"""To Do (Microsoft To Do / tasks) — lists, tasks, checklist items."""

from __future__ import annotations

from ._common import fail, graph, graph_tool, require_write, run_sync, to_query


@graph_tool("todo", "GET", "/me/todo/lists", delegated=["Tasks.Read"])
def list_todo_lists(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/me/todo/lists", params=params))
    return go()


@graph_tool("todo", "GET", "/me/todo/lists/{listId}/tasks", delegated=["Tasks.Read"])
def list_todo_tasks(list_id: str, top: int = None, filter: str = None):
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        return run_sync(graph().get_all(f"/me/todo/lists/{list_id}/tasks", params=params))
    return go()


@graph_tool("todo", "GET", "/me/todo/lists/{listId}/tasks/{taskId}", delegated=["Tasks.Read"])
def get_todo_task(list_id: str, task_id: str):
    def go():
        return run_sync(graph().get(f"/me/todo/lists/{list_id}/tasks/{task_id}"))
    return go()


@graph_tool("todo", "POST", "/me/todo/lists", delegated=["Tasks.ReadWrite"])
def create_todo_list(display_name: str):
    def go():
        require_write()
        return run_sync(graph().post("/me/todo/lists", json={"displayName": display_name}))
    return go()


@graph_tool("todo", "POST", "/me/todo/lists/{listId}/tasks", delegated=["Tasks.ReadWrite"])
def create_todo_task(
    list_id: str,
    title: str,
    due_date: str = None,
    importance: str = None,
    reminder_datetime: str = None,
    is_reminder_on: bool = None,
    body_text: str = None,
):
    """Create a To Do task. due_date: YYYY-MM-DD. importance: 'low', 'normal', 'high'."""
    def go():
        require_write()
        body: dict = {"title": title}
        if due_date:
            body["dueDateTime"] = {"dateTime": f"{due_date}T00:00:00", "timeZone": "UTC"}
        if importance:
            body["importance"] = importance
        if reminder_datetime and is_reminder_on is not None:
            body["reminderDateTime"] = {"dateTime": reminder_datetime, "timeZone": "UTC"}
            body["isReminderOn"] = is_reminder_on
        if body_text:
            body["body"] = {"content": body_text, "contentType": "text"}
        return run_sync(graph().post(f"/me/todo/lists/{list_id}/tasks", json=body))
    return go()


@graph_tool("todo", "PATCH", "/me/todo/lists/{listId}/tasks/{taskId}", delegated=["Tasks.ReadWrite"])
def update_todo_task(
    list_id: str,
    task_id: str,
    title: str = None,
    due_date: str = None,
    status: str = None,
    importance: str = None,
):
    """Update a To Do task. status: 'notStarted', 'inProgress', 'completed', 'deferred'."""
    def go():
        require_write()
        body = {}
        if title is not None:
            body["title"] = title
        if due_date is not None:
            body["dueDateTime"] = {"dateTime": f"{due_date}T00:00:00", "timeZone": "UTC"}
        if status is not None:
            body["status"] = status
        if importance is not None:
            body["importance"] = importance
        if not body:
            return fail("No fields to update")
        return run_sync(graph().patch(f"/me/todo/lists/{list_id}/tasks/{task_id}", json=body))
    return go()


@graph_tool("todo", "DELETE", "/me/todo/lists/{listId}/tasks/{taskId}", delegated=["Tasks.ReadWrite"])
def delete_todo_task(list_id: str, task_id: str):
    def go():
        require_write()
        return run_sync(graph().delete(f"/me/todo/lists/{list_id}/tasks/{task_id}"))
    return go()


@graph_tool("todo", "PATCH", "/me/todo/lists/{listId}/tasks/{taskId}/checklistItems", delegated=["Tasks.ReadWrite"])
def add_checklist_item(list_id: str, task_id: str, display_name: str):
    def go():
        require_write()
        return run_sync(graph().post(
            f"/me/todo/lists/{list_id}/tasks/{task_id}/checklistItems",
            json={"displayName": display_name},
        ))
    return go()


@graph_tool("todo", "GET", "/me/todo/lists/{listId}/tasks/{taskId}/checklistItems", delegated=["Tasks.Read"])
def list_checklist_items(list_id: str, task_id: str):
    def go():
        return run_sync(graph().get_all(f"/me/todo/lists/{list_id}/tasks/{task_id}/checklistItems"))
    return go()
