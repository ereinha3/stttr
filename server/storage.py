"""Storage helpers for pending payloads and final artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from server import markdown
from server import github_ops
from server.settings import ARTIFACTS_ROOT, MARKDOWN_ROOT, REPO_ROOT

_PENDING_DIR = ARTIFACTS_ROOT / "pending"


def store_pending_payload(job_id: str, payload: Dict[str, Any]) -> None:
    _PENDING_DIR.mkdir(parents=True, exist_ok=True)
    (_PENDING_DIR / f"{job_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def load_pending_payload(job_id: str) -> Dict[str, Any] | None:
    path = _PENDING_DIR / f"{job_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    finally:
        path.unlink(missing_ok=True)


def process_job_result(job_id: str, result: Dict[str, Any]) -> None:
    payload = load_pending_payload(job_id) or {}
    slug = result.get("slug") or job_id
    artifact_dir = MARKDOWN_ROOT / slug
    artifact_dir.mkdir(parents=True, exist_ok=True)

    summary = result.get("summary") or {}
    summary_path = artifact_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    sections = result.get("sections") or summary.get("sections", [])
    markdown_content = markdown.render_markdown(
        title=summary.get("title", slug),
        overview=summary.get("overview", ""),
        sections=sections,
        glossary=summary.get("glossary"),
        follow_up_questions=summary.get("follow_up_questions"),
        transcript_path=None,
    )
    markdown_path = artifact_dir / "index.md"
    markdown.write_markdown(markdown_path, markdown_content)

    github_ops.configure_user()
    github_ops.add_files([summary_path, markdown_path])
    title = summary.get("title", slug)
    github_ops.commit(f"Add summary for {title}")
    github_ops.push()


__all__ = ["store_pending_payload", "process_job_result"]

