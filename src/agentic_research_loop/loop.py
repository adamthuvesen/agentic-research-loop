from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .case_contracts import CHALLENGE_REVIEW_HEADING, CaseProfile
from .cycle_execution import (
    CycleContext,
    execute_run_cycle,
    invoke_runner_with_timer,
    prepare_cycle,
)
from .cycle_markers import (
    CASE_COMPLETE_MARKER,
    CHALLENGE_REQUIRED_RESULT,
    CYCLE_DONE_MARKER,
    DEFAULT_MAX_ATTEMPTS_PER_CYCLE,
    classify_cycle_outcome,
    detect_completion_marker,
)
from .io import load_json, now_iso, read_text, write_json, write_text
from .layout import (
    plan_path,
    progress_path,
    report_path,
    status_json_path,
    status_markdown_path,
)
from .prompts import build_plan_prompt
from .run_ui import print_plan_status, print_run_header, print_run_summary
from .runner import builtin_runner_path, load_runner_config
from .runner_context import build_runner_context
from .runtime_artifacts import (
    artifact_snapshot as _artifact_snapshot,
    compute_progress,
    mutable_artifact_texts,
    protected_input_texts,
    restore_artifacts,
)
from .runtime_state import CycleSummary, ProgressState, StatusState
from .status import render_status_markdown

DEFAULT_STALL_LIMIT = 3
DEFAULT_FAILURE_LIMIT = 3

__all__ = [
    "CASE_COMPLETE_MARKER",
    "CHALLENGE_REQUIRED_RESULT",
    "CYCLE_DONE_MARKER",
    "DEFAULT_MAX_ATTEMPTS_PER_CYCLE",
    "DEFAULT_FAILURE_LIMIT",
    "DEFAULT_STALL_LIMIT",
    "apply_cycle_result",
    "artifact_snapshot",
    "case_requires_challenge",
    "challenge_cycle_pending",
    "classify_cycle_outcome",
    "compute_progress",
    "detect_completion_marker",
    "has_challenge_review",
    "is_plan_blank",
    "run_cycle",
    "run_loop",
    "run_plan_step",
    "should_stop",
    "update_progress",
    "write_status",
]


def _status_payload(case_path: Path) -> dict[str, Any]:
    payload = load_json(status_json_path(case_path))
    return StatusState.from_payload(payload).to_payload()


def _progress_state(case_path: Path) -> ProgressState:
    payload = load_json(progress_path(case_path))
    return ProgressState.from_payload(payload)


def _progress_payload(case_path: Path) -> dict[str, Any]:
    return _progress_state(case_path).to_payload()


def write_status(
    case_path: Path,
    status_payload: dict[str, Any],
    *,
    snapshot: dict[str, Any] | None = None,
) -> None:
    status_payload["updated_at"] = now_iso()
    write_json(status_json_path(case_path), status_payload)
    write_text(
        status_markdown_path(case_path),
        render_status_markdown(case_path, status_payload, snapshot=snapshot),
    )


def update_progress(case_path: Path, **changes: Any) -> dict[str, Any]:
    progress = _progress_payload(case_path)
    progress.update(changes)
    progress = ProgressState.from_payload(progress).to_payload()
    write_json(progress_path(case_path), progress)
    return progress


def artifact_snapshot(case_path: Path) -> dict[str, Any]:
    return _artifact_snapshot(case_path, _progress_payload(case_path))


def should_stop(
    progress: dict[str, Any], *, challenge_required: bool = False
) -> tuple[bool, str]:
    if progress.get("status") == "complete" and (
        not challenge_required or progress.get("last_challenge_outcome") == "passed"
    ):
        return True, "case_complete"
    if progress.get("consecutive_no_progress_cycles", 0) >= DEFAULT_STALL_LIMIT:
        return True, "evidence_stall"
    if progress.get("consecutive_failures", 0) >= DEFAULT_FAILURE_LIMIT:
        return True, "consecutive_failures"
    return False, ""


def challenge_cycle_pending(progress: dict[str, Any]) -> bool:
    return bool(progress.get("pending_challenge_cycle", False))


def case_requires_challenge(case_path: Path) -> bool:
    return CaseProfile.load(case_path).requires_challenge


def has_challenge_review(case_path: Path) -> bool:
    heading = f"## {CHALLENGE_REVIEW_HEADING}"
    report = read_text(report_path(case_path))
    notes = read_text(case_path / "notes.md")
    return heading in report and heading in notes


def is_plan_blank(case_path: Path) -> bool:
    text = read_text(plan_path(case_path))
    return not text.strip() or any(
        line.strip().startswith("No plan yet") for line in text.splitlines()
    )


def run_plan_step(repo_root: Path, case_path: Path, runner_name: str) -> bool:
    """Run a planning-only agent invocation. Returns True if plan.md was written."""
    runner_config_path = builtin_runner_path(repo_root, runner_name)
    runner_config = load_runner_config(runner_config_path)
    plan_dir = case_path / "state" / "cycles" / "plan"
    plan_dir.mkdir(parents=True, exist_ok=True)

    prompt = build_plan_prompt(repo_root, case_path)
    (plan_dir / "prompt.md").write_text(prompt, encoding="utf-8")
    mutable_backup = mutable_artifact_texts(case_path, include_plan=False)
    plan_backup = {"plan.md": read_text(plan_path(case_path))}
    protected_backup = protected_input_texts(case_path)
    stdout_path = plan_dir / "stdout.log"
    stderr_path = plan_dir / "stderr.log"
    agent_message_path = plan_dir / "agent_message.md"

    context = build_runner_context(
        repo_root=repo_root,
        case_path=case_path,
        cycle_dir=plan_dir,
        prompt_file=plan_dir / "prompt.md",
        agent_message_file=agent_message_path,
        cycle_id="plan",
    )
    print_plan_status("building research plan")
    result: dict[str, Any] | None = None
    elapsed_seconds = 0.0
    try:
        result, elapsed_seconds = invoke_runner_with_timer(
            "Planning",
            runner_config,
            repo_root=repo_root,
            context=context,
            prompt_text=prompt,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            agent_message_path=agent_message_path,
        )
    except Exception:
        restore_artifacts(case_path, plan_backup)
        print_plan_status("runner could not be invoked", failed=True)
        return False
    finally:
        restore_artifacts(case_path, mutable_backup)
        restore_artifacts(case_path, protected_backup)

    if result is None or result["timed_out"] or result["returncode"] != 0:
        restore_artifacts(case_path, plan_backup)
        print_plan_status("runner failed to produce a valid plan", failed=True)
        return False

    if is_plan_blank(case_path):
        return False
    print_plan_status("wrote plan.md", success=True, elapsed_seconds=elapsed_seconds)
    return True


def run_cycle(
    repo_root: Path,
    case_path: Path,
    runner_name: str,
    *,
    cycle_number: int,
) -> CycleSummary:
    runner_config = load_runner_config(builtin_runner_path(repo_root, runner_name))
    prepared = prepare_cycle(
        case_path,
        cycle_number=cycle_number,
        artifact_snapshot=artifact_snapshot,
        write_status=write_status,
        challenge_cycle_pending=challenge_cycle_pending,
    )
    status_payload = _status_payload(case_path)
    status_payload.update(
        {
            "status": "running",
            "runner_name": runner_name,
            "active_cycle_id": prepared.cycle_id,
            "active_attempt": None,
        }
    )
    write_status(case_path, status_payload, snapshot=prepared.before_snapshot)
    return execute_run_cycle(
        CycleContext(
            repo_root=repo_root,
            case_path=case_path,
            runner_config=runner_config,
            prepared=prepared,
            write_status=write_status,
            artifact_snapshot=artifact_snapshot,
            status_payload=status_payload,
            has_challenge_review=has_challenge_review,
        ),
    )


def apply_cycle_result(
    case_path: Path, summary: CycleSummary, runner_name: str
) -> dict[str, Any]:
    progress_state = _progress_state(case_path)
    progress = progress_state.to_payload()
    status_payload = _status_payload(case_path)
    progress["cycle_count"] = progress.get("cycle_count", 0) + 1
    status_payload.update(
        {
            "runner_name": runner_name,
            "status": "idle",
            "active_cycle_id": None,
            "active_attempt": None,
            "last_attempt_outcome": summary.result,
        }
    )
    if summary.result in {"progress", "complete", CHALLENGE_REQUIRED_RESULT}:
        progress["consecutive_no_progress_cycles"] = 0
        progress["consecutive_failures"] = 0
    elif summary.result == "no_progress":
        progress["consecutive_no_progress_cycles"] = (
            progress.get("consecutive_no_progress_cycles", 0) + 1
        )
        progress["consecutive_failures"] = 0
    elif summary.result == "failed":
        progress["consecutive_no_progress_cycles"] = 0
        progress["consecutive_failures"] = progress.get("consecutive_failures", 0) + 1

    if summary.result == CHALLENGE_REQUIRED_RESULT:
        progress["pending_challenge_cycle"] = True
        progress["last_challenge_outcome"] = "queued"
    elif summary.challenge_cycle and summary.result != "failed":
        progress["pending_challenge_cycle"] = False
        if summary.result == "complete":
            progress["last_challenge_outcome"] = "passed"
        elif summary.completion_marker == "CYCLE_DONE":
            progress["last_challenge_outcome"] = "reopened"

    if summary.result == "complete":
        progress["status"] = "complete"
        progress["stop_reason"] = "case_complete"
    elif progress.get("status") == "complete":
        progress["status"] = "active"
        progress["stop_reason"] = None
    progress = ProgressState.from_payload(progress).to_payload()
    write_json(progress_path(case_path), progress)
    write_status(case_path, status_payload)
    return progress


def run_loop(
    repo_root: Path,
    case_path: Path,
    *,
    runner_name: str,
    max_cycles: int | None = None,
) -> list[CycleSummary]:
    results: list[CycleSummary] = []
    run_started_at = time.monotonic()
    progress = _progress_payload(case_path)
    print_run_header(case_path.name, runner_name, max_cycles)
    if progress.get("cycle_count", 0) == 0 and is_plan_blank(case_path):
        plan_written = run_plan_step(repo_root, case_path, runner_name=runner_name)
        progress = _progress_payload(case_path)
        if not plan_written:
            progress["stop_reason"] = "planning_failed"
            write_json(progress_path(case_path), progress)
            status_payload = _status_payload(case_path)
            status_payload["stop_reason"] = "planning_failed"
            status_payload["status"] = "idle"
            write_status(case_path, status_payload)
            print_run_summary(
                [],
                "planning_failed",
                elapsed_seconds=time.monotonic() - run_started_at,
            )
            return results
    next_cycle_number = progress.get("cycle_count", 0) + 1
    while True:
        progress = _progress_payload(case_path)
        if max_cycles is not None and len(results) >= max_cycles:
            break
        should_end, reason = should_stop(
            progress, challenge_required=case_requires_challenge(case_path)
        )
        if should_end:
            progress["stop_reason"] = reason
            write_json(progress_path(case_path), progress)
            status_payload = _status_payload(case_path)
            status_payload["stop_reason"] = reason
            status_payload["status"] = "idle"
            write_status(case_path, status_payload)
            break
        summary = run_cycle(
            repo_root, case_path, runner_name, cycle_number=next_cycle_number
        )
        next_cycle_number += 1
        apply_cycle_result(case_path, summary, runner_name)
        results.append(summary)
        if summary.result == "complete":
            break
    stop_reason = results[-1].result if results else "none"
    print_run_summary(
        [item.to_payload() for item in results],
        stop_reason,
        elapsed_seconds=time.monotonic() - run_started_at,
    )
    return results
