from __future__ import annotations


from agentic_research_loop.loop import classify_cycle_outcome, detect_completion_marker


def test_classify_cycle_outcome_progress() -> None:
    outcome = classify_cycle_outcome(
        completion_marker="<promise>CYCLE_DONE</promise>",
        challenge_cycle=False,
        made_progress=True,
    )

    assert outcome.result == "progress"
    assert outcome.challenge_required is False
    assert outcome.complete is False


def test_classify_cycle_outcome_no_progress() -> None:
    outcome = classify_cycle_outcome(
        completion_marker="<promise>CYCLE_DONE</promise>",
        challenge_cycle=False,
        made_progress=False,
    )

    assert outcome.result == "no_progress"


def test_classify_cycle_outcome_challenge_required() -> None:
    outcome = classify_cycle_outcome(
        completion_marker="<promise>CASE_COMPLETE</promise>",
        challenge_cycle=False,
        made_progress=True,
    )

    assert outcome.result == "challenge_required"
    assert outcome.challenge_required is True
    assert outcome.complete is False


def test_classify_cycle_outcome_complete() -> None:
    outcome = classify_cycle_outcome(
        completion_marker="<promise>CASE_COMPLETE</promise>",
        challenge_cycle=True,
        made_progress=True,
    )

    assert outcome.result == "complete"
    assert outcome.challenge_required is False
    assert outcome.complete is True


def test_classify_cycle_outcome_challenge_complete_requires_progress() -> None:
    outcome = classify_cycle_outcome(
        completion_marker="<promise>CASE_COMPLETE</promise>",
        challenge_cycle=True,
        made_progress=False,
    )

    assert outcome.result == "no_progress"
    assert outcome.complete is False


def test_detect_completion_marker_accepts_trailing_whitespace() -> None:
    text = "I have finished.\n\n<promise>CASE_COMPLETE</promise>   \n"
    assert detect_completion_marker(text) == "<promise>CASE_COMPLETE</promise>"


def test_detect_completion_marker_ignores_marker_in_fenced_code_block() -> None:
    text = (
        "Here is an example:\n\n"
        "```\n<promise>CASE_COMPLETE</promise>\n```\n\n"
        "Continuing with more work.\n"
    )
    assert detect_completion_marker(text) is None


def test_detect_completion_marker_detects_cycle_done() -> None:
    text = "Work done.\n<promise>CYCLE_DONE</promise>\n"
    assert detect_completion_marker(text) == "<promise>CYCLE_DONE</promise>"


def test_detect_completion_marker_rejects_multiple_markers() -> None:
    text = "<promise>CYCLE_DONE</promise>\n<promise>CASE_COMPLETE</promise>\n"
    assert detect_completion_marker(text) is None


def test_detect_completion_marker_rejects_non_terminal_marker() -> None:
    text = "<promise>CYCLE_DONE</promise>\nActually, one more thing.\n"
    assert detect_completion_marker(text) is None
