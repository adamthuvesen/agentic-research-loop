from __future__ import annotations

import os
import sys
import threading
import time
from typing import Any


_ANSI_RESET = "\033[0m"
_ANSI_STYLES = {
    "bold": "\033[1m",
    "dim": "\033[2m",
    "cyan": "\033[36m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "red": "\033[31m",
}


def supports_ansi() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def style(text: str, *styles: str) -> str:
    if not supports_ansi():
        return text
    prefix = "".join(_ANSI_STYLES[name] for name in styles)
    return f"{prefix}{text}{_ANSI_RESET}"


def muted(text: str) -> str:
    return style(text, "dim")


def status_text(kind: str, text: str) -> str:
    palette = {
        "info": ("cyan", "bold"),
        "success": ("green", "bold"),
        "warning": ("yellow", "bold"),
        "error": ("red", "bold"),
    }
    return style(text, *palette[kind])


def print_header(title: str) -> None:
    width = max(len(title) + 6, 30)
    bar = "━" * width
    side_padding = max((width - len(title)) // 2, 1)
    title_line = f"{' ' * side_padding}{title}"
    if len(title_line) < width:
        title_line = f"{title_line}{' ' * (width - len(title_line))}"
    print()
    print(f"  {muted('┏')}{muted(bar)}{muted('┓')}")
    print(f"  {muted('┃')}{style(title_line, 'bold')}{muted('┃')}")
    print(f"  {muted('┗')}{muted(bar)}{muted('┛')}")
    print()


def print_section(label: str) -> None:
    rule_len = max(50 - len(label) - 2, 4)
    rule = "─" * rule_len
    print()
    print(f"  {muted('──')} {style(label, 'bold')} {muted(rule)}")
    print()


def print_kv(label: str, value: str) -> None:
    print(f"  {muted(f'{label:<14}')}{value}")


def format_elapsed(total_seconds: float) -> str:
    seconds = max(0, int(total_seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}m"


class LiveTimer:
    def __init__(self, label: str) -> None:
        self.label = label
        self.started_at = 0.0
        self.elapsed_seconds = 0.0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> LiveTimer:
        self.started_at = time.monotonic()
        if supports_ansi():
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def stop(self) -> float:
        self.elapsed_seconds = time.monotonic() - self.started_at
        if self._thread is not None:
            self._stop.set()
            self._thread.join(timeout=1.5)
            sys.stdout.write("\r\033[2K")
            sys.stdout.flush()
        return self.elapsed_seconds

    def _run(self) -> None:
        while not self._stop.is_set():
            elapsed = format_elapsed(time.monotonic() - self.started_at)
            sys.stdout.write(
                f"\r\033[2K  {muted(f'{self.label:<14}')}{style(elapsed, 'cyan', 'bold')}"
            )
            sys.stdout.flush()
            if self._stop.wait(1):
                break


def print_run_header(case_name: str, runner_name: str, max_cycles: int | None) -> None:
    cycle_limit = "∞" if max_cycles is None else str(max_cycles)
    print_header("Research")
    print_section("Config")
    print_kv("Case", case_name)
    print_kv("Runner", runner_name)
    print_kv("Max cycles", cycle_limit)
    print_kv("Status", f"{status_text('info', 'Starting')} research loop")


def print_plan_status(
    message: str,
    *,
    success: bool = False,
    failed: bool = False,
    elapsed_seconds: float | None = None,
) -> None:
    kind = "success" if success else "error" if failed else "info"
    suffix = (
        f" {muted(f'(in {format_elapsed(elapsed_seconds)})')}"
        if elapsed_seconds is not None
        else ""
    )
    print_kv("Planning", f"{status_text(kind, '•')} {message}{suffix}")


def print_cycle_start(cycle_id: str) -> None:
    print_section(f"Cycle {cycle_id}")


def print_attempt_start(attempt: int, total_attempts: int) -> None:
    print_kv("Attempt", f"{attempt}/{total_attempts}")


def print_attempt_failure(
    attempt: int, reason: str, *, elapsed_seconds: float | None = None
) -> None:
    suffix = (
        f" {muted(f'(after {format_elapsed(elapsed_seconds)})')}"
        if elapsed_seconds is not None
        else ""
    )
    print_kv(
        "Status",
        f"{status_text('error', 'x')} attempt {attempt} failed: {reason}{suffix}",
    )


def print_cycle_result(
    result_name: str, made_progress: bool, *, elapsed_seconds: float | None = None
) -> None:
    if result_name in {"progress", "complete"}:
        kind = "success"
        icon = "✓"
    elif result_name == "challenge_required":
        kind = "info"
        icon = "→"
    else:
        kind = "warning"
        icon = "!"
    print_kv("Result", f"{status_text(kind, icon)} {status_text(kind, result_name)}")
    print_kv("Progress", "yes" if made_progress else "no")
    if elapsed_seconds is not None:
        print_kv("Elapsed", format_elapsed(elapsed_seconds))


def print_run_summary(
    results: list[dict[str, Any]],
    stop_reason: str,
    *,
    elapsed_seconds: float | None = None,
) -> None:
    print_section("Summary")
    print_kv("Cycles", str(len(results)))
    if elapsed_seconds is not None:
        print_kv("Elapsed", format_elapsed(elapsed_seconds))
    print_kv("Stop reason", stop_reason)
    print()


def print_failed_cycle_summary(attempt_count: int) -> None:
    print(
        f"  {status_text('error', 'x')} {muted('result')} {status_text('error', 'failed')}"
    )
    print(f"  {muted('attempts')} {attempt_count}")


def print_partial_progress_note(kept_paths: list[str]) -> None:
    print(
        f"  {muted('note')} keeping partial artifact changes from earlier attempts: "
        + ", ".join(kept_paths)
    )


def print_run_footer(summaries: list[dict[str, Any]]) -> None:
    count = len(summaries)
    line = f"{style(str(count), 'bold')} cycle(s) completed"
    if summaries:
        last = summaries[-1].get("result", "")
        line += f"  {muted('·')}  last result: {style(last, 'bold')}"
    print(f"  {line}")
    print()
