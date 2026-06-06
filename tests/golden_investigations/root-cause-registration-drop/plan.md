# Research Plan

### T1: Confirm the post-launch registration break
**Priority:** high
**Source:** Snowflake
**Objective:** Confirm whether registrations and conversion changed materially after the launch and localize the break by segment.
**Main Explanation:** Launch friction reduced registration conversion for a concentrated user segment.
**Strongest Rival:** The apparent break is mostly traffic mix change or ordinary variance.
**Discriminating Test:** Compare pre/post registration conversion by landing page, device, and country, then verify the same inflection in a second metric source.
**Evidence Needed:** A concentrated conversion drop with consistent timing across at least two sources.
**Completion Threshold:** done when the affected segment and relative magnitude are explicit; blocked when the necessary segment cut is unavailable; pivot when the break disappears after cross-checking.
**Confounders / Freshness Risks:** Partial-period March data and attribution changes can distort the pre/post picture.
**Cross-Check:** Validate the change in both Snowflake registrations and a second source or derived funnel metric.
**Depends on:** none
**Status:** pending

### T2: Test whether upstream traffic quality softened first
**Priority:** high
**Source:** Web exports + Snowflake
**Objective:** Determine whether weaker qualified traffic explains part of the registration drop.
**Main Explanation:** High-intent traffic weakened before or during the launch window, lowering qualified registrations.
**Strongest Rival:** Upstream traffic stayed steady and the problem is downstream conversion only.
**Discriminating Test:** Compare high-intent traffic, query mix, and page-level visitor quality before and after launch, then test for a lead/lag relationship to registrations.
**Evidence Needed:** A measurable upstream softness that aligns in timing and affected slices with the registration decline.
**Completion Threshold:** done when upstream contribution is ranked against conversion effects; blocked when comparable traffic cuts are missing; pivot when traffic stays stable.
**Confounders / Freshness Risks:** Export cutoff dates may lag live warehouse data.
**Cross-Check:** Reconcile web-export trends with Snowflake visitor and registration models using one shared cutoff date.
**Depends on:** T1
**Status:** pending

### T3: Bound measurement and freshness risk
**Priority:** medium
**Source:** Knowledge + Snowflake + Confidence
**Objective:** Determine whether tracking, routing, or freshness issues exaggerate the apparent registration drop.
**Main Explanation:** Measurement changes near launch make the drop look larger than it is.
**Strongest Rival:** Independent sources agree on the same decline, so measurement issues are secondary.
**Discriminating Test:** Recompute the pre/post comparison with a matched cutoff date and an independent metric definition.
**Evidence Needed:** A concrete source mismatch or confirmed instrumentation change that overlaps the break.
**Completion Threshold:** done when measurement risk is ruled in as material or bounded tightly enough that the remaining explanation is still actionable.
**Confounders / Freshness Risks:** Snapshot exports and live models may not share the same cutoff date.
**Cross-Check:** Compare the launch-period trend across warehouse, exported, and experiment-timeline evidence.
**Depends on:** T1
**Status:** pending
