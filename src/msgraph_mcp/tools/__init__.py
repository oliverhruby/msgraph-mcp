"""Tool modules auto-discovery and registration."""

from __future__ import annotations

import importlib
import logging
import pkgutil

logger = logging.getLogger("msgraph_mcp.tools")

# Populated by __init_subclass__ or explicit registration
_registry: dict[str, dict] = {}


def register_tool_info(
    name: str,
    *,
    module: str,
    method: str,
    graph_endpoint: str,
    required_scopes_delegated: list[str] | None = None,
    required_scopes_application: list[str] | None = None,
    workload: str,
):
    """Register tool metadata for coverage checking."""
    _registry[name] = {
        "module": module,
        "method": method,
        "graph_endpoint": graph_endpoint,
        "required_scopes_delegated": required_scopes_delegated or [],
        "required_scopes_application": required_scopes_application or [],
        "workload": workload,
    }


def get_registry() -> dict:
    return dict(_registry)


def _discover():
    """Import all tool modules to trigger their @_tool decorators."""
    for _importer, modname, _ispkg in pkgutil.iter_modules(__path__):
        if modname.startswith("_"):
            continue
        full = f".tools.{modname}"
        try:
            importlib.import_module(full, package="msgraph_mcp")
        except Exception:
            logger.exception("Failed to load tool module: %s", modname)


# Run discovery on import
_discover()
