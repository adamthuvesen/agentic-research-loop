"""Tests for the self-contained HTML replay generator."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from viz.generate import md_to_html, read_case, render  # noqa: E402

EXAMPLE = PROJECT_ROOT / "examples" / "demo-registration-drop"


def test_renders_demo_example() -> None:
    out = render(read_case(EXAMPLE))
    assert out.startswith("<!doctype html>")
    assert "Why did weekly registrations drop" in out
    assert "Challenge Review" in out
    assert 'class="badge good"' in out  # status complete / challenge passed


def test_replay_is_self_contained() -> None:
    """No external resources — opens straight from disk."""
    out = render(read_case(EXAMPLE))
    assert "<link" not in out
    assert "src=" not in out
    assert "@import" not in out


def test_render_is_deterministic() -> None:
    case = read_case(EXAMPLE)
    assert render(case) == render(case)


def test_committed_replay_is_up_to_date() -> None:
    """The committed replay.html must match a fresh render of the example."""
    committed = (EXAMPLE / "replay.html").read_text(encoding="utf-8")
    assert committed == render(read_case(EXAMPLE))


def test_markdown_subset() -> None:
    html = md_to_html("# Title\n\n- **bold** and `code`\n\n> a quote")
    assert "<h1>Title</h1>" in html
    assert "<strong>bold</strong>" in html
    assert "<code>code</code>" in html
    assert "<blockquote>" in html
