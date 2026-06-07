from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .cycle_markers import (
    CASE_COMPLETE_MARKER,
    DEFAULT_MAX_ATTEMPTS_PER_CYCLE,
    classify_cycle_outcome,
    detect_completion_marker,
)
from .io import now_iso, read_text, write_json
from .layout import cycle_dir, report_path
from .prompts import build_cycle_prompt
from .run_ui import (
    LiveTimer,
    print_attempt_failure,
    print_attempt_start,
    print_cycle_result,
    print_cycle_start,
    print_failed_cycle_summary,
    print_partial_progress_note,
)
from .runner import invoke_runner
from .runner_context import build_runner_context
from .runtime_artifacts import (
    compute_progress,
    mutable_artifact_texts,
    partial_progress_artifact_texts,
    protected_input_texts,
    protected_inputs_changed,
    restore_artifacts,
)
from .runtime_state import AttemptRecord, CycleSummary
from .validation import report_has_substance


@dataclass
class PreparedCycle:
    cycle_id: str
    cycle_path: Path
    before_snapshot: dict[str, Any]
    challenge_cycle: bool
    prompt_text: str
    prompt_file: Path
    mutable_backup: dict[str, str]
    protected_backup: dict[str, str]


@dataclass
class CycleContext:
    repo_root: Path
    case_path: Path
    runner_config: dict[str, Any]
    prepared: PreparedCycle
    write_status: Callable[..., None]
    artifact_snapshot: Callable[[Path], dict[str, Any]]
    status_payload: dict[str, Any]
    has_challenge_review: Callable[[Path], bool]


def invoke_runner_with_timer(
    timer_label: str,
    runner_config: dict[str, Any],
    *,
    repo_root: Path,
    context: dict[str, str],
    prompt_text: str,
    stdout_path: Path,
    stderr_path: Path,
    agent_message_path: Path,
) -> tuple[dict[str, Any], float]:
    timer = LiveTimer(timer_label).start()
    try:
        result = invoke_runner(
            runner_config,
            repo_root=repo_root,
            context=context,
            prompt_text=prompt_text,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            agent_message_path=agent_message_path,
        )
    finally:
        elapsed_seconds = timer.stop()
    return result, elapsed_seconds


def prepare_cycle(
    case_path: Path,
    *,
    cycle_number: int,
    artifact_snapshot: Callable[[Path], dict[str, Any]],
    write_status: Callable[..., None],
    challenge_cycle_pending: Callable[[dict[str, Any]], bool],
) -> PreparedCycle:
    cycle_id = f"{cycle_number:04d}"
    cycle_path = cycle_dir(case_path, cycle_id)
    cycle_path.mkdir(parents=True, exist_ok=True)
    before_snapshot = artifact_snapshot(case_path)
    challenge_cycle = challenge_cycle_pending(before_snapshot["progress"])
    print_cycle_start(cycle_id)
    prompt_text = build_cycle_prompt(case_path, snapshot=before_snapshot)
    prompt_file = cycle_path / "prompt.md"
    prompt_file.write_text(prompt_text, encoding="utf-8")
    return PreparedCycle(
        cycle_id=cycle_id,
        cycle_path=cycle_path,
        before_snapshot=before_snapshot,
        challenge_cycle=challenge_cycle,
        prompt_text=prompt_text,
        prompt_file=prompt_file,
        mutable_backup=mutable_artifact_texts(case_path, snapshot=before_snapshot),
        protected_backup=protected_input_texts(case_path),
    )


def _retry_nudge(prompt_text: str, attempt_records: list[dict[str, Any]]) -> str:
    last = attempt_records[-1]
    reason = last.get("failure_reason", "unknown")
    nudge = "\n## Retry\nYour previous attempt failed"
    if reason == "completion_marker_missing":
        nudge += (
            ": you forgot the completion marker. "
            "End your final message with exactly "
            "<promise>CYCLE_DONE</promise> or <promise>CASE_COMPLETE</promise>"
        )
    else:
        nudge += f" ({reason})"
    return prompt_text + nudge + ". Try again.\n"


def _attempt_record_from_failure(
    attempt: int, *, failure_reason: str, error_message: str | None = None
) -> dict[str, Any]:
    record: dict[str, Any] = {"attempt": attempt, "failure_reason": failure_reason}
    if error_message is not None:
        record["error_message"] = error_message
    return record


def execute_run_cycle(ctx: CycleContext) -> CycleSummary:
    prepared = ctx.prepared
    case_path = ctx.case_path
    cycle_path = prepared.cycle_path
    cycle_id = prepared.cycle_id
    before_snapshot = prepared.before_snapshot
    challenge_cycle = prepared.challenge_cycle
    mutable_backup = prepared.mutable_backup
    protected_backup = prepared.protected_backup
    prompt_text = prepared.prompt_text
    status_payload = ctx.status_payload

    attempt_records: list[dict[str, Any]] = []
    partial_progress_changes: dict[str, str] = {}

    for attempt in range(1, DEFAULT_MAX_ATTEMPTS_PER_CYCLE + 1):
        if attempt > 1:
            restore_artifacts(case_path, mutable_backup)
            restore_artifacts(case_path, protected_backup)
        prompt = (
            _retry_nudge(prompt_text, attempt_records)
            if attempt_records
            else prompt_text
        )

        status_payload["active_attempt"] = attempt
        ctx.write_status(case_path, status_payload, snapshot=before_snapshot)

        stdout_path = cycle_path / f"attempt_{attempt:02d}_stdout.log"
        stderr_path = cycle_path / f"attempt_{attempt:02d}_stderr.log"
        agent_message_path = cycle_path / "agent_last_message.md"
        agent_message_path.unlink(missing_ok=True)

        context = build_runner_context(
            repo_root=ctx.repo_root,
            case_path=case_path,
            cycle_dir=cycle_path,
            prompt_file=prepared.prompt_file,
            agent_message_file=agent_message_path,
            cycle_id=cycle_id,
        )
        record: dict[str, Any] = {"attempt": attempt}
        print_attempt_start(attempt, DEFAULT_MAX_ATTEMPTS_PER_CYCLE)
        try:
            result, elapsed_seconds = invoke_runner_with_timer(
                "Running",
                ctx.runner_config,
                repo_root=ctx.repo_root,
                context=context,
                prompt_text=prompt,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                agent_message_path=agent_message_path,
            )
        except Exception as exc:
            record = _attempt_record_from_failure(
                attempt,
                failure_reason=f"runner_invocation_error:{type(exc).__name__}",
                error_message=str(exc),
            )
            partial_progress_changes.update(
                partial_progress_artifact_texts(case_path, mutable_backup)
            )
            print_attempt_failure(attempt, record["failure_reason"])
            attempt_records.append(record)
            continue

        record.update(result)
        record["elapsed_seconds"] = elapsed_seconds
        if result["timed_out"]:
            record["failure_reason"] = "runner_timeout"
            partial_progress_changes.update(
                partial_progress_artifact_texts(case_path, mutable_backup)
            )
            print_attempt_failure(
                attempt, record["failure_reason"], elapsed_seconds=elapsed_seconds
            )
            attempt_records.append(record)
            continue
        if result["returncode"] != 0:
            record["failure_reason"] = f"runner_exit_code_{result['returncode']}"
            partial_progress_changes.update(
                partial_progress_artifact_texts(case_path, mutable_backup)
            )
            print_attempt_failure(
                attempt, record["failure_reason"], elapsed_seconds=elapsed_seconds
            )
            attempt_records.append(record)
            continue

        output_text = (
            read_text(agent_message_path)
            if agent_message_path.exists()
            else read_text(stdout_path)
        )
        completion_marker = detect_completion_marker(output_text)
        if completion_marker is None:
            record["failure_reason"] = "completion_marker_missing"
            partial_progress_changes.update(
                partial_progress_artifact_texts(case_path, mutable_backup)
            )
            print_attempt_failure(
                attempt, record["failure_reason"], elapsed_seconds=elapsed_seconds
            )
            attempt_records.append(record)
            continue

        if protected_inputs_changed(case_path, protected_backup):
            restore_artifacts(case_path, protected_backup)

        if completion_marker == CASE_COMPLETE_MARKER:
            report_text = read_text(report_path(case_path))
            if not report_has_substance(report_text):
                record["failure_reason"] = "completion_without_report"
                partial_progress_changes.update(
                    partial_progress_artifact_texts(case_path, mutable_backup)
                )
                print_attempt_failure(
                    attempt,
                    "complete but report has no content",
                    elapsed_seconds=elapsed_seconds,
                )
                attempt_records.append(record)
                continue

        after_snapshot = ctx.artifact_snapshot(case_path)
        if after_snapshot.get("sources_parse_error"):
            record["failure_reason"] = "sources_json_parse_error"
            partial_progress_changes.update(
                partial_progress_artifact_texts(case_path, mutable_backup)
            )
            print_attempt_failure(
                attempt,
                f"sources.json parse error: {after_snapshot['sources_parse_error']}",
                elapsed_seconds=elapsed_seconds,
            )
            attempt_records.append(record)
            continue

        made_progress = compute_progress(before_snapshot, after_snapshot)
        if challenge_cycle and completion_marker == CASE_COMPLETE_MARKER:
            if not made_progress:
                record["failure_reason"] = "challenge_without_progress"
                print_attempt_failure(
                    attempt, record["failure_reason"], elapsed_seconds=elapsed_seconds
                )
                attempt_records.append(record)
                continue
            if not ctx.has_challenge_review(case_path):
                record["failure_reason"] = "challenge_review_missing"
                print_attempt_failure(
                    attempt, record["failure_reason"], elapsed_seconds=elapsed_seconds
                )
                attempt_records.append(record)
                continue

        outcome = classify_cycle_outcome(
            completion_marker=completion_marker,
            challenge_cycle=challenge_cycle,
            made_progress=made_progress,
        )
        summary = CycleSummary(
            cycle_id=cycle_id,
            completed_at=now_iso(),
            result=outcome.result,
            made_progress=made_progress,
            challenge_cycle=challenge_cycle,
            completion_marker=(
                "CASE_COMPLETE"
                if completion_marker == CASE_COMPLETE_MARKER
                else "CYCLE_DONE"
            ),
            attempts=[
                AttemptRecord.from_payload(item) for item in attempt_records + [record]
            ],
        )
        print_cycle_result(
            outcome.result, made_progress, elapsed_seconds=elapsed_seconds
        )
        write_json(cycle_path / "cycle_summary.json", summary.to_payload())
        return summary

    partial_progress_changes.update(
        partial_progress_artifact_texts(case_path, mutable_backup)
    )
    if partial_progress_changes:
        print_partial_progress_note(list(partial_progress_changes))
        restore_artifacts(case_path, mutable_backup)
        restore_artifacts(case_path, partial_progress_changes)
    else:
        restore_artifacts(case_path, mutable_backup)
    restore_artifacts(case_path, protected_backup)

    summary = CycleSummary(
        cycle_id=cycle_id,
        completed_at=now_iso(),
        result="failed",
        made_progress=False,
        attempts=[AttemptRecord.from_payload(item) for item in attempt_records],
    )
    print_failed_cycle_summary(len(attempt_records))
    write_json(cycle_path / "cycle_summary.json", summary.to_payload())
    return summary
