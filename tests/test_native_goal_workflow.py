"""Pin the documented native-goal workflow.

These strings are the whole user-facing contract: the two client invocation
forms, and the mode dispatch that stops the skill from either recursing into a
nested goal or stalling after scaffolding.
"""

from __future__ import annotations

from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".agents" / "skills"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_readme_shows_both_client_invocations() -> None:
    readme = _read(ROOT / "README.md")

    assert "/goal Use the research-goal skill to investigate:" in readme
    assert "/goal Use $research-goal to investigate:" in readme


def test_research_goal_skill_dispatches_on_whether_a_goal_is_active() -> None:
    skill = _read(SKILLS / "research-goal" / "SKILL.md")

    assert "execution mode" in skill
    assert "preparation mode" in skill
    assert "Do not submit it as a nested slash command" in skill
    assert "Do not begin the investigation." in skill


def test_research_spec_skill_hands_off_to_the_goal() -> None:
    skill = _read(SKILLS / "research-spec" / "SKILL.md")

    assert "uv run research goal" in skill
    assert "nested slash command" in skill


@pytest.mark.parametrize("name", ["research-goal", "research-spec"])
def test_skills_forbid_a_second_execution_system(name: str) -> None:
    skill = _read(SKILLS / name / "SKILL.md")

    assert "Agent SDK" in skill
    assert "subprocess" in skill


def test_codex_sidecar_uses_the_dollar_skill_reference() -> None:
    sidecar = _read(SKILLS / "research-goal" / "agents" / "openai.yaml")

    assert "$research-goal" in sidecar


# The decision record has to name the flags to explain why they are gone.
_BYPASS_FLAG_EXEMPT = {
    Path("tests/test_native_goal_workflow.py"),
    Path(".agents/docs/decisions/native-goals.md"),
}
_SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
    "research",
}


def test_no_permission_bypass_flag_ships_anywhere() -> None:
    """The bypass flags existed only because the loop was headless."""
    banned = ("dangerously-skip-permissions", "dangerously-bypass-approvals")
    offenders = [
        relative
        for path in ROOT.rglob("*")
        if path.is_file()
        and not _SKIP_DIRS & set(path.parts)
        and (relative := path.relative_to(ROOT)) not in _BYPASS_FLAG_EXEMPT
        and any(
            flag in path.read_text(encoding="utf-8", errors="ignore") for flag in banned
        )
    ]

    assert offenders == []
