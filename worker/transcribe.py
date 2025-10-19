"""Reusable transcription helpers for the RunPod worker."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from faster_whisper import WhisperModel

from worker.settings import MODEL_CACHE_ROOT


_MODEL_CACHE: Dict[Tuple[str, str], WhisperModel] = {}


def _auto_select_device(device_override: Optional[str] = None) -> str:
    if device_override:
        return device_override

    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _resolve_compute_type(device: str, compute_type_override: Optional[str] = None) -> str:
    if compute_type_override:
        return compute_type_override
    return "float16" if device == "cuda" else "int8"


def ensure_model(
    *,
    device: Optional[str] = None,
    compute_type: Optional[str] = None,
) -> WhisperModel:
    resolved_device = _auto_select_device(device)
    resolved_compute_type = _resolve_compute_type(resolved_device, compute_type)
    cache_key = (resolved_device, resolved_compute_type)

    model = _MODEL_CACHE.get(cache_key)
    if model is None:
        model = WhisperModel(
            "large-v3",
            device=resolved_device,
            compute_type=resolved_compute_type,
            download_root=str(MODEL_CACHE_ROOT),
        )
        _MODEL_CACHE[cache_key] = model

    return model


def _write_plaintext(segments: Iterable[dict], out_path: Path) -> None:
    with open(out_path, "w", encoding="utf-8") as handle:
        for segment in segments:
            handle.write(segment["text"].strip() + " ")


def transcribe_file(
    input_path: str | Path,
    *,
    output_dir: str | Path = "transcripts",
    beam_size: int = 5,
    vad_filter: bool = False,
    language: Optional[str] = None,
    word_timestamps: bool = False,
    device: Optional[str] = None,
    compute_type: Optional[str] = None,
) -> dict:
    resolved_input = Path(input_path).expanduser().resolve()
    if not resolved_input.exists():
        raise FileNotFoundError(f"Input not found: {resolved_input}")

    transcripts_dir = Path(output_dir)
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    model = ensure_model(device=device, compute_type=compute_type)

    start_time = time.time()
    raw_segments, info = model.transcribe(
        str(resolved_input),
        beam_size=beam_size,
        vad_filter=vad_filter,
        language=language,
        word_timestamps=word_timestamps,
    )

    collected: List[dict] = []
    for item in raw_segments:
        segment_payload: dict = {
            "start": item.start,
            "end": item.end,
            "text": item.text,
        }
        if word_timestamps and getattr(item, "words", None):
            segment_payload["words"] = [
                {"start": word.start, "end": word.end, "text": word.word}
                for word in item.words
            ]
        collected.append(segment_payload)

    txt_path = transcripts_dir / f"{resolved_input.stem}.txt"
    _write_plaintext(collected, txt_path)

    duration = time.time() - start_time

    return {
        "segments": collected,
        "language": info.language,
        "language_probability": info.language_probability,
        "transcript_path": str(txt_path),
        "duration": duration,
        "device": model.device,
        "compute_type": model.compute_type,
    }


__all__ = ["ensure_model", "transcribe_file"]

