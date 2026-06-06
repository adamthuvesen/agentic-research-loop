from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = ROOT / "scripts" / "check_claude_setup.py"


def _load_setup_module():
    spec = importlib.util.spec_from_file_location("check_claude_setup", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_setup_check_skips_server_checks_when_claude_is_missing(
    monkeypatch, capsys
) -> None:
    module = _load_setup_module()
    monkeypatch.setattr(
        module.shutil,
        "which",
        lambda name: None if name == "claude" else f"/usr/bin/{name}",
    )
    monkeypatch.setattr(module, "_load_servers", lambda: {"snowflake": {}, "slack": {}})
    monkeypatch.setattr(
        module,
        "_check_snowflake_profile",
        lambda: module.CheckResult("snowflake-profile", True, "default found"),
    )

    exit_code = module.main()

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "[FAIL] claude: missing from PATH" in output
    assert "[FAIL] snowflake: skipped" in output
    assert "[FAIL] slack: skipped" in output
