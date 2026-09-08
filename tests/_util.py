"""Pure helpers shared by conftest fixtures and test modules."""

from __future__ import annotations

import json


def all_registered_names() -> list[str]:
    from msgraph_mcp import coverage

    return sorted(coverage.TOOL_REGISTRY.keys())


def is_write_tool(name: str) -> bool:
    from msgraph_mcp import coverage

    return coverage.TOOL_REGISTRY[name]["method"] in {"POST", "PUT", "PATCH", "DELETE"}


def json_content(result: dict) -> object:
    """Extract the text payload from an MCP tool result dict."""
    blocks = result.get("content", [])
    texts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
    return json.loads("".join(texts)) if texts else None


def dummy_value(schema: dict, defs: dict | None = None, *, param_name: str = "") -> object:
    """Build a syntactically-valid dummy value for a JSON-schema property."""
    defs = defs or {}
    if "$ref" in schema:
        inner = defs.get(schema["$ref"].split("/")[-1], {})
        return dummy_value(inner, defs, param_name=param_name)
    if "anyOf" in schema:
        for sub in schema["anyOf"]:
            v = dummy_value(sub, defs, param_name=param_name)
            if v is not None:
                return v
        return None
    if "oneOf" in schema:
        for sub in schema["oneOf"]:
            v = dummy_value(sub, defs, param_name=param_name)
            if v is not None:
                return v
        return None
    if schema.get("const") is not None:
        return schema["const"]
    if schema.get("enum"):
        return schema["enum"][0]

    name = param_name.lower()
    if "datetime" in name or name in ("start", "end", "due_date", "reminder_datetime"):
        return "2026-01-01T10:00:00Z"
    if "date" in name:
        return "2026-01-01"
    if "time" in name:
        return "10:00:00"
    if name in ("message_id", "event_id", "user_id", "list_id", "task_id", "group_id"):
        return "id-1"
    if name == "top":
        return 10

    t = schema.get("type")
    if t == "string":
        if "recipient" in name or "email" in name:
            return "claude@contoso.com"
        if "base64" in name:
            return "dGVzdA=="
        if "json" in name.lower():
            return '[{"id": "1", "method": "GET", "url": "/me"}]'
        return "test"
    if t in ("integer", "number"):
        return 1
    if t == "boolean":
        return False
    if t == "array":
        item = schema.get("items", {})
        v = dummy_value(item, defs, param_name=param_name) if item else None
        return [v] if v is not None else []
    if t == "object":
        return {}
    if t == "null":
        return None
    return None


def required_dummy_args(tool) -> dict:
    """Build minimal args satisfying the tool's required input fields.

    ``tool.parameters`` may be a pydantic model (FastMCP input schema) or a plain
    JSON-schema dict — handle both.
    """
    p = tool.parameters
    schema = p.model_json_schema() if hasattr(p, "model_json_schema") else p
    defs = schema.get("$defs", {})
    props = schema.get("properties", {})
    return {
        key: dummy_value(props.get(key, {}), defs, param_name=key)
        for key in schema.get("required", [])
    }
