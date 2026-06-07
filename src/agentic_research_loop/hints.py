from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .case_contracts import ROOT_CAUSE_DESIGN_FIELDS
from .io import extract_section, read_text
from .layout import plan_path
from .validation import parse_plan_threads, report_has_substance

DEFAULT_HINT_LIMIT = 4

_RETIRED_STATUS_RE = re.compile(
    r"\*\*Status:\*\*\s*(weakened|rejected|ruled out|discarded|pivoted)\b",
    re.IGNORECASE,
)

_FRESHNESS_TERMS = (
    "latest",
    "today",
    "yesterday",
    "this week",
    "this month",
    "current",
    "live data",
    "fresh",
)


@dataclass(frozen=True)
class CycleHint:
    priority: int
    key: str
    message: str


def build_cycle_hints(
    case_path: Path,
    *,
    snapshot: dict[str, Any] | None = None,
    limit: int = DEFAULT_HINT_LIMIT,
) -> list[str]:
    """Return bounded local-only nudges for the next normal cycle."""
    notes = _snapshot_text(case_path, snapshot, "notes", "notes.md")
    report = _snapshot_text(case_path, snapshot, "report", "report.md")
    progress = snapshot.get("progress", {}) if snapshot else {}
    cycle_count = progress.get("cycle_count", 0) if isinstance(progress, dict) else 0
    plan = read_text(plan_path(case_path)) if plan_path(case_path).exists() else ""

    hints = [
        _missing_hypothesis_ledger(notes, cycle_count),
        _no_hypotheses_retired(notes, cycle_count),
        _thin_evidence_for_report(notes, report),
        _missing_thread_fields(plan),
        _freshness_without_caveat(notes, report),
    ]
    return _dedup_and_cap([hint for hint in hints if hint], limit=limit)


def _snapshot_text(
    case_path: Path,
    snapshot: dict[str, Any] | None,
    key: str,
    filename: str,
) -> str:
    if snapshot and isinstance(snapshot.get(key), str):
        return snapshot[key]
    path = case_path / filename
    return read_text(path) if path.exists() else ""


def _missing_hypothesis_ledger(notes: str, cycle_count: int) -> CycleHint | None:
    if cycle_count < 1:
        return None
    if _has_usable_hypothesis_section(notes):
        return None
    return CycleHint(
        priority=90,
        key="hypothesis-ledger",
        message="`notes.md` does not yet have a usable hypothesis ledger; record active hypotheses and current status before updating the report.",
    )


def _no_hypotheses_retired(notes: str, cycle_count: int) -> CycleHint | None:
    if cycle_count < 2 or not _has_usable_hypothesis_section(notes):
        return None
    if _RETIRED_STATUS_RE.search(notes):
        return None
    return CycleHint(
        priority=80,
        key="hypothesis-falsification",
        message="No hypothesis appears weakened, rejected, ruled out, or pivoted after multiple cycles; test the strongest rival and retire weak explanations.",
    )


def _thin_evidence_for_report(notes: str, report: str) -> CycleHint | None:
    if not report_has_substance(report):
        return None
    evidence = extract_section(notes, "Evidence Log")
    if _section_has_real_content(evidence):
        return None
    return CycleHint(
        priority=70,
        key="evidence-log",
        message="`report.md` has enough content to present, but the evidence log is thin; connect key claims to source families and caveats in `notes.md`.",
    )


def _missing_thread_fields(plan: str) -> CycleHint | None:
    missing: list[str] = []
    for thread in parse_plan_threads(plan):
        priority = thread["fields"].get("Priority", "").lower()
        if priority != "high":
            continue
        for field in ROOT_CAUSE_DESIGN_FIELDS:
            if not thread["fields"].get(field):
                missing.append(f"{thread['heading']} missing `{field}`")
    if not missing:
        return None
    first = "; ".join(missing[:2])
    suffix = "" if len(missing) <= 2 else f"; plus {len(missing) - 2} more"
    return CycleHint(
        priority=60,
        key="thread-design",
        message=f"High-priority thread design is incomplete: {first}{suffix}. Fill the field or mark it N/A with a reason.",
    )


def _freshness_without_caveat(notes: str, report: str) -> CycleHint | None:
    report_lower = report.lower()
    if not any(term in report_lower for term in _FRESHNESS_TERMS):
        return None
    combined = f"{notes}\n{report}".lower()
    if "freshness" in combined or "caveat" in combined or "last verified" in combined:
        return None
    return CycleHint(
        priority=50,
        key="freshness-caveat",
        message="The report uses freshness-sensitive language; add a date, freshness caveat, or last-verified note before treating the claim as stable.",
    )


def _has_usable_hypothesis_section(notes: str) -> bool:
    section = extract_section(notes, "Hypotheses")
    if not _section_has_real_content(section):
        return False
    return bool(re.search(r"^###\s+H\d+:\s+(?!<)", section or "", re.MULTILINE))


def _section_has_real_content(section: str | None) -> bool:
    if not section:
        return False
    stripped = section.strip()
    if "<" in stripped and ">" in stripped:
        return False
    content_lines = [
        line.strip()
        for line in stripped.splitlines()
        if line.strip()
        and line.strip() != "-"
        and not re.fullmatch(r"\*\*[^*]+:\*\*", line.strip())
    ]
    text = " ".join(content_lines).strip()
    return len(text) >= 20


def _dedup_and_cap(hints: list[CycleHint], *, limit: int) -> list[str]:
    seen: set[str] = set()
    messages: list[str] = []
    for hint in sorted(hints, key=lambda item: item.priority, reverse=True):
        if hint.key in seen:
            continue
        seen.add(hint.key)
        messages.append(hint.message)
        if len(messages) >= limit:
            break
    return messages
