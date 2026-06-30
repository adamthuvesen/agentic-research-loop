from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import threading
from pathlib import Path
from typing import Any


DEFAULT_MAX_OUTPUT_BYTES = 5 * 1024 * 1024
DEFAULT_AGENT_MESSAGE_TAIL_BYTES = 512 * 1024

BUILTIN_RUNNERS = {
    "claude": "config/runners/claude.json",
    "codex": "config/runners/codex.json",
    "demo": "config/runners/demo.json",
    "claude-local": "config/runners/claude-local.json",
}


def builtin_runner_path(repo_root: Path, runner_name: str) -> Path:
    try:
        filename = BUILTIN_RUNNERS[runner_name]
    except KeyError as exc:
        supported = ", ".join(sorted(BUILTIN_RUNNERS))
        raise ValueError(
            f"Unknown runner {runner_name!r}. Supported runners: {supported}"
        ) from exc
    return repo_root / filename


def _load_runner_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Runner config must be a JSON object: {path}")
    return payload


def _command_config(
    path: Path, payload: dict[str, Any]
) -> tuple[list[str] | None, str | None]:
    command = payload.get("command")
    command_template = payload.get("command_template")
    if bool(command) == bool(command_template):
        raise ValueError(
            f"Runner config must define exactly one of 'command' or 'command_template': {path}"
        )
    if command is not None:
        if not isinstance(command, list) or not all(
            isinstance(item, str) for item in command
        ):
            raise ValueError(f"'command' must be a JSON list of strings: {path}")
    if command_template is not None and not isinstance(command_template, str):
        raise ValueError(f"'command_template' must be a string: {path}")
    return command, command_template


def _bool_config(path: Path, payload: dict[str, Any], key: str, default: bool) -> bool:
    value = payload.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"'{key}' must be a boolean: {path}")
    return value


def _env_config(path: Path, payload: dict[str, Any]) -> dict[str, str]:
    env = payload.get("env", {})
    if not isinstance(env, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in env.items()
    ):
        raise ValueError(f"'env' must be a string-to-string object: {path}")
    return env


def _positive_int_config(
    path: Path, payload: dict[str, Any], key: str, default: int
) -> int:
    value = payload.get(key, default)
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"'{key}' must be a positive integer: {path}")
    return value


def load_runner_config(path: Path) -> dict[str, Any]:
    payload = _load_runner_payload(path)
    command, command_template = _command_config(path, payload)
    allow_shell = _bool_config(path, payload, "allow_shell", False)
    if command_template is not None and not allow_shell:
        raise ValueError(f"'command_template' requires 'allow_shell': true in {path}")

    return {
        "command": command,
        "command_template": command_template,
        "allow_shell": allow_shell,
        "env": _env_config(path, payload),
        "timeout_seconds": _positive_int_config(path, payload, "timeout_seconds", 1800),
        "prompt_via_stdin": _bool_config(path, payload, "prompt_via_stdin", False),
        "max_output_bytes": _positive_int_config(
            path, payload, "max_output_bytes", DEFAULT_MAX_OUTPUT_BYTES
        ),
        "agent_message_tail_bytes": _positive_int_config(
            path,
            payload,
            "agent_message_tail_bytes",
            DEFAULT_AGENT_MESSAGE_TAIL_BYTES,
        ),
    }


class _SafeFormatMap(dict):
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


def render_placeholders(value: str, context: dict[str, str]) -> str:
    return value.format_map(_SafeFormatMap(context))


def render_shell_placeholders(value: str, context: dict[str, str]) -> str:
    def _replace(m: re.Match) -> str:
        key = m.group(1)
        return shlex.quote(context[key]) if key in context else m.group(0)

    return re.sub(r"\{(\w+)\}", _replace, value)


class _StreamCapture:
    def __init__(self, path: Path, *, max_bytes: int, tail_bytes: int) -> None:
        self.path = path
        self.max_bytes = max_bytes
        self.tail_bytes = tail_bytes
        self.total_bytes = 0
        self.truncated = False
        self.tail = bytearray()

    def capture(self, stream: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        with self.path.open("wb") as handle:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    break
                self.total_bytes += len(chunk)
                if written < self.max_bytes:
                    keep = chunk[: self.max_bytes - written]
                    handle.write(keep)
                    written += len(keep)
                self.tail.extend(chunk)
                if len(self.tail) > self.tail_bytes:
                    del self.tail[: len(self.tail) - self.tail_bytes]
            if self.total_bytes > self.max_bytes:
                self.truncated = True
                handle.write(
                    b"\n[agentic-research-loop: output truncated after "
                    + str(self.max_bytes).encode("ascii")
                    + b" bytes]\n"
                )

    def tail_text(self) -> str:
        return bytes(self.tail).decode("utf-8", errors="replace")


def _write_stdin(stream: Any, text: str) -> None:
    try:
        stream.write(text.encode("utf-8"))
    except BrokenPipeError:
        pass
    finally:
        try:
            stream.close()
        except BrokenPipeError:
            pass


def _runner_env(
    runner_config: dict[str, Any], context: dict[str, str]
) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            key: render_placeholders(value, context)
            for key, value in runner_config["env"].items()
        }
    )
    return env


def _runner_command(
    runner_config: dict[str, Any], context: dict[str, str]
) -> tuple[list[str] | str, bool]:
    if runner_config["command"] is not None:
        return [
            render_placeholders(token, context) for token in runner_config["command"]
        ], False
    return render_shell_placeholders(runner_config["command_template"], context), True


def _capture_for(path: Path, runner_config: dict[str, Any]) -> _StreamCapture:
    return _StreamCapture(
        path,
        max_bytes=runner_config["max_output_bytes"],
        tail_bytes=runner_config["agent_message_tail_bytes"],
    )


def _start_capture_thread(capture: _StreamCapture, stream: Any) -> threading.Thread:
    thread = threading.Thread(target=capture.capture, args=(stream,), daemon=True)
    thread.start()
    return thread


def _start_stdin_thread(
    process: subprocess.Popen, *, enabled: bool, prompt_text: str
) -> threading.Thread | None:
    if not enabled or process.stdin is None:
        return None
    thread = threading.Thread(
        target=_write_stdin, args=(process.stdin, prompt_text), daemon=True
    )
    thread.start()
    return thread


def _wait_for_process(
    process: subprocess.Popen, *, timeout_seconds: int
) -> tuple[bool, int | None]:
    try:
        return False, process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        return True, None


def _write_agent_message_tail(
    agent_message_path: Path, stdout_capture: _StreamCapture
) -> None:
    if agent_message_path.exists():
        return
    stdout_tail = stdout_capture.tail_text()
    if stdout_tail.strip():
        agent_message_path.write_text(stdout_tail, encoding="utf-8")


def _runner_result(
    *,
    timed_out: bool,
    returncode: int | None,
    command: list[str] | str,
    stdout_path: Path,
    stderr_path: Path,
    agent_message_path: Path,
    stdout_capture: _StreamCapture,
    stderr_capture: _StreamCapture,
) -> dict[str, Any]:
    return {
        "timed_out": timed_out,
        "returncode": returncode,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "agent_message_path": str(agent_message_path)
        if agent_message_path.exists()
        else None,
        "command": command,
        "stdout_bytes": stdout_capture.total_bytes,
        "stderr_bytes": stderr_capture.total_bytes,
        "stdout_truncated": stdout_capture.truncated,
        "stderr_truncated": stderr_capture.truncated,
    }


def invoke_runner(
    runner_config: dict[str, Any],
    *,
    repo_root: Path,
    context: dict[str, str],
    prompt_text: str,
    stdout_path: Path,
    stderr_path: Path,
    agent_message_path: Path,
) -> dict[str, Any]:
    command, shell = _runner_command(runner_config, context)
    stdout_capture = _capture_for(stdout_path, runner_config)
    stderr_capture = _capture_for(stderr_path, runner_config)

    process = subprocess.Popen(
        command,
        cwd=repo_root,
        env=_runner_env(runner_config, context),
        stdin=subprocess.PIPE if runner_config["prompt_via_stdin"] else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=shell,
    )
    stdout_thread = _start_capture_thread(stdout_capture, process.stdout)
    stderr_thread = _start_capture_thread(stderr_capture, process.stderr)
    stdin_thread = _start_stdin_thread(
        process,
        enabled=runner_config["prompt_via_stdin"],
        prompt_text=prompt_text,
    )
    timed_out, returncode = _wait_for_process(
        process, timeout_seconds=runner_config["timeout_seconds"]
    )

    if stdin_thread is not None:
        stdin_thread.join()
    stdout_thread.join()
    stderr_thread.join()

    _write_agent_message_tail(agent_message_path, stdout_capture)
    return _runner_result(
        timed_out=timed_out,
        returncode=returncode,
        command=command,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        agent_message_path=agent_message_path,
        stdout_capture=stdout_capture,
        stderr_capture=stderr_capture,
    )
