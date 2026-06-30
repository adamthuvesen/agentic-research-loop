from datetime import date
from pathlib import Path
from typing import Any

from .io import (
    extract_section,
    load_json,
    load_json_optional,
    read_text,
    read_text_optional,
    write_text,
)
from .layout import (
    cycles_dir,
    findings_path,
    notes_path,
    report_path,
)
from .templates import finding_template
from .validation import validate_case

_DEFAULT_FRESHNESS_CAVEAT = "This finding should be re-checked against live systems before being treated as current."
_FALLBACK_FRESHNESS_CAVEAT = (
    "Re-verify this finding when the underlying source systems or definitions change."
)
_CAVEAT_TEXT = {
    "live": "Live metrics and rollout state may change as source systems update.",
    "web": "External context may age quickly and should be re-verified before reusing the conclusion.",
    "docs": "Internal documentation may lag operational reality for fast-moving questions.",
}


def _finding_items(findings: Any) -> list[dict[str, Any]]:
    if not isinstance(findings, list):
        return []
    return [item for item in findings if isinstance(item, dict)]


def _first_truthy_value(item: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = item.get(key)
        if value:
            return str(value).strip()
    return ""


def _source_list(findings: Any) -> list[str]:
    sources: list[str] = []
    for item in _finding_items(findings):
        ref = _first_truthy_value(item, ("source_ref", "source"))
        if ref and ref not in sources:
            sources.append(ref)
    return sources


def _source_family_list(findings: Any) -> list[str]:
    families = sorted(
        {
            str(item.get("source_type", "")).strip()
            for item in _finding_items(findings)
            if str(item.get("source_type", "")).strip()
        }
    )
    return families or ["none recorded"]


def _freshness_caveats(findings: Any) -> list[str]:
    from .sources import SOURCE_CONFIGS

    if not isinstance(findings, list) or not findings:
        return [_DEFAULT_FRESHNESS_CAVEAT]
    source_types = {
        str(item.get("source_type", "")).strip() for item in _finding_items(findings)
    }
    # Build source_type → caveat_group lookup from config (key field matches source_type in findings)
    type_to_group: dict[str, str] = {}
    for spec in SOURCE_CONFIGS.values():
        group = spec.get("freshness_caveat_group")
        if group:
            type_to_group[spec["key"]] = group
    groups_present = {type_to_group[st] for st in source_types if st in type_to_group}
    caveats = [_CAVEAT_TEXT[g] for g in ("live", "web", "docs") if g in groups_present]
    return caveats or [_FALLBACK_FRESHNESS_CAVEAT]


def _reverification_triggers(findings: Any) -> list[str]:
    if not isinstance(findings, list) or not findings:
        return ["Re-verify when the business question becomes time-sensitive again."]
    return [
        "Re-verify after major metric-definition, instrumentation, or rollout changes.",
        "Re-verify when new evidence materially changes the leading explanation.",
    ]


def _report_section_lines(report_text: str, heading: str) -> list[str]:
    section = extract_section(report_text, heading) or ""
    if not section:
        return []
    lines = []
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- "):
            lines.append(line[2:].strip())
        else:
            lines.append(line)
    return lines


def _research_shifts(case_path: Path) -> list[str]:
    shifts: list[str] = []
    for summary_path in sorted(cycles_dir(case_path).glob("*/cycle_summary.json"))[-5:]:
        summary = load_json(summary_path)
        if not isinstance(summary, dict):
            raise ValueError(f"Cycle summary must be a JSON object: {summary_path}")
        result = str(summary.get("result", "unknown"))
        made_progress = summary.get("made_progress", False)
        progress_text = "progress" if made_progress else "no progress"
        shifts.append(
            f"{summary.get('cycle_id', 'unknown')}: {result} — {progress_text}"
        )
    return shifts or ["No recorded case shifts."]


def _ruled_out_lines(case_path: Path, report_text: str) -> list[str]:
    lines = _report_section_lines(report_text, "Rejected Leads")
    if lines:
        return lines
    return ["None recorded yet."]


def _process_caveats(case_path: Path, report_text: str) -> list[str]:
    report_lines = _report_section_lines(report_text, "Risks And Caveats")
    if report_lines:
        return report_lines
    report_lines = _report_section_lines(report_text, "Open Questions")
    if report_lines:
        return report_lines
    notes = read_text_optional(notes_path(case_path))
    if notes is None:
        return ["No major process caveats were explicitly recorded."]
    dead_ends = extract_section(notes, "Dead Ends")
    if dead_ends:
        lines = []
        for raw_line in dead_ends.splitlines():
            line = raw_line.strip()
            if line.startswith("- "):
                lines.append(line[2:].strip())
        if lines:
            return lines
    return ["No major process caveats were explicitly recorded."]


def publish(case_path: Path) -> Path:
    errors = validate_case(case_path, strict_completion=True)
    if errors:
        joined = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"Case is not ready to publish:\n{joined}")

    report = read_text(report_path(case_path))
    short_answer = extract_section(report, "Executive Summary")
    if short_answer is None:
        raise ValueError(
            "Case is not ready to publish:\n- Missing non-empty Executive Summary section"
        )
    conclusion = (
        extract_section(report, "Conclusions")
        or extract_section(report, "Conclusion")
        or short_answer
    )
    findings_data = load_json_optional(findings_path(case_path))
    sources = _source_list(findings_data)
    finding = finding_template(
        title=case_path.name,
        short_answer=short_answer,
        conclusion=conclusion,
        sources=sources,
        source_families=_source_family_list(findings_data),
        research_shifts=_research_shifts(case_path),
        ruled_out=_ruled_out_lines(case_path, report),
        process_caveats=_process_caveats(case_path, report),
        last_verified=date.today().isoformat(),
        freshness_caveats=_freshness_caveats(findings_data),
        reverification_triggers=_reverification_triggers(findings_data),
    )
    output_path = case_path / "published.md"
    write_text(output_path, finding)
    return output_path
