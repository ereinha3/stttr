"""Job orchestration server for Whispr."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from server.jobs import JOB_REGISTRY, JobStatus
from server.pod_launcher import launch_worker
from server.settings import TEMP_ROOT
from server.storage import store_pending_payload, process_job_result


app = FastAPI(title="Whispr Server", version="0.3.0")


class JobSubmission(BaseModel):
    title: str
    understanding_level: int = Field(3, ge=1, le=5)
    context: dict | None = None
    audio_url: str | None = None

    @staticmethod
    def validate(audio: UploadFile | None, audio_url: str | None) -> None:
        if audio is None and not audio_url:
            raise HTTPException(status_code=400, detail="Audio upload or audio_url required")


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: Dict[str, Any] | None = None
    error: str | None = None
    runpod_pod_id: str | None = None


class JobCallback(BaseModel):
    status: JobStatus
    result: Dict[str, Any] | None = None
    error: str | None = None
    pod_id: str | None = None


@app.post("/jobs", response_model=JobStatusResponse)
async def submit_job(
    background_tasks: BackgroundTasks,
    title: str = Field(...),
    understanding_level: int = Field(3, ge=1, le=5),
    audio: UploadFile | None = File(None),
    audio_url: str | None = None,
    context: str | None = None,
):
    JobSubmission.validate(audio, audio_url)

    payload: Dict[str, Any] = {
        "title": title,
        "understanding_level": understanding_level,
        "context": json.loads(context) if context else {},
    }

    if audio is not None:
        suffix = Path(audio.filename or "audio").suffix or ".mp3"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=TEMP_ROOT) as tmp:
            tmp.write(await audio.read())
            payload["audio_path"] = tmp.name
            payload["audio_filename"] = audio.filename or "upload"
        background_tasks.add_task(Path(payload["audio_path"]).unlink, missing_ok=True)  # type: ignore[arg-type]
    else:
        payload["audio_url"] = audio_url

    job = JOB_REGISTRY.create_job(payload)
    store_pending_payload(job.job_id, payload)

    launch_worker(job.job_id, payload)

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        result=job.result,
        error=job.error,
        runpod_pod_id=job.runpod_pod_id,
    )


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str):
    try:
        job = JOB_REGISTRY.get(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        result=job.result,
        error=job.error,
        runpod_pod_id=job.runpod_pod_id,
    )


@app.post("/jobs/{job_id}/callback", response_model=JobStatusResponse)
async def job_callback(job_id: str, update: JobCallback):
    try:
        job = JOB_REGISTRY.update_status(
            job_id,
            update.status,
            result=update.result,
            error=update.error,
            pod_id=update.pod_id,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

    if update.status is JobStatus.COMPLETED and update.result:
        process_job_result(job_id, update.result)

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        result=job.result,
        error=job.error,
        runpod_pod_id=job.runpod_pod_id,
    )

