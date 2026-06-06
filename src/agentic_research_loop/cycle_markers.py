from __future__ import annotations

import re

from .runtime_state import CycleOutcome

DEFAULT_MAX_ATTEMPTS_PER_CYCLE = 2
CYCLE_DONE_MARKER = "<promise>CYCLE_DONE</promise>"
CASE_COMPLETE_MARKER = "<promise>CASE_COMPLETE</promise>"
CHALLENGE_REQUIRED_RESULT = "challenge_required"


def detect_completion_marker(output_text: str) -> str | None:
    text = re.sub(r"```.*?```", "", output_text, flags=re.DOTALL)
    markers = list(re.finditer(r"<promise>([^<]+)</promise>", text))
    if len(markers) != 1:
        return None
    marker_match = markers[0]
    if text[marker_match.end() :].strip():
        return None
    marker = marker_match.group(1).strip()
    if marker == "CASE_COMPLETE":
        return CASE_COMPLETE_MARKER
    if marker == "CYCLE_DONE":
        return CYCLE_DONE_MARKER
    return None


def classify_cycle_outcome(
    *,
    completion_marker: str,
    challenge_cycle: bool,
    made_progress: bool,
) -> CycleOutcome:
    requested_completion = completion_marker == CASE_COMPLETE_MARKER
    challenge_required = requested_completion and not challenge_cycle
    complete = requested_completion and challenge_cycle and made_progress
    if complete:
        result = "complete"
    elif challenge_required:
        result = CHALLENGE_REQUIRED_RESULT
    else:
        result = "progress" if made_progress else "no_progress"
    return CycleOutcome(
        result=result,
        challenge_required=challenge_required,
        complete=complete,
    )
