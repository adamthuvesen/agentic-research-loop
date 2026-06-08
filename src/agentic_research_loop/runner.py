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


def load_runner_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Runner config must be a JSON object: {path}")

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

    allow_shell = payload.get("allow_shell", False)
    if not isinstance(allow_shell, bool):
        raise ValueError(f"'allow_shell' must be a boolean: {path}")
    if command_template is not None and not allow_shell:
        raise ValueError(f"'command_template' requires 'allow_shell': true in {path}")

    env = payload.get("env", {})
    if not isinstance(env, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in env.items()
    ):
        raise ValueError(f"'env' must be a string-to-string object: {path}")

    timeout_seconds = payload.get("timeout_seconds", 1800)
    if not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
        raise ValueError(f"'timeout_seconds' must be a positive integer: {path}")

    prompt_via_stdin = payload.get("prompt_via_stdin", False)
    if not isinstance(prompt_via_stdin, bool):
        raise ValueError(f"'prompt_via_stdin' must be a boolean: {path}")

    max_output_bytes = payload.get("max_output_bytes", DEFAULT_MAX_OUTPUT_BYTES)
    if not isinstance(max_output_bytes, int) or max_output_bytes <= 0:
        raise ValueError(f"'max_output_bytes' must be a positive integer: {path}")

    agent_message_tail_bytes = payload.get(
        "agent_message_tail_bytes", DEFAULT_AGENT_MESSAGE_TAIL_BYTES
    )
    if not isinstance(agent_message_tail_bytes, int) or agent_message_tail_bytes <= 0:
        raise ValueError(
            f"'agent_message_tail_bytes' must be a positive integer: {path}"
        )

    return {
        "command": command,
        "command_template": command_template,
        "allow_shell": allow_shell,
        "env": env,
        "timeout_seconds": timeout_seconds,
        "prompt_via_stdin": prompt_via_stdin,
        "max_output_bytes": max_output_bytes,
        "agent_message_tail_bytes": agent_message_tail_bytes,
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
    env = os.environ.copy()
    env.update(
        {
            key: render_placeholders(value, context)
            for key, value in runner_config["env"].items()
        }
    )
    if runner_config["command"] is not None:
        command = [
            render_placeholders(token, context) for token in runner_config["command"]
        ]
        shell = False
    else:
        command = render_shell_placeholders(runner_config["command_template"], context)
        shell = True

    kwargs: dict[str, Any] = {
        "cwd": repo_root,
        "env": env,
        "stdin": subprocess.PIPE if runner_config["prompt_via_stdin"] else None,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": shell,
    }

    stdout_capture = _StreamCapture(
        stdout_path,
        max_bytes=runner_config["max_output_bytes"],
        tail_bytes=runner_config["agent_message_tail_bytes"],
    )
    stderr_capture = _StreamCapture(
        stderr_path,
        max_bytes=runner_config["max_output_bytes"],
        tail_bytes=runner_config["agent_message_tail_bytes"],
    )

    process = subprocess.Popen(command, **kwargs)
    stdout_thread = threading.Thread(
        target=stdout_capture.capture, args=(process.stdout,), daemon=True
    )
    stderr_thread = threading.Thread(
        target=stderr_capture.capture, args=(process.stderr,), daemon=True
    )
    stdout_thread.start()
    stderr_thread.start()

    stdin_thread: threading.Thread | None = None
    if runner_config["prompt_via_stdin"] and process.stdin is not None:
        stdin_thread = threading.Thread(
            target=_write_stdin, args=(process.stdin, prompt_text), daemon=True
        )
        stdin_thread.start()

    timed_out = False
    returncode: int | None
    try:
        returncode = process.wait(timeout=runner_config["timeout_seconds"])
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        process.wait()
        returncode = None

    if stdin_thread is not None:
        stdin_thread.join()
    stdout_thread.join()
    stderr_thread.join()

    if not agent_message_path.exists():
        stdout_tail = stdout_capture.tail_text()
        if stdout_tail.strip():
            agent_message_path.write_text(stdout_tail, encoding="utf-8")

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
