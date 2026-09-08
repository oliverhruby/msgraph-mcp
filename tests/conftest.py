"""Shared fixtures for the msgraph-mcp test suite.

Unit tests drive every registered tool through the FastMCP tool manager with the
Graph client seam (`tools/_common._get_client`) patched to a deterministic fake,
so no network or Entra credentials are required. Integration tests (marker
``integration``) intentionally leave the seam untouched and hit a real tenant.
"""

from __future__ import annotations

import asyncio

import pytest
from _util import required_dummy_args

import msgraph_mcp
import msgraph_mcp.tools._common as common


class FakeClient:
    """Deterministic GraphClient stand-in with a call log.

    Responses are keyed by (method, path-prefix); anything unmatched falls back to
    a generic shape per HTTP method. ``set_response`` lets individual tests or the
    tool sweep provide richer fixtures for tools that index deeper into responses.
    """

    def __init__(self) -> None:
        self.calls: list[tuple] = []
        self.responses: dict[tuple[str, str], object] = {}
        self.defaults = {
            "GET": {"value": [{"id": "test-id", "displayName": "test"}], "id": "test-id"},
            "GET_ALL": [],
            "GET_DELTA": [],
            "POST": {"id": "new-id"},
            "PATCH": {"id": "new-id"},
            "PUT": {"id": "new-id"},
            "DELETE": {},
        }

    def set_response(self, method: str, path_prefix: str, value: object) -> None:
        self.responses[(method, path_prefix)] = value

    def _lookup(self, method: str, path: str):
        for (m, prefix), value in self.responses.items():
            if m == method and path.startswith(prefix):
                return value
        return None

    def _record(self, method, path, kw):
        self.calls.append((method, path, kw))

    async def _handle(self, method: str, path: str, kw: dict):
        self._record(method, path, kw)
        hit = self._lookup(method, path)
        if hit is not None:
            return hit
        if path == "/$batch":
            return {}  # batch returns {"responses": [...]}; see batch()
        return self.defaults.get(method, self.defaults["GET"])

    async def get(self, path, **kw):
        return await self._handle("GET", path, kw)

    async def post(self, path, **kw):
        return await self._handle("POST", path, kw)

    async def patch(self, path, **kw):
        return await self._handle("PATCH", path, kw)

    async def put(self, path, **kw):
        return await self._handle("PUT", path, kw)

    async def delete(self, path, **kw):
        return await self._handle("DELETE", path, kw)

    async def request(self, method, path, **kw):
        return await self._handle(method, path, kw)

    async def get_all(self, path, **kw):
        self._record("GET_ALL", path, kw)
        hit = self._lookup("GET_ALL", path)
        return hit if hit is not None else list(self.defaults["GET_ALL"])

    async def get_delta(self, path, **kw):
        self._record("GET_DELTA", path, kw)
        hit = self._lookup("GET_DELTA", path)
        return (hit if hit is not None else [], None)

    async def batch(self, requests):
        self._record("BATCH", "/$batch", {"count": len(requests)})
        return [
            {"id": r.get("id", str(i)), "status": "200", "body": {"id": "new-id"}}
            for i, r in enumerate(requests)
        ]


@pytest.fixture
def fake_client(monkeypatch):
    """Patch the client seam so every tool talks to a FakeClient."""
    fc = FakeClient()
    monkeypatch.setattr(common, "_get_client", lambda: fc)
    return fc


@pytest.fixture
def read_only(monkeypatch):
    """Force read-only mode for the duration of a test."""
    monkeypatch.setattr(common, "MSGRAPH_READ_ONLY", True)


@pytest.fixture
def call():
    """Invoke a registered tool through the FastMCP tool manager.

    Returns the raw tool dict (``convert_result=False``) so tests can assert on
    ``isError``/``content`` exactly as the tool produced them.
    """

    def _call(name: str, args: dict | None = None, **overrides):
        kwargs = (args or {}) | overrides
        return asyncio.run(
            msgraph_mcp.server._tool_manager.call_tool(name, kwargs, convert_result=False)
        )

    return _call


@pytest.fixture
def dummy_args():
    """Factory returning required-args dicts for a registered tool."""

    def _factory(name: str) -> dict:
        tool = msgraph_mcp.server._tool_manager.get_tool(name)
        if tool is None:
            raise AssertionError(f"tool not registered: {name}")
        return required_dummy_args(tool)

    return _factory
