# Research Plan

### T1: Confirm the post-change export reliability break
**Priority:** high
**Source:** Snowflake
**Objective:** Confirm whether export success rate and failure counts changed materially after the scheduler change and localize the break.
**Main Explanation:** Queue contention from rescheduled heavy jobs reduced success rate.
**Strongest Rival:** The apparent break is mostly volume growth or ordinary variance.
**Discriminating Test:** Compare pre/post success rate, failures, and queue minutes while holding scheduled volume flat, then verify the same inflection in a second metric source.
**Evidence Needed:** A concentrated reliability drop with consistent timing across at least two sources.
**Completion Threshold:** done when the affected window and relative magnitude are explicit; blocked when the necessary queue cut is unavailable; pivot when the break disappears after cross-checking.
**Confounders / Freshness Risks:** Partial-period March data and concurrent maintenance can distort the pre/post picture.
**Cross-Check:** Validate the change in both warehouse export metrics and a second source or derived queue metric.
**Depends on:** none
**Status:** pending

### T2: Test whether scheduled volume spiked first
**Priority:** high
**Source:** Snowflake + local context
**Objective:** Determine whether rising scheduled jobs explains part of the success-rate drop.
**Main Explanation:** More jobs were queued during the change window, overwhelming capacity without queue contention from scheduling alone.
**Strongest Rival:** Scheduled volume stayed steady and the problem is queue contention from timing.
**Discriminating Test:** Compare scheduled job counts before and after the change, then test whether volume alone explains the failure growth.
**Evidence Needed:** A measurable volume shift that aligns in timing with the success-rate decline.
**Completion Threshold:** done when volume contribution is ranked against queue effects; blocked when comparable cuts are missing; pivot when volume stays stable.
**Confounders / Freshness Risks:** Snapshot cutoff dates may lag live warehouse data.
**Cross-Check:** Reconcile scheduled-volume trends with queue-minute telemetry using one shared cutoff date.
**Depends on:** T1
**Status:** pending

### T3: Bound measurement and freshness risk
**Priority:** medium
**Source:** Knowledge + Snowflake
**Objective:** Determine whether counting or freshness issues exaggerate the apparent reliability drop.
**Main Explanation:** Metric definition changes near the scheduler change make failures look larger than they are.
**Strongest Rival:** Independent sources agree on the same decline, so measurement issues are secondary.
**Discriminating Test:** Recompute the pre/post comparison with a matched cutoff date and an independent metric definition.
**Evidence Needed:** A concrete source mismatch or confirmed counting change that overlaps the break.
**Completion Threshold:** done when measurement risk is ruled in as material or bounded tightly enough that the remaining explanation is still actionable.
**Confounders / Freshness Risks:** Snapshot exports and live models may not share the same cutoff date.
**Cross-Check:** Compare the change-period trend across warehouse, exported, and change-log evidence.
**Depends on:** T1
**Status:** pending
