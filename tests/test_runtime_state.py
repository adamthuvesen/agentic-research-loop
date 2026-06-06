from __future__ import annotations

import pytest

from agentic_research_loop.runtime_state import (
    AttemptRecord,
    CycleSummary,
    ProgressState,
    StatusState,
)


def test_progress_state_round_trips_known_and_extra_fields() -> None:
    payload = {
        "status": "active",
        "cycle_count": 2,
        "consecutive_no_progress_cycles": 1,
        "consecutive_failures": 0,
        "pending_challenge_cycle": True,
        "last_challenge_outcome": "queued",
        "stop_reason": None,
        "future_field": "keep me",
    }

    state = ProgressState.from_payload(payload)

    assert state.cycle_count == 2
    assert state.to_payload() == payload


def test_progress_state_defaults_historical_optional_fields() -> None:
    state = ProgressState.from_payload(
        {
            "status": "active",
            "cycle_count": 1,
            "consecutive_no_progress_cycles": 0,
            "stop_reason": None,
        }
    )

    assert state.consecutive_failures == 0
    assert state.pending_challenge_cycle is False
    assert state.last_challenge_outcome is None


def test_progress_state_rejects_non_object_payload() -> None:
    with pytest.raises(ValueError, match="progress.json"):
        ProgressState.from_payload([])


def test_progress_state_rejects_bad_field_shape() -> None:
    with pytest.raises(ValueError, match="cycle_count"):
        ProgressState.from_payload({"status": "active", "cycle_count": "one"})


def test_status_state_round_trips_extra_fields() -> None:
    payload = {
        "case_id": "case-1",
        "mode": "autonomous",
        "template": "root-cause",
        "status": "idle",
        "runner_name": None,
        "active_cycle_id": None,
        "active_attempt": None,
        "last_attempt_outcome": "progress",
        "stop_reason": None,
        "updated_at": "2026-04-25T00:00:00+00:00",
    }

    assert StatusState.from_payload(payload).to_payload() == payload


def test_attempt_record_round_trips_runner_fields() -> None:
    payload = {
        "attempt": 1,
        "returncode": 0,
        "timed_out": False,
        "elapsed_seconds": 1.25,
    }

    assert AttemptRecord.from_payload(payload).to_payload() == payload


def test_cycle_summary_round_trips_attempts_and_extra_fields() -> None:
    payload = {
        "cycle_id": "0001",
        "completed_at": "2026-04-25T00:00:00+00:00",
        "result": "progress",
        "made_progress": True,
        "challenge_cycle": False,
        "completion_marker": "CYCLE_DONE",
        "attempts": [{"attempt": 1, "returncode": 0, "timed_out": False}],
        "diagnostic": "keep me",
    }

    assert CycleSummary.from_payload(payload).to_payload() == payload


def test_cycle_summary_rejects_bad_attempts_shape() -> None:
    with pytest.raises(ValueError, match="attempts"):
        CycleSummary.from_payload(
            {
                "cycle_id": "0001",
                "completed_at": "2026-04-25T00:00:00+00:00",
                "result": "failed",
                "made_progress": False,
                "attempts": {},
            }
        )
