#!/usr/bin/env python3
"""Standalone test script for transcription pipeline.

Usage:
    python -m worker.test_transcribe /path/to/audio.m4a
    python -m worker.test_transcribe /path/to/audio.m4a --understanding-level 2
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from worker.transcribe import transcribe_file
from worker.utils import ensure_directory, slugify


def main() -> int:
    parser = argparse.ArgumentParser(description="Test transcription pipeline")
    parser.add_argument("audio_path", type=Path, help="Path to audio file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./test-output"),
        help="Output directory for transcripts",
    )
    parser.add_argument(
        "--understanding-level",
        type=int,
        default=3,
        choices=[1, 2, 3, 4, 5],
        help="Understanding level (1=novice, 5=expert)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device to use (cuda/cpu). Auto-detected if not specified.",
    )
    parser.add_argument(
        "--word-timestamps",
        action="store_true",
        help="Include word-level timestamps",
    )
    args = parser.parse_args()

    audio_path = args.audio_path.expanduser().resolve()
    if not audio_path.exists():
        print(f"Error: Audio file not found: {audio_path}", file=sys.stderr)
        return 1

    output_dir = ensure_directory(args.output_dir.expanduser().resolve())
    slug = slugify(audio_path.stem)
    job_dir = ensure_directory(output_dir / slug)

    print(f"{'=' * 60}")
    print(f"Whispr Transcription Test")
    print(f"{'=' * 60}")
    print(f"Input:            {audio_path}")
    print(f"Output:           {job_dir}")
    print(f"Understanding:    {args.understanding_level}/5")
    print(f"Device:           {args.device or 'auto'}")
    print(f"{'=' * 60}")
    print()

    print("[1/2] Transcribing audio...")
    start_time = time.time()

    try:
        result = transcribe_file(
            audio_path,
            output_dir=job_dir / "transcripts",
            device=args.device,
            word_timestamps=args.word_timestamps,
        )
    except Exception as e:
        print(f"Error during transcription: {e}", file=sys.stderr)
        return 1

    transcribe_time = time.time() - start_time

    # Save full result as JSON
    result_path = job_dir / "transcription.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Extract transcript text
    transcript_text = " ".join(seg["text"] for seg in result["segments"])
    
    # Save plain text transcript
    txt_path = job_dir / "transcript.txt"
    txt_path.write_text(transcript_text, encoding="utf-8")

    print(f"[2/2] Transcription complete!")
    print()
    print(f"{'=' * 60}")
    print(f"Results")
    print(f"{'=' * 60}")
    print(f"Language:         {result.get('language')} ({result.get('language_probability', 0):.1%} confidence)")
    print(f"Segments:         {len(result['segments'])}")
    print(f"Device used:      {result.get('device')}")
    print(f"Compute type:     {result.get('compute_type')}")
    print(f"Duration:         {transcribe_time:.1f}s")
    print(f"{'=' * 60}")
    print()
    print(f"Output files:")
    print(f"  - {result_path}")
    print(f"  - {txt_path}")
    print(f"  - {result.get('transcript_path')}")
    print()
    print(f"Preview (first 500 chars):")
    print(f"{'─' * 60}")
    print(transcript_text[:500] + ("..." if len(transcript_text) > 500 else ""))
    print(f"{'─' * 60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

