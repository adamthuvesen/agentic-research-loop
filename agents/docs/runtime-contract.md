# Runtime Contract

All source access is agent-executed. The agent handles research strategy,
source selection, and synthesis directly using MCP tools.

## Agent-executed research

The agent accesses all sources via MCP tools and APIs. Web tools, `research gsc`,
and local context are built in; the other sources below are **opt-in bundles** —
wire one with `research source enable <name>` (see `examples/sources/`):

- Snowflake
- Notion MCP
- Slack
- Linear
- Confidence MCP
- Google Search Console — **default:** Snowflake (GSC-synced tables; use the Snowflake MCP server and warehouse discovery). **Fallback:** `research gsc` CLI when you need fresher data than the sync, suspect Fivetran lag, or API-only dimensions
- Google Analytics 4 — official GA4 MCP server (enable the `examples/sources/ga4/` bundle)
- web tools
- local context
- higher-level synthesis and source strategy

These flows should land in the same artifacts:

- `notes.md`
- `report.md`
- `state/sources.json`

They may also update `state/findings.json` when the case is maintaining
structured findings. That file is optional, but when present it must validate
against the optional findings schema below.

Legacy one-off state files from older layouts (`source_activity.json`, `observations.json`, etc.) are not used; durable machine state is `state/progress.json`, `state/sources.json`, and `state/status.json`.

`state/status.json` stores the canonical case kind: `mode` and `template` (written at init). The runtime falls back to parsing `brief.md` metadata only when `template` is missing on older cases.

## Cycle execution

Each cycle runs with up to 2 attempts (one base attempt + one retry with a
nudge explaining the failure reason). The agent must emit exactly one completion
marker at the end of each cycle:

- `<promise>CYCLE_DONE</promise>` — research should continue
- `<promise>CASE_COMPLETE</promise>` — research is genuinely complete

Normal research cycles are hypothesis-led. The agent chooses one or two active
hypotheses, leads, or plan threads; names the rival explanation and
confidence-changing evidence; performs source work; and records hypothesis
movement, evidence, caveats, dead ends, and next checks in `notes.md`.

## Progress detection

Progress is measured by hashing `notes.md` and `report.md` before and after
each cycle. Only visible artifact changes count — updating `state/*.json`
alone does not register as progress. Changes to `plan.md` alone also do not
register as progress (intentional: plan updates are bookkeeping, not cycle
evidence movement).

Three consecutive no-progress cycles or three consecutive failures stop the
research automatically.

## Planning step

If `plan.md` is blank when the first cycle starts, the loop runs a dedicated
planning step before research begins. For autonomous root-cause
cases, the plan enforces a stronger design contract: discriminating
tests, rival explanations, completion thresholds, and required cross-checks.

## Challenge cycle

Before an autonomous case can complete, it must survive a mandatory
challenge cycle:

1. Agent emits `<promise>CASE_COMPLETE</promise>`.
2. Runtime queues a challenge cycle instead of closing.
3. Challenge must identify: strongest competing explanation, weakest-supported
  claim, most fragile dependency, and whether these are resolved.
4. If unresolved material risks remain, the case reopens.
5. Only when the challenge passes does the case truly complete.

## Artifact protection

- `brief.md` is read-only during autonomous loops. The runtime backs it up
before each cycle and restores it if modified.
- Mutable artifacts (`notes.md`, `report.md`, `plan.md`, `state/sources.json`,
`state/progress.json`, `state/status.json`, `status.md`) are backed up before
each cycle and restored on failure.
- Malformed optional machine-history files such as cycle summaries should not
prevent status rendering, prompt rendering, or publish from inspecting an
otherwise valid case. Invalid required state is still surfaced by validation.

## Optional findings schema

`state/findings.json` is a flat JSON list. Each entry is a JSON object with at
minimum:

- `id` — unique non-empty string (e.g. `"F1"`, `"F2"`)
- `summary` — non-empty string describing the finding

Additional fields (e.g. `confidence`, `source`) are allowed but not required.

`research validate` and `research publish` enforce this shape when the file
exists. Missing `state/findings.json` is valid.

## Shared rule

No matter where the work happens, the case should leave one coherent,
reproducible record behind.
