# Metric definitions (synthetic)

> Fictional offline demo data. Not from any real company or customer.

The columns in `exports_weekly.csv`:

| Column | Meaning |
|--------|---------|
| `jobs_scheduled` | Export jobs queued for the week |
| `jobs_succeeded` | Jobs that finished and delivered output |
| `jobs_failed` | Jobs that timed out, were rejected from queue, or failed delivery |
| `avg_queue_minutes` | Mean time jobs waited in the export queue before starting |

**Success rate** = `jobs_succeeded / jobs_scheduled` (expressed as a percentage).

**Queue pressure** rises when heavy jobs share the queue with interactive load —
long waits often precede timeouts and failures.
