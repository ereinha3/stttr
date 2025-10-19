"""Server configuration values."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(os.getenv("WHISPR_REPO_ROOT", BASE_DIR))
ARTIFACTS_ROOT = REPO_ROOT / "artifacts"
MARKDOWN_ROOT = REPO_ROOT / "notes"
TEMP_ROOT = Path(os.getenv("WHISPR_TEMP_DIR", "/tmp"))

__all__ = [
    "BASE_DIR",
    "REPO_ROOT",
    "ARTIFACTS_ROOT",
    "MARKDOWN_ROOT",
    "TEMP_ROOT",
]

