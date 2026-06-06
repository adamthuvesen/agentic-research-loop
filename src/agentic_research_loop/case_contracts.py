from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .io import load_json_object_or_empty, read_text
from .layout import brief_path, status_json_path

VALID_MODES = frozenset({"quick", "guided", "autonomous"})
VALID_TEMPLATES = frozenset({"exploration", "root-cause", "comparison"})

ROOT_CAUSE_DESIGN_FIELDS: tuple[str, ...] = (
    "Discriminating Test",
    "Strongest Rival",
    "Completion Threshold",
    "Cross-Check",
)

CHALLENGE_REVIEW_HEADING = "Challenge Review"


def brief_mode_and_template(brief_text: str) -> tuple[str | None, str | None]:
    """Parse mode/template from brief markdown metadata (legacy fallback)."""
    mode_match = re.search(r"Selected mode:\s*`([^`]+)`", brief_text)
    template_match = re.search(
        r"(?:Research|Investigation) shape:\s*`([^`]+)`", brief_text
    )
    return (
        mode_match.group(1) if mode_match else None,
        template_match.group(1) if template_match else None,
    )


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
        status = load_json_object_or_empty(status_json_path(case_path))
        mode = status.get("mode")
        template = status.get("template")
        status_mode = mode if isinstance(mode, str) and mode else None
        status_template = template if isinstance(template, str) and template else None
        if status_mode and status_template:
            return cls(mode=status_mode, template=status_template)

        brief_text = (
            read_text(brief_path(case_path)) if brief_path(case_path).exists() else ""
        )
        brief_mode, brief_template = brief_mode_and_template(brief_text)
        return cls(
            mode=status_mode or brief_mode,
            template=status_template or brief_template,
        )

    @classmethod
    def from_values(cls, *, mode: str, template: str) -> CaseProfile:
        return cls(mode=mode, template=template)
