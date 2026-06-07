# First-time setup

This repo **commits shared MCP configuration** (no API keys or personal tokens). Each collaborator still **authenticates personally** to Slack, Notion, Linear, Confidence, and Snowflake. Nothing in git replaces your OAuth sign-ins or Snowflake login.

## What you get from `git clone`

- `.mcp.json` — hand-maintained **Claude Code** project MCP config (repo root).
- `.codex/config.toml` — hand-maintained **Codex** project MCP config ([Codex MCP](https://developers.openai.com/codex/mcp)).
- `.cursor/mcp.json` — hand-maintained **Cursor** project MCP config (Cursor drives OAuth via its own UI, so this file does not carry a `callbackPort`).
- `.claude/`, `.codex/`, and `.cursor/` — committed project agent layout (e.g. Claude `settings.json`). **Skills:** `.claude/skills`, `.codex/skills`, and `.cursor/skills` are the same committed symlink to `agents/skills/`, so Claude Code, Codex, and Cursor all load repo skills from clone with no extra sync.
- `config/snowflake-mcp-tools.yaml` — Snowflake MCP tool allowlists (read-only SQL posture).

Each of the three MCP config files is its own canonical source of truth for its tool. There is no generator, no intermediate registry — edit in place in each tool's native format. `uv run pytest -q` will fail if the three files disagree on the set of MCP server names, which catches the "added to one, forgot the others" mistake.

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

Opening the repo in Cursor should surface all servers from the committed `.cursor/mcp.json` automatically. Cursor handles OAuth via its own Settings → MCP panel using a fixed redirect URI — complete Slack (and any other OAuth server) sign-in there on first use. Do not commit secrets or personal OAuth state.

## Autonomous `research run` / `plan` and agent CLIs

The default external agent is **Claude** (`config/runners/claude.json` uses `--dangerously-skip-permissions` with `claude --print`). Optional `--runner codex` uses `config/runners/codex.json` (`codex exec` with `--dangerously-bypass-approvals-and-sandbox`). Those flags are **intentional**: the case loop is **non-interactive** and must not block on per-step approval dialogs.

## MCP: Claude Code

Official reference: [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp).

1. Open a terminal in this repository.
2. Run `claude`.
3. Run `/mcp`, approve project servers, and complete OAuth for each HTTP provider when prompted.
4. Snowflake uses the `default` connection in your Snowflake config (see below).

## MCP: Codex (optional)

Official references: [Codex MCP](https://developers.openai.com/codex/mcp), [Codex config basics](https://developers.openai.com/codex/config-basic).

Codex only loads **project-scoped** `.codex/config.toml` when this repository is marked as a **trusted** project. If tools do not appear, confirm trust first.

1. Mark this repo as a trusted project in Codex.
2. Use `codex mcp` (and `codex mcp login <server-name>` for OAuth HTTP servers such as Slack) per Codex docs. The committed TOML sets `mcp_oauth_callback_port` for Slack; complete OAuth locally — tokens are **not** stored in git.

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

## Optional: Google Search Console CLI (Application Default Credentials)

**GSC:** Prefer a **warehouse** (Snowflake or BigQuery) for organic search metrics (synced GSC data). The steps below apply only when you use the `research gsc` command — the **live Search Console API fallback**, not the default path.

**GA4:** served by the official GA4 MCP server, not a CLI — enable the `examples/sources/ga4/` bundle (read-only via the `analytics.readonly` scope).

Code under `agentic_research_loop.google_api` uses **Application Default Credentials**. If you need `research gsc`, run (see repo for current scopes):

```bash
gcloud auth application-default login \
  --client-id-file="$HOME/.config/gcloud/oauth-client.json" \
  --scopes="https://www.googleapis.com/auth/webmasters.readonly,https://www.googleapis.com/auth/cloud-platform"
```

The `research gsc` command validates `--start-date` and `--end-date` locally as
real `YYYY-MM-DD` dates and rejects inverted ranges before making API calls.

## Opt-in source bundles

Sources beyond the built-ins ship as **copy-to-enable bundles** under
[`examples/sources/`](../../examples/sources/) — the committed MCP configs stay
neutral. Each bundle has a `source.json` (merge into `config/sources.json`), an
`mcp.snippet.json` (paste into the three MCP configs), and a `SETUP.md`
(credentials + read-only setup).

**Do the credential-only sources first** — for these, *nothing in committed config
can guarantee read-only*; the account or IAM role you connect is the only guardrail:

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
  so the **account role is the only guardrail**: use a dedicated **Amplitude Viewer** /
  **Mixpanel Consumer** account and verify a write returns 403 before autonomous use.
  Prefer **PostHog** for a provably read-only product-analytics source.

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

See each bundle's `SETUP.md` for exact steps.

## Verify

```bash
uv run python scripts/check_claude_setup.py
```

This checks `uv`, optional `codex` presence, Snowflake profile, and (when `claude` is installed) `claude mcp get` for each server listed in `.mcp.json`. Failures on Slack/Notion/etc. are normal until you complete OAuth in your IDE. Repo-level drift across the three MCP config files is caught by `uv run pytest -q`, not this script.

## Adding a new MCP server

Each of the three files is its tool's canonical MCP config. To add a server, edit all three directly:

1. **`.mcp.json`** (Claude Code) — add an entry under `mcpServers`. Use `type: "stdio"` + `command`/`args` for local servers, or `type: "http"` + `url` (and `oauth.callbackPort` if the server needs OAuth with a fixed callback).
2. **`.codex/config.toml`** — add a `[mcp_servers.<name>]` block with either `command`/`args` (stdio) or `url` (http), plus `enabled = true`. If the server uses OAuth with a callback port and no existing server already sets `mcp_oauth_callback_port`, add that at the top level.
3. **`.cursor/mcp.json`** — add an entry under `mcpServers`. stdio needs an explicit `"type": "stdio"` plus `command`/`args`. HTTP entries are bare `{"url": "..."}` — do not include `type: "http"` or an `oauth` block (Cursor handles OAuth through its own UI with a fixed redirect URI).

Worked example: the `slack` entry across all three files shows the http + OAuth shape; the `snowflake` entry shows stdio.

After editing, run `uv run pytest -q`. The consistency test (`tests/test_mcp_configs_consistent.py`) fails if the three files disagree on the set of server names.
