"""Markdown utilities for the server."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List


def render_markdown(
    *,
    title: str,
    overview: str,
    sections: Iterable[Dict[str, Any]],
    glossary: Iterable[Dict[str, str]] | None = None,
    follow_up_questions: Iterable[str] | None = None,
    transcript_path: Path | None = None,
) -> str:
    lines: List[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## Overview")
    lines.append(overview.strip())
    lines.append("")

    for section in sections:
        lines.append(f"## {section.get('title', 'Section')}")
        if image := section.get("image"):
            local_path = image.get("local_path") or image.get("url")
            if local_path:
                alt_text = image.get("title") or section.get("title", "Section image")
                lines.append(f"![{alt_text}]({local_path})")
                lines.append("")
        summary = section.get("summary", "").strip()
        if summary:
            lines.append(summary)
            lines.append("")
        key_points = section.get("key_points") or []
        if key_points:
            lines.append("### Key Points")
            for point in key_points:
                lines.append(f"- {point}")
            lines.append("")

    if glossary:
        glossary = [g for g in glossary if g.get("term") and g.get("definition")]
        if glossary:
            lines.append("## Glossary")
            for entry in glossary:
                lines.append(f"- **{entry['term']}**: {entry['definition']}")
            lines.append("")

    if follow_up_questions:
        follow_up_questions = [q for q in follow_up_questions if q]
        if follow_up_questions:
            lines.append("## Follow-up Questions")
            for question in follow_up_questions:
                lines.append(f"- {question}")
            lines.append("")

    if transcript_path:
        lines.append("## Transcript")
        lines.append(f"[Download transcript]({transcript_path})")

    return "\n".join(lines).strip() + "\n"


def write_markdown(output_path: Path, content: str) -> None:
    output_path.write_text(content, encoding="utf-8")


__all__ = ["render_markdown", "write_markdown"]

