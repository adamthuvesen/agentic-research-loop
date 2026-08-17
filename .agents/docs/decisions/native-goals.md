# Use Native Goals For Research Execution

Date: 2026-08-17

## Decision

Run autonomous research inside the Claude Code or Codex native `/goal`. Keep this
repo as a research kit: case framing, read-only source access, durable artifacts,
and deterministic validation.

Remove the cycle loop, the subprocess runners, completion markers, progress
hashing, stall and failure counters, machine lifecycle state, the permission
bypass flags, the status renderer, and the publishing layer.

## Why

The loop reimplemented persistence and continuation that the clients now provide,
and its own mechanisms were weaker than the thing they substituted for:

- **Progress-by-hash measured writing, not research.** Progress was a SHA-256
  diff of `notes.md` and `report.md`. A cycle that spent its budget on legitimate
  tool work without writing counted as no progress, and three of those killed the
  run.
- **Marker-in-stdout was a parser defending against prose.** Detection stripped
  fenced code, required exactly one `<promise>` match, and required it to be
  terminal — three rules that existed only because the model might write a
  sentence.
- **A cold subprocess per cycle discarded context every iteration** and
  re-serialized case state into a fresh prompt. `research resume` was a literal
  alias for `run`: there was never a session to resume.
- **`--dangerously-skip-permissions` existed only because the loop was headless.**

Upstream evidence pointed the same way. A sibling project ran both designs on the
same question with the same model; the native goal completed unattended while the
custom runtime produced nothing usable. The proximate cause there was a bug — the
cycle prompt used relative artifact paths, so correct analysis was written into
the wrong directory and progress detection saw unchanged files. That is a
one-line fix, not an architectural verdict, and it should not be quoted as proof
that native goals are categorically better. It is a fair illustration of the
failure surface a second execution system buys you, which is the actual argument.

## Consequences

- Users start inside Claude Code or Codex with one native `/goal` naming the
  `research-goal` skill. Outside a goal, the skill returns the launch command.
- Case artifacts are the only durable record. There is no `state/` directory.
  Older cases with one remain readable; validation ignores it.
- Every path in the generated contract is absolute. `templates.goal_prompt` and
  `research.resolve_case_path` both enforce that boundary, because misdirected
  writes are the failure mode this design is most exposed to.
- The challenge cycle becomes a delegated independent subagent, verified by
  parsing `## Final Challenge` in `notes.md` rather than by machine state.
- **Unattended execution is gone.** `research run` could be scripted or
  scheduled; `/goal` needs a live client session. No current workflow depends on
  it. If one appears, the answer is a thin Agent SDK entry point kept separate
  from the goal flow, not a revived cycle loop.
- **Per-cycle prompts and outputs are gone.** Debugging a case that went sideways
  means reading a client transcript instead of `state/cycles/<id>/prompt.md`.
  `queries.sql` and `source-objects.md` partly offset this: they are better
  provenance than the case directory previously held.
- Client goal behavior is an unpinned external dependency, so
  [the canary](../../../evals/native-goal/README.md) stays part of release
  evaluation.
