# Research Report

## Question

Why did the weekly batch-export success rate drop in March 2026?

## Executive Summary

Export success rate stepped down from 98.0% to 84.0% after the 2026-03-09
scheduler change that moved **large warehouse export jobs** from overnight into
business hours. Scheduled volume held flat (+2.0%), so the loss is a **queue
contention** problem, not a demand spike. Average queue wait rose from 8 to 42
minutes in the same window, consistent with heavy jobs competing with interactive
load on the shared export queue.

## Ranked Causes

1. **Business-hours scheduling overloaded the export queue** (leading). Timing,
   queue minutes, and flat scheduled volume all point here.
2. Residual retry-policy noise (minor): a smaller February tweak did not move the
   inflection.

## Evidence

Pre-change is the nine weeks from 2026-01-05 to 2026-03-02; post-change is the
five weeks from 2026-03-09 to 2026-04-06.

| Measure | Pre | Post | Change |
| --- | ---: | ---: | ---: |
| Success rate | 98.0% | 84.0% | -14.0 pp |
| Jobs failed | 900 | 4,080 | +353% |
| Jobs scheduled | 44,990 | 25,500 | +2.0% per week |
| Avg queue minutes | 8.0 | 42.0 | +425% |

The inflection week is exactly the week of the documented scheduler change, and
`context/change-log.md` records no change to success/failure counting logic in
the window.

## Reconciliation

Successes and failures reconcile to scheduled jobs in both windows: pre-change
44,090 + 900 = 44,990; post-change 21,420 + 4,080 = 25,500. Weekly totals are
compared as pooled rates over each window, not as a mean of weekly rates.

## Rejected Leads

- **Volume spike**: ruled out. Weekly scheduled jobs rose about 2% (4,998.9 →
  5,100) against an 8× rise in failures.
- **Random variance**: ruled out. The step change aligns to the scheduler change
  and holds across all five post-change weeks.
- **Metric definition change**: ruled out. The columns reconcile on both sides of
  the break, and the operational notes state counting logic did not change.

## Risks And Caveats

- The window ends at 2026-04-06, so the post-change period is five weeks. A
  longer window could reveal partial recovery as the queue settles.
- All evidence comes from one weekly aggregate file. There is no per-job or
  per-tenant cut to confirm which workloads absorbed the failures.
- Queue minutes are a weekly mean; a within-week peak could carry more of the
  effect than the average suggests.

## Recommended Next Actions

- Move large warehouse exports back to the overnight window and monitor queue
  minutes.
- Cap concurrent heavy exports during business hours until the queue SLO
  recovers.
