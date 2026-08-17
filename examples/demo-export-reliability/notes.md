# Research Notes

## Working Theory

- Current best explanation: The 2026-03-09 scheduler change moved heavy export jobs into business hours, overloading the shared queue and cutting success rate.
- Confidence: high.
- What would change this: a non-scheduler change in the same window, or a metric-definition shift.

## Hypotheses

### H1: An operational change degraded export reliability
- **Status:** supported
- **Why plausible:** The break lands on a single week rather than drifting.
- **Strongest rival:** Gradual load growth with no discrete cause.
- **Discriminating test:** Locate the break week, then check the operational notes for the same date.
- **Evidence so far:** The break is the week of 2026-03-09, the same date as the recorded scheduler change.
- **Next check:** None. Confirmed by a second signal (queue minutes).

### H2: Volume growth outran capacity
- **Status:** rejected
- **Why plausible:** More jobs on fixed capacity would raise queueing and timeouts.
- **Strongest rival:** Volume is flat and cannot account for the magnitude.
- **Discriminating test:** Compare the percentage change in scheduled jobs with the change in failure rate.
- **Evidence so far:** Volume +2.0% against failures +353%.
- **Next check:** None.

### H3: Counting logic changed
- **Status:** rejected
- **Why plausible:** An apparent reliability break is sometimes a measurement break.
- **Strongest rival:** The notes explicitly rule it out.
- **Discriminating test:** Check that successes plus failures still equal scheduled jobs across the break.
- **Evidence so far:** Both windows reconcile exactly.
- **Next check:** None.

## Evidence Log

- Claim: Success rate fell from 98.0% to 84.0% at the week of 2026-03-09.
  - Source: examples/local-sources/exports_weekly.csv
  - Supports: H1
  - Caveat or freshness limit: Static weekly aggregate; no per-job detail.
- Claim: Scheduled volume rose only about 2% between the windows.
  - Source: examples/local-sources/exports_weekly.csv
  - Supports: Rejects H2
  - Caveat or freshness limit: Weekly means; within-week peaks are not visible.
- Claim: Average queue wait rose from 8.0 to 42.0 minutes in the same week.
  - Source: examples/local-sources/exports_weekly.csv
  - Supports: H1 (queue contention mechanism)
  - Caveat or freshness limit: Weekly mean, not a peak measure.
- Claim: The scheduler moved heavy exports into business hours on 2026-03-09.
  - Source: examples/local-sources/context/change-log.md
  - Supports: H1
  - Caveat or freshness limit: Operational note, not an audited config diff.

## Dead Ends

- Volume spike: ruled out, scheduled jobs flat.
- Random variance: the step change aligns to the schedule change and holds for five post weeks.
- February retry-policy tweak: predates the inflection by two weeks; success rate held at 98% until the schedule change.

## Open Questions

- Which tenants or job classes absorbed the failures? The weekly aggregate cannot say.
- Does the queue recover as the new schedule settles, or is the loss persistent?

## Final Challenge

- Independent reviewer: demo-reviewer-subagent
- Strongest competing explanation: A volume spike or unrelated platform change in the same window. Rejected because scheduled jobs stayed flat and the notes record no counting change.
- Weakest-supported material claim: That the February retry-policy tweak contributed materially. It predates the inflection by two weeks and success rate held at 98% until the schedule change.
- Most fragile source or calculation: Partial-week data at the window edges, and reliance on a single weekly aggregate file. Re-checked; the step change holds across all full post-change weeks.
- Resolution: resolved. The conclusion survives challenge; the single-source limitation is disclosed in Risks And Caveats.
