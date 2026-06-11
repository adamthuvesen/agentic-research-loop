# Runtime Playbook

Use this playbook to stay effective, not compliant.

## Source strategy

- Start from `state/sources.json`, but adapt it when the work teaches you something better.
- Prefer the smallest source that can answer the question well.
- Pivot quickly when a source path is weak.

## Findings

Use `state/findings.json` when the case needs structured findings.
Each entry needs just an `id` and a `summary`. Add optional fields like
`confidence` when they help, but do not let schema overhead slow you down.

A good finding is one you would tell a teammate: concrete, specific, and
directly relevant to the case question.

## Hypothesis discipline

Treat `notes.md` as the cockpit:

- Keep the working theory current.
- Track hypotheses as active, supported, weakened, rejected, or pivoted.
- Record the strongest rival before you call a thread done.
- Put evidence in the evidence log with source family, source detail, what it supports, and caveats.
- Preserve dead ends. They are useful proof that a tempting explanation was checked.

Before each cycle, pick one or two hypotheses, leads, or plan threads. Ask what
would change your confidence, then go get that evidence.

## Steering between cycles

Humans steer by editing `notes.md` or `plan.md` before the next cycle. The runtime
does not read a separate feedback file. Keep `brief.md` stable unless reframing the case.

## Challenge cycles

When you believe the case is complete, emit `<promise>CASE_COMPLETE</promise>`. The
runtime will run a challenge cycle before actually closing. During the challenge:

- Name the strongest rival explanation and whether the report distinguishes it.
- Flag the weakest-supported claim and most fragile dependency.
- Declare whether objections are resolved or still open.

If material risks remain unresolved, the case reopens. This is expected — treat
the challenge as a quality gate, not an obstacle.

## Good loop behavior

- Improve the answer, not just the artifacts.
- Keep `report.md` readable.
- Keep `notes.md` honest.
- Weaken or reject hypotheses when evidence does not support them.
- Keep `state/sources.json` current when the source strategy changes.
- Leave a smarter starting point for the next cycle.
- Write visible reasoning each cycle — only `notes.md` and `report.md` changes count as progress.
