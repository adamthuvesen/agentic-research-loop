# Evaluation Rubric

Score only what the case artifacts and the bundled CSV support. Every figure
below is derivable from `examples/local-sources/exports_weekly.csv`.

## Ground truth

Pre-break window is the nine weeks from `2026-01-05` to `2026-03-02`; the
post-break window is the five weeks from `2026-03-09` to `2026-04-06`.

| Measure | Pre | Post |
| --- | ---: | ---: |
| Jobs scheduled | 44,990 | 25,500 |
| Jobs succeeded | 44,090 | 21,420 |
| Jobs failed | 900 | 4,080 |
| Success rate | 98.0% | 84.0% |
| Failure rate | 2.0% | 16.0% |
| Avg queue minutes | 8.0 | 42.0 |

The break lands on the week starting **2026-03-09**, the same date as the
scheduler change in `examples/local-sources/context/change-log.md` that moved
heavy export jobs into business hours onto the shared queue. That is the largest
cause.

Weekly volume rises about 2% between the windows (mean 4,998.9 → 5,100), against
an 8× rise in failures. Volume growth cannot account for the change and should be
rejected on those numbers.

## Scoring

| Criterion | Points |
| --- | ---: |
| Pre and post success rates are correct (98.0% / 84.0%, or the equivalent failure rates) | 20 |
| The break is localized to the week starting 2026-03-09 | 20 |
| The scheduler change is named as the largest cause and tied to its dated note | 20 |
| The volume rival is quantified and rejected on the numbers | 15 |
| Queue minutes are used as an independent corroborating signal | 10 |
| Evidence is preserved: `source-objects.md` names the files used, `queries.sql` holds the SQL or an explicit no-SQL reason | 10 |
| The independent challenge is real: a named reviewer, findings, and a resolution | 5 |

Total: 100 points.

## Critical failures

Any one of these fails the canary regardless of score.

- A material datum, figure, source, or citation is fabricated.
- Arithmetic does not reconcile: the stated failures and successes do not sum to the stated scheduled jobs.
- Evidence comes from outside the bundled local files (web search, a live system, or model recall).
- The run sees the committed demo case, a prior canary result, or the decision record.
- The run claims completion without a usable report, or `research validate --strict` does not pass.
- The final challenge is self-reviewed rather than delegated to an independent subagent.
