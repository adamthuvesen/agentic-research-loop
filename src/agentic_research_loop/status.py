from pathlib import Path
from typing import Any

from .io import extract_section, load_json_object_or_empty, read_text
from .validation import report_has_substance
from .layout import (
    cycles_dir,
    notes_path,
    progress_path,
    report_path,
    sources_path,
)


def executive_summary_excerpt(report_text: str) -> str:
    body = extract_section(report_text, "Executive Summary")
    if body is None:
        return "No executive summary yet."
    condensed = " ".join(body.split()).strip()
    if not condensed:
        return "No executive summary yet."
    return condensed[:280] + ("..." if len(condensed) > 280 else "")


def recent_cycle_lines(case_path: Path) -> list[str]:
    summaries = sorted(cycles_dir(case_path).glob("*/cycle_summary.json"))
    if not summaries:
        return ["- No completed cycles yet"]
    lines: list[str] = []
    for summary_path in summaries[-3:]:
        summary = load_json_object_or_empty(summary_path)
        if not summary:
            continue
        result = str(summary.get("result", "unknown"))
        lines.append(f"- `{summary.get('cycle_id', 'unknown')}`: `{result}`")
    return lines or ["- No completed cycles yet"]


def enabled_sources_summary(sources: dict[str, Any]) -> str:
    from .sources import SOURCE_CONFIGS

    labels: list[str] = []
    for spec in SOURCE_CONFIGS.values():
        if sources.get(spec["key"], {}).get("enabled"):
            labels.append(spec["display_label"])
    if sources.get("local_context_folders"):
        labels.append("local-context")
    return ", ".join(labels) if labels else "none"


def challenge_status(progress: dict[str, Any]) -> str:
    if progress.get("pending_challenge_cycle"):
        return "pending"
    return str(progress.get("last_challenge_outcome") or "not run")


def _status_inputs(
    case_path: Path, snapshot: dict[str, Any] | None
) -> tuple[dict[str, Any], str, dict[str, Any], str]:
    s = snapshot or {}
    progress = (
        s["progress"]
        if isinstance(s.get("progress"), dict)
        else load_json_object_or_empty(progress_path(case_path))
    )
    report = s["report"] if "report" in s else read_text(report_path(case_path))
    sources = (
        s["sources"]
        if isinstance(s.get("sources"), dict)
        else load_json_object_or_empty(sources_path(case_path))
    )
    notes = s["notes"] if "notes" in s else read_text(notes_path(case_path))
    return progress, report, sources, notes


def _overview_lines(
    case_path: Path,
    status_payload: dict[str, Any],
    progress: dict[str, Any],
    sources: dict[str, Any],
    report: str,
) -> list[str]:
    report_state = "substantive" if report_has_substance(report) else "draft"
    return [
        f"# Research Status: {case_path.name}",
        "",
        f"- Status: `{status_payload.get('status', 'unknown')}`",
        f"- Cycle count: `{progress.get('cycle_count', 0)}`",
        f"- Challenge status: `{challenge_status(progress)}`",
        f"- Sources in play: `{enabled_sources_summary(sources)}`",
        f"- Report state: `{report_state}`",
        "",
        "## Current Answer",
        "",
        executive_summary_excerpt(report),
        "",
    ]


def _working_theory_lines(notes: str) -> list[str]:
    working_theory = extract_section(notes, "Working Theory")
    if not working_theory:
        return []
    return [
        "## Working Theory",
        "",
        working_theory,
        "",
    ]


def _system_lines(
    case_path: Path, status_payload: dict[str, Any], progress: dict[str, Any]
) -> list[str]:
    return [
        "## Recent Cycles",
        "",
        *recent_cycle_lines(case_path),
        "",
        "## System",
        "",
        f"- Runner: `{status_payload.get('runner_name') or 'n/a'}`",
        f"- Active cycle: `{status_payload.get('active_cycle_id') or 'n/a'}`",
        f"- Stop reason: `{progress.get('stop_reason') or status_payload.get('stop_reason') or 'n/a'}`",
    ]


def render_status_markdown(
    case_path: Path,
    status_payload: dict[str, Any],
    *,
    snapshot: dict[str, Any] | None = None,
) -> str:
    progress, report, sources, notes = _status_inputs(case_path, snapshot)
    lines = _overview_lines(case_path, status_payload, progress, sources, report)
    lines += _working_theory_lines(notes)
    lines += _system_lines(case_path, status_payload, progress)
    return "\n".join(lines) + "\n"
