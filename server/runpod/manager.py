"""High-level RunPod orchestration used by the server."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from server.runpod.finders.schemas import SchemaFinder
from server.runpod.finders.machines import MachineFinder
from server.runpod.classes.pod import Pod

logger = logging.getLogger(__name__)


class RunPodManager:
    def __init__(self) -> None:
        schemas = SchemaFinder(schema_dir="server.runpod.templates").schemas
        if not schemas:
            raise RuntimeError("RunPod templates not found")
        self.template = schemas[0]
        machines = MachineFinder().find_available_machines()
        if not machines:
            raise RuntimeError("No available machines")
        self.machine = machines[0]

    def launch(self, job_id: str, payload: Dict[str, Any]) -> None:
        logger.info("Launching RunPod worker for job %s", job_id)
        pod = Pod(
            template=self.template["template"],
            storage=self.template["storage"],
            machine=self.machine,
        )
        resp = pod.create()
        logger.info("Pod creation response: %s", json.dumps(resp))

