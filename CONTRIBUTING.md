# Contributing

Thanks for taking a look at Agentic Research Loop.

## Local Setup

```bash
uv sync --dev
uv run pre-commit install
```

## Before Opening A Pull Request

Run the same checks used by CI:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

Keep example data synthetic and reproducible. Do not commit real datasets,
investigation outputs, credentials, internal source names, or private business
context. Live research cases live under `research/` and are git-ignored by
default.

## Runner Changes

A runner is any command that accepts the cycle prompt on stdin and writes its
result to stdout (or to the agent-message file). The final message must include
exactly one completion marker:

- `<promise>CYCLE_DONE</promise>` — this cycle made progress; keep going.
- `<promise>CASE_COMPLETE</promise>` — the case is done (a root-cause case must
  still pass the mandatory challenge cycle before it actually closes).

See `config/runners/` for the built-in runner configs and
`runners/demo_runner.py` for a fully offline reference runner.
