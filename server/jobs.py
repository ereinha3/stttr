"""Job registry for the orchestration server."""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobRecord:
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    payload: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    runpod_pod_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mark(
        self,
        status: JobStatus,
        *,
        result: Dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        self.status = status
        self.updated_at = time.time()
        if result is not None:
            self.result = result
        if error is not None:
            self.error = error


class JobRegistry:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}

    def create_job(self, payload: Dict[str, Any]) -> JobRecord:
        job_id = uuid.uuid4().hex
        record = JobRecord(job_id=job_id, payload=payload)
        self._jobs[job_id] = record
        return record

    def get(self, job_id: str) -> JobRecord:
        if job_id not in self._jobs:
            raise KeyError(job_id)
        return self._jobs[job_id]

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
        *,
        result: Dict[str, Any] | None = None,
        error: str | None = None,
        pod_id: str | None = None,
    ) -> JobRecord:
        job = self.get(job_id)
        job.mark(status, result=result, error=error)
        if pod_id is not None:
            job.runpod_pod_id = pod_id
        return job


JOB_REGISTRY = JobRegistry()


__all__ = ["JobRegistry", "JobRecord", "JobStatus", "JOB_REGISTRY"]

