"""Coverage registry — exposes all registered tool metadata.

Consumed by scripts/check_graph_api_coverage.py to verify that the
registered tool surface matches the official Microsoft Graph OpenAPI spec.
"""

from __future__ import annotations

from .tools import get_registry

# Re-export the registry populated by tool modules at import time.
TOOL_REGISTRY = get_registry()


def tool_count() -> int:
    return len(TOOL_REGISTRY)


def by_workload() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for name, meta in TOOL_REGISTRY.items():
        workload = meta["workload"]
        grouped.setdefault(workload, []).append(name)
    return grouped
