# Research Report

## Question

Why did weekly export job success rate drop in recent weeks?

## Executive Summary

Export success rate stepped down from 98.0% to
84.0% after the 2026-03-09 scheduler change that moved
**large warehouse export jobs** from overnight into business hours. Scheduled
volume held flat (+2.0%), so the loss is a **queue
contention** problem, not a demand spike. Average queue wait rose from
8 to 42 minutes in the same window,
consistent with heavy jobs competing with interactive load on the shared export queue.

## Ranked Causes

1. **Business-hours scheduling overloaded the export queue** (leading). Timing,
   queue minutes, and flat scheduled volume all point here.
2. Residual retry-policy noise (minor) — a smaller Feb tweak did not move the
   inflection.

## Evidence Highlights

- Success rate: 98.0% -> 84.0%.
- Scheduled jobs flat (+2.0%).
- Failed jobs up 716.0%.
- Avg queue minutes: 8.0 -> 42.0.

## Recommended Next Actions

- Move large warehouse exports back to the overnight window and monitor queue minutes.
- Cap concurrent heavy exports during business hours until queue SLO recovers.

## Confidence

High. The mechanism is well supported by timing, queue pressure, and flat volume.

## Challenge Review

- Strongest competing explanation tested: a volume spike or unrelated platform change in the same window. Rejected — scheduled jobs stayed flat, and the context notes record no counting change.
- Weakest-supported claim tested: that the Feb retry-policy tweak contributed materially. It predates the inflection by two weeks and success rate held at 98% until the schedule change.
- Most fragile dependency: partial-week data at the window edges. Re-checked — the step change holds across the full post-change weeks.
- Outcome: Resolved. The conclusion survives challenge.
