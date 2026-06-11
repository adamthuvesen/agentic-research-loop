# First-time setup

This repo **ships neutral MCP configs** — no servers wired by default. Sources are opt-in bundles under `examples/sources/`; enable the ones you need with `uv run research source enable <name>`, then **authenticate personally** to each (OAuth, an API key, a Snowflake login). Nothing in git carries credentials.

## What you get from `git clone`

- `.mcp.json` / `.codex/config.toml` / `.cursor/mcp.json` — **neutral** project MCP configs for Claude Code / Codex / Cursor (no servers by default). `research source enable <name>` wires a bundle's server into all three.
- `.claude/`, `.codex/`, and `.cursor/` — committed project agent layout (e.g. Claude `settings.json`). **Skills:** `.claude/skills`, `.codex/skills`, and `.cursor/skills` are the same committed symlink to `.agents/skills/`, so Claude Code, Codex, and Cursor all load repo skills from clone with no extra sync.
- `config/snowflake-mcp-tools.yaml` — Snowflake MCP tool allowlists (read-only SQL posture).

The three MCP config files ship **neutral** and stay that way in git. To wire a source, run `uv run research source enable <name>` — it edits all three locally from the bundle's `mcp.snippet.json` (don't commit your enabled configs back). `uv run pytest -q` still checks the three files agree on server names.

## Prerequisites

- `uv` ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Claude Code** (primary agent setup for this repo) and/or **Codex CLI** (optional; uses `.codex/config.toml`)
- Org access to the MCP-backed systems you need (Slack, Notion, Linear, Confidence, Snowflake, etc.)

## Fast path

From the repository root:

```bash
./scripts/setup-dev.sh
```

This runs `uv sync --dev` and the setup checker. The MCP config files are already committed — the script does not modify them. The checker may exit non-zero if you have not completed personal auth yet; see below.

## Python / CLI

```bash
uv sync --dev
uv run pytest -q # optional
```

## Cursor

The committed `.cursor/mcp.json` ships neutral. After you `research source enable <name>`, Cursor surfaces the wired servers; complete OAuth in its Settings → MCP panel (fixed redirect URI) on first use. Do not commit secrets or personal OAuth state.

## Autonomous `research run` / `plan` and agent CLIs

The default external agent is **Claude** (`config/runners/claude.json` uses `--dangerously-skip-permissions` with `claude --print`). Optional `--runner codex` uses `config/runners/codex.json` (`codex exec` with `--dangerously-bypass-approvals-and-sandbox`). Those flags are **intentional**: the case loop is **non-interactive** and must not block on per-step approval dialogs.

## MCP: Claude Code

Official reference: [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp).

1. Enable the sources you want: `uv run research source enable <name>` (see `research source list`).
2. Open a terminal in this repository and run `claude`.
3. Run `/mcp`, approve the servers you enabled, and complete OAuth for each HTTP provider when prompted.
4. Each bundle's `SETUP.md` covers its credentials (Snowflake uses your `default` connection; see below).

## MCP: Codex (optional)

Official references: [Codex MCP](https://developers.openai.com/codex/mcp), [Codex config basics](https://developers.openai.com/codex/config-basic).

Codex only loads **project-scoped** `.codex/config.toml` when this repository is marked as a **trusted** project. If tools do not appear, confirm trust first.

1. Mark this repo as a trusted project in Codex.
2. Enable sources with `research source enable <name>`, then `codex mcp login <server-name>` for OAuth HTTP servers. Slack needs a top-level `mcp_oauth_callback_port` — its bundle `SETUP.md` says where to add it. Complete OAuth locally — tokens are **not** stored in git.

## Snowflake

Create a personal `default` connection in `~/.snowflake/config.toml`. Example shape (placeholders only — copy from [`examples/snowflake-config.toml.example`](examples/snowflake-config.toml.example)):

```toml
[connections.default]
account = "YOUR_ACCOUNT"
user = "you@company.com"
authenticator = "externalbrowser"
warehouse = "AD_HOC_WH"
database = "YOUR_DB"
schema = "PUBLIC"
role = "YOUR_ROLE"
```

Adjust to match your access. The MCP server is started with `--connection-name default`.

## Optional: Google Search Console (GSC) and GA4

**GSC** is an opt-in bundle. Prefer a **warehouse** (Snowflake or BigQuery) for
organic-search metrics (synced GSC data); the `research gsc` CLI is the live
Search Console API fallback. Run `research source enable gsc`, then follow
[`examples/sources/gsc/SETUP.md`](../../examples/sources/gsc/) for the ADC login,
the `webmasters.readonly` scope, and the `GSC_SITE` / `GCP_QUOTA_PROJECT` env.

**GA4** is served by the official GA4 MCP server, not a CLI — enable the
`examples/sources/ga4/` bundle (read-only via the `analytics.readonly` scope).

## Opt-in source bundles

Sources beyond the built-ins ship as **copy-to-enable bundles** under
[`examples/sources/`](../../examples/sources/) — the committed MCP configs stay
neutral. Each bundle has a `source.json` (merge into `config/sources.json`), an
`mcp.snippet.json` (paste into the three MCP configs), and a `SETUP.md`
(credentials + read-only setup). Run `uv run research source enable <name>` to do
the merge + wiring automatically (`research source list` / `disable` too), then
follow the bundle's `SETUP.md`.

**Do the credential-only sources first** — for these, *nothing in committed config
can guarantee read-only*; the account or IAM role you connect is the only read-only rule:

- **Jira** — provision a **view-only Atlassian account** (Browse Projects; no
  create/edit/transition). The remote server has no read-only flag.
- **BigQuery** — authenticate a principal with only **BigQuery Data Viewer + Job
  User**, and prefer the `execute_sql_readonly` tool.
- **Confluence** — same Atlassian server as Jira; provision a **view-only account**
  (Confluence read; no add/edit/comment).
- **Datadog** — authenticate a principal with the **Datadog Read-Only Role** (or
  `*_read` app-key scopes). Preview API — may change.
- **Amplitude / Mixpanel** — **read+write MCP servers with destructive tools** (create
  experiments/feature-flags; Mixpanel can delete dashboards and bulk-edit the
  taxonomy) and **no read-only flag**. The autonomous runner skips permission prompts,
  so the **account role is the only read-only rule**: use a dedicated **Amplitude Viewer** /
  **Mixpanel Consumer** account and verify a write returns 403 before autonomous use.
  Prefer **PostHog** for a provably read-only product-analytics source.
- **HubSpot** — **read+write MCP server, no read-only flag.** Create the MCP Auth App
  and **grant only `*.read` scopes** (HubSpot then 403s writes), and connect a read-only
  user. The enforcement is real but lives in the grant — not auditable from config.
- **Azure DevOps** (local server) — **read+write MCP server, no read-only flag.** Provision a
  **read-only-scoped PAT** (Read scopes only, no write) or a **Stakeholder / read-only
  account**; the credential is the only read-only rule. The remote server's `X-MCP-Readonly`
  header isn't usable from Claude/Codex/Cursor yet (pending Entra dynamic client registration).

The rest enforce read-only via a config flag or a read-only scope (the contract test
checks each declares its mechanism) — still scope the credential as defense in depth:

- **GitHub** — `/readonly` endpoint (strict filter); pair with a read-only PAT.
- **Postgres** — `--access-mode=restricted`; pair with a SELECT-only role and pass
  `DATABASE_URI` via the environment, never committed config.
- **DuckDB** — read-only by default (omit `--read-write`).
- **GA4** — `analytics.readonly` ADC scope.
- **Sentry** — a read-scoped auth token (`org:read`, `project:read`, `event:read`);
  not the hosted OAuth flow, which grants write.
- **PostHog** — a personal API key with only `*:read` scopes (not the `mcp_server`
  preset, which adds `feature_flag:write`); the read-scoped key blocks writes
  server-side (403), so read-only is enforced by the credential itself.
- **LaunchDarkly** — run the local server with `--scope read` **and** a **Reader-role**
  API token (writes are 403'd at the API); never a Writer/Developer token.
- **Statsig** — a Console API key with the **`omni_read_only`** scope (the API rejects
  writes); never an `omni_read_write` key.
- **Stripe** — a **Restricted API Key (`rk_`)** scoped Read-only (writes 403 at the
  API); never a secret (`sk_`) or write-scoped key.
- **Salesforce** — pin `--toolsets=data,users` (drops deploy/Apex tools) **and** log
  the CLI into a **read-only-permission-set** org user; Beta — re-check toolsets.
- **Databricks** — wire the **Genie** endpoint (`/api/2.0/mcp/genie`, read-only by
  design); not the SQL server (read+write, UC-grant-guarded).
- **Redshift** — engine-enforced read-only (every query in `BEGIN READ ONLY`, no write
  tools); still scope a read-only IAM role + DB user (writes are on AWS's roadmap).
- **Google Drive** — `drive.readonly` OAuth scope (Google's official Drive MCP); grant only
  the read-only scope at consent, never `drive` (full) or `drive.file` (write).
- **Microsoft 365** — `--read-only` flag on `ms-365-mcp-server` (disables every Graph write);
  add `--org-mode` for SharePoint/OneDrive/Teams; back it with a read-only work account.
- **Azure** — `--read-only` flag on the official Azure MCP Server (filters to read-only tools
  across Monitor/Log Analytics, Azure SQL, Kusto…); also scope an Azure **Reader** RBAC role.

See each bundle's `SETUP.md` for exact steps.

## Verify

```bash
uv run python scripts/check_claude_setup.py
```

This checks `uv`, optional `codex` presence, Snowflake profile, and (when `claude` is installed) `claude mcp get` for any servers you've enabled. With neutral configs and nothing enabled yet it has little to check; failures on an enabled HTTP server are normal until you complete OAuth in your IDE.

## Adding a new source

Sources are **bundles**, not committed config. To add one, create
`examples/sources/<name>/` with three files (copy an existing bundle; see
[`examples/sources/README.md`](../../examples/sources/README.md)):

1. **`source.json`** — the registry spec (`transport`, `read_only_mechanism`, `base_notes`, …).
2. **`mcp.snippet.json`** — the server block in all three tool shapes (`claude`, `cursor`, `codex_toml`). stdio needs `command`/`args`; HTTP needs `url` (+ `oauth` in the `claude` shape if it uses a fixed callback, like Slack).
3. **`SETUP.md`** — credentials + how read-only is enforced (must mention read-only).

Then `uv run research source enable <name>` wires it into all three MCP configs. `uv run pytest -q` runs the read-only contract test (`tests/test_readonly_contract.py`) over every bundle plus the three-file consistency check.
