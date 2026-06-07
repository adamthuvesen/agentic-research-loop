# Agentic Research Loop

Autonomous research engine for business questions.

Ask a question, point it at your sources, and let it run. It creates a case
spec, runs bounded agentic cycles, and produces a research report with findings.
It uses the same "keep going until the job is done" loop pattern as Ralph
Wiggum, with autoresearch-style reasoning at each step.

The repo ships with a **fully offline demo** — a deterministic runner over
synthetic data — so you can see the whole loop work end-to-end with no LLM, no
network, and no credentials.

## Quick start (offline demo)

```bash
uv sync --dev

# Scaffold a case that investigates the bundled synthetic dataset
uv run research init registration-drop --template root-cause --mode autonomous \
  --context-path examples/local-sources

# Run it with the offline demo runner (no API keys needed)
uv run research run <slug> --runner demo --max-cycles 6
```

`<slug>` is the dated case name printed by `init` (e.g. `2026-03-21-registration-drop`).

The run goes `plan → explore → build evidence → conclude → challenge cycle →
complete`. The figures in the report are computed from the bundled CSV, so the
output reflects the data rather than canned text.

Prefer not to run anything? The committed result lives in
[`examples/demo-registration-drop/`](examples/demo-registration-drop/) — read
[`report.md`](examples/demo-registration-drop/report.md), or open
[`replay.html`](examples/demo-registration-drop/replay.html) for the whole case
on one page (`uv run python viz/generate.py <case_dir>`).

## How it works

1. **Spec** — design the question into hypotheses and a source plan (the
   `/research-spec` skill does this with a real agent runner; see below).
2. **Scaffold** (`research init`) — creates a workspace under
   `research/<date>-<slug>/` with a brief, plan, and machine state.
3. **Run** (`research run`) — the runner investigates autonomously, updating
   artifacts each cycle until the case is done or stalls.

Each cycle must make visible progress in `notes.md` or `report.md`. Three
consecutive no-progress cycles stop the run. When the runner believes a
root-cause case is complete, a mandatory adversarial **challenge cycle**
stress-tests the conclusions before the case can close.

## Runners

A runner is any command that takes the cycle prompt on stdin and emits exactly
one completion marker — `<promise>CYCLE_DONE</promise>` or
`<promise>CASE_COMPLETE</promise>`. Built-in runners (`config/runners/`):

| Runner         | What it is                                                                              |
| -------------- | -------------------------------------------------------------------------------------- |
| `demo`         | Offline, deterministic reference runner. No LLM, no network.                           |
| `claude-local` | Real Claude Code agent, **local files only** — no MCP, no setup beyond your Claude login. |
| `claude`       | Claude Code CLI with your full MCP source stack.                                       |
| `codex`        | Codex CLI (`codex exec`) with your full MCP source stack.                              |

Point `--runner` at the one you want. `demo` shows the loop with zero setup;
`claude-local` runs a **real** agentic investigation over the bundled data; `claude`
and `codex` do real investigations against your live sources once configured.

## Run it for real with Claude (local, no setup)

If you have Claude Code installed and signed in, you can watch a real agent run
the loop over the bundled synthetic data — no MCP servers, no API keys, no
external sources:

```bash
uv run research init registration-drop --template root-cause --mode autonomous \
  --context-path examples/local-sources
uv run research run <slug> --runner claude-local --max-cycles 8
```

The `claude-local` runner pins Claude Code to local file tools only
(`--strict-mcp-config` with an empty MCP config), so the agent reads the CSV and
context notes, forms and tests hypotheses, writes `notes.md`/`report.md`, and
runs the mandatory challenge cycle — entirely on your machine. Swap to `--runner
claude` once you've wired up real sources (see Setup).

A committed snapshot of a real run lives in
[`examples/claude-local-registration-drop/`](examples/claude-local-registration-drop/)
— the agent decomposed the drop into two effects, computed a counterfactual
impact split, and capped its own confidence in the challenge cycle.

## Sources

With a real agent runner, cases pull from whatever sources you wire up. Every
source is **read-only**, and each declares *how* read-only is enforced — a config
flag, an OAuth scope, or, where only the credential can guarantee it, a read-only
account. A test (`tests/test_readonly_contract.py`) checks that the shipped config
actually carries the declared mechanism.

**Built in** (no MCP server needed — always available):

| Source          | What it provides                                                       | Read-only |
| --------------- | ---------------------------------------------------------------------- | --------- |
| **GSC**         | Organic search — warehouse-synced default; `research gsc` CLI fallback | `webmasters.readonly` scope |
| **Web**         | External context                                                       | native read-only tool |
| **Local files** | CSVs, markdown, exports scoped to the question                         | read-only |

**Opt-in bundles** ([`examples/sources/<name>/`](examples/sources/) — `research source enable <name>`):

| Source       | What it provides                              | Read-only mechanism |
| ------------ | --------------------------------------------- | ------------------- |
| **Notion**   | Workspace pages, databases, discussions       | read account (credential-only) |
| **Slack**    | Decisions, thread context, informal signals   | read account (credential-only) |
| **Linear**   | Issue state, project progress, ownership      | read account (credential-only) |
| **Confidence** | Experiments, flags, rollouts, decision history | read account (credential-only) |
| **Snowflake** | Live metric evidence                          | SQL statement allowlist |
| **GitHub**   | Issues, PRs, commits, code search             | `/readonly` endpoint (strict filter) |
| **Jira**     | Issue state, projects, ownership              | view-only account (credential-only) |
| **Postgres** | Application-DB / live metric evidence         | `--access-mode=restricted` |
| **DuckDB**   | Local files (CSV/Parquet), embedded analytics | read-only by default |
| **BigQuery** | Warehouse metrics (incl. GA4/GSC exports)     | IAM: Data Viewer + Job User |
| **GA4**      | Site analytics — sessions, users, conversions | `analytics.readonly` scope |
| **Sentry**   | Errors, events, stack traces, releases        | read-scoped token (`*:read`) |
| **Datadog**  | Metrics, monitors, logs, traces, incidents    | Datadog Read-Only Role (credential-only) |
| **Confluence** | Wiki spaces, pages, curated docs            | view-only account (credential-only) |
| **PostHog**  | Product analytics — funnels, retention, HogQL, flags | read-scoped API key (`*:read`) |
| **Amplitude** | Product analytics — charts, cohorts, experiments   | Viewer account (credential-only) \* |
| **Mixpanel** | Product analytics — funnels, retention, JQL          | Consumer account (credential-only) \* |
| **LaunchDarkly** | Feature flags, rollout timing, audit log, experiments | Reader-role token + `--scope read` |
| **Statsig**  | Feature gates, experiments, results                  | `omni_read_only` Console key |
| **Stripe**   | Revenue — subscriptions, invoices, churn, disputes   | restricted read-only key (`rk_`) |
| **HubSpot**  | CRM — deals, pipeline, contacts, companies           | read-scope OAuth grant (credential-only) \* |
| **Salesforce** | CRM — opportunities, accounts, pipeline (SOQL)     | `--toolsets data,users` + read-only perm set |
| **Databricks** | Warehouse over Unity Catalog (Genie NL/SQL)        | Genie endpoint — read-only by design |
| **Redshift**   | Warehouse — clusters + serverless (SQL)            | engine read-only (`BEGIN READ ONLY`) |

\* Amplitude, Mixpanel, and HubSpot MCP servers are read+write with no read-only flag — the
account role is the only guardrail (and the autonomous runner skips permission
prompts); see their `SETUP.md`. PostHog enforces read-only in the API key itself.

The three committed MCP configs (`.mcp.json`, `.codex/config.toml`,
`.cursor/mcp.json`) **ship neutral** — no servers wired by default, so a clone carries
nobody's stack. Every source is an opt-in bundle; `uv run research source enable <name>`
wires one into all three configs locally (`research source list` / `disable` too).
Source routing per case is stored in `state/sources.json`.

Two extension points: pass `--local-only` to `init` to disable every external
source and investigate just `--context-path` files, and enable any bundle with
`uv run research source enable <name>` (`research source list` / `disable` too), or
copy `config/sources.json.example` for a custom one.

## Research workspace

Each case lives in `research/<date>-<slug>/`.

Human-facing artifacts:

- `brief.md` — question, scope, source plan, success criteria
- `plan.md` — research plan (threads with discriminating tests)
- `notes.md` — working theory, evidence, dead ends, open questions
- `report.md` — best current answer
- `status.md` — answer-first human summary

Machine state under `state/`:

- `progress.json` — lifecycle state, cycle/failure counts, challenge state
- `sources.json` — enabled sources, hints, local context paths
- `cycles/*` — per-cycle prompts, outputs, and summaries

## Modes

| Mode         | Use when                                      |
| ------------ | --------------------------------------------- |
| `autonomous` | Multi-cycle root-cause work, runner runs solo |
| `guided`     | Human-in-the-loop, no long-running loops      |
| `quick`      | Single-pass answer scaffold                   |

## Using a real agent runner

To run live investigations with Claude Code or Codex against your own sources,
follow **[`agents/docs/setup.md`](agents/docs/setup.md)** for MCP/OAuth and
(optionally) a Snowflake connection. The `/research-spec` skill
(`agents/skills/research-spec/`) discovers sources and designs hypotheses before
scaffolding. The `research gsc` CLI reads `GSC_SITE` and `GCP_QUOTA_PROJECT`
from the environment; GA4 is served by the official GA4 MCP (`examples/sources/ga4/`).

## Development

```bash
uv sync --dev
uv run pre-commit install
uv run ruff check . && uv run ruff format --check . && uv run pytest -q
```

## Documentation

- **[Architecture](agents/docs/architecture.md)** — components and lifecycle
- **[Runtime contract](agents/docs/runtime-contract.md)** — loop, progress, challenge cycle
- **[Runtime playbook](agents/docs/runtime-playbook.md)** — practical runner behavior
- **[Setup](agents/docs/setup.md)** — MCP, Snowflake, verification

## License

[Apache 2.0](LICENSE) © 2026 Adam Thuvesen
