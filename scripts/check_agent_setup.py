#!/usr/bin/env python3
"""Check the local prerequisites for running research inside a native goal.

The MCP server list is read from the committed `.mcp.json`, so this checks
exactly the bundles you enabled rather than a fixed roster. `.codex/config.toml`
and `.cursor/mcp.json` are local-only files created by `research source enable`.
Drift across the three is caught by `tests/test_mcp_configs_consistent.py`, not
this script.

Run from the repo root: ``uv run python scripts/check_agent_setup.py``
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MCP = ROOT / ".mcp.json"
CODEX_CONFIG = ROOT / ".codex" / "config.toml"


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    message: str


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)


def _load_servers() -> dict[str, dict]:
    if not CLAUDE_MCP.exists():
        return {}
    payload = json.loads(CLAUDE_MCP.read_text(encoding="utf-8"))
    servers = payload.get("mcpServers", {})
    return servers if isinstance(servers, dict) else {}


def _check_command(name: str) -> CheckResult:
    if shutil.which(name):
        return CheckResult(name, True, "installed")
    return CheckResult(name, False, "missing from PATH")


def _check_claude_goals() -> CheckResult:
    """Claude Code has no feature probe for goals, so check for a recent CLI."""
    if not shutil.which("claude"):
        return CheckResult("claude-goals", False, "skipped because claude is missing")
    result = _run(["claude", "--version"])
    if result.returncode != 0:
        return CheckResult(
            "claude-goals", False, "could not read the Claude Code version"
        )
    version = result.stdout.strip() or "unknown version"
    return CheckResult(
        "claude-goals",
        True,
        f"{version} — run `/goal` in Claude Code to confirm it is available",
    )


def _check_codex_goals() -> CheckResult:
    """Codex gates goals behind a feature flag, which `codex features` reports."""
    if not shutil.which("codex"):
        return CheckResult(
            "codex-goals", True, "optional — codex is not on PATH, skipping"
        )
    result = _run(["codex", "features", "list"])
    enabled = any(
        line.split()[:3] == ["goals", "stable", "true"]
        for line in result.stdout.splitlines()
    )
    if result.returncode == 0 and enabled:
        return CheckResult("codex-goals", True, "stable feature enabled")
    return CheckResult(
        "codex-goals",
        False,
        f"not enabled. Add `[features] goals = true` to {CODEX_CONFIG.name}",
    )


def _check_server(name: str, spec: dict) -> CheckResult:
    result = _run(["claude", "mcp", "get", name])
    if result.returncode == 0:
        return CheckResult(name, True, "reachable from Claude")

    output = "\n".join(
        part for part in (result.stdout.strip(), result.stderr.strip()) if part
    ).strip()
    hint = output or "health check failed"
    if "url" in spec:
        # Remote servers authenticate per provider on first use.
        hint += " | First run: use `/mcp` in Claude Code to approve and authenticate."
    else:
        hint += " | Check the bundle's SETUP.md for its credential or config step."
    return CheckResult(name, False, hint)


def _server_checks(servers: dict[str, dict]) -> list[CheckResult]:
    if not servers:
        return [
            CheckResult(
                "mcp-servers",
                True,
                "none wired — fine for web-search and --context-path cases. "
                "Add one with `research source enable <name>`",
            )
        ]
    if not shutil.which("claude"):
        return [
            CheckResult(name, False, "skipped — claude command is missing")
            for name in servers
        ]
    return [_check_server(name, spec) for name, spec in servers.items()]


def main() -> int:
    servers = _load_servers()
    checks = [
        _check_command("uv"),
        _check_command("claude"),
        _check_claude_goals(),
        _check_codex_goals(),
        *_server_checks(servers),
    ]

    print("Native goal research setup")
    print(f"Repo: {ROOT}\n")

    for check in checks:
        print(f"[{'PASS' if check.ok else 'FAIL'}] {check.name}: {check.message}")

    if all(check.ok for check in checks):
        print("\nReady to run a case inside a native goal.")
        return 0

    print("\nSee `.agents/docs/setup.md` for authentication and setup steps.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
