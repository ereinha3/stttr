# Whispr RunPod Worker

This directory defines the GPU worker image responsible for the full content
pipeline: transcription, summarisation via vLLM (`gpt-oss-20b`), image
selection, markdown generation, and orchestrator callbacks.

## Build

```
docker build -t whispr-runpod-worker .
```

## Local Test

```
docker compose up
```

Ensure the orchestrator is available at `WHISPR_ORCHESTRATOR_URL` and the vLLM
service is reachable at `VLLM_BASE_URL`.

