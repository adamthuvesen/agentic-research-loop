# Demo case: export reliability (offline)

This is the committed output shape for the offline demo — a complete root-cause case
produced with no network, no LLM, and no credentials, by the deterministic
`demo` runner over the synthetic data in [`../local-sources/`](../local-sources/).

Regenerate it yourself:

```bash
uv run research init export-reliability --template root-cause --mode autonomous \
  --context-path examples/local-sources --local-only
uv run research run <slug> --runner demo --max-cycles 6
```

The case runs `plan → explore → build evidence → conclude → challenge`, then
closes. Read [`report.md`](report.md) for the answer and the `## Challenge Review`
section for the challenge pass.

Figures in the committed copy match a direct run of `runners/demo_runner.py` over
`exports_weekly.csv`. After a live `research run`, refresh this folder from the
completed case under `research/<date>-export-reliability/` and regen replay:

```bash
uv run python viz/generate.py examples/demo-export-reliability
```
