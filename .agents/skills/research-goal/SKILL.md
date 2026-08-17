---
name: research-goal
description: Run a bounded research case inside an active Claude Code or Codex native /goal, or prepare the launch command when no goal is active. Use for starting, continuing, or completing a reproducible investigation without a repository agent runtime.
---

# Research Goal

The repository CLI is internal plumbing. Execution stays inside the current
Claude Code or Codex session.

## Choose the mode first

- **A native `/goal` is active** → execution mode. Scaffold if needed, then
  complete the investigation in this session.
- **No native goal is active** → preparation mode. Scaffold if needed, then
  return the generated `/goal` command for the user to submit.

Do not run the investigation outside a native goal. A case run without one has
no persistence: the work dies with the turn.

## Prepare the case

1. Work from the repository root.
2. Resolve an existing case with `uv run research goal <case>`, or scaffold a
   new one:

   ```bash
   uv run research init <slug> \
     --question "<specific question>" \
     --template <exploration|root-cause|comparison>
   ```

   Sources default to everything registered in `config/sources.json`. Narrow
   them with `--no-<source>`, focus one with `--<source>-hint TEXT`, attach
   read-only local files with `--context-path PATH`, or pass `--local-only` to
   investigate attached files alone. Check what is wired with
   `uv run research source list`.

3. Read `brief.md`. Resolve placeholders that would materially change the
   answer. Do not ask for confirmation when the question is already bounded.
4. Run `uv run research validate <case>` and fix structural failures.
5. Run `uv run research goal <case>` to get the canonical contract with the
   absolute case path.

## Execution mode

Treat the generated contract as the operating instructions for the active goal.
Do not submit it as a nested slash command, return it to the user, or stop after
scaffolding.

Continue immediately with the research. Write only inside the absolute case
path, use only the sources the brief allows, maintain every required artifact,
delegate the final challenge to an independent subagent, run strict validation,
fix every failure, and finish with the validation result and conclusion visible
in your final response.

## Preparation mode

Return the case path and the exact generated `/goal` command in a code block.
Do not begin the investigation.

---

Never launch a Claude or Codex subprocess, invoke an Agent SDK, or add a custom
continuation loop. Native `/goal` owns persistence, continuation, pause, and
resume.
