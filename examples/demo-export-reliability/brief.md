# Research Brief

## Question

Why did weekly export job success rate drop after the March scheduler change?

## Mode

- Selected mode: `autonomous`
- Research shape: `root-cause`
- Created: `2026-06-07`

## Decision Or Deliverable

Decide whether to revert the business-hours schedule for large warehouse exports or add queue isolation before the next reliability review.

## Scope

- In scope: Export success rate, queue wait times, and the 2026-03-09 scheduler change.
- Out of scope: Interactive query performance tuning, unrelated batch pipelines, and customer-facing SLA reporting.

## Hypotheses

- **H1: Queue contention from rescheduled heavy jobs reduced success rate.** [priority: high, status: untested]
  - Discriminating test: Compare success rate, failures, and queue minutes before vs after the change week while holding scheduled volume flat.
  - Strongest rival: Scheduled volume rose and overwhelmed capacity without any schedule change.
  - Evidence needed: A step down in success rate with rising queue minutes and flat scheduled jobs.
  - Completion threshold: Done when magnitude, timing, and primary mechanism are explicit.
- **H2: A platform or counting change inflated failures.** [priority: medium, status: untested]
  - Discriminating test: Verify metric definitions stayed constant and reconcile weekly totals across the inflection.
  - Strongest rival: Independent weekly cuts show the same decline with unchanged definitions.
  - Evidence needed: No definition change plus consistent failure growth tied to queue pressure.
  - Completion threshold: Done when measurement risk is ruled in or bounded tightly enough to trust the operational explanation.
- **H3: Retry-policy drift explains part of the movement.** [priority: low, status: untested]
  - Discriminating test: Check whether any pre-March policy tweak moved the inflection; if not, deprioritize.
  - Strongest rival: The Feb retry tweak caused no break until the schedule change.
  - Evidence needed: Timing misalignment between policy tweak and inflection.
  - Completion threshold: Done when retry policy is ruled out as the primary driver.

## Source Plan

- Local CSV and context notes for the offline demo bundle
- Snowflake or observability exports for live cross-checks when available

## Source Registry

- All sources are strictly read-only. Search, query, and retrieve only — never send messages, create or update issues, modify data, post comments, or alter any external system.
- Local context folder: examples/local-sources

## Known Confounders

- Partial-week rows near window edges can blur pre/post comparisons.
- Concurrent platform maintenance could mimic queue pressure if it overlaps the change week.

## Required Cross-Checks

- Cross-check the inflection timing against the change log before ranking causes.
- Record the strongest rival explanation for each major thread before calling it done.

## Freshness Requirements

- Weekly export metrics and scheduler change timing come from the bundled local CSV and notes.
- Live queue telemetry would be needed for operational sign-off beyond the demo bundle.

## Success Criteria

- The break is quantified and localized to queue pressure vs volume.
- The leading explanation is ranked against the strongest rival.
- Challenge review passes before the case closes.
