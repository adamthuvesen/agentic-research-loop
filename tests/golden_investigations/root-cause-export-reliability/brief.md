# Investigation Brief

## Question

Why did export job success rate drop after the March scheduler change?

## Mode

- Selected mode: `autonomous`
- Investigation shape: `root-cause`
- Created: `2026-04-05`

## Decision Or Deliverable

Determine whether the March scheduler change caused the export reliability break, and whether the right next move is reverting the schedule, isolating heavy jobs, or fixing measurement.

## Scope

- In scope: Scheduler timing, export success rate, queue wait times, and failure counts.
- Out of scope: Interactive query tuning, unrelated batch pipelines, and customer SLA reporting.

## Hypotheses

- **H1: Queue contention from rescheduled heavy jobs reduced success rate.** [priority: high, status: untested]
  - Discriminating test: Compare success rate, failures, and queue minutes before vs after the change while scheduled volume stays flat.
  - Strongest rival: Scheduled volume rose and overwhelmed capacity without any schedule change.
  - Evidence needed: A step down in success rate with rising queue minutes and flat scheduled jobs.
  - Completion threshold: Done when magnitude, timing, and mechanism are explicit, or blocked with the missing cut named.
- **H2: A platform or counting change inflated failures.** [priority: high, status: untested]
  - Discriminating test: Verify metric definitions stayed constant and reconcile weekly totals across the inflection.
  - Strongest rival: Independent weekly cuts show the same decline with unchanged definitions.
  - Evidence needed: A concrete mismatch tied to definitions or a confirmed counting change overlapping the break.
  - Completion threshold: Done when measurement risk is ranked against operational causes, or ruled out as too small.
- **H3: Retry-policy drift explains part of the movement.** [priority: medium, status: untested]
  - Discriminating test: Check whether any pre-March policy tweak moved the inflection; if not, deprioritize.
  - Strongest rival: The Feb retry tweak caused no break until the schedule change.
  - Evidence needed: Timing misalignment between policy tweak and inflection.
  - Completion threshold: Done when retry policy is ruled in as material or bounded tightly enough for action.

## Source Plan

- Snowflake or observability exports for success rate, queue minutes, and scheduled volume
- Local context notes for scheduler change timing
- Change-management docs for operational corroboration

## Source Registry

- Snowflake for live metrics and warehouse-backed evidence.
- Notion for runbooks and change records.
- Web tools for external context and public platform changes.

## Known Confounders

- Partial-period March data can distort pre/post comparisons.
- Concurrent maintenance can mimic queue pressure if it overlaps the change week.

## Required Cross-Checks

- Cross-check every high-confidence reliability claim in at least two source families when possible.
- Match the freshness cutoff date before comparing live data with local snapshots.
- Preserve `brief.md` if the case pivots; record the new theory in `notes.md` and thread status in `plan.md`.

## Freshness Requirements

- Scheduler timing, export actuals, and queue telemetry must be verified live when available.
- Historical context and metric definitions can come from existing docs.

## Success Criteria

- The leading explanation is ranked against the strongest rival.
- The main schedule effect is either quantified or explicitly ruled out.
- Freshness and measurement risks are bounded clearly enough for action.
