from __future__ import annotations

from pathlib import Path

import pytest

from agentic_research_loop.from_spec import (
    load_from_spec_dir,
    splice_source_registry,
)


def test_splice_replaces_existing_section(tmp_path: Path) -> None:
    brief = (
        "# Research Brief\n\n"
        "## Question\n\nWhy?\n\n"
        "## Source Registry\n\n"
        "- old content that should be replaced\n"
        "- more old content\n\n"
        "## Scope\n\n- in scope\n"
    )
    new_block = "- NEW line 1\n- NEW line 2"
    result = splice_source_registry(brief, new_block)
    assert "## Source Registry\n\n- NEW line 1\n- NEW line 2\n" in result
    assert "old content" not in result
    assert "## Scope\n\n- in scope\n" in result
    assert "## Question\n\nWhy?\n" in result


def test_splice_appends_when_section_missing() -> None:
    brief = "# Research Brief\n\n## Question\n\nWhy?\n"
    new_block = "- generated line"
    result = splice_source_registry(brief, new_block)
    assert result.endswith("## Source Registry\n\n- generated line\n")
    assert "## Question\n\nWhy?" in result


def test_splice_handles_multiple_sections(capsys: pytest.CaptureFixture) -> None:
    brief = "## Source Registry\n\n- first\n\n## Source Registry\n\n- second\n"
    result = splice_source_registry(brief, "- replacement")
    captured = capsys.readouterr()
    assert "2 `## Source Registry`" in captured.err
    # First occurrence replaced; second left alone
    assert result.count("- replacement") == 1
    assert "- second" in result


def test_splice_handles_no_trailing_newline() -> None:
    brief = "# Brief\n\n## Question\n\nWhy?"
    result = splice_source_registry(brief, "- block")
    assert result.endswith("## Source Registry\n\n- block\n")


def test_load_all_three_files(tmp_path: Path) -> None:
    (tmp_path / "brief.md").write_text("# brief content\n", encoding="utf-8")
    (tmp_path / "plan.md").write_text("# plan content\n", encoding="utf-8")
    (tmp_path / "notes.md").write_text("# notes content\n", encoding="utf-8")
    result = load_from_spec_dir(tmp_path)
    assert result == {
        "brief": "# brief content\n",
        "plan": "# plan content\n",
        "notes": "# notes content\n",
    }


def test_load_subset(tmp_path: Path) -> None:
    (tmp_path / "brief.md").write_text("only brief\n", encoding="utf-8")
    result = load_from_spec_dir(tmp_path)
    assert result["brief"] == "only brief\n"
    assert result["plan"] is None
    assert result["notes"] is None


def test_load_empty_dir_warns(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    result = load_from_spec_dir(tmp_path)
    captured = capsys.readouterr()
    assert "empty" in captured.err
    assert result == {"brief": None, "plan": None, "notes": None}


def test_load_unknown_files_warn(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    (tmp_path / "readme.txt").write_text("nope\n", encoding="utf-8")
    (tmp_path / "brief.txt").write_text("wrong ext\n", encoding="utf-8")
    result = load_from_spec_dir(tmp_path)
    captured = capsys.readouterr()
    assert "Unknown files" in captured.err
    assert "readme.txt" in captured.err
    assert "brief.txt" in captured.err
    assert result == {"brief": None, "plan": None, "notes": None}


def test_load_missing_dir_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    with pytest.raises(FileNotFoundError) as exc_info:
        load_from_spec_dir(missing)
    assert str(missing) in str(exc_info.value)


def test_load_non_directory_raises(tmp_path: Path) -> None:
    file_path = tmp_path / "not-a-dir.md"
    file_path.write_text("content", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        load_from_spec_dir(file_path)


def test_load_non_utf8_raises(tmp_path: Path) -> None:
    bad = tmp_path / "brief.md"
    bad.write_bytes(b"\xff\xfe not utf8")
    with pytest.raises(ValueError) as exc_info:
        load_from_spec_dir(tmp_path)
    assert "UTF-8" in str(exc_info.value)
    assert "brief.md" in str(exc_info.value)
