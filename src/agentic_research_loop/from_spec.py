from __future__ import annotations

import sys
from pathlib import Path


RECOGNIZED_FILES = ("brief.md", "plan.md", "notes.md")


def _validate_spec_dir(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"--from-spec path does not exist: {path}")
    if not path.is_dir():
        raise FileNotFoundError(f"--from-spec path is not a directory: {path}")


def _read_spec_file(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"--from-spec file is not valid UTF-8: {file_path}") from exc


def _warn_when_no_spec_files(path: Path, recognized_present: list[str]) -> None:
    if recognized_present:
        return
    all_entries = [item.name for item in path.iterdir() if item.is_file()]
    if not all_entries:
        print(
            f"warning: --from-spec directory is empty: {path}. "
            f"Using default templates for all artifacts.",
            file=sys.stderr,
        )
        return
    print(
        f"warning: --from-spec directory {path} contains no "
        f"brief.md/plan.md/notes.md. Unknown files: "
        f"{', '.join(sorted(all_entries))}. "
        f"Using default templates for all artifacts.",
        file=sys.stderr,
    )


def load_from_spec_dir(path: Path) -> dict[str, str | None]:
    """Load pre-authored brief/plan/notes from a directory.

    Returns a dict with keys "brief", "plan", "notes"; each value is the file
    contents as UTF-8 text or `None` if the file is absent.

    Raises `FileNotFoundError` if `path` does not exist.
    Raises `ValueError` if a recognized file exists but is not UTF-8.
    Warns to stderr when the directory is empty or contains only unknown files.
    """
    _validate_spec_dir(path)

    loaded: dict[str, str | None] = {"brief": None, "plan": None, "notes": None}
    recognized_present: list[str] = []
    for name in RECOGNIZED_FILES:
        file_path = path / name
        if not file_path.exists():
            continue
        recognized_present.append(name)
        key = name.removesuffix(".md")
        loaded[key] = _read_spec_file(file_path)

    _warn_when_no_spec_files(path, recognized_present)
    return loaded


_SOURCE_REGISTRY_HEADER = "## Source Registry"
_MODE_HEADER = "## Mode"


def ensure_mode_metadata(brief_md: str, *, mode: str, template: str) -> str:
    """Ensure supplied briefs carry machine-readable mode/template metadata."""
    lines = brief_md.splitlines(keepends=True)
    header_indices = [
        i for i, line in enumerate(lines) if line.rstrip("\n").strip() == _MODE_HEADER
    ]
    mode_block = (
        f"{_MODE_HEADER}\n\n- Selected mode: `{mode}`\n- Research shape: `{template}`\n"
    )
    if not header_indices:
        insert_at = len(lines)
        for i, line in enumerate(lines):
            if line.rstrip("\n").strip() == _SOURCE_REGISTRY_HEADER:
                insert_at = i
                break
        result = "".join(lines[:insert_at]).rstrip("\n")
        suffix = "".join(lines[insert_at:]).lstrip("\n")
        return (
            f"{result}\n\n{mode_block}\n{suffix}"
            if suffix
            else f"{result}\n\n{mode_block}"
        )

    start = header_indices[0]
    end = len(lines)
    for i in range(start + 1, len(lines)):
        stripped = lines[i].rstrip("\n")
        if stripped.startswith("## "):
            end = i
            break
    return "".join(lines[:start] + [mode_block + "\n"] + lines[end:])


def splice_source_registry(brief_md: str, source_registry_block: str) -> str:
    """Replace the body of the `## Source Registry` section in `brief_md`.

    If the section is present, its body (from the header up to the next `##`
    top-level section or end-of-file) is replaced with `source_registry_block`.

    If the section is absent, the new section is appended to the brief.

    If multiple `## Source Registry` headers are present, the first is
    replaced and a warning is emitted for the rest.
    """
    body = source_registry_block.rstrip()
    new_section = f"{_SOURCE_REGISTRY_HEADER}\n\n{body}\n"

    lines = brief_md.splitlines(keepends=True)
    header_indices = [
        i
        for i, line in enumerate(lines)
        if line.rstrip("\n").strip() == _SOURCE_REGISTRY_HEADER
    ]

    if not header_indices:
        return brief_md.rstrip("\n") + "\n\n" + new_section

    if len(header_indices) > 1:
        print(
            f"warning: supplied brief.md has {len(header_indices)} "
            f"`## Source Registry` headers; replacing the first and leaving "
            f"the rest unchanged.",
            file=sys.stderr,
        )

    start = header_indices[0]
    end = len(lines)
    for i in range(start + 1, len(lines)):
        stripped = lines[i].rstrip("\n")
        if stripped.startswith("## "):
            end = i
            break

    replaced = lines[:start] + [new_section] + lines[end:]
    result = "".join(replaced)
    return result
