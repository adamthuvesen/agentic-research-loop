# Research Notes

## Working Theory

- Current best explanation: The 2026-03-09 scheduler change moved heavy export jobs into business hours, overloading the shared queue and cutting success rate.
- Confidence: high.
- What would change this: a non-scheduler change in the same window, or a metric-definition shift.

## Evidence Log

- Success rate: 98.0% -> 84.0% (-14.0 pp).
- Scheduled jobs: +2.0% (flat) — not a volume problem.
- Failed jobs: +716.0% vs pre-change baseline.
- Avg queue minutes: 8.0 -> 42.0 (+425.0%).
- The inflection week matches the documented scheduler change; no counting change in the window.

## Rejected Leads

- Volume spike: ruled out, scheduled jobs flat.
- Random variance: the step change aligns to the schedule change and holds for five post weeks.

## Challenge Review

- Strongest competing explanation tested: a volume spike or unrelated platform change in the same window. Rejected — scheduled jobs stayed flat, and the context notes record no counting change.
- Weakest-supported claim tested: that the Feb retry-policy tweak contributed materially. It predates the inflection by two weeks and success rate held at 98% until the schedule change.
- Most fragile dependency: partial-week data at the window edges. Re-checked — the step change holds across the full post-change weeks.
- Outcome: Resolved. The conclusion survives challenge.
