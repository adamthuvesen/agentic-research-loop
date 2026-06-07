# agentic-research-loop program

This repo supports cases that may start lightweight and later
escalate into bounded autonomous work.

## Starting cases

- From the repo root, invoke the CLI via `uv run research ...`.
- The normal entrypoint is the `/research-spec` skill, which discovers sources, designs hypotheses and research threads, and presents the spec for human confirmation before scaffolding.
- After confirmation, the skill scaffolds the workspace via `uv run research init <slug> --template <template> --mode <mode>` and enriches the brief, plan, and notes with the researched content.
- To run the case: `uv run research run <case-id> --max-cycles 10` (uses the **Claude** runner by default). Use `--runner codex` to use the Codex CLI instead.
- `uv run research plan <case-id>` is optional, but useful when the framing needs a clearer durable plan before running cycles (same `--runner` options as `run`).
- `uv run research status <case-id>` is the quick way to inspect the current answer and progress.

## Operating rules

- Stay read-only with external systems.
- Prefer evidence over speculation.
- Keep durable conclusions and freshness caveats visible to humans.
- Write findings, reasoning, and conclusions to notes.md and report.md.
- Do not mutate `brief.md` during autonomous loops unless explicitly asked.
- For Snowflake work, follow the repo's `AGENTS.md` rule: use the Snowflake MCP server
  rather than improvised querying.
- For other warehouses, enable the matching bundle — **BigQuery**, **Postgres**, or
  **DuckDB** (`examples/sources/<name>/`). Treat them like Snowflake: discover objects
  live, query SELECT-only, stay read-only.
- Use Notion MCP for curated context, internal documentation, live workspace pages, databases, and discussions.
- Use Confluence (enable `examples/sources/confluence/`) for wiki spaces, runbooks, RFCs, and curated internal docs — complements Notion.
- Use Slack when the question depends on recent decisions, incident threads, or informal context that has not landed in docs yet.
- Use Linear when the question depends on issue state, project progress, cycle planning, or ownership context.
- Use GitHub (enable `examples/sources/github/`) when the question depends on code, pull requests, commits, or who changed what — strong for engineering root-cause.
- Use Jira (enable `examples/sources/jira/`) when work is tracked there instead of Linear — issue state, projects, and ownership.
- Use Sentry or Datadog (enable `examples/sources/sentry/` or `examples/sources/datadog/`) for incident, error, and performance root-cause — Sentry for errors, events, stack traces, and releases; Datadog for metrics, monitors, logs, traces, and incidents.
- Use Google Search Console (GSC) for organic search traffic, query performance,
  CTR, impressions, and ranking trends. **Default:** query GSC-shaped data in your **warehouse** (Snowflake or BigQuery)
  (e.g. the GSC-synced staging schema, or the GSC BigQuery bulk export).
  **Fallback:** `research gsc` CLI for fresher data, sync lag, or API-only dimensions
  (e.g. `research gsc --start-date 2026-03-01 --end-date 2026-04-06 --dimensions query`).
- Use Google Analytics 4 (GA4) for site analytics — page views, sessions, users,
  engagement, and conversions. Query via the official GA4 MCP server (enable the
  `examples/sources/ga4/` bundle); read-only via the `analytics.readonly` scope.
- Use product analytics — **PostHog** (`examples/sources/posthog/`, the read-only default), or **Amplitude** / **Mixpanel** (read+write servers; read-only depends on a minimal-role account — see setup) — for funnels, retention, activation, and feature-adoption questions; complements GA4 (web traffic).
- Use revenue/CRM sources — **Stripe** (`examples/sources/stripe/`, billing/MRR/churn/disputes, provably read-only via a restricted key), and **HubSpot** or **Salesforce** (`examples/sources/hubspot/` / `salesforce/`, deals/pipeline/accounts) — for "why did revenue, churn, or pipeline move." Use read-only credentials (Stripe restricted key / HubSpot read scopes / Salesforce read-only permission set + pinned toolsets).
- Use web tools when the explanation depends on external context.
- If Confidence MCP is enabled in the sources registry, treat it as a primary
  source for rollout and experiment questions.
- Use LaunchDarkly or Statsig (enable `examples/sources/launchdarkly/` or `examples/sources/statsig/`) for feature-flag and experiment causation — flag/gate rollout timing, targeting changes, audit history, and experiment results. Use a read-only credential (LaunchDarkly Reader role / Statsig `omni_read_only` key).
- If local context folders are present in the sources registry, search them
  before broad doc exploration when they are relevant.

## Research modes

- `quick`: synthesize a first pass and leave behind a reproducible workspace.
- `guided`: work collaboratively with humans and keep the machine state in sync.
- `autonomous`: make meaningful progress each cycle, write up results, stop
  when done.

## Artifact expectations

- `brief.md` captures the question, scope, source plan, freshness needs, and
  success criteria. Protected — do not modify during cycles.
- `notes.md` is the research cockpit. It stores working theory, a lightweight
  hypothesis ledger, evidence log, dead ends, open questions, and active leads.
- `plan.md` stores the durable research plan.
- `report.md` holds the best current business answer.
- `status.md` is the quick answer-first summary for humans.
- `state/progress.json` stores minimal lifecycle state: `status`, `cycle_count`,
  `consecutive_no_progress_cycles`, `consecutive_failures`,
  `pending_challenge_cycle`, `last_challenge_outcome`, and `stop_reason`. The
  runtime manages all fields except `status` which the agent may set to
  `"complete"`.
- `state/findings.json` is optional and appears when structured findings are
  gathered or explicitly logged. When present, it is validated before publish.
- `state/sources.json` stores the source registry for the case.

## Planning

- If `plan.md` is blank when the first cycle starts, the loop runs a dedicated planning step before the first case cycle.
- `uv run research plan <case-id>` can also be triggered manually.
- For autonomous root-cause cases, the plan enforces a stronger design contract: each thread must include a discriminating test, rival explanation, completion threshold, and required cross-checks.

## Hypothesis-led cycles

Each autonomous cycle should pick one or two active hypotheses, leads, or plan
threads before source work begins. The agent should name the strongest rival
explanation, define what evidence would change confidence, gather the sharpest
available context or data, then update `notes.md` with what moved: supported,
weakened, rejected, pivoted, or newly discovered.

This is a research notebook, not a compliance checklist. Use the hypothesis
ledger and evidence log to preserve thinking that helps the next cycle start
smarter.

## Steering between cycles

Adjust direction by editing `notes.md` or `plan.md` before the next `uv run research run` / `uv run research resume`. Keep `brief.md` stable once an autonomous case is underway unless you are explicitly reframing the question.

## Stall and failure limits

- Three consecutive no-progress cycles stop the case (`stalled`).
- Three consecutive failures (timeout, missing completion marker, non-zero exit) also stop the case.
- Each cycle gets up to 2 attempts (one attempt + one retry with a nudge explaining the failure).

## Challenge cycle

Before an autonomous case can complete, it must pass a mandatory adversarial challenge cycle:

1. The agent emits `<promise>CASE_COMPLETE</promise>`.
2. Instead of closing, the runtime queues a challenge cycle.
3. The challenge cycle reviews the report and must answer:
   - What is the strongest competing explanation?
   - What is the weakest-supported important claim?
   - What is the most fragile source, freshness, or caveat dependency?
   - Are these resolved or still open?
4. If unresolved material risks remain, the case reopens for more research cycles.
5. Only when the challenge passes does the case truly complete.

## Autonomous cycle finish contract

At the end of a cycle:

- update `notes.md` and `report.md` with your findings and reasoning
- leave `brief.md` unchanged
- emit exactly one completion marker:
  - `<promise>CYCLE_DONE</promise>` — when the case should continue
  - `<promise>CASE_COMPLETE</promise>` — when the case is genuinely complete
