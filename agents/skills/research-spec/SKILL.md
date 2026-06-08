---
name: research-spec
description: Transform a raw business question into a detailed investigation spec — classified shape, ranked falsifiable hypotheses, a source plan built from the sources actually enabled, and research threads with discriminating tests — then scaffold a validated agentic-research-loop case. Use before starting any research investigation in this repo.
argument-hint: "<business question>"
---

# Investigation Spec

Turn a raw question into a confirmation-ready case workspace for the
agentic-research-loop engine. The output is a **spec**, not an investigation: you
design the case and hand it to the loop.

**Question**: $ARGUMENTS

A 10/10 spec has four properties. Hold the work to them:

1. **Source-true** — every thread names a source that is actually enabled, with
   specific objects, not a wished-for stack.
2. **Falsifiable** — every hypothesis has a discriminating test and a stated
   observation that would kill it. No unfalsifiable claims.
3. **Decision-anchored** — the success criteria are specific and checkable, tied
   to what the reader will *do* with the answer.
4. **Contract-clean** — `research validate --design` passes before you hand it over.

## NEVER

- Leave a section heading with an empty or placeholder body.
- Design hypotheses or threads before discovering what data exists (Phase 2).
- Assume a source is available — check `research source list`. Emit CLI flags only
  for **enabled** sources; an unknown `--<source>-hint` aborts `research init`.
- Scaffold before the user confirms the spec (Phase 3 checkpoint).
- Edit `state/sources.json` by hand — route sources through `research init` flags.
- Guess metric definitions, table names, or tool names — discover them live.
- Run investigation cycles. This skill produces the spec and stops.

## Phase 1 — Frame the question

Reason about the question before any tool calls.

**Parse it.** Extract metric names, entities (product areas, segments, channels),
time references, and causal language ("why", "because", "impact of").

**Classify the shape:**
- `root-cause` — why did X happen? what caused Y? (declining, spiking, stagnating)
- `comparison` — how does A differ from B? which is better?
- `exploration` — what is the state of X? how does Y work?

**Pick the mode:**
- `autonomous` — root-cause work the loop runs solo over bounded cycles. Enforces
  the strong design contract and a mandatory challenge cycle.
- `guided` — exploration/comparison where a human steers the write-up.
- `quick` — a single-pass answer to a simple lookup.

**Catch local context and exclusions.** If the user pointed at a folder/file
("context in `web/seo/`"), plan to read it early and pass it via `--context-path`.
If they excluded a source ("skip Slack", "no GA4"), record it as `user_excluded`;
default stance is every enabled source stays on. Only disable on an explicit ask —
a source that looks irrelevant at planning time sometimes cracks the case
mid-cycle.

**Ask at most one clarifying question** — and only if the question is critically
ambiguous (missing which metric, which product, or which timeframe). Otherwise
proceed.

### 1b. Map the causal system (reasoning, no tool calls)

Before searching, decompose the target the way it is actually produced. This is
what surfaces the upstream sources that share no keywords with the metric name but
drive it. Write down:

- **Decomposition** — how the target breaks down mechanically. A rate splits into
  numerator and denominator; a funnel into stage conversions; revenue into
  volume × price × mix; reliability into load, capacity, and retries; latency into
  queue plus service time.
- **Upstream inputs** — what feeds each component, one or two levels up.
- **Downstream effects** — what the target feeds, to scope what is in vs out.
- **Search terms** — translate the chain into concrete keywords for discovery.
  Search every upstream and downstream concept, not just the metric name.

## Phase 2 — Discover what you can actually use

### 2a. Enumerate the usable source set (do this first)

```bash
uv run research source list      # which bundles are enabled (* = enabled)
```

The usable set is: the **enabled** bundles, plus the built-in **web search**, plus
any folders the user attached with `--context-path`. Everything else is off the
table for this case. See [references/source-families.md](references/source-families.md)
for the map from question type → source family → example bundles, and the
warehouse-vs-live nuance (GSC, GA4).

If the causal chain needs a family that is **not** enabled, note it now — you will
flag it at the orientation checkpoint and suggest `research source enable <name>`,
rather than designing around a hole.

### 2b. Orient across the usable sources

Discover live — in parallel where you can. Use whatever tools the enabled MCP
servers expose; discover their real tool, object, and schema names rather than
assuming. By family:

- **Warehouse / metrics** — discover objects live (semantic views or `SHOW TABLES`
  / `DESCRIBE`), confirm grain, dimensions, and metrics. The semantic layer is a
  convenience, not a boundary — drop to fact/staging tables when they hold the
  signal. Confirm metric definitions; do not guess them.
- **Experiments / flags** — scan the timeframe for rollouts, A/B tests, and flag
  changes. This is the most common hidden cause of a metric shift; even a null
  experiment rules a surface out.
- **Docs / comms / issue tracking** — search strategy, retros, decisions, incident
  threads, and what shipped during the window.
- **Local context** — read attached folders/files now; they are usually curated,
  high-signal context.

Right-size the sweep to the shape: a `quick` lookup needs one or two sources; an
`autonomous` root-cause case earns a broad orientation.

### 2c. Orientation summary

Print a short paragraph to the user: what the target means and how it is produced;
which sources are enabled and confirmed; key qualitative context (recent changes,
discussions); known gotchas or confounders; and any causally important source that
is **not enabled** (with the `research source enable <name>` suggestion). End with
the `Sources ON` / `Sources OFF` lines from the checkpoint format below.

## Phase 3 — Design the spec

The core reasoning step. This applies **strong inference**: hold several rival
explanations at once and design tests that *exclude* them, rather than
accumulating support for one. Take your time.

### Hypotheses (root-cause / trend) or angles (exploration / comparison)

Generate **3–5 ranked hypotheses**. Good ones are:

- **Competing, not overlapping** — together they roughly partition the explanation
  space (include a measurement/attribution/freshness hypothesis — instrumentation
  is a real cause, not a footnote). Confirming one should weaken another.
- **Falsifiable** — each carries a **discriminating test** whose result points to
  this hypothesis *or* its rival (not both), and a **kill criterion**: the
  observation that would make you drop it.
- **Ranked by prior** — most plausible first; mark weak-evidence ones speculative.
- **Paired** with a strongest rival, an evidence target, and `status: untested`.

For exploration/comparison, frame these as investigation angles instead — the
falsifiability bar relaxes, but ranking by information value still applies.

### Research threads

Design **4–8 threads** using the format in
[references/artifact-templates.md](references/artifact-templates.md). Principles:

- **Anchor first** — T1 confirms the trend/event with hard numbers before anything
  explains it. Don't skip quantification.
- **Order by information gain** — sharpest discriminating test first, not easiest.
- **Declare dependencies** — if T3 only makes sense after T1 confirms X, say so.
- **Be specific about sources** — `Snowflake (registrations_daily, gsc_synced)`,
  not "Snowflake". Every source named must be enabled.
- **Flag speculation** — mark threads that may not pan out and the signal to abandon.

### Remaining brief sections

Define each concretely (templates in the reference):

- **Decision or Deliverable** — what the answer is *for*.
- **Scope** — explicit in/out boundaries.
- **Source Plan** — table over the enabled families, each with specific objects and
  Primary/Supporting priority.
- **Key Dates** — launches, incidents, config changes, seasonal boundaries, external events.
- **Known Confounders** — effects that could mimic or mask the signal.
- **Required Cross-Checks** — how key claims get a second-source check (this is the
  triangulation commitment).
- **Freshness Requirements** — which facts need live verification vs cached docs.
- **Success Criteria** — specific and checkable ("top 2–3 drivers ranked with
  quantified contribution"), never generic ("a clear answer").

### Right-size by shape

| Shape / mode | Hypotheses | Threads | Design contract |
|--------------|-----------|---------|-----------------|
| autonomous root-cause | 3–5, falsifiable | 4–8 | full + confounders + cross-checks (validator-enforced) |
| guided comparison/exploration | 3–5 angles | 3–6 | lighter — rivals where they help |
| quick lookup | 1–3 | 1–3 | minimal — anchor + answer |

### Checkpoint

Present the spec compactly and **wait for confirmation or edits** before Phase 4:

```
Hypotheses: H1–H5 one-liners (with priority)
Threads:    T1–T6 one-liners with sources
Scope:      in / out, one line
Mode:       <mode> | Template: <template>
Sources ON:  <enabled, comma-separated>
Sources OFF: <source> (user excluded: <reason>), ...   # omit if none
Not enabled but relevant: <source> — enable with `research source enable <name>`   # omit if none
```

Default is every enabled source ON. List a source OFF only if the user excluded
it. The user can adjust here ("keep GSC on", "also skip Slack").

## Phase 4 — Scaffold

Write the three files into a tmpdir, call `research init --from-spec`, then
**validate**. `research init` splices the `## Source Registry` block into your
brief from the `--*-hint` flags and generates `report.md`, `status.md`, and
`state/*.json`.

**4a. Create the tmpdir.** Slug: short, lowercase, hyphenated (`active-users-decline`).

```bash
TMPDIR="$(mktemp -d -t research-spec-<slug>.XXXXXX)"
```

**4b–4d. Write `brief.md`, `plan.md`, `notes.md` into `$TMPDIR`** using
[references/artifact-templates.md](references/artifact-templates.md). Fill every
section with real Phase 2/3 content. The reference lists the exact headers and
bold field names the validator parses — match them verbatim.

**4e. Build the init command from the *enabled* source set.** Only emit a
`--<name>-hint` / `--no-<name>` flag for a source that is enabled (a flag for a
disabled source aborts the command). Use `--context-path` for attached folders and
`--local-only` if the case is local-files-only.

```bash
uv run research init <slug> \
  --template <template> \
  --mode <mode> \
  --from-spec "$TMPDIR" \
  [--context-path <path> ...] \
  [--<name>-hint "<focus>"  for each enabled source with a focus] \
  [--no-<name>              for each source the user excluded at the checkpoint]
```

**4f. Validate, then fix-and-revalidate (feedback loop).** `research init` prints
the dated case id (`research/<date>-<slug>/`). Run the design gate against it:

```bash
uv run research validate <date>-<slug> --design
```

If it reports issues (a missing `## Required Cross-Checks`, a high-priority thread
without all four design fields, etc.), fix them directly in the scaffolded
`research/<date>-<slug>/` files and re-run until it prints `Validation passed`.
Editing the case files pre-run is fine — the brief is only protected once cycles start.

**4g. Clean up** — always, even on failure:

```bash
rm -rf "$TMPDIR"
```

## Phase 5 — Confirm ready

Print a compact summary:

```
Investigation workspace ready:
  Path:   research/<date>-<slug>/
  Mode:   <mode> | Template: <template>
  Design: validate --design passed
  Hypotheses: <count> | Threads: <count>
  Sources: <enabled source list>

To start:
  uv run research run <date>-<slug> --max-cycles 3
  (Add `--runner codex` to use the Codex CLI instead of Claude.)
```

Offer to adjust anything before the loop starts.
