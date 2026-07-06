from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .io import load_json
from .layout import status_json_path

VALID_MODES = frozenset({"quick", "guided", "autonomous"})
VALID_TEMPLATES = frozenset({"exploration", "root-cause", "comparison"})

ROOT_CAUSE_DESIGN_FIELDS: tuple[str, ...] = (
    "Discriminating Test",
    "Strongest Rival",
    "Completion Threshold",
    "Cross-Check",
)

CHALLENGE_REVIEW_HEADING = "Challenge Review"


def _required_case_field(status: dict, key: str, valid_values: frozenset[str]) -> str:
    value = status.get(key)
    if not isinstance(value, str) or value not in valid_values:
        choices = ", ".join(sorted(valid_values))
        raise ValueError(f"status.json {key} must be one of: {choices}")
    return value


@dataclass(frozen=True)
class CaseProfile:
    mode: str | None
    template: str | None

    @property
    def is_autonomous_root_cause(self) -> bool:
        return self.mode == "autonomous" and self.template == "root-cause"

    @property
    def requires_challenge(self) -> bool:
        return self.is_autonomous_root_cause

    @property
    def strong_design_contract(self) -> bool:
        return self.is_autonomous_root_cause

    @classmethod
    def load(cls, case_path: Path) -> CaseProfile:
        status = load_json(status_json_path(case_path))
        if not isinstance(status, dict):
            raise ValueError("status.json must be a JSON object")
        return cls(
            mode=_required_case_field(status, "mode", VALID_MODES),
            template=_required_case_field(status, "template", VALID_TEMPLATES),
        )

    @classmethod
    def from_values(cls, *, mode: str, template: str) -> CaseProfile:
        return cls(mode=mode, template=template)
