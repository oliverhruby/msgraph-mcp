"""Sweep tests that exercise every registered tool through the MCP tool manager.

Each tool is invoked with only its required arguments against the FakeClient
seam, so these run fully offline. Failures are aggregated so one pass surfaces
every misbehaving tool at once (deep response indexing, missing guards, etc.).
"""

from __future__ import annotations

from _util import all_registered_names, dummy_value, is_write_tool
from mcp.server.fastmcp.exceptions import ToolError

import msgraph_mcp

# Post-like Graph "action" endpoints that are pure reads (no mutation), so they
# intentionally do NOT call require_write() and must not be expected to block in
# read-only mode.
NONMUTATING_POST_ACTIONS = {
    "batch_request",           # POST /$batch (caller controls the requests)
    "find_meeting_times",      # POST /me/findMeetingTimes
    "get_objects_by_ids",      # POST /directoryObjects/getByIds
    "get_presences_by_user_id",  # POST /communications/getPresencesByUserId
    "get_schedule",            # POST /users/{id}/schedule
    "search_external",         # POST /search/query
    "search_query",            # POST /search/query
}

# Tools whose required-arg dummies need realistic values to pass validation.
ARG_OVERRIDES: dict[str, dict] = {
    "create_subscription": {"resource": "me/messages"},
    "delta_query": {"resource": "me/messages"},
}


def _schema(name: str) -> dict:
    tool = msgraph_mcp.server._tool_manager.get_tool(name)
    p = tool.parameters
    return p.model_json_schema() if hasattr(p, "model_json_schema") else p


def _error_text(result) -> str:
    if not isinstance(result, dict):
        return ""
    return " ".join(
        str(b.get("text", "")) for b in result.get("content", []) if isinstance(b, dict)
    )


def _invoke(call, dummy_args, fake_client, name: str):
    """Call a tool with dummy args, retrying once when the tool reports it has
    no fields to act on (all-optional update tools)."""
    args = dict(dummy_args(name))
    args.update(ARG_OVERRIDES.get(name, {}))
    result = call(name, args)
    if _error_text(result) == "No fields to update":
        schema = _schema(name)
        optional = [
            key
            for key in schema.get("properties", {})
            if key not in schema.get("required", [])
        ]
        if optional:
            props = schema["properties"]
            defs = schema.get("$defs", {})
            args[optional[0]] = dummy_value(props[optional[0]], defs, param_name=optional[0])
            result = call(name, args)
    return result


def test_every_tool_responds_without_error(fake_client, dummy_args, call):
    failures = []
    no_graph_calls = []
    for name in all_registered_names():
        try:
            result = _invoke(call, dummy_args, fake_client, name)
        except Exception as e:  # noqa: BLE001
            failures.append(f"{name}: raised {type(e).__name__}: {e}")
            continue
        if isinstance(result, dict) and result.get("isError"):
            failures.append(f"{name}: isError: {_error_text(result)}")
        if not fake_client.calls:
            no_graph_calls.append(name)
        fake_client.calls.clear()

    assert not failures, "\n".join(failures)
    assert not no_graph_calls, f"tools never touched the Graph client: {no_graph_calls}"


def test_write_tools_are_guarded_in_read_only_mode(fake_client, read_only, dummy_args, call):
    unguarded = []
    for name in all_registered_names():
        if not is_write_tool(name) or name in NONMUTATING_POST_ACTIONS:
            continue
        blocked = False
        try:
            result = _invoke(call, dummy_args, fake_client, name)
        except (ToolError, RuntimeError) as e:
            blocked = "read-only" in str(e)
        else:
            if isinstance(result, dict) and result.get("isError") and "read-only" in _error_text(result):
                blocked = True
        if not blocked:
            unguarded.append(name)
        fake_client.calls.clear()
    assert not unguarded, (
        "write tools not blocked by MSGRAPH_READ_ONLY=true: "
        + ", ".join(unguarded)
    )


def test_write_tools_succeed_when_writes_enabled(fake_client, dummy_args, call):
    """Outside read-only mode, every write tool should pass require_write()."""
    failures = []
    for name in all_registered_names():
        if not is_write_tool(name):
            continue
        result = _invoke(call, dummy_args, fake_client, name)
        if isinstance(result, dict) and result.get("isError"):
            failures.append(f"{name}: {_error_text(result)}")
        fake_client.calls.clear()
    assert not failures, "\n".join(failures)


def test_get_message_hits_expected_endpoint(fake_client, call):
    result = call("get_message", {"message_id": "msg-1"})
    assert not isinstance(result, dict) or not result.get("isError"), result
    calls = [c for c in fake_client.calls if c[0] == "GET"]
    assert any("/me/messages/msg-1" in c[1] for c in calls), calls
    fake_client.calls.clear()


def test_get_my_profile_records_a_get(fake_client, call):
    result = call("get_my_profile")
    assert not isinstance(result, dict) or not result.get("isError"), result
    assert any(c[0] == "GET" and "/me" in c[1] for c in fake_client.calls), fake_client.calls
    fake_client.calls.clear()
