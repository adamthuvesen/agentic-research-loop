# Research Brief

## Question

Research: registration-drop

## Mode

- Selected mode: `autonomous`
- Research shape: `root-cause`
- Created: `2026-06-06`

## Decision Or Deliverable

What decision, update, or deliverable should this case support?

## Scope

- In scope:
- Out of scope:

## Hypotheses

- **H1: A real behavior shift changed the metric in a concentrated segment or cohort.** [priority: high, status: untested]
  - Discriminating test: Break `Research: registration-drop` by segment, cohort, geography, or workflow step and confirm the shift survives at least one cross-source check.
  - Strongest rival: The apparent movement is mostly composition drift, seasonality, or normal variance.
  - Evidence needed: A concentrated change with a plausible mechanism, plus corroboration from a second source family or adjacent metric.
  - Completion threshold: Done when the leading segment(s) and direction of effect are explicit, or blocked with the exact missing cut/data dependency named.
- **H2: Upstream inputs or feeder cohorts changed before the observed metric moved.** [priority: high, status: untested]
  - Discriminating test: Check the upstream driver for `Research: registration-drop` one step earlier in the funnel or lifecycle and compare timing, magnitude, and affected slices.
  - Strongest rival: The outcome changed without a matching upstream shift, which points to downstream execution or retention instead.
  - Evidence needed: A lead/lag relationship or a clearly weaker feeder cohort that lines up with the downstream pattern.
  - Completion threshold: Done when the upstream contribution is quantified or directionally clear enough to rank against other drivers, or ruled out as too small or mistimed.
- **H3: Measurement, attribution, or freshness issues explain part of the movement.** [priority: medium, status: untested]
  - Discriminating test: Verify `Research: registration-drop` with an independent definition, source, or cutoff date and inspect known tracking, routing, or reporting changes near the inflection.
  - Strongest rival: Multiple independent sources show the same movement, so the change is real even if measurement is noisy.
  - Evidence needed: A concrete mismatch between sources/definitions or a confirmed instrumentation change that overlaps the observed shift.
  - Completion threshold: Done when measurement risk is either ruled in as material or bounded tightly enough that the remaining explanation is still trustworthy.

## Source Plan

- Live systems for fresh facts
- Notion, Slack, Linear, web, Snowflake, Confidence, GSC, GA4 for context and evidence

## Source Registry

- All sources are strictly read-only. Search, query, and retrieve only — never send messages, create or update issues, modify data, post comments, or alter any external system.
- Notion for workspace pages, databases, and discussions.
- Slack for recent discussions, decisions, and informal context. Ephemeral — cite with caveat.
- Linear for project status, issue tracking, and ownership context.
- Web tools for external context and public changes.
- Snowflake for live metrics and warehouse-backed evidence.
- Confidence for experiments, rollouts, and decision history.
- GSC organic search — default Snowflake (synced); `research gsc` only as API fallback.
- Google Analytics 4 for site analytics — page views, sessions, users, engagement, and conversions.
- Local context folder: examples/local-sources

## Known Confounders

- Which seasonality, composition, routing, or attribution effects could mimic the observed change?
- Which freshness caveats matter before you compare sources?

## Required Cross-Checks

- Name the main freshness hazard before comparing live data with snapshots or local exports.
- Cross-check every high-confidence claim in at least two source families when possible.
- Record the strongest rival explanation for each major thread before calling it done.
- If a surprising finding changes the case, preserve `brief.md` and log the pivot in `notes.md` plus the relevant thread status in `plan.md`.

## Freshness Requirements

- Which facts must be verified live?
- Which context can come from existing docs?

## Success Criteria

- The case question is well scoped.
- The workspace is ready for human or autonomous follow-through.
