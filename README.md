# msgraph-mcp

A self-hosted **Model Context Protocol (MCP)** server that exposes the
**Microsoft Graph API** as **200+ MCP tools**, covering mail, calendar, files,
Teams, SharePoint, Planner, To Do, OneNote, Excel, presence, search, identity
governance, security, reports, and more.

Unlike the [official Microsoft MCP Server for Enterprise], which is a hosted,
read-only Entra-directory service with three tools, `msgraph-mcp` is a
bring-your-own-credentials, full-coverage Graph client you run yourself.

[official Microsoft MCP Server for Enterprise]: https://learn.microsoft.com/graph/mcp-server-overview

---

## Highlights

- **219 tools** across 25 workloads (see [Tool reference](#tool-reference)).
- **No `azure-identity`, no `msgraph-sdk`** — a thin raw-HTTP client (`httpx`)
  + `msal`. Fewer dependencies, smaller attack surface.
- **Six auth modes**: interactive, device-code, client-secret, certificate,
  on-behalf-of, managed identity — plus pre-existing-token.
- **Sovereign cloud support** (US Gov L4/L5, China, Germany).
- **Read-only mode** with a hard guard: set `MSGRAPH_READ_ONLY=true` to forbid
  every write tool via `require_write()`.
- Retries on `429`/`503`/`504`, automatic pagination, `$batch`, and delta queries.
- Runs over **stdio** or **HTTP/SSE**, in-process or as a **Docker** container.
- CI/CD: quality gates, security/pip-audit, Trivy container scan, coverage
  drift vs the official Graph OpenAPI spec, PyPI + GHCR publishing.

---

## Install

```bash
pip install msgraph-mcp
```

Or clone and run from source:

```bash
git clone https://github.com/oliverhruby/msgraph-mcp.git
cd msgraph-mcp
python -m venv .venv
.venv/Scripts/activate        # Windows
.venv/bin/activate            # macOS / Linux
pip install -e .
```

### Docker

```bash
docker build -t msgraph-mcp .
docker run --rm -i \
  -e MSGRAPH_AUTH_MODE=client_secret \
  -e MSGRAPH_CLIENT_ID=... -e MSGRAPH_CLIENT_SECRET=... \
  -e MSGRAPH_TENANT_ID=... \
  msgraph-mcp
```

---

## Quick start

### 1. Register an app in Microsoft Entra ID (once)

1. [.NET portal > App registrations](https://aka.ms/AppRegistrations) → New
   registration.
2. Under **Authentication**, add a public client / redirect for the auth mode
   you plan to use (device-code and interactive need no redirect URI).
3. Grant the API permissions your tools need (delegated and/or
   application). `DEFAULT_DELEGATED_SCOPES` in `auth.py` lists sensible
   defaults.
4. Note the **Tenant ID**, **Client ID**, (and **Client Secret** / **cert** if
   using those modes).

### 2. Authenticate

#### Interactive (default)

```bash
export MSGRAPH_CLIENT_ID=00000000-0000-0000-0000-000000000000
export MSGRAPH_TENANT_ID=11111111-1111-1111-1111-111111111111
msgraph-mcp
```

A browser opens, you sign in, and a token cache is saved at
`~/.msgraph-mcp/token_cache.json` for later runs.

#### Device code

```bash
export MSGRAPH_AUTH_MODE=device_code
export MSGRAPH_CLIENT_ID=...
msgraph-mcp
```

#### Client secret (app-only / daemon)

```bash
export MSGRAPH_AUTH_MODE=client_secret
export MSGRAPH_CLIENT_ID=...
export MSGRAPH_CLIENT_SECRET=...
export MSGRAPH_TENANT_ID=...
msgraph-mcp
```

#### Certificate (app-only)

```bash
export MSGRAPH_AUTH_MODE=certificate
export MSGRAPH_CLIENT_ID=...
export MSGRAPH_CERT_PATH=/path/to/cert.pem
export MSGRAPH_TENANT_ID=...
msgraph-mcp
```

#### On-behalf-of

```bash
export MSGRAPH_AUTH_MODE=obo
export MSGRAPH_CLIENT_ID=... MSGRAPH_CLIENT_SECRET=... MSGRAPH_TENANT_ID=...
msgraph-mcp
```

#### Managed identity (Azure)

```bash
export MSGRAPH_AUTH_MODE=managed_identity     # or `managed_identity_user`
export MSGRAPH_CLIENT_ID=...                  # the managed identity's client id
msgraph-mcp
```

#### Pre-existing token

```bash
export MSGRAPH_AUTH_MODE=pre_token
export MSGRAPH_ACCESS_TOKEN=eyJ...
msgraph-mcp
```

### 3. Connect your MCP client

Point your MCP client at `msgraph-mcp`. For example, in Claude Desktop or an
agent runtime:

```json
{
  "mcpServers": {
    "msgraph": {
      "command": "msgraph-mcp",
      "args": []
    }
  }
}
```

Over HTTP/SSE (see [Configuration](#configuration) for `MCP_TRANSPORT=streamable-http`):

```json
{
  "mcpServers": {
    "msgraph": {
      "url": "http://127.0.0.1:3000/mcp",
      "headers": { "Authorization": "Bearer <MCP_API_KEY>" }
    }
  }
}
```

---

## Configuration

Configuration is entirely via environment variables.

| Variable | Default | Description |
|---|---|---|
| `MSGRAPH_AUTH_MODE` | `interactive` | `interactive`, `device_code`, `client_secret`, `certificate`, `obo`, `managed_identity`, `managed_identity_user`, `pre_token` |
| `MSGRAPH_CLIENT_ID` | *(empty)* | Entra app (client) ID |
| `MSGRAPH_TENANT_ID` | `common` | Entra tenant ID |
| `MSGRAPH_CLIENT_SECRET` | *(empty)* | App secret (client_secret / obo) |
| `MSGRAPH_CERT_PATH` | *(empty)* | Path to PEM cert (certificate mode) |
| `MSGRAPH_CERT_PASSWORD` | *(empty)* | Optional cert password |
| `MSGRAPH_SCOPES` | *(built-in defaults)* | Comma-separated extra scopes |
| `MSGRAPH_CLOUD` | `global` | `global`, `us_gov_l4`, `us_gov_l5`, `china`, `germany` |
| `MSGRAPH_BASE_URL` | *(from cloud)* | Override Graph base URL |
| `MSGRAPH_API_VERSION` | `v1.0` | `v1.0` or `beta` |
| `MSGRAPH_ACCESS_TOKEN` | *(empty)* | Pre-acquired token (pre_token) |
| `MSGRAPH_TOKEN_CACHE_PATH` | `~/.msgraph-mcp/token_cache.json` | Token cache location |
| `MSGRAPH_READ_ONLY` | `false` | `true` disables every write tool |
| `MSGRAPH_MAX_PAGES` | `50` | Max pages auto-paginated per collection |
| `MSGRAPH_LOG_LEVEL` | `WARNING` | Python log level |
| `MSGRAPH_TOOLSETS` | `core` | Reserved for future per-workload gating |
| `MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http` |
| `MCP_HOST` | `127.0.0.1` | HTTP bind host |
| `MCP_PORT` | `3000` | HTTP bind port |
| `MCP_API_KEY` | *(empty)* | Bearer token required for HTTP transport |

---

## Tool reference

Tools are grouped by workload (each module under `src/msgraph_mcp/tools/`).

| Workload | # Tools | Examples |
|---|---|---|
| `mail` | 19 | list/send/reply/forward messages, folders, drafts, rules, attachments, mailbox settings |
| `files` | 19 | OneDrive/SharePoint items, upload sessions, versions, permissions, sharing links, revoke |
| `calendar` | 14 | events, calendars, free/busy, findMeetingTimes, rooms, schedule |
| `teams` | 13 | teams, channels, messages, replies, members, tabs |
| `users` | 12 | profiles, photo, direct reports, licenses, transitive memberships |
| `onenote` | 11 | notebooks, sections, section groups, pages (CRUD + copy) |
| `planner` | 11 | plans, buckets, tasks, task details, assignments |
| `excel` | 10 | workbooks, worksheets, ranges, tables, sessions |
| `directory` | 9 | directory objects, members, roles |
| `groups` | 9 | CRUD, members, owners, transitive membership |
| `todo` | 9 | task lists, tasks, checklist items |
| `online_meetings` | 8 | create meetings, transcripts, attendance, recordings |
| `chat` | 7 | chats, messages, create chat |
| `contacts` | 7 | contacts, contact folders |
| `device_management` | 7 | managed devices, compliance |
| `security` | 6 | alerts, incidents, secure scores |
| `change_notifications` | 5 | subscriptions (webhooks), delta |
| `identity_governance` | 5 | access reviews, entitlement mgmt, PIM |
| `people` | 5 | relevance search, insights, profile |
| `reports` | 5 | Microsoft 365 usage reports |
| `audit_logs` | 4 | sign-ins, directory audits, provisioning |
| `presence` | 4 | user presence, batch presence |
| `search` | 2 | unified Microsoft Search (KQL) |
| `batch` | 1 | Graph `$batch` |
| **Total** | **219** | |

Each tool is decorated with `@graph_tool(...)` carrying its HTTP method, Graph
endpoint, and the delegated + application scopes required. Read the docstring
of any tool for its exact behaviour; write tools call `require_write()` and
fail fast in read-only mode.

---

## How this differs from the official Microsoft MCP Server

The [official Microsoft MCP Server for Enterprise] and `msgraph-mcp` are
intentionally **divergent, complementary** tools:

| | Official Microsoft MCP Server | **msgraph-mcp** |
|---|---|---|
| Hosting | Microsoft-hosted | **Self-hosted** (your machine / container) |
| Auth | Your Graph connection | **Bring your own credentials** (6 modes) |
| Scope | Read-only Entra **directory** | **Full Graph**: mail, files, calendar, Teams, SharePoint, Planner, Excel, admin… |
| Tools | ~3 | **219** |
| Write access | Read-only | Read + write (with read-only guard) |
| Transport | stdio | stdio + HTTP/SSE |

Use the official server when you only need read-only directory lookups with
zero infra. Use `msgraph-mcp` when you want full Graph coverage, self-hosting,
writes, and control over auth.

---

## Development

```bash
pip install -e ".[dev]"
ruff check src scripts
python -m py_compile src/msgraph_mcp/__init__.py
python -m msgraph_mcp      # then drive an MCP client; tools/list should show all 219
```

Coverage drift check (needs network to fetch the Graph OpenAPI spec):

```bash
python scripts/check_graph_api_coverage.py
```

See [AGENTS.md](AGENTS.md) for conventions and [CONTRIBUTING.md](CONTRIBUTING.md)
for contributing.

---

## License

[MIT](LICENSE)
