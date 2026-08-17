from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "evals" / "native-goal" / "prepare_workspace.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("prepare_workspace", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _fake_repo(tmp_path: Path) -> Path:
    source = tmp_path / "repo"
    for relative in (
        "README.md",
        "research/2026-01-01-old-case/report.md",
        "examples/local-sources/exports_weekly.csv",
        "examples/demo-export-reliability/report.md",
        ".agents/docs/setup.md",
        ".agents/docs/decisions/native-goals.md",
        "evals/native-goal/rubric.md",
        "evals/native-goal/results/2026-01-01.md",
        "src/pkg/__pycache__/thing.pyc",
        ".env.local",
        ".mcp.json",
        ".codex/config.toml",
        ".cursor/mcp.json",
        ".claude/settings.json",
        ".claude/settings.local.json",
        ".claude/skills/research-goal/SKILL.md",
    ):
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")
    return source


def test_workspace_hides_everything_that_leaks_the_answer(tmp_path: Path) -> None:
    module = _load_module()
    source = _fake_repo(tmp_path)

    workspace = module.prepare_workspace(source, tmp_path / "canary")

    assert not (workspace / "research").exists()
    assert not (workspace / "examples" / "demo-export-reliability").exists()
    assert not (workspace / ".agents" / "docs" / "decisions").exists()
    assert not (workspace / "evals" / "native-goal" / "results").exists()
    assert not (workspace / ".env.local").exists()
    assert not (workspace / "src" / "pkg" / "__pycache__").exists()


def test_workspace_carries_no_live_mcp_wiring(tmp_path: Path) -> None:
    """The canary claims no MCP and no network, and the export is uncommitted."""
    module = _load_module()
    source = _fake_repo(tmp_path)

    workspace = module.prepare_workspace(source, tmp_path / "canary")

    assert not (workspace / ".mcp.json").exists()
    assert not (workspace / ".codex").exists()
    assert not (workspace / ".cursor").exists()
    assert not (workspace / ".claude" / "settings.json").exists()
    assert not (workspace / ".claude" / "settings.local.json").exists()
    # ...but the skills the run needs must survive.
    assert (workspace / ".claude" / "skills" / "research-goal" / "SKILL.md").exists()


def test_workspace_keeps_what_the_run_needs(tmp_path: Path) -> None:
    module = _load_module()
    source = _fake_repo(tmp_path)

    workspace = module.prepare_workspace(source, tmp_path / "canary")

    assert (workspace / "examples" / "local-sources" / "exports_weekly.csv").exists()
    assert (workspace / "evals" / "native-goal" / "rubric.md").exists()
    assert (workspace / ".agents" / "docs" / "setup.md").exists()


def test_target_inside_the_source_repo_is_rejected(tmp_path: Path) -> None:
    module = _load_module()
    source = _fake_repo(tmp_path)

    with pytest.raises(ValueError, match="outside"):
        module.prepare_workspace(source, source / "canary")


def test_existing_target_is_rejected(tmp_path: Path) -> None:
    module = _load_module()
    source = _fake_repo(tmp_path)
    target = tmp_path / "canary"
    target.mkdir()

    with pytest.raises(FileExistsError):
        module.prepare_workspace(source, target)
