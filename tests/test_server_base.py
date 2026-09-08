"""Structural tests for the server bootstrap and the tool registry.

These assert the wiring-level invariants the whole server depends on: response
helpers produce MCP-shaped dicts, serialization handles every type the tools
emit, and the registry (the thing the coverage drift checker measures) is
internally consistent with what the MCP server actually exposes.
"""

from __future__ import annotations

import importlib
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from types import SimpleNamespace

import msgraph_mcp
import msgraph_mcp.tools._common as common
from msgraph_mcp import coverage

HTTP_VERBS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


class _Color(Enum):
    RED = "red"
    BLUE = "blue"


def test_helpers_produce_mcp_shaped_dicts():
    ok = msgraph_mcp.ok({"a": 1})
    fail = msgraph_mcp.fail("boom")
    ok_text = msgraph_mcp.ok_text("plain")

    assert ok["content"][0]["type"] == "text"
    assert fail["isError"] is True
    assert fail["content"][0]["text"] == "boom"
    assert ok_text["content"][0]["text"] == "plain"
    assert ok["content"][0]["text"].startswith("{")


def test_serialize_handles_all_emit_types():
    from msgraph_mcp import _serialize

    obj = {
        "dt": datetime(2026, 1, 2, 3, 4, 5),
        "d": date(2026, 1, 2),
        "dec": Decimal("1.50"),
        "enum": _Color.RED,
        "set": {1, 2},
        "ns": SimpleNamespace(x=1, y="v"),
        "list": [1, "two", None],
    }
    out = _serialize(obj)
    assert out["dt"] == "2026-01-02T03:04:05"
    assert out["d"] == "2026-01-02"
    assert out["dec"] == 1.5
    assert out["enum"] == "red"
    assert sorted(out["set"]) == [1, 2]
    assert out["ns"] == {"x": 1, "y": "v"}


def test_to_query_filters_none_and_stringifies():
    assert common.to_query(top=10, filter=None) == {"top": "10"}
    assert common.to_query() == {}


def test_to_query_keeps_boolean_and_zero():
    assert common.to_query(active=False, skip=0) == {"active": "False", "skip": "0"}


def test_select_and_expand_join_fields():
    assert common.select_fields("id", "subject", "body") == "id,subject,body"
    assert common.expand_refs("attachments", "singleValueExtendedProperties") == "attachments,singleValueExtendedProperties"


def test_require_write_respects_read_only_flag(monkeypatch):
    monkeypatch.setattr(common, "MSGRAPH_READ_ONLY", False)
    common.require_write()  # no-op

    monkeypatch.setattr(common, "MSGRAPH_READ_ONLY", True)
    try:
        common.require_write()
    except RuntimeError as e:
        assert "read-only" in str(e)
    else:
        raise AssertionError("require_write() should raise in read-only mode")


def test_registry_meets_minimum_tool_count():
    assert coverage.tool_count() >= 150


def test_registry_entries_are_well_formed():
    for name, meta in coverage.TOOL_REGISTRY.items():
        assert name and meta["module"], name
        assert meta["method"] in HTTP_VERBS, f"{name}: bad method {meta['method']}"
        assert meta["graph_endpoint"].startswith("/"), f"{name}: bad endpoint {meta['graph_endpoint']}"
        assert meta["workload"], name


def test_every_registered_tool_is_exposed_by_server():
    server_names = {t.name for t in msgraph_mcp.server._tool_manager.list_tools()}
    missing = [n for n in coverage.TOOL_REGISTRY if n not in server_names]
    assert not missing, f"registered but not exposed on server: {missing}"


def test_every_registered_tool_resolves_to_a_module_function():
    for name, meta in coverage.TOOL_REGISTRY.items():
        module = importlib.import_module(meta["module"])
        assert hasattr(module, name), f"{name} missing from {meta['module']}"
        assert callable(getattr(module, name))


def test_by_workload_matches_registry_size():
    grouped = coverage.by_workload()
    assert sum(len(v) for v in grouped.values()) == coverage.tool_count()


def test_workloads_match_tool_modules():
    """One workload per module: registry workloads = tool module filenames."""
    import pkgutil

    import msgraph_mcp.tools as tools_pkg

    modules = {
        m.name
        for m in pkgutil.iter_modules(tools_pkg.__path__)
        if not m.name.startswith("_")
    }
    grouped = coverage.by_workload()
    assert set(grouped) == modules
    for workload, tools in grouped.items():
        assert tools, workload


def test_read_only_guard_blocks_write_tools_via_tool_manager(read_only, dummy_args, call):
    """End-to-end check that MSGRAPH_READ_ONLY=true hard-blocks writes through the MCP layer."""
    import pytest
    from mcp.server.fastmcp.exceptions import ToolError

    for name in ("create_event", "send_mail", "create_todo_task", "upload_file", "create_group"):
        with pytest.raises(ToolError, match="read-only"):
            call(name, dummy_args(name))
