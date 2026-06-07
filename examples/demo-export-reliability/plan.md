# Research Plan

### T1: Confirm and localize the export reliability break
**Priority:** high
**Source:** Local files
**Objective:** Confirm export success rate fell and check whether volume or queue pressure changed.
**Main Explanation:** Queue contention from rescheduled heavy jobs caused more failures.
**Strongest Rival:** Job volume rose and overwhelmed capacity, unrelated to the schedule change.
**Discriminating Test:** Compare success rate, failure count, and queue minutes before vs after the change week.
**Evidence Needed:** A step down in success rate with a matching queue spike while scheduled volume stays flat.
**Completion Threshold:** done when the break magnitude and timing are explicit.
**Confounders / Freshness Risks:** Partial-week data near the window edges.
**Cross-Check:** Reconcile with the scheduler change date in the context notes.
**Depends on:** none
**Status:** pending

### T2: Tie the break to the scheduler change
**Priority:** medium
**Source:** Local files (context notes)
**Objective:** Check whether the documented schedule change lines up with the inflection.
**Main Explanation:** Moving heavy exports into business hours overloaded the shared queue.
**Strongest Rival:** An unrelated platform or counting change explains the failures.
**Discriminating Test:** Match the inflection week to the documented 2026-03-09 schedule change.
**Evidence Needed:** Timing alignment plus a plausible queue-contention mechanism.
**Completion Threshold:** done when timing and mechanism are established.
**Confounders / Freshness Risks:** Other operational changes in the same window.
**Cross-Check:** Confirm no metric-definition change in the window.
**Depends on:** T1
**Status:** pending
