#!/usr/bin/env python3
"""Render a completed research case into a single self-contained HTML replay.

No external dependencies and no network — just stdlib. The output is one HTML
file with everything inlined, so it opens in any browser straight from disk.

Usage:
    python viz/generate.py <case_dir> [output.html]

`<case_dir>` is a research case folder (e.g. research/2026-03-21-foo or one of
the committed examples/). If `output.html` is omitted, writes
`<case_dir>/replay.html`.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Minimal, dependency-free markdown -> HTML (the subset our artifacts use)
# --------------------------------------------------------------------------- #


def _inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return text


def md_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    list_stack: list[str] = []  # track open <ul>/<ol> with their indent

    def close_lists(to_depth: int = 0) -> None:
        while len(list_stack) > to_depth:
            out.append(f"</{list_stack.pop()}>")

    para: list[str] = []

    def flush_para() -> None:
        if para:
            out.append(f"<p>{_inline(' '.join(para))}</p>")
            para.clear()

    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        if not stripped:
            flush_para()
            close_lists()
            i += 1
            continue

        if stripped.startswith("#"):
            flush_para()
            close_lists()
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            out.append(f"<h{level}>{_inline(text)}</h{level}>")
            i += 1
            continue

        if stripped in {"---", "***", "___"}:
            flush_para()
            close_lists()
            out.append("<hr/>")
            i += 1
            continue

        if stripped.startswith(">"):
            flush_para()
            close_lists()
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(f"<blockquote>{_inline(' '.join(quote))}</blockquote>")
            continue

        ol = re.match(r"^(\s*)(\d+)\.\s+(.*)$", raw)
        ul = re.match(r"^(\s*)[-*]\s+(.*)$", raw)
        if ol or ul:
            flush_para()
            indent = len((ol or ul).group(1))
            depth = indent // 2 + 1
            tag = "ol" if ol else "ul"
            content = (ol.group(3) if ol else ul.group(2)).strip()
            while len(list_stack) > depth:
                out.append(f"</{list_stack.pop()}>")
            if len(list_stack) < depth:
                out.append(f"<{tag}>")
                list_stack.append(tag)
            out.append(f"<li>{_inline(content)}</li>")
            i += 1
            continue

        close_lists()
        para.append(stripped)
        i += 1

    flush_para()
    close_lists()
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Case reading
# --------------------------------------------------------------------------- #


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _section(md: str, heading: str) -> str:
    """Return the body under a `## heading` (up to the next `##`)."""
    pattern = rf"(?ms)^#{{1,3}}\s+{re.escape(heading)}\s*\n(.*?)(?=^\#{{1,3}}\s|\Z)"
    m = re.search(pattern, md)
    return m.group(1).strip() if m else ""


def _meta_value(status_md: str, label: str) -> str:
    m = re.search(rf"(?im)^-\s*{re.escape(label)}:\s*`([^`]*)`", status_md)
    return m.group(1).strip() if m else ""


def read_case(case_dir: Path) -> dict[str, str]:
    report = _read(case_dir / "report.md")
    brief = _read(case_dir / "brief.md")
    status = _read(case_dir / "status.md")
    question = _section(report, "Question") or _section(brief, "Question")
    return {
        "slug": case_dir.name,
        "question": question.strip() or case_dir.name,
        "report": report,
        "notes": _read(case_dir / "notes.md"),
        "plan": _read(case_dir / "plan.md"),
        "status": _meta_value(status, "Status"),
        "cycles": _meta_value(status, "Cycle count"),
        "challenge": _meta_value(status, "Challenge status"),
        "report_state": _meta_value(status, "Report state"),
    }


# --------------------------------------------------------------------------- #
# HTML rendering
# --------------------------------------------------------------------------- #

_CSS = """
:root { --bg:#0f1117; --card:#171a23; --ink:#e6e8ee; --muted:#9aa3b2;
  --line:#262b38; --accent:#6ea8fe; --good:#3fb950; --warn:#d29922; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
.wrap { max-width:860px; margin:0 auto; padding:40px 22px 80px; }
header.hero { border-bottom:1px solid var(--line); padding-bottom:22px; margin-bottom:26px; }
.kicker { color:var(--accent); font-weight:600; letter-spacing:.04em;
  text-transform:uppercase; font-size:12px; }
h1.q { font-size:26px; line-height:1.3; margin:.35em 0 .6em; }
.badges { display:flex; flex-wrap:wrap; gap:8px; }
.badge { font-size:12.5px; padding:3px 10px; border-radius:999px;
  border:1px solid var(--line); color:var(--muted); background:var(--card); }
.badge b { color:var(--ink); font-weight:600; }
.badge.good { border-color:rgba(63,185,80,.5); color:#9be6a8; }
section.card { background:var(--card); border:1px solid var(--line);
  border-radius:12px; padding:6px 22px 18px; margin:20px 0; }
section.card > h2.section-title { color:var(--muted); font-size:13px;
  text-transform:uppercase; letter-spacing:.05em; border-bottom:1px solid var(--line);
  padding-bottom:10px; }
section.challenge { border-color:rgba(210,153,34,.5);
  box-shadow:0 0 0 1px rgba(210,153,34,.15) inset; }
section.challenge > h2.section-title { color:var(--warn); }
h1,h2,h3 { line-height:1.3; }
.body h2 { font-size:19px; margin:1.2em 0 .4em; }
.body h3 { font-size:16px; color:var(--muted); margin:1em 0 .3em; }
.body ul,.body ol { padding-left:22px; }
.body li { margin:.2em 0; }
.body code { background:#0b0d13; border:1px solid var(--line); border-radius:5px;
  padding:1px 5px; font-size:.88em; }
.body blockquote { margin:.8em 0; padding:.4em 14px; border-left:3px solid var(--warn);
  background:rgba(210,153,34,.08); color:var(--muted); }
.body strong { color:#fff; }
.body hr { border:0; border-top:1px solid var(--line); margin:1.2em 0; }
footer { color:var(--muted); font-size:12.5px; text-align:center; margin-top:36px; }
footer code { color:var(--accent); }
"""


def _badge(label: str, value: str, good: bool = False) -> str:
    if not value:
        return ""
    cls = "badge good" if good else "badge"
    return (
        f'<span class="{cls}">{html.escape(label)} <b>{html.escape(value)}</b></span>'
    )


def render(case: dict[str, str]) -> str:
    badges = "".join(
        [
            _badge("status", case["status"], good=case["status"] == "complete"),
            _badge("cycles", case["cycles"]),
            _badge("challenge", case["challenge"], good=case["challenge"] == "passed"),
            _badge("report", case["report_state"]),
        ]
    )

    # Split the report so the Challenge Review renders in its own highlighted card.
    report = case["report"]
    challenge_md = ""
    m = re.search(r"(?ms)^##\s+Challenge Review\s*\n.*\Z", report)
    if m:
        challenge_md = m.group(0)
        report = report[: m.start()].rstrip()

    def card(title: str, md: str, *, extra: str = "") -> str:
        if not md.strip():
            return ""
        cls = f"card {extra}".strip()
        return (
            f'<section class="{cls}"><h2 class="section-title">{html.escape(title)}</h2>'
            f'<div class="body">{md_to_html(md)}</div></section>'
        )

    parts = [
        card("Report", report),
        card("Challenge Review", challenge_md, extra="challenge"),
        card("Working notes", case["notes"]),
        card("Research plan", case["plan"]),
    ]

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Case replay — {html.escape(case["slug"])}</title>
<style>{_CSS}</style></head>
<body><div class="wrap">
<header class="hero">
  <div class="kicker">Agentic Research Loop · case replay</div>
  <h1 class="q">{html.escape(case["question"])}</h1>
  <div class="badges">{badges}</div>
</header>
{"".join(p for p in parts if p)}
<footer>Self-contained replay generated by <code>viz/generate.py</code>.</footer>
</div></body></html>
"""


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        sys.stderr.write("usage: python viz/generate.py <case_dir> [output.html]\n")
        return 2
    case_dir = Path(argv[1])
    if not case_dir.is_dir():
        sys.stderr.write(f"not a directory: {case_dir}\n")
        return 1
    output = Path(argv[2]) if len(argv) > 2 else case_dir / "replay.html"
    case = read_case(case_dir)
    output.write_text(render(case), encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
