from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _mapping(payload: Any, *, name: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"{name} must be a JSON object")
    return dict(payload)


def _int_field(payload: dict[str, Any], key: str, *, default: int | None = None) -> int:
    value = payload.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    return value


def _bool_field(
    payload: dict[str, Any], key: str, *, default: bool | None = None
) -> bool:
    value = payload.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _str_field(payload: dict[str, Any], key: str, *, default: str | None = None) -> str:
    value = payload.get(key, default)
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _optional_str_field(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{key} must be a string or null")
    return value


@dataclass
class ProgressState:
    status: str
    cycle_count: int = 0
    consecutive_no_progress_cycles: int = 0
    consecutive_failures: int = 0
    pending_challenge_cycle: bool = False
    last_challenge_outcome: str | None = None
    stop_reason: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(
        cls, payload: Any, *, name: str = "progress.json"
    ) -> "ProgressState":
        values = _mapping(payload, name=name)
        known = {
            "status",
            "cycle_count",
            "consecutive_no_progress_cycles",
            "consecutive_failures",
            "pending_challenge_cycle",
            "last_challenge_outcome",
            "stop_reason",
        }
        return cls(
            status=_str_field(values, "status"),
            cycle_count=_int_field(values, "cycle_count", default=0),
            consecutive_no_progress_cycles=_int_field(
                values, "consecutive_no_progress_cycles", default=0
            ),
            consecutive_failures=_int_field(values, "consecutive_failures", default=0),
            pending_challenge_cycle=_bool_field(
                values, "pending_challenge_cycle", default=False
            ),
            last_challenge_outcome=_optional_str_field(
                values, "last_challenge_outcome"
            ),
            stop_reason=_optional_str_field(values, "stop_reason"),
            extra={key: value for key, value in values.items() if key not in known},
        )

    def to_payload(self) -> dict[str, Any]:
        payload = dict(self.extra)
        payload.update(
            {
                "status": self.status,
                "cycle_count": self.cycle_count,
                "consecutive_no_progress_cycles": self.consecutive_no_progress_cycles,
                "consecutive_failures": self.consecutive_failures,
                "pending_challenge_cycle": self.pending_challenge_cycle,
                "last_challenge_outcome": self.last_challenge_outcome,
                "stop_reason": self.stop_reason,
            }
        )
        return payload


@dataclass
class StatusState:
    status: str
    case_id: str | None = None
    mode: str | None = None
    template: str | None = None
    runner_name: str | None = None
    active_cycle_id: str | None = None
    active_attempt: int | None = None
    last_attempt_outcome: str | None = None
    stop_reason: str | None = None
    updated_at: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Any, *, name: str = "status.json") -> "StatusState":
        values = _mapping(payload, name=name)
        known = {
            "status",
            "case_id",
            "mode",
            "template",
            "runner_name",
            "active_cycle_id",
            "active_attempt",
            "last_attempt_outcome",
            "stop_reason",
            "updated_at",
        }
        active_attempt = values.get("active_attempt")
        if active_attempt is not None and (
            not isinstance(active_attempt, int) or isinstance(active_attempt, bool)
        ):
            raise ValueError("active_attempt must be an integer or null")
        return cls(
            status=_str_field(values, "status"),
            case_id=_optional_str_field(values, "case_id"),
            mode=_optional_str_field(values, "mode"),
            template=_optional_str_field(values, "template"),
            runner_name=_optional_str_field(values, "runner_name"),
            active_cycle_id=_optional_str_field(values, "active_cycle_id"),
            active_attempt=active_attempt,
            last_attempt_outcome=_optional_str_field(values, "last_attempt_outcome"),
            stop_reason=_optional_str_field(values, "stop_reason"),
            updated_at=_optional_str_field(values, "updated_at"),
            extra={key: value for key, value in values.items() if key not in known},
        )

    def to_payload(self) -> dict[str, Any]:
        payload = dict(self.extra)
        payload.update(
            {
                "status": self.status,
                "case_id": self.case_id,
                "mode": self.mode,
                "template": self.template,
                "runner_name": self.runner_name,
                "active_cycle_id": self.active_cycle_id,
                "active_attempt": self.active_attempt,
                "last_attempt_outcome": self.last_attempt_outcome,
                "stop_reason": self.stop_reason,
                "updated_at": self.updated_at,
            }
        )
        return payload


@dataclass
class AttemptRecord:
    attempt: int
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Any, *, name: str = "attempt") -> "AttemptRecord":
        values = _mapping(payload, name=name)
        return cls(
            attempt=_int_field(values, "attempt"),
            extra={key: value for key, value in values.items() if key != "attempt"},
        )

    def to_payload(self) -> dict[str, Any]:
        return {"attempt": self.attempt, **self.extra}


@dataclass
class CycleSummary:
    cycle_id: str
    completed_at: str
    result: str
    made_progress: bool
    attempts: list[AttemptRecord] = field(default_factory=list)
    challenge_cycle: bool | None = None
    completion_marker: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(
        cls, payload: Any, *, name: str = "cycle summary"
    ) -> "CycleSummary":
        values = _mapping(payload, name=name)
        known = {
            "cycle_id",
            "completed_at",
            "result",
            "made_progress",
            "attempts",
            "challenge_cycle",
            "completion_marker",
        }
        attempts = values.get("attempts", [])
        if not isinstance(attempts, list):
            raise ValueError("attempts must be a list")
        challenge_cycle = values.get("challenge_cycle")
        if challenge_cycle is not None and not isinstance(challenge_cycle, bool):
            raise ValueError("challenge_cycle must be a boolean or null")
        return cls(
            cycle_id=_str_field(values, "cycle_id"),
            completed_at=_str_field(values, "completed_at"),
            result=_str_field(values, "result"),
            made_progress=_bool_field(values, "made_progress"),
            attempts=[
                AttemptRecord.from_payload(item, name=f"attempts[{index}]")
                for index, item in enumerate(attempts)
            ],
            challenge_cycle=challenge_cycle,
            completion_marker=_optional_str_field(values, "completion_marker"),
            extra={key: value for key, value in values.items() if key not in known},
        )

    def to_payload(self) -> dict[str, Any]:
        payload = dict(self.extra)
        payload.update(
            {
                "cycle_id": self.cycle_id,
                "completed_at": self.completed_at,
                "result": self.result,
                "made_progress": self.made_progress,
                "attempts": [attempt.to_payload() for attempt in self.attempts],
            }
        )
        if self.challenge_cycle is not None:
            payload["challenge_cycle"] = self.challenge_cycle
        if self.completion_marker is not None:
            payload["completion_marker"] = self.completion_marker
        return payload


@dataclass(frozen=True)
class CycleOutcome:
    result: str
    challenge_required: bool
    complete: bool
