from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "check_agent_setup.py"


def _load_setup_module():
    spec = importlib.util.spec_from_file_location("check_agent_setup", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _which(*present: str):
    return lambda name: f"/usr/bin/{name}" if name in present else None


def test_server_checks_are_skipped_when_claude_is_missing(monkeypatch, capsys) -> None:
    module = _load_setup_module()
    monkeypatch.setattr(module.shutil, "which", _which("uv"))
    monkeypatch.setattr(module, "_load_servers", lambda: {"postgres": {}, "slack": {}})

    exit_code = module.main()

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "[FAIL] claude: missing from PATH" in output
    assert "[FAIL] postgres: skipped" in output
    assert "[FAIL] slack: skipped" in output


def test_no_wired_servers_is_not_a_failure(monkeypatch, capsys) -> None:
    """A web-search or --context-path case needs no MCP server at all."""
    module = _load_setup_module()
    monkeypatch.setattr(module.shutil, "which", _which("uv", "claude"))
    monkeypatch.setattr(module, "_load_servers", lambda: {})
    monkeypatch.setattr(
        module,
        "_check_claude_goals",
        lambda: module.CheckResult("claude-goals", True, "ok"),
    )

    exit_code = module.main()

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "[PASS] mcp-servers: none wired" in output
    assert "research source enable" in output


def test_codex_is_optional_but_its_goals_flag_is_checked(monkeypatch, capsys) -> None:
    module = _load_setup_module()
    monkeypatch.setattr(module.shutil, "which", _which("uv", "claude", "codex"))
    monkeypatch.setattr(module, "_load_servers", lambda: {})
    monkeypatch.setattr(
        module,
        "_check_claude_goals",
        lambda: module.CheckResult("claude-goals", True, "ok"),
    )
    monkeypatch.setattr(
        module,
        "_run",
        lambda cmd: type(
            "R", (), {"returncode": 0, "stdout": "goals stable false\n", "stderr": ""}
        )(),
    )

    exit_code = module.main()

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "[FAIL] codex-goals: not enabled" in output
    assert "goals = true" in output


def test_codex_absence_does_not_fail_the_check(monkeypatch, capsys) -> None:
    module = _load_setup_module()
    monkeypatch.setattr(module.shutil, "which", _which("uv", "claude"))
    monkeypatch.setattr(module, "_load_servers", lambda: {})
    monkeypatch.setattr(
        module,
        "_check_claude_goals",
        lambda: module.CheckResult("claude-goals", True, "ok"),
    )

    exit_code = module.main()

    assert exit_code == 0
    assert "[PASS] codex-goals: optional" in capsys.readouterr().out
