from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .from_spec import (
    SOURCE_CONSTRAINTS_HEADER,
    load_from_spec_dir,
    replace_markdown_section,
)
from .io import extract_section, write_text
from .layout import (
    brief_path,
    case_dir,
    case_slug,
    notes_path,
    plan_path,
    queries_path,
    report_path,
    research_dir,
    source_objects_path,
)
from .sources import build_sources_config, source_constraint_lines
from .templates import (
    brief_template,
    goal_prompt,
    notes_template,
    plan_template,
    queries_template,
    report_template,
    source_objects_template,
)

DEFAULT_SUCCESS_CRITERIA = (
    "The answer directly addresses the question.",
    "Material claims have traceable evidence.",
    "Competing explanations are tested or left as explicit open risks.",
    "Calculated contributions reconcile to the relevant total when applicable.",
)


@dataclass(frozen=True)
class ResearchInitResult:
    case_id: str
    path: Path


def create_manual(
    repo_root: Path,
    slug: str,
    *,
    template: str,
    question: str | None = None,
    enabled: dict[str, bool] | None = None,
    hints: dict[str, str] | None = None,
    local_context_paths: list[str] | None = None,
    local_only: bool = False,
    from_spec_path: Path | None = None,
) -> ResearchInitResult:
    case_id = case_slug(slug)
    path = case_dir(repo_root, case_id)
    if path.exists():
        raise FileExistsError(f"Case already exists: {path}")

    sources_config = build_sources_config(
        enabled=enabled,
        hints=hints,
        local_context_paths=local_context_paths,
        local_only=local_only,
    )
    constraints = source_constraint_lines(sources_config)
    supplied = load_from_spec_dir(from_spec_path) if from_spec_path is not None else {}
    case_question = question or f"Research: {slug}"

    supplied_brief = supplied.get("brief")
    if supplied_brief is not None:
        brief = replace_markdown_section(
            supplied_brief,
            SOURCE_CONSTRAINTS_HEADER.removeprefix("## "),
            "\n".join(f"- {line}" for line in constraints if line.strip())
            + "\n\nAll external systems are read-only.",
        )
        case_question = extract_section(brief, "Question") or case_question
    else:
        brief = brief_template(
            question=case_question,
            template=template,
            source_constraints=constraints,
            success_criteria=list(DEFAULT_SUCCESS_CRITERIA),
        )

    path.mkdir(parents=True)
    write_text(brief_path(path), brief)
    write_text(notes_path(path), supplied.get("notes") or notes_template())
    write_text(report_path(path), report_template(template, case_question))
    write_text(queries_path(path), queries_template())
    write_text(source_objects_path(path), source_objects_template())
    write_text(
        plan_path(path), supplied.get("plan") or plan_template(template=template)
    )

    return ResearchInitResult(case_id=case_id, path=path.resolve())


def _resolve_existing_case_path(
    candidate: Path, expected_parent: Path, *, require_dir: bool
) -> Path | None:
    if not candidate.exists():
        return None
    resolved = candidate.resolve()
    if (require_dir and not resolved.is_dir()) or resolved.parent != expected_parent:
        raise FileNotFoundError(
            f"Case path {resolved} is outside the research directory {expected_parent}"
        )
    return resolved


def _suffix_case_match(expected_parent: Path, value: str) -> Path | None:
    if not expected_parent.exists():
        return None
    matches = [
        path
        for path in expected_parent.iterdir()
        if path.is_dir() and path.name.endswith(f"-{value}")
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(path.name for path in sorted(matches))
        raise FileNotFoundError(f"Ambiguous case slug '{value}' — matches: {names}")
    return None


def resolve_case_path(repo_root: Path, value: str) -> Path:
    """Resolve a case identifier to its directory path within research_dir.

    Accepts a bare slug, a full case ID, or a date-stripped suffix.
    Raises FileNotFoundError if the path cannot be found or resolves outside research_dir.
    """
    if not value:
        raise FileNotFoundError("Case identifier must not be empty")
    expected_parent = research_dir(repo_root).resolve()
    resolved = _resolve_existing_case_path(
        Path(value), expected_parent, require_dir=False
    )
    if resolved is not None:
        return resolved

    resolved = _resolve_existing_case_path(
        case_dir(repo_root, value), expected_parent, require_dir=True
    )
    if resolved is not None:
        return resolved

    resolved = _suffix_case_match(expected_parent, value)
    if resolved is not None:
        return resolved
    raise FileNotFoundError(f"Could not find case: {value}")


def render_goal(case_path: Path) -> str:
    """Render the `/goal` contract, scoped to the sources this case may use.

    Only the bullet list is a source. Both brief writers close the section with a
    read-only reminder in prose, and the contract states that rule itself — left
    in, that sentence reads as another allowed source.
    """
    brief = brief_path(case_path).read_text(encoding="utf-8")
    constraints = extract_section(brief, "Source Constraints") or ""
    sources = [
        stripped.removeprefix("-").strip()
        for line in constraints.splitlines()
        if (stripped := line.strip()).startswith("-")
        and stripped.removeprefix("-").strip()
    ]
    return goal_prompt(case_path, sources or ["No sources recorded in brief.md."])
