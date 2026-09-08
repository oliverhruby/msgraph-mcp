"""Microsoft Graph MCP Server — 200+ tools across the full Microsoft Graph API."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from .auth import AuthManager
from .graph_client import GraphClient

logger = logging.getLogger("msgraph_mcp")

# ---------------------------------------------------------------------------
# Optional FastMCP import with fallback
# ---------------------------------------------------------------------------
try:
    from mcp.server.fastmcp import FastMCP
except Exception:
    FastMCP = None  # type: ignore[assignment,misc]

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "3000"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")
MCP_API_KEY = os.getenv("MCP_API_KEY", "")

MSGRAPH_LOG_LEVEL = os.getenv("MSGRAPH_LOG_LEVEL", "WARNING").upper()
MSGRAPH_TOOLSETS = os.getenv("MSGRAPH_TOOLSETS", "core")
MSGRAPH_READ_ONLY = os.getenv("MSGRAPH_READ_ONLY", "false").lower() in ("1", "true", "yes")

logging.basicConfig(
    level=getattr(logging, MSGRAPH_LOG_LEVEL, logging.WARNING),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    stream=sys.stderr,
)

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
_auth: AuthManager | None = None
_client: GraphClient | None = None


def _get_auth() -> AuthManager:
    global _auth
    if _auth is None:
        _auth = AuthManager()
    return _auth


def _get_client() -> GraphClient:
    global _client
    if _client is None:
        _client = GraphClient(_get_auth())
    return _client


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------
_server_kwargs: dict[str, Any] = {}
if MCP_TRANSPORT != "stdio":
    _server_kwargs["host"] = MCP_HOST
    _server_kwargs["port"] = MCP_PORT

server = FastMCP("msgraph", **_server_kwargs) if FastMCP is not None else None


# ---------------------------------------------------------------------------
# Tool registration helpers (same pattern as edupage-mcp)
# ---------------------------------------------------------------------------
def _tool(fn):
    if server is not None:
        return server.tool()(fn)
    return fn


def _run(fn, label: str = "msgraph call"):
    try:
        return fn()
    except Exception as e:
        logger.exception("Tool error: %s", label)
        return fail(f"{label} failed: {type(e).__name__}: {e}")


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------
def fail(message: str) -> dict:
    return {"isError": True, "content": [{"type": "text", "text": message}]}


def ok(data: Any) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(_serialize(data), indent=2, default=str)}]}


def ok_text(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


def _serialize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, set):
        return sorted(_serialize(v) for v in obj)
    if hasattr(obj, "__dict__"):
        return _serialize(vars(obj))
    if hasattr(obj, "model_dump"):
        return _serialize(obj.model_dump())
    return obj


def _params(**kwargs) -> dict:
    """Filter out None values from keyword arguments."""
    return {k: v for k, v in kwargs.items() if v is not None}


# ---------------------------------------------------------------------------
# Discover and register all tool modules
# ---------------------------------------------------------------------------
def _register_tools():
    import importlib
    import pkgutil

    from . import tools as tools_pkg

    for importer, modname, ispkg in pkgutil.iter_modules(tools_pkg.__path__):
        if modname.startswith("_"):
            continue
        try:
            importlib.import_module(f".tools.{modname}", package=__package__)
        except Exception:
            logger.exception("Failed to load tool module: %s", modname)


_register_tools()


# ---------------------------------------------------------------------------
# Startup helpers
# ---------------------------------------------------------------------------
def _autologin():
    """Attempt login from environment variables."""
    auth = _get_auth()
    try:
        auth.acquire_token_silent()
    except Exception:
        logger.info("No cached token; interactive auth will be triggered on first call.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    if FastMCP is None:
        print("Error: 'mcp' package is required. Install with: pip install 'mcp<2'", file=sys.stderr)
        sys.exit(1)

    _autologin()
    logger.info("Starting msgraph-mcp with %s transport", MCP_TRANSPORT)
    server.run(transport=MCP_TRANSPORT)  # type: ignore[union-attr]


if __name__ == "__main__":
    main()
