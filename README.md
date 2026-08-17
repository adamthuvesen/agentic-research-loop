# Agentic Research Loop

![License](https://img.shields.io/github/license/adamthuvesen/agentic-research-loop) ![Python](https://img.shields.io/badge/python-3.11%2B-blue)

A research kit for bounded investigations. Give it a question and a set of
read-only sources, and it creates a workspace, frames the case, and validates the
evidence the investigation leaves behind.

Execution runs inside your agent client's native `/goal`. The client owns
persistence and continuation; this repo owns the research contract, read-only
source access, durable artifacts, and deterministic validation. There is no
subprocess runner and no second agent loop — see
[the decision record](.agents/docs/decisions/native-goals.md) for why.

## Quick start (no API keys, no MCP)

The repo ships a synthetic dataset, so the first run needs nothing but a client
you are already signed in to.

```bash
uv sync --dev

uv run research init export-reliability --template root-cause \
  --question "Why did the weekly batch-export success rate drop in March 2026?" \
  --local-only --context-path examples/local-sources

uv run research goal <slug>
```

`<slug>` is the dated case name printed by `init` (e.g.
`2026-06-07-export-reliability`). The last command prints a `/goal ...` block.
Paste it into Claude Code or Codex from the repo root and the investigation runs
to completion in that session, ending with strict validation.

Prefer not to run anything? The committed result of this case lives in
[`examples/demo-export-reliability/`](examples/demo-export-reliability/) — start
with [`report.md`](examples/demo-export-reliability/report.md).

## Run inside Claude Code or Codex

Open either client from the repository root and submit one native goal.

Claude Code:

```text
/goal Use the research-goal skill to investigate:

Why did the weekly batch-export success rate drop in March 2026? Use only the local files under examples/local-sources. Stop when the largest cause is named with reconciling numbers and strict validation passes.
```

Codex:

```text
/goal Use $research-goal to investigate:

Why did the weekly batch-export success rate drop in March 2026? Use only the local files under examples/local-sources. Stop when the largest cause is named with reconciling numbers and strict validation passes.
```

The skill scaffolds the case, adopts the generated contract, performs the
research, and validates the artifacts in the same session.

For an ambiguous, causal, cross-source, or high-stakes question, name
`research-spec` instead. It runs targeted discovery and designs falsifiable
hypotheses before handing the case to the goal.

## Case artifacts

Each case lives in `research/<date>-<slug>/`:

- `brief.md` — binding question, scope, source constraints, success criteria
- `notes.md` — hypotheses, evidence log, dead ends, open questions, final challenge
- `report.md` — the answer, evidence, reconciliation, rejected leads, caveats
- `queries.sql` — every query used, or an explicit reason none was
- `source-objects.md` — fully qualified objects or stable URLs, with access dates
- `plan.md` — optional, when sequencing helps

`brief.md` stays stable once the goal starts unless you explicitly reframe the
case. There is no machine state directory; older cases carrying one remain
readable and validation ignores it.

## The completion gate

A case is done when `research validate --strict` passes. It requires a specific
question, a substantive report with no placeholder sections, at least one
complete evidence record, concrete source objects, preserved read-only SQL (or a
stated reason there is none), and a completed independent challenge.

That last one is the sharp check. Before finishing, the goal delegates a review
to a **subagent that did not conduct the research**, which names the strongest
competing explanation, the weakest-supported claim, and the most fragile
dependency. Naming yourself as the reviewer fails validation. So does leaving the
resolution open — though `unresolved because <reason>` passes, because disclosing
an objection you could not settle is honest and hiding it is not.

## Sources

Every shipped source bundle is **read-only**, and each declares how that is
enforced: a config flag, an OAuth scope, SQL allowlisting, or a read-only
credential. [`tests/test_readonly_contract.py`](tests/test_readonly_contract.py)
checks that the shipped config carries the declared mechanism.

**Built in:** web search, for external context.

**Local files** attach per case with `--context-path` (CSVs, markdown, exports
scoped to the question, read-only).

**Opt-in bundles** live under [`examples/sources/`](examples/sources/) and enable
with `uv run research source enable <name>`:

- Work context: Slack, Notion, Linear, Jira, GitHub, Confluence, Google Drive,
  Microsoft 365, Azure DevOps
- Warehouses and databases: Snowflake, BigQuery, Postgres, DuckDB, Databricks,
  Redshift, Azure
- Product, web, and experiment data: GA4, GSC, PostHog, Amplitude, Mixpanel,
  Confidence, LaunchDarkly, Statsig
- Observability and revenue: Sentry, Datadog, Stripe, HubSpot, Salesforce

Some upstream MCP servers are read+write unless you provide a read-only account,
PAT, or scoped key. Each bundle's setup notes call that out explicitly.

`.mcp.json` **ships neutral** — no servers wired by default.
`research source enable <name>` wires a bundle into `.mcp.json` and the local
(uncommitted) `.codex/config.toml` and `.cursor/mcp.json`; `source list` and
`source disable` do the obvious things. Which sources a case may use is recorded
in its brief and read back into the goal contract. Copy
`config/sources.json.example` for a custom registry.

## CLI

The skills call these internally. They are also useful for debugging or manual
preparation.

```bash
uv run research init --help
uv run research goal <case>            # print the /goal contract
uv run research validate <case>        # structure + read-only SQL
uv run research validate <case> --strict   # the completion gate
uv run research source list

# Read-only API fallback for data not synced to a warehouse
uv run research gsc --start-date 2026-07-01 --end-date 2026-07-31 --dimensions query,page
```

## Setup

For live investigations against your own sources, follow
[`.agents/docs/setup.md`](.agents/docs/setup.md), then:

```bash
./scripts/setup-dev.sh
uv run python scripts/check_agent_setup.py
```

The checker verifies the goal prerequisites and exactly the bundles you enabled.
Codex needs `[features] goals = true`, which `research source enable` writes into
your local `.codex/config.toml`.

Research quality tracks model strength here — the goal does the reasoning. A
frontier model at high reasoning effort is worth the tokens for a real case.

## Development

```bash
uv sync --dev
uv run pre-commit install
uv run ruff check . && uv run ruff format --check . && uv run pytest -q
```

Client goal behavior is an external dependency this repo cannot pin, so
[`evals/native-goal/`](evals/native-goal/README.md) holds a blind, keyless canary
that scores a full unattended run against the bundled dataset.

## Documentation

- **[Architecture](.agents/docs/architecture.md)**: components, contract, validation
- **[Program](program.md)**: research contract and source selection
- **[Decision record](.agents/docs/decisions/native-goals.md)**: why there is no runtime
- **[Setup](.agents/docs/setup.md)**: MCP, credentials, verification

## License

[Apache 2.0](LICENSE) © 2026 Adam Thuvesen
