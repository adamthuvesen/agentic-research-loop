# Change log (synthetic)

> Fictional offline demo data. Not from any real company or customer.

Northwind Analytics batch export platform — operational notes:

- **2026-03-09** — Rescheduled the **large warehouse export jobs** from overnight
  (02:00–06:00 UTC) into **business hours** (09:00–17:00 UTC) to align with
  on-call coverage. Heavy jobs now compete with interactive query load on the
  shared export queue.
- 2026-02-20 — Minor retry-policy tweak (no schedule change).
- 2026-01-05 — Start of the reporting window in `exports_weekly.csv`.

There was no change to success/failure counting logic in this window — weekly
metrics are comparable before and after the scheduler change.
