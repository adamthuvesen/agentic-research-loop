from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .case_contracts import ROOT_CAUSE_DESIGN_FIELDS, CaseProfile
from .io import extract_section, load_json, read_text
from .layout import brief_path, findings_path, plan_path, progress_path, report_path
from .runtime_state import ProgressState

MIN_SUBSTANTIVE_CONTENT_LENGTH = 60
_ROOT_CAUSE_BRIEF_SECTIONS = (
    (
        "## Hypotheses",
        "autonomous root-cause brief should include a `## Hypotheses` section",
    ),
    (
        "## Known Confounders",
        "autonomous root-cause brief should capture `## Known Confounders`",
    ),
    (
        "## Required Cross-Checks",
        "autonomous root-cause brief should capture `## Required Cross-Checks`",
    ),
)

THREAD_PATTERN = re.compile(
    r"^###\s+(T[^\n:]*:[^\n]*?)\n(?P<body>.*?)(?=^###\s+T|\Z)", re.MULTILINE | re.DOTALL
)
FIELD_PATTERN = re.compile(r"^\*\*(?P<name>[^*]+):\*\*\s*(?P<value>.+)$", re.MULTILINE)


def report_has_substance(report_text: str) -> bool:
    executive_summary = extract_section(report_text, "Executive Summary")
    if executive_summary is None:
        return False
    placeholder = "fill in the executive summary before publishing"
    if placeholder in executive_summary.lower():
        return False
    return len(" ".join(executive_summary.split())) >= MIN_SUBSTANTIVE_CONTENT_LENGTH


def validate_progress(payload: Any) -> list[str]:
    try:
        ProgressState.from_payload(payload)
    except ValueError as exc:
        return [str(exc)]
    return []


def validate_findings(payload: Any) -> list[str]:
    if not isinstance(payload, list):
        return ["findings.json must be a JSON list"]

    errors: list[str] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            errors.append(f"findings[{index}] must be a JSON object")
            continue
        finding_id = item.get("id")
        if not isinstance(finding_id, str) or not finding_id.strip():
            errors.append(f"findings[{index}].id must be a non-empty string")
        summary = item.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            errors.append(f"findings[{index}].summary must be a non-empty string")
    return errors


def parse_plan_threads(plan_text: str) -> list[dict[str, Any]]:
    threads: list[dict[str, Any]] = []
    for match in THREAD_PATTERN.finditer(plan_text):
        heading = match.group(1).strip()
        fields = {
            field.group("name").strip(): field.group("value").strip()
            for field in FIELD_PATTERN.finditer(match.group("body"))
        }
        threads.append({"heading": heading, "fields": fields})
    return threads


def _root_cause_brief_warnings(brief_text: str) -> list[str]:
    return [
        warning
        for section_heading, warning in _ROOT_CAUSE_BRIEF_SECTIONS
        if section_heading not in brief_text
    ]


def _thread_design_warnings(threads: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for thread in threads:
        priority = thread["fields"].get("Priority", "").lower()
        if priority != "high":
            continue
        for field_name in ROOT_CAUSE_DESIGN_FIELDS:
            if field_name not in thread["fields"]:
                warnings.append(
                    f"{thread['heading']} is high priority but missing `{field_name}`"
                )
    return warnings


def _root_cause_plan_warnings(case_path: Path) -> list[str]:
    if not plan_path(case_path).exists():
        return ["autonomous root-cause case should include `plan.md`"]

    plan_text = read_text(plan_path(case_path))
    if "No plan yet" in plan_text:
        return ["autonomous root-cause case has no research threads yet"]

    threads = parse_plan_threads(plan_text)
    if not threads:
        return ["plan.md does not contain any numbered research threads"]
    return _thread_design_warnings(threads)


def collect_validation_warnings(case_path: Path) -> list[str]:
    warnings: list[str] = []
    if not brief_path(case_path).exists():
        return warnings

    profile = CaseProfile.load(case_path)
    if not profile.is_autonomous_root_cause:
        return warnings

    brief_text = read_text(brief_path(case_path))
    warnings.extend(_root_cause_brief_warnings(brief_text))
    warnings.extend(_root_cause_plan_warnings(case_path))
    return warnings


def _load_progress_for_validation(
    case_path: Path,
) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        progress = load_json(progress_path(case_path))
    except json.JSONDecodeError as exc:
        return None, [f"progress.json is invalid JSON: {exc.msg}"]
    except OSError as exc:
        return None, [f"Could not read progress.json: {exc}"]

    errors = validate_progress(progress)
    if errors:
        return None, errors
    return progress, []


def _challenge_completion_errors(
    case_path: Path, progress: dict[str, Any]
) -> list[str]:
    profile = CaseProfile.load(case_path)
    if not profile.requires_challenge:
        return []
    if progress.get("pending_challenge_cycle"):
        return ["strict completion requires the challenge cycle to be run"]
    if progress.get("last_challenge_outcome") is None:
        return [
            "strict completion requires the challenge cycle to be run "
            "(this case has not run one yet — run more cycles or use "
            "`validate --design` for a structural check)"
        ]
    if progress.get("last_challenge_outcome") != "passed":
        return [
            "strict completion requires the challenge cycle to have passed "
            f"(last outcome: {progress.get('last_challenge_outcome')!r})"
        ]
    return []


def _report_completion_errors(case_path: Path) -> list[str]:
    rp = report_path(case_path)
    if not rp.exists():
        return ["Missing required file: report.md"]

    report_text = read_text(rp)
    if report_has_substance(report_text):
        return []
    if extract_section(report_text, "Executive Summary") is None:
        return ["strict completion requires a non-empty Executive Summary"]
    return ["strict completion requires substantive report content"]


def _strict_completion_errors(case_path: Path, progress: dict[str, Any]) -> list[str]:
    return _challenge_completion_errors(
        case_path, progress
    ) + _report_completion_errors(case_path)


def _findings_errors(case_path: Path) -> list[str]:
    fp = findings_path(case_path)
    if not fp.exists():
        return []
    try:
        findings = load_json(fp)
    except json.JSONDecodeError as exc:
        return [f"findings.json is invalid JSON: {exc.msg}"]
    except OSError as exc:
        return [f"Could not read findings.json: {exc}"]
    return validate_findings(findings)


def validate_case(
    case_path: Path,
    *,
    strict_completion: bool = False,
    strict_design: bool = False,
) -> list[str]:
    """Minimal case validation: brief exists, progress is valid, report on completion.

    `strict_design` promotes design-contract warnings on high-priority threads
    (`Discriminating Test`, `Completion Threshold`, `Strongest Rival`, `Cross-Check`)
    to errors. Safe to run at scaffold/planning time — it does NOT gate on challenge
    cycle or report.md.

    `strict_completion` is the end-of-case publish gate: everything in
    `strict_design` plus challenge-cycle outcome and a substantive report.md.
    """
    errors: list[str] = []
    if not brief_path(case_path).exists():
        errors.append("Missing required file: brief.md")
    if not progress_path(case_path).exists():
        errors.append("Missing required file: progress.json")

    if progress_path(case_path).exists():
        progress, progress_errors = _load_progress_for_validation(case_path)
        if progress_errors:
            errors.extend(progress_errors)
            return errors
        if progress is None:
            return errors

        status_complete = progress.get("status") == "complete"
        should_enforce_design_contract = (
            strict_completion or strict_design or status_complete
        )
        if should_enforce_design_contract:
            errors.extend(collect_validation_warnings(case_path))

        if strict_completion or status_complete:
            errors.extend(_strict_completion_errors(case_path, progress))

    errors.extend(_findings_errors(case_path))
    return errors
