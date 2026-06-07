---
name: research-spec
description: Transform a raw business question into a rich investigation spec with hypotheses, source planning, and research threads. Use before starting an agentic-research-loop investigation.
argument-hint: "<business question>"
---

# Investigation Spec

Generate a rich investigation workspace for the agentic-research-loop research engine.

**Question**: $ARGUMENTS

## NEVER

- Write a brief with placeholder sections ("In scope:" with nothing after it)
- Skip source discovery — always check what data sources are available before designing
- Generate hypotheses without domain context (discover sources and search first)
- Scaffold the workspace before presenting the spec for user confirmation
- Modify `sources.json` directly — use `uv run research init` CLI flags instead
- Run investigation cycles — this skill produces the spec only
- Guess metric definitions or table names — look them up

## Phase 1: Parse and Classify

Analyze the question before making any tool calls:

- Extract **metric names** (WAU, ARR, conversion rate), **entities** (product
  areas, user segments, channels), **time references** (Q1 2026, last month,
  since March), and **causal language** (why, because, impact of)
- Classify the **investigation shape**:
  - `root-cause` — why did X happen? what caused Y? (stagnating, declining, spiking)
  - `comparison` — how does A differ from B? which is better?
  - `exploration` — what is the state of X? how does Y work?
- Determine **mode**:
  - `autonomous` for root-cause investigations (bounded cycles until done)
  - `guided` for exploration and comparison (human steers synthesis)
  - `quick` for simple lookups (what is X? how many Y?)
- Check if the user mentioned **local context** — a folder path, file, or
  dataset they want included (e.g., "I have some context in `web/seo/`").
  If so, read it early in Phase 2 and use it to inform hypotheses and threads.
  Pass it to the workspace via `--context-path` in Phase 4.
- Check for **explicit source exclusions** in the question — phrasing like
  "skip GSC", "without Slack", "don't use GA4", "no experiments data". Capture
  these as a `user_excluded` list. Default stance: every source stays on. Only
  disable on explicit user ask — a source the skill judges "not relevant" at
  planning time sometimes turns out to be the one that cracks the case
  mid-cycle. Cheap to have on, expensive to have missing.
- If the question is critically ambiguous — missing which metric, which product,
  or which timeframe — ask **one** focused clarifying question. Otherwise proceed.

### 1b. Map the causal chain (reasoning step — no tool calls yet)

Before searching for data sources, reason through the **full causal system**
that produces the metric in question. Write out:

1. **Metric decomposition** — how does this metric break down mechanically?
   (e.g., WAU ≈ registrations × activation rate × retention; ARR = users ×
   ARPU; conversion rate = conversions / visitors)
2. **Upstream inputs** — what feeds into each component? Think one or two
   levels up the causal chain. For a user-count metric, this includes:
   website traffic, organic search, paid acquisition, viral loops,
   referral programs, product-led signups, etc.
3. **Downstream outputs** — what does this metric feed into? This helps
   scope what's in vs out.
4. **Data domains to search** — translate the causal chain into concrete
   data domain keywords. Don't just search for the metric name — search
   for every upstream and downstream concept. Example for WAU:
   - `user`, `active`, `engaged` (the metric itself)
   - `visitor`, `registration`, `signup` (upstream: acquisition)
   - `activation`, `conversion`, `onboarding` (upstream: activation)
   - `retention`, `churn`, `return` (retention component)
   - `website`, `page`, `traffic` (website funnel)
   - `experiment`, `rollout` (product changes)

This list drives the source discovery searches in Phase 2. If you skip this
step, you will miss data sources that don't share keywords with the metric
name but are causally critical.

## Phase 2: Discover and Orient

Gather domain context from **all relevant source families** before designing
the spec. The goal is a 360° picture — quantitative data, qualitative context,
and confounder awareness. Run searches in parallel where possible.

### 2a. Quantitative sources (always do this for metric questions)

**Snowflake schema discovery** — use the data domain keywords from Phase 1b
to search broadly across semantic views and tables:
- Start with `list_semantic_views` using **multiple keyword searches** derived
  from the causal chain — not just the metric name. For example, if investigating
  WAU, search for `%user%`, `%visitor%`, `%registration%`, `%activation%`,
  `%conversion%`, `%retention%`, `%website%`, etc.
- Use `describe_semantic_view` on promising matches to confirm grain,
  dimensions, and metrics
- **Don't stop at the semantic layer.** Semantic views are a good starting
  point, but they don't cover everything. Use Snowflake metadata queries
  (`SHOW TABLES IN SCHEMA` / `DESCRIBE TABLE`) to find upstream
  tables that are relevant but not modeled as semantic views. If a fact table,
  staging table, or raw source has signal for the investigation, use it
  directly — the semantic layer is a convenience, not a boundary.
- Note: some semantic views can't be queried directly via Snowflake MCP —
  identify the underlying mart tables (e.g., the relevant fact and dimension
  tables) and query those instead

**Google Search Console — default Snowflake** — GSC is synced into the warehouse.
For registration/growth/traffic questions, **query GSC-shaped data in Snowflake first**
(semantic views / marts when available; otherwise `SHOW TABLES` in the GSC-synced staging schema and downstream models). Use the
same analysis lenses you would from the API:
  - Top queries and intent, organic shifts, geo/device slices, volatility vs launches
**GSC API fallback only** — `research gsc` when Snowflake is stale, incomplete for the slice you need, or you require fresher-than-sync data (arbitrary dimensions, pagination).

**Live APIs (when Snowflake is not enough)** — still check when relevant:
- **GA4** (Google Analytics 4) for site analytics: page views, sessions,
  active users, engagement, conversions by page/source/device/country. Use it
  to:
  - Measure on-site behavior and engagement patterns
  - Identify top pages and traffic sources
  - Detect changes in user flow or drop-off points
  - Cross-reference with GSC to connect search intent to on-site behavior
  - Query via the official GA4 MCP server (enable the `examples/sources/ga4/` bundle)

**Local context folders** — if the user pointed to a local folder or file,
read it now — it's likely high-signal context they curated for this question.
Also check if `web/` or other data directories exist in the repo root.
These often contain:
- SEO exports and search console historical data
- Website launch timelines (useful as confounder context)
- Search engine update timelines (explains external traffic volatility)
- Analytics exports (GA4 or similar)

### 2b. Qualitative and organizational sources (don't skip these)

These surface the "why" behind quantitative trends. Not every investigation
needs all of them — pick the ones relevant to the question:

**Notion** — search for strategy docs, retrospectives, forecasts, and
initiative pages related to the question domain.

**Slack** — search for recent discussions, decisions, and informal context
about the metric or domain. Catches product changes, incidents, or shifts
that haven't landed in formal docs.

**Linear** — search for product changes, feature launches, and cycle work
shipped in the investigation timeframe. Useful for identifying what changed.

**Confidence** (critical) — always check for experiments and feature rollouts
running or recently concluded in the investigation timeframe. Experiments
frequently affect registration, activation, and conversion metrics in ways
that look like organic trends. Use `list_experiments` to scan the timeframe,
then `get_results` for anything potentially relevant. Even null-result
experiments are useful context (they rule out that surface as a cause).

### 2c. Search trends and external context (enrich with external signals)

For traffic, growth, or behavior shifts: **GSC in Snowflake first**, then
**`research gsc`** only as fallback; for **GA4** use the official GA4 MCP server (the `examples/sources/ga4/` bundle) when you need site analytics the warehouse does not cover. Organic search and
on-site behavior often explain registration and funnel moves that product
metrics alone do not surface.

### 2d. Orientation summary

Print a brief orientation paragraph to the user summarizing:
- What the metric means and how it's calculated
- Which data sources are available and confirmed
- Key context from qualitative sources (product changes, discussions)
- Any known gotchas or confounders
- Whether **GSC** will be satisfied from **Snowflake** or needs **`research gsc`**, and which **GA4** API slices matter
- **Sources enablement** — list sources that will be ON (the default) and
  any the user explicitly excluded in Phase 1, with the user's reason.
  Do not mark sources OFF based on the skill's own relevance judgment.

## Phase 3: Design the Spec

Build the investigation spec using your domain context. This is the core
reasoning step — take your time.

### Hypotheses (root-cause/trend) or Investigation Angles (exploration/comparison)

Generate **3-5 ranked hypotheses** with brief rationale for each. Good
hypotheses are:
- Testable with available data sources
- Mutually informative (confirming H1 should weaken H2, or vice versa)
- Ordered by prior probability (most likely first)
- Honest about uncertainty ("speculative" if you have weak evidence)
- Paired with a strongest rival, discriminating test, evidence target, and
  initial status (`untested`)

### Research Threads

Design **4-8 threads** following the plan.md format:

```markdown
### T<n>: <short descriptive title>
**Priority:** high / medium / low
**Source:** <source family + specific tables/views/channels>
**Objective:** <the specific question this thread answers>
**Main Explanation:** <current best explanation under test>
**Strongest Rival:** <best competing explanation>
**Discriminating Test:** <the concrete check that would change confidence>
**Evidence Needed:** <what would count as enough evidence>
**Completion Threshold:** done when ... / blocked when ... / pivot when ...
**Confounders / Freshness Risks:** <what could mislead this thread>
**Cross-Check:** <which second source or method will validate the claim>
**Depends on:** <T<n> if applicable, otherwise "none">
**Status:** pending
```

Thread design principles:
- **Anchor first** — T1 should confirm the trend with hard numbers before
  explaining it. Don't skip quantification.
- **High-signal threads first** — order by expected information gain, not ease
- **Declare dependencies** — if T3 only makes sense after T1 confirms X, say so
- **Flag speculation** — mark threads that may not pan out
- **Be specific about sources** — "Snowflake (`your_semantic_view`, `your_metrics_table`)"
  not just "Snowflake"

### Remaining Spec Sections

Define each of these concretely:

- **Decision or Deliverable** — what decision should this investigation support?
  What will the reader do with the answer?
- **Scope** — explicit in-scope / out-of-scope boundaries
- **Source Plan** — table format covering **all source families**, not just
  Snowflake. Include quantitative sources (Snowflake incl. GSC-synced tables,
  GA4 API, local data), qualitative sources (Notion, Slack, Linear), and
  experiment data (Confidence).
  **For traffic/growth questions, treat GSC as primary in Snowflake; `research gsc` is fallback:**
  ```
  | Source | What we get | Priority |
  |--------|-------------|----------|
  | Snowflake (`your_metrics_table`, etc.) | Registration counts, WAU, conversion funnel | Primary |
  | Snowflake (GSC sync / `GOOGLE_SEARCH_CONSOLE`) | Organic queries, clicks, impressions, CTR, rankings | Primary |
  | GSC API (`research gsc`) | Same family when warehouse is stale or incomplete | Fallback |
  | GA4 (GA4 MCP) | Page views, sessions, users, engagement, conversions by page/source | Primary |
  | Confidence | Experiments, rollouts, feature flags affecting metrics | Primary |
  | Notion | Strategy docs, SEO roadmap, retrospectives | Supporting |
  | Slack | Team discussions, incidents, product changes | Supporting |
  | Linear | Feature launches, product changes during investigation window | Supporting |
  ```
- **Key Dates** — temporal anchors relevant to the investigation (launches,
  incidents, config changes, seasonal patterns, external events)
- **Known Confounders** — from documentation, past incidents, and domain
  knowledge (attribution bugs, tracking breaks, seasonal effects, external
  platform changes like search engine updates)
- **Freshness Requirements** — which facts need **Snowflake** refresh checks vs **`research gsc` CLI / GA4 MCP** live queries vs. cached docs or local exports
- **Success Criteria** — specific and checkable, not generic. Example:
  "Top 2-3 drivers ranked with quantified contribution estimates" not
  "Clear answer for a teammate"

### Checkpoint

Present the spec to the user in a scannable format:

```
Hypotheses: H1-H5 summary
Threads: T1-T6 summary with sources
Scope: in/out one-liner
Mode: autonomous | Template: root-cause
Sources ON:  <comma-separated list of enabled sources>
Sources OFF: <source> (user excluded: <reason>), ...   # omit line if none
```

Default is every source ON. Only list a source under OFF if the user
explicitly excluded it in Phase 1; never auto-disable based on the skill's
own relevance judgment. The user can adjust at this checkpoint
("actually keep GSC on" / "also skip Slack").

Wait for confirmation or adjustment before proceeding to Phase 4.

## Phase 4: Scaffold

Write the designed `brief.md`, `plan.md`, and `notes.md` into a temporary
directory outside the repo, then call `research init --from-spec <tmpdir>`.
`research init` reads your files, splices the generated `## Source Registry`
block into your brief (from the `--*-hint` flags), and creates the rest of
the case workspace (`state/*.json`, `report.md`, `status.md`).

### 4a. Create a temporary spec directory

Slug format: short, descriptive, lowercase with hyphens (e.g.,
`active-users-decline`).

```bash
TMPDIR="$(mktemp -d -t research-spec-<slug>.XXXXXX)"
```

Use the printed path for steps 4b–4d. Clean it up in 4f even if earlier
steps fail.

### 4b. Write brief.md into the tmpdir

Fill every section with real content based on Phase 2 / Phase 3 work. You
MAY include a `## Source Registry` section header (its body will be replaced
by the generated block); leaving it out is also fine — the generated
section will be appended.

```markdown
# Research Brief

## Question

<the raw question>

## Mode

- Selected mode: `<mode>`
- Research shape: `<template>`
- Created: `<YYYY-MM-DD>`

## Decision Or Deliverable

<what decision this case supports — filled in, not placeholder>

## Background

<context from source discovery — metric definitions, recent trends,
prior findings, and organizational context relevant to this question>

## Hypotheses

- **H1: <title>** [status: untested]
  - Why plausible: <brief rationale>
  - Strongest rival: <competing explanation>
  - Discriminating test: <what would move confidence>
  - Evidence needed: <what enough evidence looks like>
- **H2: <title>** [status: untested]
  - Why plausible: <brief rationale>
  - Strongest rival: <competing explanation>
  - Discriminating test: <what would move confidence>
  - Evidence needed: <what enough evidence looks like>
- ...

## Scope

- In scope: <specific items>
- Out of scope: <specific exclusions with brief reason>

## Source Plan

| Source | What we get | Priority |
|--------|-------------|----------|
| <specific table/view> | <what data> | Primary/Supporting |
| ... | ... | ... |

## Key Dates

- <YYYY-MM-DD>: <event relevant to the case>
- ...

## Known Confounders

- <confounder from prior work or domain knowledge>
- ...

## Source Registry

<optional — the generated block will replace this body>

## Freshness Requirements

- <which facts need live verification and from where>
- <which context can come from existing docs>

## Success Criteria

- <specific, checkable criterion>
- <specific, checkable criterion>
- ...
```

### 4c. Write plan.md into the tmpdir

```markdown
# Research Plan

**Case:** <question>
**Mode:** <mode> | <template>
**Created:** <YYYY-MM-DD>

## Threads

### T1: <title>
**Priority:** high
**Source:** <source family + specific objects>
**Objective:** <what this thread answers>
**Discriminating Test:** <how a specific check distinguishes this explanation>
**Strongest Rival:** <the best alternative explanation>
**Cross-Check:** <freshness or confounder hazard + cross-source check>
**Completion Threshold:** <what counts as done / blocked / pivoted>
**Depends on:** none
**Status:** pending

### T2: ...
...

## Dependencies

<brief note on thread ordering and why>

## Risks

- <threads that may not pan out and why>
```

The bolded labels (`**Discriminating Test:**`, `**Strongest Rival:**`,
`**Cross-Check:**`, `**Completion Threshold:**`) must use exactly that
capitalization — the validator matches on the exact string.

### 4d. Write notes.md into the tmpdir

```markdown
# Research Notes

## Working Theory

- <1-2 sentence initial theory based on domain context and hypotheses>

## Hypotheses

### H1: <title>
- **Status:** active | supported | weakened | rejected | pivoted
- **Why plausible:** <brief rationale from source discovery>
- **Strongest rival:** <competing explanation>
- **Discriminating test:** <what would move confidence>
- **Evidence so far:** <initial context, or none yet>
- **Next check:** <thread/source to start with>

### H2: <title>
- **Status:** active | supported | weakened | rejected | pivoted
- **Why plausible:** <brief rationale from source discovery>
- **Strongest rival:** <competing explanation>
- **Discriminating test:** <what would move confidence>
- **Evidence so far:** <initial context, or none yet>
- **Next check:** <thread/source to start with>

## Evidence Log

- **Claim:** <source-discovery fact or tentative claim>
  **Source family:** <Snowflake / Confidence / Notion / Slack / Linear / web / local>
  **Source detail:** <table, page, thread, query, file, etc.>
  **Supports:** <which hypothesis or confounder>
  **Caveat / freshness:** <what could make it stale or misleading>

## Dead Ends

- <anything already checked and ruled out during source discovery, or none yet>

## Open Questions

- <questions that still matter>

## Leads

- **<finding or thread to follow>** [high/medium/low]
  Why it matters: <impact on the case>
  Next: <specific next step>
  Sources to check: <source families>
```

### 4e. Invoke `research init` with --from-spec

From the repo root:

```bash
uv run research init <slug> \
  --template <template> \
  --mode <mode> \
  --from-spec "$TMPDIR" \
  [--no-<source> for each source on the Phase 3 checkpoint OFF list] \
  [--<source>-hint "<focus text>" for each enabled source with hints]
```

Only pass `--no-<source>` for sources the user explicitly excluded (and
confirmed at the Phase 3 checkpoint). Default stance: all sources stay on.

`research init` will:
- read `brief.md` / `plan.md` / `notes.md` from `$TMPDIR`
- splice the Source Registry into the brief based on the `--*-hint` flags
- create `state/*.json`, `report.md`, `status.md` from defaults

### 4f. Clean up the tmpdir

Always remove the tmpdir when done, including on failure:

```bash
rm -rf "$TMPDIR"
```

## Phase 5: Confirm Ready State

Print a compact summary:

```
Investigation workspace ready:
  Path: research/<slug>/
  Mode: <mode> | Template: <template>
  Hypotheses: <count> | Threads: <count>
  Sources: <enabled source list>

To start:
  uv run research run <slug> --max-cycles 3
  (Optional: `uv run research run <slug> --runner codex --max-cycles 3` for Codex CLI.)
```

Offer to adjust anything before the loop starts.
