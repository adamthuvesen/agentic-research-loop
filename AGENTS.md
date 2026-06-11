# AGENTS.md

This repo is `agentic-research-loop`, an autonomous case engine for bounded research cycles.

Start with `program.md` for the operating model, then use `README.md` for the CLI surface and `.agents/docs/runtime-contract.md` for the runtime contract.

## READ-ONLY RULE

This repo is a **read/search-only consumer** of all external systems.

Every source bundle is read-only by design. If a workflow seems to require writing to an external system, stop and ask the user.

## Core behavior

- Prefer agent judgment over deterministic choreography.
- Use the system for context, provenance, and safety, not for micromanaging the case.
- Let the agent decide which sources to use, what to validate next, and when the answer is good enough to stop.

## Shared Skills

Shared repo-local skills live in `.agents/skills/`. Treat that directory as the canonical source of truth.

After `git clone`, the **same tree** is wired into each tool via **committed symlinks** (no copy step):

- **Claude Code:** `.claude/skills` → `../.agents/skills`
- **Codex:** `.codex/skills` → `../.agents/skills`
- **Cursor:** `.cursor/skills` → `../.agents/skills`

Do not duplicate skill content under `.claude/`, `.codex/`, or `.cursor/`—extend `.agents/skills/` only.

## Warehouses

When a warehouse bundle is enabled, query it through its MCP server, not improvised connections — and never write. Snowflake's read-only is enforced by the committed SQL allowlist in `config/snowflake-mcp-tools.yaml` (SELECT/DESCRIBE/SHOW/USE only, pinned via `--service-config-file`); BigQuery, Postgres, Redshift, Databricks, and DuckDB each enforce read-only through their own bundle's mechanism (see `examples/sources/<name>/SETUP.md`). Each is self-contained — no dependency on any sibling repo.

## Research operating rules

- From the repo root, invoke the CLI via `uv run research ...`.
- The canonical way to start a case is the `/research-spec` skill, which discovers sources, designs hypotheses, and presents the spec for confirmation before scaffolding. Do not bypass this with ad-hoc `uv run research init` unless the user explicitly asks.
- Treat external systems as read-only. If a task appears to require writing to Slack, Notion, Linear, Confidence, or another external system, stop and ask the user.
- Keep `brief.md` stable once an autonomous case has started unless the user explicitly asks to reframe the case.
- During cycles, the visible progress signal is changes to `notes.md` or `report.md`. Updating only JSON state files does not count as progress.
- The autonomous loop stops after three consecutive no-progress cycles, so write visible reasoning and answer updates as you go.
- End each autonomous slice with exactly one marker:
  - `<promise>CYCLE_DONE</promise>` when more work is needed
  - `<promise>CASE_COMPLETE</promise>` when the case is actually complete

## Research design contract

Autonomous root-cause cases enforce a stronger design contract at planning time:

- Each high-priority hypothesis must include a **discriminating test**.
- Each plan thread must name the **strongest competing explanation** and the evidence to distinguish it.
- Each thread must define a **completion threshold** for when to mark it done, blocked, or pivoted.
- The brief and plan must surface known **confounders** and required **cross-source cross-checks**.

Validation (`research validate --strict`) enforces these requirements.

## Challenge cycle

Before an autonomous case can close, a mandatory challenge cycle stress-tests the conclusions:

- Identifies the strongest competing explanation
- Flags the weakest-supported claim and most fragile dependency
- Declares whether objections are resolved or still open
- If unresolved material risks remain, the case reopens for more cycles

Do not skip or shortcut the challenge cycle. The case only completes when the challenge passes.

## Steering

The `research feedback` command and `state/feedback.json` are removed. Steer by editing `notes.md` or `plan.md` between cycles. Keep `brief.md` stable once an autonomous case has started unless the user explicitly reframes the case.

## Artifact and publishing guardrails

- `state/findings.json` is optional. Do not assume it exists on a newly scaffolded research.
- When reading research state, prefer the repo's optional IO helpers for files that may not exist yet.
- If `state/findings.json` is used, each finding should include a valid `source_type` when possible — match it to a registered source key (see `research source list`). Publish derives each finding's freshness caveat from that source's caveat group, so any enabled source is recognized.
- Do not casually rename report section headers that publishing relies on. These headings have special meaning:
  - `Executive Summary`
  - `Conclusions` or `Conclusion`
  - `Rejected Leads`
  - `Risks And Caveats` or `Open Questions`
- In `notes.md`, keep the standard sections for `Working Theory`, `Dead Ends`, and `Open Questions` when they are relevant. The runtime and publish step mine those sections.
