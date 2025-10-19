"""RunPod worker FastAPI service for transcription and enrichment."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from worker.image_search import suggest_images_for_sections
from worker.llm import VLLMClient
from worker.settings import ARTIFACTS_ROOT, OPENSERP_BASE_URL, VLLM_BASE_URL, VLLM_MODEL
from worker.summary import summarise_with_vllm
from worker.transcribe import transcribe_file
from worker.utils import ensure_directory, slugify

app = FastAPI(title="Whispr Worker", version="0.1.0")


async def _write_temp_audio(audio: UploadFile) -> Path:
    suffix = Path(audio.filename or "audio").suffix or ".wav"
    temp_dir = ensure_directory(Path("/tmp") / f"whispr-{uuid.uuid4().hex}")
    temp_path = temp_dir / f"input{suffix}"
    data = await audio.read()
    temp_path.write_bytes(data)
    return temp_path


async def _download_audio(url: str) -> Path:
    temp_dir = ensure_directory(Path("/tmp") / f"whispr-{uuid.uuid4().hex}")
    temp_path = temp_dir / "input"
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        temp_path.write_bytes(resp.content)
    return temp_path


def _load_metadata(
    metadata: Optional[str],
    title: Optional[str],
    understanding_level: int,
    context: Optional[str],
) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    if metadata:
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Invalid metadata JSON") from exc

    if title:
        meta.setdefault("title", title)
    meta.setdefault("understanding_level", understanding_level)
    if context and "context" not in meta:
        try:
            meta["context"] = json.loads(context)
        except json.JSONDecodeError:
            meta["context"] = {"notes": context}

    return meta


def _build_markdown(title: str, summary_data: Dict[str, Any], sections: list[Dict[str, Any]], transcript_link: Optional[str]) -> str:
    lines = [f"# {title}", ""]
    overview = (summary_data.get("overview") or "").strip()
    if overview:
        lines.append("## Overview")
        lines.append(overview)
        lines.append("")

    for section in sections:
        lines.append(f"## {section.get('title', 'Section')}")
        image = section.get("image")
        if image and image.get("url"):
            lines.append(f"![{image.get('title', 'Image')}]({image['url']})")
            lines.append("")
        summary = (section.get("summary") or "").strip()
        if summary:
            lines.append(summary)
            lines.append("")
        key_points = section.get("key_points") or []
        if key_points:
            lines.append("### Key Points")
            lines.extend(f"- {point}" for point in key_points)
            lines.append("")

    glossary = summary_data.get("glossary") or []
    if glossary:
        lines.append("## Glossary")
        for entry in glossary:
            lines.append(f"- **{entry['term']}**: {entry['definition']}")
        lines.append("")

    follow_up = summary_data.get("follow_up_questions") or []
    if follow_up:
        lines.append("## Follow-up Questions")
        lines.extend(f"- {question}" for question in follow_up)
        lines.append("")

    if transcript_link:
        lines.append("## Transcript")
        lines.append(f"[Download transcript]({transcript_link})")

    return "\n".join(lines).strip() + "\n"


async def process_audio(
    audio_path: Path,
    *,
    title: Optional[str],
    understanding_level: int,
    context: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    job_dir = ensure_directory(ARTIFACTS_ROOT / uuid.uuid4().hex)

    transcription = transcribe_file(
        audio_path,
        output_dir=job_dir / "transcripts",
    )

    transcript_text = " ".join(segment["text"] for segment in transcription["segments"])

    llm_client = VLLMClient(base_url=VLLM_BASE_URL, api_key=os.getenv("VLLM_API_KEY"))

    summary_json = await summarise_with_vllm(
        transcript_text,
        understanding_level=understanding_level,
        context=context,
        model=VLLM_MODEL,
        llm_client=llm_client,
    )
    summary_data = json.loads(summary_json)

    final_title = summary_data.get("title") or title or "Untitled Session"
    slug = slugify(final_title)

    sections = summary_data.get("sections", [])
    enriched_sections = await suggest_images_for_sections(
        sections,
        download=False,
        image_dir=str(job_dir / "images"),
        llm_client=llm_client,
        model=VLLM_MODEL,
        base_url=OPENSERP_BASE_URL,
    )
    summary_data["sections"] = enriched_sections

    transcript_path = transcription.get("transcript_path")
    markdown = _build_markdown(final_title, summary_data, enriched_sections, transcript_path)

    return {
        "slug": slug,
        "title": final_title,
        "summary": summary_data,
        "markdown": markdown,
        "sections": enriched_sections,
        "transcript": {
            "language": transcription.get("language"),
            "language_probability": transcription.get("language_probability"),
            "segments": transcription.get("segments"),
            "text": transcript_text,
        },
    }


@app.post("/process")
async def process_endpoint(
    audio: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    understanding_level: int = Form(3),
    context: Optional[str] = Form(None),
    audio_url: Optional[str] = Form(None),
):
    if understanding_level < 1 or understanding_level > 5:
        raise HTTPException(status_code=400, detail="understanding_level must be between 1 and 5")

    meta = _load_metadata(metadata, title, understanding_level, context)
    meta_title = meta.get("title")
    meta_understanding = int(meta.get("understanding_level", 3))
    meta_context = meta.get("context")

    if audio_url and audio.filename:
        raise HTTPException(status_code=400, detail="Provide either audio file or audio_url, not both")

    try:
        if audio.filename:
            audio_path = await _write_temp_audio(audio)
        elif audio_url:
            audio_path = await _download_audio(audio_url)
        else:
            raise HTTPException(status_code=400, detail="Audio input is required")

        result = await process_audio(
            audio_path,
            title=meta_title,
            understanding_level=meta_understanding,
            context=meta_context,
        )
        return JSONResponse(result)
    finally:
        try:
            if "audio_path" in locals():
                tmp_root = audio_path.parent
                if audio_path.exists():
                    audio_path.unlink()
                if tmp_root.exists():
                    asyncio.create_task(asyncio.to_thread(lambda: None))
        except Exception:
            pass


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "worker.worker:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "9000")),
        log_level="info",
    )

