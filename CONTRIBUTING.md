# Contributing to msgraph-mcp

Thanks for contributing! This document covers how to set up your environment,
add tools, and get your changes merged.

## Development setup

```bash
git clone https://github.com/oliverhruby/msgraph-mcp.git
cd msgraph-mcp

python -m venv .venv
.venv/Scripts/activate        # Windows
.venv/bin/activate            # macOS / Linux

pip install -e ".[dev]"
```

## Lint & verify

```bash
ruff check src scripts
python -m py_compile src/msgraph_mcp/__init__.py
python -c "import sys; sys.path.insert(0,'src'); from msgraph_mcp import coverage; print(coverage.tool_count())"
```

Coverage drift (needs network for the Graph OpenAPI spec):

```bash
python scripts/check_graph_api_coverage.py
```

Security audit of the dependency tree:

```bash
pip install pip-audit && pip-audit
```

## Adding a tool

1. Add the function to the matching workload module under
   `src/msgraph_mcp/tools/` (or create a new module named after the workload).
2. Decorate with `@graph_tool(workload, method, endpoint, delegated=[...], application=[...])`
   — the arguments also drive coverage metadata, so keep them accurate.
3. For write tools, call `require_write()` at the start of `go()` and document
   the mutation in the docstring.
4. Verify with the commands above and confirm `tool_count()` increased.
5. Update the README "Tool reference" table and totals.

## Git commits

We use **Conventional Commits**:

```
<type>(<scope>): <description>
```

Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
`build`, `ci`, `chore`, `revert`. Keep subjects short and imperative.

## Pull requests

- Keep changes focused; one logical change per PR.
- Ensure `ruff check src scripts` passes and the MCP handshake lists all tools.
- If your change alters tool coverage, run the coverage check and update the
  baseline if the change is intentional (see AGENTS.md).
- Branch protection requires the quality-gates, security, container-security,
  and upstream-coverage checks to pass.

## Report issues

For bugs, tool gaps, or the official Microsoft Graph API adding endpoints you
want wrapped, open an issue. The scheduled coverage canary also files issues
automatically for newly detected, uncovered Graph endpoints.
