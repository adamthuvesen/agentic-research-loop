from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .case_contracts import VALID_MODES
from .from_spec import ensure_mode_metadata, load_from_spec_dir, splice_source_registry
from .io import now_iso, write_json, write_text
from .layout import (
    brief_path,
    case_dir,
    case_slug,
    notes_path,
    plan_path,
    progress_path,
    report_path,
    research_dir,
    sources_path,
    state_dir,
    status_json_path,
    status_markdown_path,
)
from .sources import build_sources_config, enabled_source_labels, source_plan_lines
from .status import render_status_markdown
from .templates import brief_template, notes_template, plan_template, report_template


@dataclass(frozen=True)
class IntakeDecision:
    question: str
    mode: str
    template: str
    source_plan: list[str]
    success_criteria: list[str]
    initial_summary: str


@dataclass(frozen=True)
class ResearchInitResult:
    case_id: str
    path: Path
    decision: IntakeDecision


def initial_progress(*, mode: str) -> dict[str, Any]:
    if mode not in VALID_MODES:
        raise ValueError(
            f"Invalid mode {mode!r}. Must be one of: {', '.join(sorted(VALID_MODES))}"
        )
    return {
        "status": "draft" if mode == "quick" else "active",
        "cycle_count": 0,
        "consecutive_no_progress_cycles": 0,
        "consecutive_failures": 0,
        "pending_challenge_cycle": False,
        "last_challenge_outcome": None,
        "stop_reason": None,
    }


def initial_status(*, case_id: str, mode: str, template: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "mode": mode,
        "template": template,
        "status": "idle",
        "runner_name": None,
        "started_at": now_iso(),
        "updated_at": now_iso(),
        "active_cycle_id": None,
        "active_attempt": None,
        "last_attempt_outcome": None,
        "stop_reason": None,
    }


def write_initial_files(
    repo_root: Path,
    case_id: str,
    decision: IntakeDecision,
    sources_config: dict,
    supplied: dict[str, str | None] | None = None,
) -> Path:
    path = case_dir(repo_root, case_id)
    if path.exists():
        raise FileExistsError(f"Case already exists: {path}")
    state_path = state_dir(path)
    state_path.mkdir(parents=True)

    supplied = supplied or {}
    source_registry_block = "\n".join(source_plan_lines(sources_config))

    if supplied.get("brief") is not None:
        brief_content = splice_source_registry(supplied["brief"], source_registry_block)
        brief_content = ensure_mode_metadata(
            brief_content, mode=decision.mode, template=decision.template
        )
    else:
        brief_content = brief_template(
            question=decision.question,
            template=decision.template,
            mode=decision.mode,
            source_plan=decision.source_plan,
            source_registry_lines=source_plan_lines(sources_config),
            success_criteria=decision.success_criteria,
        )
    write_text(brief_path(path), brief_content)

    notes_content = (
        supplied["notes"] if supplied.get("notes") is not None else notes_template()
    )
    write_text(notes_path(path), notes_content)

    plan_content = (
        supplied["plan"]
        if supplied.get("plan") is not None
        else plan_template(template=decision.template, mode=decision.mode)
    )
    write_text(plan_path(path), plan_content)

    write_text(
        report_path(path),
        report_template(decision.template, decision.question, decision.initial_summary),
    )
    write_json(progress_path(path), initial_progress(mode=decision.mode))
    write_json(sources_path(path), sources_config)
    status_payload = initial_status(
        case_id=case_id, mode=decision.mode, template=decision.template
    )
    write_json(status_json_path(path), status_payload)
    write_text(status_markdown_path(path), render_status_markdown(path, status_payload))
    return path


def create_manual(
    repo_root: Path,
    slug: str,
    *,
    template: str,
    mode: str,
    enabled: dict[str, bool] | None = None,
    hints: dict[str, str] | None = None,
    local_context_paths: list[str] | None = None,
    local_only: bool = False,
    from_spec_path: Path | None = None,
) -> ResearchInitResult:
    question = f"Research: {slug}"
    sources_config = build_sources_config(
        enabled=enabled,
        hints=hints,
        local_context_paths=local_context_paths,
        local_only=local_only,
    )
    enabled_names = enabled_source_labels(sources_config)
    source_plan = ["Live systems for fresh facts"]
    if enabled_names:
        source_plan.append(f"{', '.join(enabled_names)} for context and evidence")
    decision = IntakeDecision(
        question=question,
        mode=mode,
        template=template,
        source_plan=source_plan,
        success_criteria=[
            "The case question is well scoped.",
            "The workspace is ready for human or autonomous follow-through.",
        ],
        initial_summary="This case was created manually. Fill in the brief before relying on the output.",
    )
    case_id = case_slug(slug)
    supplied = (
        load_from_spec_dir(from_spec_path) if from_spec_path is not None else None
    )
    path = write_initial_files(
        repo_root, case_id, decision, sources_config, supplied=supplied
    )
    return ResearchInitResult(case_id=case_id, path=path, decision=decision)


def resolve_case_path(repo_root: Path, value: str) -> Path:
    """Resolve a case identifier to its directory path within research_dir.

    Accepts a bare slug, a full case ID, or a date-stripped suffix.
    Raises FileNotFoundError if the path cannot be found or resolves outside research_dir.
    """
    if not value:
        raise FileNotFoundError("Case identifier must not be empty")
    expected_parent = research_dir(repo_root).resolve()
    candidate = Path(value)
    if candidate.exists():
        resolved = candidate.resolve()
        if resolved.parent != expected_parent:
            raise FileNotFoundError(
                f"Case path {resolved} is outside the research directory {expected_parent}"
            )
        return resolved
    resolved = case_dir(repo_root, value)
    if resolved.exists():
        real_resolved = resolved.resolve()
        if not real_resolved.is_dir() or real_resolved.parent != expected_parent:
            raise FileNotFoundError(
                f"Case path {real_resolved} is outside the research directory {expected_parent}"
            )
        return real_resolved
    # Suffix fallback: match directories ending with -{value}
    if expected_parent.exists():
        matches = [
            d
            for d in expected_parent.iterdir()
            if d.is_dir() and d.name.endswith(f"-{value}")
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            names = ", ".join(d.name for d in sorted(matches))
            raise FileNotFoundError(f"Ambiguous case slug '{value}' — matches: {names}")
    raise FileNotFoundError(f"Could not find case: {value}")
