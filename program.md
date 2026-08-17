# agentic-research-loop program

This repo prepares and validates research cases. A Claude Code or Codex native
`/goal` runs them.

## Ownership

The native goal owns:

- persistence across turns
- continuation until the completion condition is met
- pause, resume, and client session state
- tool use and research strategy

The repo owns:

- case framing and source constraints
- read-only source access
- durable evidence artifacts
- a shared completion contract
- deterministic structural and safety validation

The repo does not launch agent subprocesses, implement a second goal loop, or use
an Agent SDK.

## Starting a case

Start Claude Code or Codex from the repository root and submit one native `/goal`
naming the `research-goal` skill and the bounded question. The skill calls the
CLI internally, scaffolds the case, adopts the generated contract, and completes
the investigation in the same session.

Name `research-spec` instead when definitions, scope, sources, confounders, or
completion criteria need targeted discovery first. Outside an active goal, both
skills prepare the case and return a ready-to-submit `/goal` command.

## Research contract

- Treat all external systems as read-only.
- Read `brief.md` first and keep it stable unless the user reframes the case.
- Prefer the smallest source set that can answer the question.
- Discover live objects before querying them.
- Preserve every query in `queries.sql` and every object in `source-objects.md`.
- Keep material claims traceable to evidence.
- Define metrics, populations, time zones, and comparison windows.
- Reconcile calculated contributions to source totals when applicable.
- Record rejected leads and unresolved risks.

Before completion, delegate the final challenge to an independent subagent that
did not conduct the research. It names the strongest competing explanation, the
weakest-supported material claim, the most fragile source or calculation, and any
material objection. Record the reviewer and findings under `## Final Challenge`
in `notes.md`. Resolve each issue or disclose its effect on the conclusion.

The final action is:

```bash
uv run research validate <case> --strict
```

Fix every failure and surface the result in the last response so the goal can see
it.

## Artifacts

`brief.md` is the framing contract. `notes.md` is the working record. `report.md`
is the answer. `queries.sql` and `source-objects.md` make the evidence
reproducible. `plan.md` is optional and earns its place only when sequencing
helps.

Machine liveness state is deliberately absent. Client-owned goal state does not
belong in the research record.

## Choosing sources

Only web search is built in. Everything else is an opt-in bundle under
`examples/sources/`; enable one with `research source enable <name>` and check
what is wired with `research source list`. Local files attach per case with
`--context-path`.

- **Warehouses and databases** — Snowflake, BigQuery, Postgres, DuckDB,
  Databricks (Genie), Redshift. Treat them alike: discover objects live, query
  SELECT-only, stay read-only. Snowflake's read-only rule is the committed
  statement allowlist in `config/snowflake-mcp-tools.yaml`.
- **Azure** for the Microsoft-cloud data and observability plane: Azure Monitor /
  Log Analytics (KQL), Azure SQL, Data Explorer. Read-only via the server's
  `--read-only` flag.
- **Docs and knowledge** — Notion for live workspace pages and databases;
  Confluence for wiki spaces, runbooks, and RFCs; Google Drive for specs and
  decision records that live in Drive; Microsoft 365 for SharePoint/OneDrive and
  Teams threads.
- **Comms** — Slack, when the question depends on recent decisions, incident
  threads, or context that has not landed in docs yet.
- **Issue tracking and code** — Linear or Jira for issue state, project progress,
  and ownership; GitHub for code, pull requests, and who changed what (strong for
  engineering root-cause); Azure DevOps where work items, repos, and pipelines
  live together.
- **Observability** — Sentry for errors, events, stack traces, and releases;
  Datadog for metrics, monitors, logs, traces, and incidents.
- **Product analytics** — PostHog (the read-only default) for funnels, retention,
  activation, and feature adoption. Amplitude and Mixpanel work too, but those
  servers are read+write, so use a minimal-role account.
- **Experiments and flags** — LaunchDarkly, Statsig, or Confidence for rollout
  timing, targeting changes, audit history, and experiment results. This is the
  most common hidden cause of a metric shift; check it early.
- **Revenue and CRM** — Stripe for billing, MRR, churn, and disputes (provably
  read-only via a restricted key); HubSpot or Salesforce for deals, pipeline, and
  accounts.
- **Search and web traffic** — GA4 for sessions, engagement, and conversions.
  For Google Search Console, prefer the **warehouse copy** when your GSC data is
  synced there, and fall back to the `research gsc` CLI for fresher-than-sync data
  or API-only dimensions.
- **Web search** for external context, public incidents, and platform changes.
- **Local context folders** first when they are relevant — they are usually
  curated and high-signal.

Some upstream MCP servers are read+write unless you supply a read-only account,
PAT, or scoped key. Each bundle's `SETUP.md` says which case it is.

## Hypothesis-led research

Pick one or two active hypotheses before source work begins. Name the strongest
rival explanation, define what evidence would change confidence, gather the
sharpest available data, then record what moved: supported, weakened, rejected,
pivoted, or newly discovered.

`notes.md` is a research notebook, not a compliance checklist. Use the hypothesis
ledger and evidence log to preserve thinking that makes the next step sharper.

For `root-cause` cases, validation enforces a stronger design contract:
`## Hypotheses`, `## Known Confounders`, and `## Required Cross-Checks` in the
brief, and a discriminating test, strongest rival, completion threshold, and
cross-check on every high-priority thread in `plan.md`.

## Steering

Adjust direction by editing `notes.md` or `plan.md`. Keep `brief.md` stable once
a goal is underway unless you are explicitly reframing the question.
