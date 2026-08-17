# Research Brief

## Question

Why did the weekly batch-export success rate drop in March 2026, and what is the single largest cause?

## Deliverable

An on-call engineer should be able to read the report and know whether to revert
the change that caused the drop, with the numbers to justify it.

## Scope

- In scope: the weekly export metrics in `examples/local-sources/exports_weekly.csv` and the operational notes in `examples/local-sources/context/`.
- Out of scope: anything requiring live systems, external APIs, or web search. This case is deliberately offline.
- Research shape: `root-cause`

## Hypotheses

- **H1: An operational change degraded export reliability.** [priority: high, status: untested]
  - Why plausible: A reliability break that starts on one specific week usually has a discrete cause rather than a gradual one.
  - Strongest rival: The drop is gradual load growth, not a discrete event.
  - Discriminating test: Locate the exact week the success rate breaks, then check whether an operational note lands on the same date.
  - Evidence needed: A step change in one week, coincident with a recorded change.
  - Kill criterion: The decline is spread across many weeks with no single inflection.
- **H2: Volume growth outran capacity.** [priority: high, status: untested]
  - Why plausible: More scheduled jobs on fixed capacity would raise queueing and timeouts.
  - Strongest rival: Volume is essentially flat and cannot account for the magnitude.
  - Discriminating test: Compare the percentage change in `jobs_scheduled` with the percentage change in the failure rate.
  - Evidence needed: Volume growth of a magnitude comparable to the reliability change.
  - Kill criterion: Volume moves by a few percent while failures move by several multiples.
- **H3: The metric definition or counting logic changed.** [priority: medium, status: untested]
  - Why plausible: An apparent reliability break is sometimes a measurement break.
  - Strongest rival: The source notes state explicitly that counting logic did not change.
  - Discriminating test: Check whether `jobs_succeeded + jobs_failed` still equals `jobs_scheduled` across the break, and read the metric definitions.
  - Evidence needed: A documented definition change or an arithmetic discontinuity.
  - Kill criterion: The columns reconcile on both sides of the break and the notes rule it out.

## Definitions And Reconciliation

- Success rate is `jobs_succeeded / jobs_scheduled` for a week, as defined in the bundled metric definitions.
- Compare the weeks before the break against the weeks from the break onward, and state both windows explicitly.
- `jobs_succeeded + jobs_failed` must reconcile to `jobs_scheduled` in every week used as evidence.

## Known Confounders

- Volume drift between the two comparison windows.
- A partial or truncated final week at the end of the reporting window.
- Reading a mean of weekly rates instead of a pooled rate over both windows.

## Required Cross-Checks

- Confirm the timing of the break against the operational notes, not the metric alone.
- Check `avg_queue_minutes` as a second, independent signal of the same mechanism.
- Quantify the rival volume explanation before rejecting it; do not dismiss it by assertion.

## Freshness Requirements

- None. Every input is a static file committed in the repository.

## Success Criteria

- The pre-break and post-break success rates are both stated, with the exact week the break occurs.
- The largest cause is named and tied to a dated entry in the operational notes.
- The volume rival is quantified and explicitly rejected or accepted.
- Every number in the report is reproducible from the bundled CSV.
