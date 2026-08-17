# Native Goal Canary

Checks that a native Claude Code or Codex goal can complete a bounded root-cause
case with correct arithmetic, preserved evidence, and no operator steering.

This repo does not control how its clients implement goals. That behavior is an
external dependency with no version pin, so it gets tested like one. Keep the
canary even when the architecture feels settled.

The canary needs **no API keys, no MCP servers, and no network** — it runs
against the synthetic dataset committed under `examples/local-sources/`.

## Run

Prepare a blind workspace and start one fresh client session inside it. The
export carries your current uncommitted changes but strips the committed demo
case, prior results, and the decision record, so the run cannot read the answer.

```bash
canary_root="$(mktemp -d)/agentic-research-loop"
uv run python evals/native-goal/prepare_workspace.py "$canary_root"
cd "$canary_root"
test ! -e evals/native-goal/results
test ! -e examples/demo-export-reliability
uv sync --dev
uv run research init export-reliability-canary \
  --template root-cause \
  --local-only \
  --context-path examples/local-sources \
  --from-spec evals/native-goal/spec
uv run research goal <created-case>
```

Submit the printed command as a native `/goal` in Claude Code or Codex. Do not
steer the analysis. Score the finished artifacts against [rubric.md](rubric.md).

A run passes only with no critical failure and at least 90 points. Record the
client, version, model, effort, wall time, interventions, validation result, and
score under `results/`.
