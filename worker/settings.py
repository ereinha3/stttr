"""Settings specific to the worker environment."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_ROOT = Path(os.getenv("WHISPR_ARTIFACTS_ROOT", BASE_DIR / "artifacts"))
MODEL_CACHE_ROOT = Path(os.getenv("WHISPR_MODEL_CACHE_ROOT", ARTIFACTS_ROOT / "models"))
MARKDOWN_DIR = ARTIFACTS_ROOT / "notes"
OPENSERP_BASE_URL = os.getenv("OPEN_SERP_BASE_URL", "http://localhost:7000")
VLLM_MODEL = os.getenv("VLLM_MODEL", "gpt-oss-20b")
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://127.0.0.1:8000")

__all__ = [
    "BASE_DIR",
    "ARTIFACTS_ROOT",
    "MARKDOWN_DIR",
    "OPENSERP_BASE_URL",
    "VLLM_MODEL",
    "VLLM_BASE_URL",
]

