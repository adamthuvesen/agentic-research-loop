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


SOURCE_CONSTRAINTS_HEADER = "## Source Constraints"


def replace_markdown_section(text: str, heading: str, body: str) -> str:
    """Replace the body of a `## <heading>` section, appending it if absent.

    The section runs from its header to the next `## ` header or end of file.
    When the heading appears more than once the first is replaced and the rest
    are left alone with a warning, since silently rewriting several sections
    would be harder to notice than a duplicate heading.
    """
    header = f"## {heading}"
    new_section = f"{header}\n\n{body.rstrip()}\n"

    lines = text.splitlines(keepends=True)
    header_indices = [
        i for i, line in enumerate(lines) if line.rstrip("\n").strip() == header
    ]

    if not header_indices:
        return text.rstrip("\n") + "\n\n" + new_section

    if len(header_indices) > 1:
        print(
            f"warning: supplied brief.md has {len(header_indices)} "
            f"`{header}` headers; replacing the first and leaving "
            f"the rest unchanged.",
            file=sys.stderr,
        )

    start = header_indices[0]
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].rstrip("\n").startswith("## "):
            end = i
            break

    return "".join(lines[:start] + [new_section] + lines[end:])
