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
[`report.md`](examples/demo-registration-drop/report.md), including its
`## Challenge Review` section.

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

With a real agent runner, cases can pull from any sources you wire up through
MCP. The defaults the framework knows about:

| Source          | What it provides                               |
| --------------- | ---------------------------------------------- |
| **Notion**      | Workspace pages, databases, discussions        |
| **Slack**       | Decisions, thread context, informal signals    |
| **Linear**      | Issue state, project progress, ownership        |
| **Snowflake**   | Live metric evidence                           |
| **Confidence**  | Experiments, flags, rollouts, decision history |
| **GSC / GA4**   | Organic search and site analytics              |
| **Web**         | External context                               |
| **Local files** | CSVs, markdown, exports scoped to the question |

The three committed MCP configs (`.mcp.json`, `.codex/config.toml`,
`.cursor/mcp.json`) are the canonical, hand-maintained source of truth for their
respective tools — edit all three when adding or removing a server; a test flags
drift. Source routing per case is stored in `state/sources.json`.

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
scaffolding. The Google API helpers read `GSC_SITE`, `GA4_PROPERTY_ID`, and
`GCP_QUOTA_PROJECT` from the environment.

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

[MIT](LICENSE) © 2026 Adam Thuvesen
