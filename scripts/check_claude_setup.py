#!/usr/bin/env python3
"""Validate local prerequisites and Claude-reachable MCP servers.

The list of MCP servers is read from the committed `.mcp.json`
(Claude Code's canonical MCP config). `.codex/config.toml` and `.cursor/mcp.json`
are their own canonical files for their respective tools. Drift across the three
is caught by `tests/test_mcp_configs_consistent.py`, not this script.

Run from repo root: ``uv run python scripts/check_claude_setup.py``
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MCP = ROOT / ".mcp.json"


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    message: str


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _load_servers() -> dict[str, dict]:
    payload = json.loads(CLAUDE_MCP.read_text())
    return payload["mcpServers"]


def _check_command(name: str) -> CheckResult:
    if shutil.which(name):
        return CheckResult(name, True, "installed")
    return CheckResult(name, False, "missing from PATH")


def _check_codex_cli_optional() -> CheckResult:
    if shutil.which("codex"):
        return CheckResult(
            "codex-cli",
            True,
            "installed — trust this project for `.codex/config.toml`, then verify with `codex mcp`",
        )
    return CheckResult(
        "codex-cli",
        True,
        "optional — not on PATH (skip if you use Claude Code only)",
    )


def _check_snowflake_profile() -> CheckResult:
    config_path = Path.home() / ".snowflake" / "config.toml"
    if not config_path.exists():
        return CheckResult(
            "snowflake-profile",
            False,
            "~/.snowflake/config.toml not found; create a personal `default` connection first",
        )

    text = config_path.read_text()
    if "[connections.default]" not in text and '[connections."default"]' not in text:
        return CheckResult(
            "snowflake-profile",
            False,
            "Snowflake config exists, but no `default` connection was found",
        )

    return CheckResult("snowflake-profile", True, "default connection found")


def _check_server(name: str) -> CheckResult:
    result = _run(["claude", "mcp", "get", name])
    if result.returncode == 0:
        return CheckResult(name, True, "reachable from Claude")

    output = "\n".join(
        part for part in [result.stdout.strip(), result.stderr.strip()] if part
    ).strip()
    if not output:
        output = "health check failed"

    hint = output
    if name == "snowflake":
        hint += " | Verify your personal Snowflake `default` connection and login flow."
    elif name in {
        "linear",
        "notion",
        "slack",
        "confidence-docs",
        "confidence-experiments",
    }:
        hint += " | First run: in Claude Code use `/mcp` to approve and authenticate per provider."
    return CheckResult(name, False, hint)


def main() -> int:
    servers = _load_servers()
    claude_available = shutil.which("claude") is not None
    checks = [
        _check_command("claude"),
        _check_command("uv"),
        _check_codex_cli_optional(),
        _check_snowflake_profile(),
    ]
    if claude_available:
        checks.extend(_check_server(name) for name in servers)
    else:
        checks.extend(
            CheckResult(name, False, "skipped — claude command is missing")
            for name in servers
        )

    print("Personal setup check (Claude Code + optional Codex / Cursor)")
    print(f"Repo: {ROOT}")
    print("")

    failed = False
    for check in checks:
        status = "PASS" if check.ok else "FAIL"
        print(f"[{status}] {check.name}: {check.message}")
        failed = failed or not check.ok

    print("")
    if failed:
        print("Next steps:")
        print(
            "- See `agents/docs/setup.md` for Claude Code (`/mcp`) and optional Codex (`codex mcp`) auth."
        )
        print(
            "- For Snowflake, ensure `~/.snowflake/config.toml` has a personal `default` connection."
        )
        print(
            "- Repo-level drift (server lists diverging across `.mcp.json`, "
            "`.codex/config.toml`, `.cursor/mcp.json`) is caught by `uv run pytest -q`."
        )
        return 1

    print(
        "All checks in this script passed (tools, Snowflake profile, Claude-reachable servers)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
