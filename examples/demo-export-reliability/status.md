# Research Status: 2026-06-07-export-reliability

- Status: `idle`
- Cycle count: `4`
- Challenge status: `passed`
- Sources in play: `local-context`
- Report state: `substantive`

## Current Answer

Export success rate stepped down from 98.0% to 84.0% after the 2026-03-09 scheduler change that moved large warehouse exports into business hours. Scheduled volume held flat (+2.0%), so the loss is a queue contention problem, not a demand spike. Average queue wait rose from 8 to 42 minutes in the same window...

## Working Theory

- Current best explanation: Business-hours scheduling overloaded the shared export queue, causing more timeouts and failures.
- Confidence: high.
- What would change this: a volume spike, a metric-definition change, or live telemetry showing flat queue minutes.

## Recent Cycles

- `0002`: `progress`
- `0003`: `challenge_required`
- `0004`: `complete`

## System

- Runner: `demo`
- Active cycle: `n/a`
- Stop reason: `case_complete`
