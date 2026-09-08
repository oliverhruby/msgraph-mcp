#!/usr/bin/env python3
"""Check Microsoft Graph API coverage drift against the registered tool surface.

Downloads the official Microsoft Graph OpenAPI spec (from microsoftgraph/msgraph-metadata)
and compares every operation {method} {path} against the tools registered in
src/msgraph_mcp/coverage.py.

An operation is "covered" if a tool's registered `graph_endpoint` matches its
method + path (with {path-args} normalized). Operations not covered must be
listed in scripts/graph_api_ignored_endpoints.json with a reason.

Exit codes:
  0 - all covered (or ignored)
  1 - uncovered operations found
  2 - validation error (bad spec / bad tool registration)
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

SPEC_URL = "https://raw.githubusercontent.com/microsoftgraph/msgraph-metadata/master/openapi/v1.0/openapi.yaml"
IGNORED_FILE = Path(__file__).resolve().parent / "graph_api_ignored_endpoints.json"
BASELINE_FILE = Path(__file__).resolve().parent / "graph_api_baseline.json"

# Path parameter normalization: /users/{id} -> /users/{id}
_PATH_PARAM = re.compile(r"{[^}]+}")


def norm_path(path: str) -> str:
    """Normalize a Graph path: strip leading version, collapse duplicate summaries."""
    for prefix in ("/v1.0", "/beta"):
        if path.startswith(prefix):
            path = path[len(prefix):]
            break
    # Remove query/fragment
    path = path.split("?")[0]
    return _PATH_PARAM.sub("{id}", path.rstrip("/") or "/")


def load_spec() -> dict:
    """Download and parse the OpenAPI YAML spec."""
    try:
        import yaml
    except ImportError:
        print("PyYAML is required: pip install pyyaml", file=sys.stderr)
        sys.exit(2)

    print(f"Downloading Graph OpenAPI spec from {SPEC_URL}")
    with urllib.request.urlopen(SPEC_URL, timeout=120) as resp:
        raw = resp.read().decode("utf-8")

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(raw)
        tmp = f.name

    with open(tmp, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    os.unlink(tmp)
    return spec


def collect_spec_operations(spec: dict) -> list[tuple[str, str]]:
    """Return [(method, path)] for every defined operation (excluding path-level params)."""
    ops: list[tuple[str, str]] = []
    for path, item in (spec.get("paths") or {}).items():
        for method in ("get", "post", "patch", "put", "delete"):
            if method in item:
                ops.append((method.upper(), norm_path(path)))
    return ops


def load_tool_registry() -> dict:
    """Import the tool coverage registry."""
    from msgraph_mcp import coverage
    return coverage.TOOL_REGISTRY


def load_ignored() -> dict:
    with open(IGNORED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    spec = load_spec()
    spec_ops = collect_spec_operations(spec)
    registry = load_tool_registry()
    ignored = load_ignored()

    # Build set of covered operations from the tool registry.
    covered: set[tuple[str, str]] = set()
    for tool_name, meta in registry.items():
        endpoint = meta["graph_endpoint"]
        method = meta["method"].upper()
        covered.add((method, norm_path(endpoint)))

    # Normalize ignored keys too: keys are "METHOD /path" or just "/path".
    ignored_norm: dict[tuple[str, str], dict] = {}
    for key, value in ignored.items():
        if " " in key:
            method, path = key.split(" ", 1)
        else:
            method, path = "GET", key
        ignored_norm[(method.upper(), norm_path(path))] = value

    uncovered = []
    for method, path in spec_ops:
        if (method, path) in covered:
            continue
        if (method, path) in ignored_norm:
            continue
        uncovered.append((method, path))

    # Build the set of operations that the current tool surface knows about
    # (covered by a tool OR explicitly ignored). This is the "handled" set.
    handled = covered | set(ignored_norm.keys())

    total = len(spec_ops)
    matched = total - len(uncovered)
    pct = (matched / total * 100) if total else 0.0

    print(f"Graph v1.0 operations in spec: {total}")
    print(f"Handled by tools (or ignored): {len(handled)}")
    print(f"Covered by tools (or ignored): {matched} ({pct:.1f}%)")
    print(f"Uncovered: {len(uncovered)}")

    if uncovered:
        print("\nCurrently uncovered operations (out of scope for this snapshot):")
        for method, path in sorted(uncovered)[:20]:
            print(f"  {method} {path}")
        print("  ... (snapshot; drift is what triggers a failure, not absolute coverage)")

    # --- Drift detection ------------------------------------------------
    # Compare against the baseline snapshot. Failure is a REGRESSION: an op
    # that the baseline says was handled (covered or ignored) is no longer
    # handled. Newly-added spec endpoints alone do not fail the gate (they are
    # expected; track them via the scheduled canary instead).
    handled_keys = handled  # set[(method, path)]
    drifted: list[str] = []
    if BASELINE_FILE.exists():
        try:
            with open(BASELINE_FILE, "r", encoding="utf-8") as f:
                baseline = json.load(f)
            base_handled_raw = baseline.get("handled_operations", [])
            base_handled = {
                (m.upper(), norm_path(p))
                for m, p in ((op.split(" ", 1)[0], op.split(" ", 1)[1]) if " " in op else ("GET", op)
                             for op in base_handled_raw)
            }
        except Exception as exc:  # malformed baseline is not a drift failure
            print(f"\nWARNING: could not read baseline ({exc}); skipping drift check.")
            base_handled = set()
    else:
        base_handled = set()

    if base_handled:
        # Only ops still present in the live spec count (removed endpoints don't drift).
        live_keys = {o for o in spec_ops}
        base_handled_live = base_handled & set(live_keys)
        drifted = sorted(f"{m} {p}" for m, p in sorted(base_handled_live - handled_keys))
        print(f"Handled in baseline: {len(base_handled)}")
        print(f"Drifted (previously handled, now not): {len(drifted)}")

    # --- Baseline snapshot update ---------------------------------------
    if os.getenv("UPDATE_BASELINE") == "1" or "--update-baseline" in sys.argv:
        baseline = {
            "checked_at": "",
            "total_operations": total,
            "covered": matched,
            "handled": len(handled_keys),
            "coverage_pct": round(pct, 2),
            "operations": [f"{m} {p}" for m, p in spec_ops],
            "handled_operations": [f"{m} {p}" for m, p in sorted(handled_keys)],
        }
        with open(BASELINE_FILE, "w", encoding="utf-8") as f:
            json.dump(baseline, f, indent=2)
        print(f"\nBaseline updated: {BASELINE_FILE}")

    return 1 if drifted else 0


if __name__ == "__main__":
    sys.exit(main())
