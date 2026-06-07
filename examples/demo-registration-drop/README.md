# Demo case: registration drop (offline)

This is the committed output of the offline demo — a complete root-cause case
produced with no network, no LLM, and no credentials, by the deterministic
`demo` runner over the synthetic data in [`../local-sources/`](../local-sources/).

Regenerate it yourself:

```bash
uv run research init registration-drop --template root-cause --mode autonomous \
  --context-path examples/local-sources
uv run research run <slug> --runner demo --max-cycles 6
```

The case runs `plan → explore → build evidence → conclude → challenge`, then
closes. Read [`report.md`](report.md) for the answer and the `## Challenge Review`
section for the challenge pass.
