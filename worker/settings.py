"""Settings specific to the worker environment."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_ROOT = Path(os.getenv("WHISPR_ARTIFACTS_ROOT", BASE_DIR / "artifacts"))
MODEL_CACHE_ROOT = Path(os.getenv("WHISPR_MODEL_CACHE_ROOT", ARTIFACTS_ROOT / "models"))
MARKDOWN_DIR = ARTIFACTS_ROOT / "notes"
OPENSERP_BASE_URL = os.getenv("OPEN_SERP_BASE_URL", "http://localhost:7000")

# LLM Configuration - defaults to local vLLM instance
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "vllm")  # vllm, openai, groq, together
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8000")
LLM_API_KEY = os.getenv("LLM_API_KEY", "not-needed")
LLM_MODEL = os.getenv("LLM_MODEL", os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct-AWQ"))

# Legacy vLLM settings (for backward compatibility)
VLLM_MODEL = os.getenv("VLLM_MODEL", LLM_MODEL)
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", LLM_BASE_URL)

# Skip LLM summarization for testing
SKIP_LLM = os.getenv("SKIP_LLM", "false").lower() in ("true", "1", "yes")

__all__ = [
    "BASE_DIR",
    "ARTIFACTS_ROOT",
    "MARKDOWN_DIR",
    "OPENSERP_BASE_URL",
    "LLM_PROVIDER",
    "LLM_BASE_URL",
    "LLM_API_KEY",
    "LLM_MODEL",
    "VLLM_MODEL",
    "VLLM_BASE_URL",
    "SKIP_LLM",
]

