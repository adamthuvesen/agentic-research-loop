from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .io import read_text, write_text
from .layout import (
    brief_path,
    notes_path,
    plan_path,
    progress_path,
    report_path,
    sources_path,
    status_json_path,
    status_markdown_path,
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def artifact_snapshot(case_path: Path, progress: dict[str, Any]) -> dict[str, Any]:
    progress_text = read_text(progress_path(case_path))
    sources_text = read_text(sources_path(case_path))
    sources_parse_error: str | None = None
    try:
        sources = json.loads(sources_text)
    except json.JSONDecodeError as exc:
        sources = {}
        sources_parse_error = str(exc)
    report = read_text(report_path(case_path))
    notes = read_text(notes_path(case_path))

    return {
        "progress": progress,
        "progress_text": progress_text,
        "report": report,
        "report_hash": sha256_text(report),
        "notes": notes,
        "notes_hash": sha256_text(notes),
        "sources": sources,
        "sources_text": sources_text,
        "sources_parse_error": sources_parse_error,
    }


def mutable_artifact_texts(
    case_path: Path,
    snapshot: dict[str, Any] | None = None,
    *,
    include_plan: bool = True,
) -> dict[str, str]:
    s = snapshot or {}
    artifacts = {
        "notes.md": s["notes"] if "notes" in s else read_text(notes_path(case_path)),
        "report.md": s["report"]
        if "report" in s
        else read_text(report_path(case_path)),
        "state/sources.json": s["sources_text"]
        if "sources_text" in s
        else read_text(sources_path(case_path)),
        "state/progress.json": s["progress_text"]
        if "progress_text" in s
        else read_text(progress_path(case_path)),
        "state/status.json": read_text(status_json_path(case_path)),
        "status.md": read_text(status_markdown_path(case_path)),
    }
    if include_plan:
        artifacts["plan.md"] = read_text(plan_path(case_path))
    return artifacts


def protected_input_texts(case_path: Path) -> dict[str, str]:
    return {"brief.md": read_text(brief_path(case_path))}


def restore_artifacts(case_path: Path, snapshot: dict[str, str]) -> None:
    for relative_path, content in snapshot.items():
        write_text(case_path / relative_path, content)


def partial_progress_artifact_texts(
    case_path: Path, baseline: dict[str, str]
) -> dict[str, str]:
    changed: dict[str, str] = {}
    for relative_path in ("notes.md", "report.md"):
        if relative_path not in baseline:
            continue
        current = read_text(case_path / relative_path)
        if current != baseline[relative_path]:
            changed[relative_path] = current
    return changed


def protected_inputs_changed(case_path: Path, snapshot: dict[str, str]) -> list[str]:
    changed: list[str] = []
    for relative_path, expected in snapshot.items():
        current = read_text(case_path / relative_path)
        if current != expected:
            changed.append(relative_path)
    return changed


def compute_progress(before: dict[str, Any], after: dict[str, Any]) -> bool:
    return (
        before["notes_hash"] != after["notes_hash"]
        or before["report_hash"] != after["report_hash"]
    )
