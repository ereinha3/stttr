"""Utility helpers for the worker."""

from __future__ import annotations

import re
from pathlib import Path


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def slugify(value: str, fallback: str = "untitled") -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or fallback


__all__ = ["ensure_directory", "slugify"]

