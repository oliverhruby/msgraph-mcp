"""Shared helpers for all tool modules."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from .. import (
    MSGRAPH_READ_ONLY,
    _get_client,
    _run,
    _serialize,
    _tool,
    fail,
    ok,
    ok_text,
)

# Names re-exported for tool modules. Explicit __all__ keeps ruff from flagging
# them as unused imports (F401) — they are a public convenience API for tools.
__all__ = [
    "MSGRAPH_READ_ONLY",
    "_get_client",
    "_run",
    "_serialize",
    "_tool",
    "fail",
    "graph",
    "graph_call",
    "graph_tool",
    "ok",
    "ok_text",
    "require_write",
    "run_sync",
    "select_fields",
    "expand_refs",
    "to_query",
]


def graph() -> Any:
    return _get_client()


def require_write():
    if MSGRAPH_READ_ONLY:
        raise RuntimeError("Server is in read-only mode (MSGRAPH_READ_ONLY=true)")


def run_sync(coro):
    """Run an async coroutine from a sync tool function."""
    loop = None
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            timeout = int(os.getenv("MSGRAPH_HTTP_TIMEOUT", "60"))
            return future.result(timeout=timeout)
    else:
        return asyncio.run(coro)


def to_query(**kwargs) -> dict:
    """Filter None values for Graph query params."""
    return {k: str(v) for k, v in kwargs.items() if v is not None}


def select_fields(*fields: str) -> str:
    return ",".join(fields)


def expand_refs(*refs: str) -> str:
    return ",".join(refs)


def graph_tool(workload: str, method: str, endpoint: str, *, delegated: list[str] | None = None, application: list[str] | None = None):
    """Decorator that registers tool metadata AND applies @_tool."""
    def decorator(fn):
        from . import register_tool_info
        register_tool_info(
            fn.__name__,
            module=fn.__module__,
            method=method,
            graph_endpoint=endpoint,
            required_scopes_delegated=delegated,
            required_scopes_application=application,
            workload=workload,
        )
        return _tool(fn)
    return decorator


def graph_call(fn, *args, **kwargs):
    """Execute an async Graph call from sync context."""
    return run_sync(fn(*args, **kwargs))
