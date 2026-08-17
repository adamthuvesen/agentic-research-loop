# AGENTS.md

This repo is `agentic-research-loop`, a research kit for bounded investigations
run inside a native agent goal.

User-level guidance (tone, principles, git etiquette) lives in the user's own
config and is *not* duplicated here. This file is for project-specific facts.

## Read the docs first

Before working in an area, read the matching doc:

- **Operating model and research contract** → [program.md](program.md)
- **CLI surface (`research ...`)** → [README.md](README.md)
- **Architecture and validation** → [.agents/docs/architecture.md](.agents/docs/architecture.md)
- **Why there is no runtime** → [.agents/docs/decisions/native-goals.md](.agents/docs/decisions/native-goals.md)
- **First-time setup / source bundles** → [.agents/docs/setup.md](.agents/docs/setup.md)

If a doc disagrees with code, fix the doc in the same change.

## READ-ONLY RULE

This repo is a **read/search-only consumer** of all external systems.

Every source bundle is read-only by design. If a workflow seems to require
writing to an external system, stop and ask the user.

## Native goals

- Use Claude Code or Codex `/goal` for autonomous execution.
- Do not add an agent subprocess runner, a custom continuation loop, cycle state,
  completion markers, a permission bypass flag, or an Agent SDK.
- Generate the canonical command with `uv run research goal <case>`.
- The native goal owns persistence, pause, resume, and continuation.
- The repo owns framing, source access, artifacts, safety, and validation.
- Every path in the generated contract is absolute. Keep it that way — a goal
  given relative paths can write a correct answer into the wrong directory.

## Starting research

- The primary path starts inside Claude Code or Codex with a native `/goal` that
  names `research-goal`.
- When a goal is active, scaffold with the CLI, adopt the generated contract, and
  complete the investigation in the same session. Do not stop after scaffolding
  or ask the user to submit a nested goal.
- Run internal CLI commands from the repo root with `uv run research ...`.
- Use `research-spec` when definitions, scope, source choice, confounders, or
  completion criteria need targeted discovery first.
- Do not ask for confirmation when the question is already bounded. Ask one
  focused question only when a missing choice would materially change the case.

## Shared skills

Canonical repo skills live in `.agents/skills/`.

- Claude Code loads the committed `.claude/skills` symlink.
- Codex and Cursor read `.agents/skills/` directly with a local, uncommitted symlink.
- Do not duplicate skill content under client-specific directories.

## Sources

Only web search is built in. Everything else is an opt-in bundle under
`examples/sources/`, wired with `research source enable <name>`. `.mcp.json`
ships neutral; `.codex/config.toml` and `.cursor/mcp.json` are local-only.

Query a warehouse through its bundle's MCP server, never an improvised
connection, and never write. Snowflake's read-only rule is the committed SQL
allowlist in `config/snowflake-mcp-tools.yaml` (SELECT/DESCRIBE/SHOW/USE only).
Other warehouses enforce read-only through their own bundle mechanism — see
`examples/sources/<name>/SETUP.md`. Each bundle is self-contained.

## Case contract

- Treat `brief.md` as binding; keep it stable after the goal starts unless the
  user reframes the case.
- Keep working evidence and rejected leads in `notes.md`, the usable answer and
  reconciliation in `report.md`, every query in `queries.sql`, and every object in
  `source-objects.md`. Use `plan.md` only when sequencing helps.
- Ignore legacy `state/` directories. New work does not create or update them.
- Before finishing, delegate the final challenge to an independent subagent that
  did not conduct the research. Record the reviewer, strongest competing
  explanation, weakest-supported claim, most fragile dependency, and resolution
  under `## Final Challenge` in `notes.md`. Self-review fails validation.
- Run `uv run research validate <case> --strict`, fix every failure, and surface
  the result in the final response.

## Report section headers

Validation parses these headings. Do not rename them casually:

- `Executive Summary`, `Evidence`, `Reconciliation`, `Rejected Leads`,
  `Risks And Caveats` in `report.md`
- `Evidence Log` and `Final Challenge` in `notes.md`
- `Question`, `Scope` (carrying the `Research shape` line), and
  `Source Constraints` in `brief.md`
