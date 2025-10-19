"""Abstraction for launching worker pods."""

from __future__ import annotations

from typing import Any, Dict

from server.runpod.manager import RunPodManager

_MANAGER = RunPodManager()


def launch_worker(job_id: str, payload: Dict[str, Any]) -> None:
    """Schedule a RunPod worker for the given job."""

    _MANAGER.launch(job_id, payload)


__all__ = ["launch_worker"]

