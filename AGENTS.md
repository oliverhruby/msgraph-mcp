# AGENTS.md

Guidance for AI agents (and humans) working on this repository. This file is
about **maintaining the code** — it is *not* end-user runtime documentation
(that lives in [README.md](README.md)).

## What this project is

A stdio/HTTP **Model Context Protocol (MCP) server** that exposes the
**Microsoft Graph API** as 219 MCP tools. Published to PyPI as **`msgraph-mcp`**;
the GitHub repo is the canonical source.

**Architecture rule:** this is a **thin, convention-driven wrapper** around the
Microsoft Graph HTTP API. All endpoint logic for a workload lives in one small
module under `src/msgraph_mcp/tools/`. There is deliberately **no
`msgraph-sdk` and no `azure-identity`** — only `mcp<2`, `msal`, and `httpx`.
Do not add the SDKs; keep the dependency surface minimal.

## Layout

| Path | Purpose |
|---|---|
| `src/msgraph_mcp/__init__.py` | Server bootstrap: `_tool`/`_run`/`ok`/`fail`/`ok_text`/`_serialize`, `_register_tools()`, `main()`, transport + read-only config. |
| `src/msgraph_mcp/auth.py` | `AuthManager`: 6 auth modes, sovereign clouds, token cache. |
| `src/msgraph_mcp/graph_client.py` | `GraphClient`: async `httpx`, retry, pagination, `$batch`, delta. |
| `src/msgraph_mcp/models.py` | Lightweight types. |
| `src/msgraph_mcp/coverage.py` | Exposes `TOOL_REGISTRY`, `tool_count()`, `by_workload()`. |
| `src/msgraph_mcp/tools/__init__.py` | Registry + auto-discovery of tool modules. |
| `src/msgraph_mcp/tools/_common.py` | `graph_tool` decorator + `graph`/`run_sync`/`require_write`/`to_query` helpers. |
| `src/msgraph_mcp/tools/*.py` | One module per workload (mail, files, calendar, …). |
| `scripts/check_graph_api_coverage.py` | Coverage-drift check vs the official Graph OpenAPI spec. |
| `scripts/check_tag_matches_version.py` | CI tag/version consistency check. |
| `scripts/graph_api_ignored_endpoints.json` | Endpoints intentionally out of scope (with reasons). |
| `scripts/graph_api_baseline.json` | Coverage snapshot for drift detection. |
| `pyproject.toml` | Packaging; console script `msgraph-mcp = "msgraph_mcp:main"`. |
| `Dockerfile` | Multi-tool container (stdio entrypoint, non-root user). |
| `README.md` | End-user docs (install, auth modes, tool reference). |

## Conventions (keep these consistent)

- **One file per workload.** Each tool module is named for a Graph workload
  (e.g. `mail.py`, `files.py`, `teams.py`). Auto-discovery imports every module
  under `tools/` whose name does not start with `_`.
- **Every tool** is a function decorated with `@graph_tool(...)`:
  ```python
  @graph_tool("mail", "GET", "/me/messages", delegated=["Mail.Read"])
  def list_messages(top: int = 10):
      def go():
          return run_sync(graph().get("/me/messages", params={"$top": top}))
      return go()
  ```
  - `graph_tool(workload, method, endpoint, *, delegated=[...], application=[...])`
    registers the tool's coverage metadata **and** applies `@_tool`. Always pass
    accurate scopes — they drive the coverage checker's endpoint matching.
  - The inner `go()` does the work so exceptions are caught by `_run` → `{ "isError": True }`.
  - Write tools **must** call `require_write()` first (enforced by
    `MSGRAPH_READ_ONLY=true`).
- **Async vs sync.** `GraphClient` methods are async. Wrap calls with
  `run_sync(...)` (or `graph()...`) as shown; never block the event loop.
- **Query params.** Use `to_query(**kwargs)` to drop `None` values and build
  `params=` dicts. Use `top`, `filter`, `select`, `expand`, `skip` arg names
  matching the Graph convention.
- **JSON output.** Return plain JSON via `ok(...)` / `fail(...)` / `ok_text(...)`.
  `_serialize` handles dataclasses, enums, and `datetime`. Don't return raw
  response objects.
- **Registry / coverage.** Every `graph_tool` call adds an entry to
  `TOOL_REGISTRY`. Keep `graph_endpoint` values stable — the coverage checker
  and baseline depend on them. When you add a tool for an endpoint, remove any
  matching entry from `graph_api_ignored_endpoints.json`.
- **Errors.** Surface Graph errors through the client's `GraphError`; `_run`
  converts them to MCP error results.

### Adding a new tool (checklist)

1. Add the function to the correct workload module (or create one).
2. Decorate with `@graph_tool(...)` — correct `workload`, `method`, `endpoint`,
   `delegated`/`application` scopes.
3. Call `require_write()` for write tools; document mutation in the docstring.
4. `ruff check src scripts` and confirm `coverage.tool_count()` increased.
5. Update the README "Tool reference" table and totals.
6. If a Graph endpoint existed but was previously ignored, drop it from
   `graph_api_ignored_endpoints.json`.

## Git commit policy

- Use **Conventional Commits** for every commit message.
- Format: `<type>(<scope>): <description>` (scope optional).
- Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
  `build`, `ci`, `chore`, `revert`.
- Keep the subject short and imperative, no trailing period. Before pushing,
  check `git log --oneline -10` and rewrite non-conforming subjects.

## Dependency pinning

`pyproject.toml` pins `mcp<2`. Reason: `mcp 2.x` renamed `FastMCP` → `MCPServer`
and changed the API; this project targets the FastMCP v1 API. Keep `mcp<2`.
`msal>=1.28` and `httpx>=0.27` may rise freely.

> On shipping versions as of v0.1.0: `mcp` resolves to a recent 1.x; staying on
> `mcp<2` is a deliberate **API-compat** decision, not a security pin. Revisit
> the v2 `MCPServer` port only if 1.x stops receiving security fixes.

## Security scanning

- **Dependabot** (repo-level): weekly version-update PRs for `pip` and
  `github-actions`. Do not remove the `ignore: mcp >=2.0.0` block.
- **`pip-audit`** (`.github/workflows/security.yml`): scans the installed
  dependency tree against OSV on every push/PR to main and weekly; a CVE fails
  the workflow. Fix the pinned version and re-verify with `pip-audit` locally.
- **Quality gates** (`.github/workflows/quality-gates.yml`):
  - `python-sanity` compiles all modules, verifies `pip install .`, and asserts
    `coverage.tool_count() >= 150`.
  - `docker-mcp-smoke` builds the image and performs an MCP stdio handshake +
    `tools/list` against the container (asserts `>= 150` tools).
- **Trivy container scan** (`.github/workflows/container-security.yml`): builds
  the image and scans every push/PR and weekly; fails on `HIGH`/`CRITICAL`
  (`ignore-unfixed: true`).
- **Coverage drift** (`.github/workflows/upstream-coverage.yml`):
  - `coverage-drift` fails only on **regression**: an operation that the
    baseline said was handled (covered or ignored) becoming uncovered. Absolute
    coverage of the ~18k-operation spec is expected to be partial; new spec
    endpoints alone do not fail this job.
  - `new-endpoint-canary` (scheduled) detects newly added spec endpoints and
    files an issue with the uncovered list.

`main` branch protection expects these required checks:

- `quality-gates / python-sanity`
- `quality-gates / docker-mcp-smoke`
- `security / pip-audit`
- `container-security / trivy-image`
- `upstream-coverage / coverage-drift`

Local checks:

```bash
pip install pip-audit && pip-audit
ruff check src scripts
python -m py_compile src/msgraph_mcp/__init__.py
python -c "import sys; sys.path.insert(0,'src'); from msgraph_mcp import coverage; print(coverage.tool_count())"
```

To run a workflow manually from `gh`:

```bash
gh workflow run quality-gates.yml --repo oliverhruby/msgraph-mcp
gh workflow run security.yml --repo oliverhruby/msgraph-mcp
gh workflow run container-security.yml --repo oliverhruby/msgraph-mcp
gh workflow run upstream-coverage.yml --repo oliverhruby/msgraph-mcp
```

## Build / verify

```bash
# from repo root
python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m ruff check src scripts
.venv/Scripts/python -m py_compile src/msgraph_mcp/__init__.py
.venv/Scripts/python -m msgraph_mcp     # drive an MCP client; tools/list shows all 219
```

There is no unit test suite; the MCP `tools/list` handshake after any change is
the primary verification, alongside `ruff` and the coverage check.

To update the coverage baseline after intentionally changing tool coverage:

```bash
$env:UPDATE_BASELINE="1"; .venv/Scripts/python scripts/check_graph_api_coverage.py
```

## Publishing (PyPI + GHCR)

- **PyPI** uses **OIDC trusted publishing** via GitHub Actions — no API token.
  See comments at the top of `.github/workflows/publish.yml` for the one-time
  registration (project `msgraph-mcp`, workflow name `publish.yml`).
- **GitHub Releases** are created automatically on tag push by
  `.github/workflows/release.yml` (autogenerated notes).
- **GHCR** images are published on tag push by
  `.github/workflows/publish-container.yml` (`linux/amd64` + `linux/arm64`).
- `auto-tag.yml` creates a `v<version>` tag from `pyproject.toml` on main.

To release a new version:

1. Bump `version` in `pyproject.toml`.
2. Commit + push.
3. Push a tag matching the version: `git tag v0.1.0 && git push --tags`
   (or let `auto-tag.yml` create it from main).
4. `publish`, `publish-container`, and `release` run automatically (the
   `release` GitHub environment may require approval).

Keep the README accurate (install, auth modes, counts).
