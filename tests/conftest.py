from __future__ import annotations

import json
from pathlib import Path

import pytest

_SUPPORT_DIR = Path(__file__).resolve().parent / "support"
_FAKE_RUNNER = _SUPPORT_DIR / "fake_runner.py"


@pytest.fixture()
def repo_root(tmp_path: Path) -> Path:
    root = tmp_path / "agentic-research-loop"
    root.mkdir()
    (root / "pyproject.toml").write_text(
        "[project]\nname = 'agentic-research-loop'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )
    (root / "program.md").write_text("# test program\n", encoding="utf-8")
    fake_runner_cfg = {
        "command": [
            "python3",
            str(_FAKE_RUNNER),
            "{case_dir}",
            "{agent_message_file}",
        ],
        "prompt_via_stdin": True,
        "timeout_seconds": 30,
        "env": {},
    }
    runners_dir = root / "config" / "runners"
    runners_dir.mkdir(parents=True, exist_ok=True)
    (runners_dir / "claude.json").write_text(
        json.dumps(fake_runner_cfg, indent=2) + "\n",
        encoding="utf-8",
    )
    (runners_dir / "codex.json").write_text(
        json.dumps(fake_runner_cfg, indent=2) + "\n",
        encoding="utf-8",
    )
    return root
