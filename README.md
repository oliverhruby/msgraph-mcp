# Microsoft Graph MCP Server

[![GitHub release](https://img.shields.io/github/v/release/oliverhruby/msgraph-mcp.svg?label=release)](https://github.com/oliverhruby/msgraph-mcp/releases)
[![Quality gates](https://img.shields.io/github/actions/workflow/status/oliverhruby/msgraph-mcp/quality-gates.yml.svg?label=quality%20gates)](https://github.com/oliverhruby/msgraph-mcp/actions/workflows/quality-gates.yml)
[![Security](https://img.shields.io/github/actions/workflow/status/oliverhruby/msgraph-mcp/security.yml.svg?label=security)](https://github.com/oliverhruby/msgraph-mcp/actions/workflows/security.yml)
[![Container security](https://img.shields.io/github/actions/workflow/status/oliverhruby/msgraph-mcp/container-security.yml.svg?label=container%20security)](https://github.com/oliverhruby/msgraph-mcp/actions/workflows/container-security.yml)
[![Coverage drift](https://img.shields.io/github/actions/workflow/status/oliverhruby/msgraph-mcp/upstream-coverage.yml.svg?label=coverage%20drift)](https://github.com/oliverhruby/msgraph-mcp/actions/workflows/upstream-coverage.yml)

## Project

A **Model Context Protocol (MCP) server** that exposes the full
**Microsoft Graph API** to AI agents such as opencode, Claude, Cursor and any
other MCP client — **219 tools** across 25 workloads: mail, calendar, files,
Teams, SharePoint, Planner, To Do, OneNote, Excel, presence, search, identity
governance, security, reports, audit logs and more.

Microsoft Graph is the single REST entry point into Microsoft 365. This server
lets an agent authenticate to your tenant **once** and then operate your real
mail, files, calendar, Teams and SharePoint data directly — reading inboxes,
drafting and sending mail, creating calendar events and meetings, uploading or
sharing files, answering Teams channels, maintaining Planner/To Do tasks, and
administering users, groups, security and audit logs.

> **Self-hosted & by-design full-coverage.** Unlike the hosted Microsoft-hosted
> "MCP Server for Enterprise", this server runs on **your** machine or
> container, uses **your own** credentials (interactive, device-code,
> client-secret, certificate, on-behalf-of, managed identity), and can **write**
> — with a hard read-only guard when you want it safe.

---

## Table of Contents

- [Why another Microsoft Graph MCP server?](#why-another-microsoft-graph-mcp-server)
- [What it provides](#what-it-provides)
- [Getting started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [1. Install](#1-install)
  - [2. Register an app in Microsoft Entra ID](#2-register-an-app-in-microsoft-entra-id)
  - [3. Authenticate](#3-authenticate)
  - [4. Register with your MCP client](#4-register-with-your-mcp-client)
- [Prompt examples](#prompt-examples)
- [Configuration](#configuration)
- [Tool reference](#tool-reference)
- [Data & safety notes](#data--safety-notes)
- [Contributing](#contributing)
- [Limitations](#limitations)
- [Support](#support)
- [License](#license)

---

## Why another Microsoft Graph MCP server?

Several Microsoft Graph / Microsoft 365 MCP servers already exist. I have **no
affiliation** with any of them — they are referenced honestly for comparison,
exactly as with this project's siblings.

### The main players

- **[Official — Microsoft MCP Server for Enterprise]** — hosted by Microsoft,
  *read-only Entra directory* only. It does not expose one tool per Graph operation;
  instead it uses RAG to *generate Queries* on the fly (`microsoft_graph_suggest_queries`,
  `microsoft_graph_get`, `microsoft_graph_list_properties`). Global cloud only,
  write support still in preview, no self-hosting.
- **[Softeria/ms-365-mcp-server]** — Node.js, the closest "full coverage"
  alternative: 300+ tools, 1:1 endpoint mapping, MSAL, read-only mode, tool
  presets + dynamic discovery. Worth evaluating.
- **[DustHoff/msgraphmcp]** — Node.js/TypeScript, 140+ tools, four auth modes,
  notably deep **Intune** coverage (~64 Intune tools).
- **[nitin27may/ms-graph-mcp]** — Python, 85 tools, no SDK / no `azure-identity`
  (raw `httpx`), namespaced tools, read/write separation behind a write scope.
- **[CodyBuilder-dev/ms-graph-mcp]** — Node.js, device-code auth, mail/calendar/
  Teams/To Do/contacts/files/OneDrive/SharePoint, but **no directory** surface.
- **[timfurlong/msgraph-mcp]** — Python, on PyPI, mail + calendar + read-only
  Teams, MSAL device code only, uses the Graph SDK.

[Official — Microsoft MCP Server for Enterprise]: https://learn.microsoft.com/graph/mcp-server/overview
[Softeria/ms-365-mcp-server]: https://github.com/softeria/ms-365-mcp-server
[DustHoff/msgraphmcp]: https://github.com/DustHoff/msgraphmcp
[nitin27may/ms-graph-mcp]: https://github.com/nitin27may/ms-graph-mcp
[CodyBuilder-dev/ms-graph-mcp]: https://github.com/CodyBuilder-dev/ms-graph-mcp
[timfurlong/msgraph-mcp]: https://github.com/timfurlong/msgraph-mcp

### What sets this project apart

| Capability | Microsoft official | Softeria | DustHoff | nitin27may | CodyBuilder | timfurlong | **this project** |
|---|---|---|---|---|---|---|---|
| Language / runtime | hosted | Node.js | Node.js | Python | Node.js | Python | **Python** |
| Tools | 3 | 300+ | 140+ | 85 | ~50 | ~45 | **219** |
| Read-only Entra directory | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Mail (send/reply/rules/archive) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Calendar + meetings + rooms | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Files / OneDrive (upload, sharing, revoke) | ❌ | ✅ | ✅ | ✅ | ✅ | partial | ✅ |
| SharePoint sites/lists/columns/items | ❌ | ✅ | ✅ | partial | ✅ | ❌ | ✅ |
| Teams channels + messages | ❌ | ✅ | ✅ | ✅ | ✅ | read-only | ✅ |
| Planner + To Do | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ |
| OneNote notebooks/pages | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Excel workbooks/ranges/tables | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Intune / device management | ❌ | partial | **deep** | ❌ | ❌ | ❌ | ✅ |
| Identity governance (reviews/PIM) | partial | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Security alerts/incidents + audit logs | ❌ | partial | ❌ | ❌ | ❌ | ❌ | ✅ |
| Reports (M365 usage) | ❌ | partial | ❌ | ❌ | ❌ | ❌ | ✅ |
| Change notifications / delta | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Graph `$batch` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **No SDK dependency** (`msgraph-sdk`/`azure-identity`) | n/a | n/a | ✅ | ✅ | n/a | ❌ | ✅ |
| **Sovereign clouds** (US Gov, China, Germany) | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Hard read-only guard** (`MSGRAPH_READ_ONLY`) | n/a | ✅ | ❌ | ✅ | partial | ❌ | ✅ |
| **Coverage drift CI** vs official Graph spec | n/a | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

> Tool counts and capabilities are approximate, from the respective READMEs at
> the time of writing — always verify against the source. The point is not that
> "more is better", but that this project is the **deliberate Python,
> self-hostable, write-capable, zero-SDK** option covering the practical day-to-day
> Microsoft 365 surface an agent actually uses, with CI that keeps it honest
> against the ever-growing Graph API.

### Key differentiators

- **Full coverage, one auth seam.** Authenticate once (six modes) and reach
  mail, files, calendar, Teams, SharePoint, Planner, To Do, OneNote, Excel,
  presence, security, audit and admin — instead of stitching together several
  single-workload servers.
- **No `msgraph-sdk`, no `azure-identity`.** A thin raw-HTTP client (`httpx`) +
  `msal`. A radically smaller dependency tree and an inspectable wire path.
- **Writes are possible but guarded.** Write tools call `require_write()`; set
  `MSGRAPH_READ_ONLY=true` to forbid every one of them. Nothing mutates your
  tenant by accident.
- **Coverage drift CI.** A scheduled job compares the tool surface against the
  official Microsoft Graph OpenAPI spec and files an issue when Microsoft ships
  endpoints we don't cover yet — so the gap is visible instead of silent.

---

## What it provides

A single stdio/HTTP MCP server exposing **219 tools** across 25 workloads:

- **Mail** — list/search/get messages, send, reply, forward, drafts, folders,
  move, rules, attachments, mailbox settings
- **Files** — OneDrive + SharePoint drives: items, upload sessions, versions,
  permissions, sharing links, revoke
- **Calendar** — events, calendars, free/busy, meeting times, rooms, schedules
- **Teams** — teams, channels, messages, replies, members, tabs
- **Users & groups** — profiles, photos, licenses, memberships, members/owners
- **Planner & To Do** — plans, buckets, tasks, assignments, checklist items
- **OneNote** — notebooks, sections, section groups, pages
- **Excel** — workbooks, worksheets, ranges, tables, sessions
- **SharePoint** — sites, lists, columns, content types, list items
- **Admin & security** — directory, device management, security
  alerts/incidents, audit logs, reports, identity governance
- **Meetings & presence** — online meetings, transcripts, attendance,
  recordings, presence
- **Search & integration** — unified Microsoft Search, `$batch`, change
  notifications / delta

—

## Getting started

You need an MCP-capable client (opencode, Claude Desktop, Cursor, etc.).

### 1. Install

**Option A — from PyPI (recommended)**

```bash
uvx msgraph-mcp-full
# or
pip install msgraph-mcp-full
```

**Option B — from GitHub (latest source)**

```bash
uvx --from "git+https://github.com/oliverhruby/msgraph-mcp.git" msgraph-mcp-full
# or
pip install "git+https://github.com/oliverhruby/msgraph-mcp.git"
```

**Option C — development from source**

```bash
git clone https://github.com/oliverhruby/msgraph-mcp.git
cd msgraph-mcp
uv sync               # or: python -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"
uv run msgraph-mcp-full
```

Run the checks before merging changes:

```bash
uv run ruff check src scripts tests
uv run pytest -q                       # offline unit suite (auth, client, 219-tool sweep)
uv run pytest -m integration -q       # live read-only tests; skips without creds
```

**Option D — Docker**

```bash
docker pull ghcr.io/oliverhruby/msgraph-mcp:latest

docker run --rm -i \
  -e MSGRAPH_AUTH_MODE=client_secret \
  -e MSGRAPH_CLIENT_ID=... -e MSGRAPH_CLIENT_SECRET=... \
  -e MSGRAPH_TENANT_ID=... \
  ghcr.io/oliverhruby/msgraph-mcp:latest
```

> `pyproject.toml` pins `mcp<2` (the stable FastMCP v1 API). `mcp 2.x` renamed
> `FastMCP` to `MCPServer` and changed the API surface; this server targets the
> FastMCP v1 API for simplicity and stability.

### 2. Register an app in Microsoft Entra ID

1. [App registrations](https://aka.ms/AppRegistrations) → New registration.
2. Under **Authentication**, add a public client / redirect for the auth mode
   you plan to use (device-code and interactive need no redirect URI).
3. Grant the API permissions your tools need (delegated and/or application).
   `DEFAULT_DELEGATED_SCOPES` in `auth.py` lists sensible defaults.
4. Note the **Tenant ID**, **Client ID** (and **Client Secret** / **cert** if
   using those modes).

### 3. Authenticate

Configuration is entirely via environment variables.

#### Interactive (default)

```bash
export MSGRAPH_AUTH_MODE=interactive
export MSGRAPH_CLIENT_ID=00000000-0000-0000-0000-000000000000
export MSGRAPH_TENANT_ID=11111111-1111-1111-1111-111111111111
msgraph-mcp-full
```

A browser opens, you sign in, and a token cache is saved at
`~/.msgraph-mcp/token_cache.json` for later runs.

#### Device code

```bash
export MSGRAPH_AUTH_MODE=device_code
export MSGRAPH_CLIENT_ID=...
msgraph-mcp-full
```

#### Client secret (app-only / daemon)

```bash
export MSGRAPH_AUTH_MODE=client_secret
export MSGRAPH_CLIENT_ID=...
export MSGRAPH_CLIENT_SECRET=...
export MSGRAPH_TENANT_ID=...
msgraph-mcp-full
```

#### Certificate (app-only)

```bash
export MSGRAPH_AUTH_MODE=certificate
export MSGRAPH_CLIENT_ID=...
export MSGRAPH_CERT_PATH=/path/to/cert.pem
export MSGRAPH_TENANT_ID=...
msgraph-mcp-full
```

#### On-behalf-of

```bash
export MSGRAPH_AUTH_MODE=obo
export MSGRAPH_CLIENT_ID=... MSGRAPH_CLIENT_SECRET=... MSGRAPH_TENANT_ID=...
msgraph-mcp-full
```

#### Managed identity (Azure)

```bash
export MSGRAPH_AUTH_MODE=managed_identity     # or `managed_identity_user`
export MSGRAPH_CLIENT_ID=...                  # the managed identity's client id
msgraph-mcp-full
```

#### Pre-existing token

```bash
export MSGRAPH_AUTH_MODE=pre_token
export MSGRAPH_ACCESS_TOKEN=eyJ...
msgraph-mcp-full
```

### 4. Register with your MCP client

**opencode** — add to `~/.config/opencode/opencode.json` (or `opencode.jsonc`):

```jsonc
{
  "mcp": {
    "msgraph": {
      "type": "local",
      "enabled": true,
      "command": ["uvx", "msgraph-mcp-full"],
      "env": {
        "MSGRAPH_AUTH_MODE": "client_secret",
        "MSGRAPH_CLIENT_ID": "{env:MSGRAPH_CLIENT_ID}",
        "MSGRAPH_CLIENT_SECRET": "{env:MSGRAPH_CLIENT_SECRET}",
        "MSGRAPH_TENANT_ID": "{env:MSGRAPH_TENANT_ID}"
      }
    }
  }
}
```

> Put credentials in your shell/environment (or a `.env`) and reference them
> with `{env:VAR}`, or hardcode them under `env:` directly.

**Claude Desktop / Cursor** — use `claude_desktop_config.json` / `.mcp.json`
with a standard `mcpServers` entry pointing `command`/`args` at the venv python
and `-m msgraph_mcp`, plus an `env` block.

Over HTTP/SSE (`MCP_TRANSPORT=streamable-http`):

```jsonc
{
  "mcpServers": {
    "msgraph": {
      "url": "http://127.0.0.1:3000/mcp",
      "headers": { "Authorization": "Bearer <MCP_API_KEY>" }
    }
  }
}
```

After editing client config, **restart the client** so the MCP server is loaded.

---

## Prompt examples

| User prompt | Likely tool call(s) | Expected response |
|---|---|---|
| "Show my last 10 emails" | `list_messages top=10` | Recent messages (sender, subject, preview). |
| "Draft a reply to Oliver accepting the meeting" | `get_message` → `reply_message` | Draft/sent confirmation (or draft body to review). |
| "What's on my calendar this week?" | `list_events_in_range` | A short event list with times. |
| "Create a 1-hour meeting tomorrow at 10:00" | `create_event` | Created event with id + link. |
| "Upload `report.xlsx` to my OneDrive root" | `upload_file` | File metadata + sharing-ready link. |
| "List questions asked in the #general channel today" | `list_channel_messages` | Channel messages with authors. |
| "What tasks are due in my To Do this week?" | `list_tasks` | Tasks with due dates and states. |
| "Any high-severity security alerts?" | `list_security_alerts` | Alerts with severity + status. |
| "Who signed in from outside the US recently?" | `list_sign_in_logs` | Matching sign-in log entries. |

---

## Configuration

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
| `files` | 19 | OneDrive items, upload sessions, versions, permissions, sharing links, revoke |
| `sharepoint` | 17 | sites, lists, columns, content types, list items |
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
endpoint, and the delegated + application scopes required. Read any tool's
docstring for exact behaviour; write tools call `require_write()` and fail fast
in read-only mode.

---

## Data & safety notes

- Most tools are **read-only**. The write tools (send/reply, create event,
  upload/share/revoke file, create task, admin mutations, …) mutate real
  Microsoft 365 state. Use them with care, or set `MSGRAPH_READ_ONLY=true` to
  disable the entire write surface.
- The server acts **as your credentials** — it can reach only what the
  authenticated principal can reach. Delegated modes honour your user's
  permissions; app-only modes use the application's granted permissions.
- Sovereign-cloud endpoints differ; set `MSGRAPH_CLOUD` accordingly.
- `MSGRAPH_API_VERSION=beta` exposes beta endpoints that may change without
  notice — prefer `v1.0` unless you know you need a beta API.

---

## Contributing

Contributor and maintainer guidance is in [CONTRIBUTING.md](CONTRIBUTING.md).

- Contribution workflow and local setup
- Architecture and implementation details
- Release process (PyPI, GitHub Releases, GHCR)
- CI quality gates and upstream coverage drift checks

---

## Limitations

- **Token lifetime = server lifetime.** The auth session lives for the lifetime
  of the MCP server process; restarting the client means signing in again (the
  on-disk cache in `~/.msgraph-mcp/` helps for interactive/device flows).
- **Beta surface is opt-in.** Only `v1.0` is covered by the coverage-drift
  baseline; beta endpoints are registered but not independently monitored.
- **Coverage is broad, not exhaustive.** The Graph API has ~18,000 v1.0
  operations; this server wraps the practical day-to-day surface (219 tools) and
  tracks the gap via the coverage-drift canary rather than claiming 100%.
- **Intune & admin depth.** Device management and Intune are covered at a useful
  level but not as deep as a dedicated Intune server (e.g. DustHoff's).
- **No Graph Explorer-grade generality.** For an arbitrary, not-yet-covered
  endpoint, prefer the official server, GraphMind-style indexing, or a raw
  `$batch` call.

---

## Support

If you like this project and want to support or request a feature, send me a
beer, it keeps my mind relaxed and ideas will come :-)

[![Support via PayPal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.me/oliverhruby/)

---

## License

[MIT](LICENSE) © Oliver Hrubý

This project is **not affiliated with or endorsed by** Microsoft or any of the
other MCP servers referenced above. Microsoft Graph and Microsoft 365 are
trademarks of Microsoft Corporation.
