# Worked example: a real Claude run (offline, local sources only)

This is the output of a **real Claude Code agent** working the case end-to-end
with the `claude-local` runner — no MCP servers, no external sources, just the
synthetic data in [`../local-sources/`](../local-sources/):

```bash
uv run research init registration-drop --template root-cause --mode autonomous \
  --context-path examples/local-sources
uv run research run <slug> --runner claude-local --max-cycles 8
```

The agent ran `plan → 4 investigation cycles → challenge cycle → complete`
(5 cycles, ~22 min) and closed the case on its own.

Unlike the deterministic [`../demo-registration-drop/`](../demo-registration-drop/)
(produced by the scripted `demo` runner), this is a **non-deterministic snapshot**
— a real model reasoning over the data. Re-running will produce different prose
and may reach different depth. What it shows: the agent went past the obvious
finding — it decomposed the drop into two distinct effects, computed a
counterfactual impact split, noticed `activations` is a derived column (so
"downstream quality intact" is true by construction, not evidence), and used the
challenge cycle to cap its own confidence at "single-source, circumstantial"
because no cross-source verification was possible offline.

Read [`report.md`](report.md) for the full writeup.
