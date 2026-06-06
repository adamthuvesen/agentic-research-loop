"""Backward-compatible re-exports for run UI helpers."""

from __future__ import annotations

from .run_ui import (
    LiveTimer,
    format_elapsed,
    muted,
    print_attempt_failure,
    print_attempt_start,
    print_cycle_result,
    print_cycle_start,
    print_kv,
    print_plan_status,
    print_run_footer,
    print_run_header,
    print_run_summary,
    status_text,
)

__all__ = [
    "LiveTimer",
    "format_elapsed",
    "muted",
    "print_attempt_failure",
    "print_attempt_start",
    "print_cycle_result",
    "print_cycle_start",
    "print_kv",
    "print_plan_status",
    "print_run_footer",
    "print_run_header",
    "print_run_summary",
    "status_text",
]

# Legacy private aliases used by older imports
_LiveTimer = LiveTimer
_format_elapsed = format_elapsed
_muted = muted
_print_attempt_failure = print_attempt_failure
_print_attempt_start = print_attempt_start
_print_cycle_result = print_cycle_result
_print_cycle_start = print_cycle_start
_print_kv = print_kv
_print_plan_status = print_plan_status
_print_run_header = print_run_header
_print_run_summary = print_run_summary
_status_text = status_text
