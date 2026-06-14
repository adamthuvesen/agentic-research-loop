# Agentic Research Loop

A small runner for bounded research work. Give it a question and a set of
read-only sources: it creates a case workspace, runs investigation cycles, and
keeps the working notes and report visible as it goes.

The repo includes a fully offline demo over synthetic data, so you can try the
loop without API keys or external services.

## Quick start (offline demo)

```bash
uv sync --dev

# Scaffold a case that investigates the bundled synthetic dataset
uv run research init export-reliability --template root-cause --mode autonomous \
  --context-path examples/local-sources --local-only

# Run it with the offline demo runner (no API keys needed)
uv run research run <slug> --runner demo --max-cycles 6
```

`<slug>` is the dated case name printed by `init` (e.g. `2026-06-07-export-reliability`).

The run plans, explores, builds evidence, concludes, and then stress-tests the
answer in a challenge cycle. The report's figures are computed from the bundled
CSV. Prefer not to run anything? The committed result lives in
[`examples/demo-export-reliability/`](examples/demo-export-reliability/) — read
[`report.md`](examples/demo-export-reliability/report.md) or open
[`replay.html`](examples/demo-export-reliability/replay.html)
(`uv run python viz/generate.py <case_dir>`).

## How it works

1. **Spec** - design the question into hypotheses and a source plan (the
   `/research-spec` skill does this with a real agent runner; see below).
2. **Scaffold** (`research init`) - creates a workspace under
   `research/<date>-<slug>/` with a brief, plan, and machine state.
3. **Run** (`research run`) - the runner investigates, updating
   artifacts each cycle until the case is done or stalls.

Each cycle must make visible progress in `notes.md` or `report.md`. Three
consecutive no-progress cycles stop the run. When the runner believes a
root-cause case is complete, a mandatory **challenge cycle**
stress-tests the conclusions before the case can close.

## Runners

A runner is any command that takes the cycle prompt on stdin and emits exactly
one completion marker — `<promise>CYCLE_DONE</promise>` or
`<promise>CASE_COMPLETE</promise>`. Built-in runners (`config/runners/`):

| Runner         | What it is                                                                              |
| -------------- | -------------------------------------------------------------------------------------- |
| `demo`         | Offline, deterministic reference runner. No model, no network.                         |
| `claude-local` | Real Claude Code agent, **local files only** — no MCP, no setup beyond your Claude login. |
| `claude`       | Claude Code CLI with your full MCP source stack.                                       |
| `codex`        | Codex CLI (`codex exec`) with your full MCP source stack.                              |

To run the loop with a **real agent** and still zero setup (just Claude Code
installed and signed in), re-run the quick start with
`--runner claude-local --max-cycles 8`. It pins Claude Code to local file tools
(`--strict-mcp-config` with an empty MCP config), so the agent investigates the
bundled data, writes `notes.md`/`report.md`, and runs the challenge cycle
entirely on your machine — see
[`examples/claude-local-export-reliability/`](examples/claude-local-export-reliability/)
for the worked example. `claude` and `codex` run against your live sources once
configured (see below).

## Sources

With a real agent runner, cases pull from the sources you wire up. Every shipped
source bundle is **read-only**, and each declares how that is enforced: a config
flag, an OAuth scope, SQL allowlisting, or a read-only credential. A test
(`tests/test_readonly_contract.py`) checks that the shipped config carries the
declared mechanism.

**Built in** (no MCP server needed):

| Source  | What it provides | Read-only |
| ------- | ---------------- | --------- |
| **Web** | External context | native read-only tool |

**Local files** are attached per case at invocation
with `--context-path` (CSVs, markdown, exports scoped to the question, read-only).

**Opt-in bundles** live under [`examples/sources/`](examples/sources/) and can
be enabled with `uv run research source enable <name>`. They cover:

- Work context: Slack, Notion, Linear, Jira, GitHub, Confluence, Google Drive,
  Microsoft 365, Azure DevOps
- Warehouses and databases: Snowflake, BigQuery, Postgres, DuckDB, Databricks,
  Redshift, Azure
- Product, web, and experiment data: GA4, GSC, PostHog, Amplitude, Mixpanel,
  Confidence, LaunchDarkly, Statsig
- Observability and revenue: Sentry, Datadog, Stripe, HubSpot, Salesforce

Some upstream MCP servers are read+write unless you provide a read-only account,
PAT, or scoped key. The setup notes for each bundle call that out explicitly;
the autonomous runner skips permission prompts, so credential scope matters.

The committed MCP config (`.mcp.json`) **ships neutral** — no servers wired by
default. `uv run research source enable <name>` wires a bundle into `.mcp.json`
and the local (uncommitted) `.codex/config.toml` and `.cursor/mcp.json`
(`research source list` / `disable` too); per-case routing lives in
`state/sources.json`. Pass `--local-only` to `init` to investigate just
`--context-path` files, or copy `config/sources.json.example` for a custom
source registry.

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

For live investigations with Claude Code or Codex against your own sources,
follow **[`.agents/docs/setup.md`](.agents/docs/setup.md)** (MCP/OAuth,
optional Snowflake). Start cases with the `/research-spec` skill
(`.agents/skills/research-spec/`) — it discovers sources and designs hypotheses
before scaffolding.

## Development

```bash
uv sync --dev
uv run pre-commit install
uv run ruff check . && uv run ruff format --check . && uv run pytest -q
```

## Documentation

- **[Architecture](.agents/docs/architecture.md)** — components and lifecycle
- **[Runtime contract](.agents/docs/runtime-contract.md)** — loop, progress, challenge cycle
- **[Runtime playbook](.agents/docs/runtime-playbook.md)** — practical runner behavior
- **[Setup](.agents/docs/setup.md)** — MCP, Snowflake, verification

## License

[Apache 2.0](LICENSE) © 2026 Adam Thuvesen
