# Worked example: claude-local export reliability (pending)

This directory will hold a **real Claude Code agent** snapshot from a
`claude-local` run over the fictional Northwind Analytics export bundle in
[`../local-sources/`](../local-sources/).

## Not populated yet

We have not run the live research CLI for this snapshot. When you are ready:

```bash
uv run research init export-reliability --template root-cause --mode autonomous \
  --context-path examples/local-sources --local-only
uv run research run <slug> --runner claude-local --max-cycles 8
```

Copy `brief.md`, `plan.md`, `notes.md`, `report.md`, and `status.md` from the
completed case into this folder. Do **not** copy `state/` unless you explicitly
want cycle JSON in the example.

Unlike the deterministic [`../demo-export-reliability/`](../demo-export-reliability/)
case, a claude-local snapshot is non-deterministic — re-running will produce
different prose and depth.

This scenario is **fictional offline demo data**, not a real customer investigation.
