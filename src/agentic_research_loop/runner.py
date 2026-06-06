from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from pathlib import Path
from typing import Any


BUILTIN_RUNNERS = {
    "claude": "config/runners/claude.json",
    "codex": "config/runners/codex.json",
    "demo": "config/runners/demo.json",
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

    return {
        "command": command,
        "command_template": command_template,
        "allow_shell": allow_shell,
        "env": env,
        "timeout_seconds": timeout_seconds,
        "prompt_via_stdin": prompt_via_stdin,
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
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "timeout": runner_config["timeout_seconds"],
        "shell": shell,
    }
    if runner_config["prompt_via_stdin"]:
        kwargs["input"] = prompt_text

    try:
        completed = subprocess.run(command, **kwargs)
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        if not agent_message_path.exists() and stdout.strip():
            agent_message_path.write_text(stdout, encoding="utf-8")
        return {
            "timed_out": False,
            "returncode": completed.returncode,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "agent_message_path": str(agent_message_path)
            if agent_message_path.exists()
            else None,
            "command": command,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = (
            exc.stdout
            if isinstance(exc.stdout, str)
            else (exc.stdout or b"").decode("utf-8", errors="replace")
        )
        stderr = (
            exc.stderr
            if isinstance(exc.stderr, str)
            else (exc.stderr or b"").decode("utf-8", errors="replace")
        )
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        return {
            "timed_out": True,
            "returncode": None,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "agent_message_path": str(agent_message_path)
            if agent_message_path.exists()
            else None,
            "command": command,
        }
