# Whispr Worker - Self-Contained AI Container

This directory contains the **self-contained AI worker** that runs everything locally:
- Whisper large-v3 transcription (GPU-accelerated)
- vLLM with Qwen2.5-7B-Instruct-AWQ for summarization
- Tesseract OCR for image text extraction
- LLM-based image analysis and placement
- FastAPI service for processing requests

## Quick Start

### Build

```bash
docker build -t whispr-worker:4090 .
```

### Run

```bash
docker run -d --gpus all \
  --name whispr \
  -p 9000:9000 \
  -v $(pwd)/artifacts:/app/artifacts \
  -v whispr-models:/app/models \
  whispr-worker:4090
```

**First startup**: Takes ~2-3 minutes to download the Qwen2.5-7B-AWQ model (~5GB)

### Test

```bash
# Health check
curl http://localhost:9000/health

# Process audio
curl -X POST http://localhost:9000/process \
  -F "audio=@test-samples/Telemetry.m4a" \
  -F "title=OCP Telemetry" \
  -F "understanding_level=2"

# Process audio + images
curl -X POST http://localhost:9000/process \
  -F "audio=@test-samples/Redfish.m4a" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  -F "title=OCP Redfish" \
  -F "understanding_level=1"
```

## Architecture

The container runs two services:
1. **vLLM API Server** (port 8000) - LLM inference
2. **FastAPI Worker** (port 9000) - Main processing endpoint

See `docker/entrypoint.sh` for startup sequence.

## Understanding Levels

- **0**: Complete novice - extensive explanations, all terms defined
- **1**: Beginner - most terms defined, background context
- **2**: Basic understanding - specialized terms defined
- **3**: Intermediate - only niche terms defined
- **4**: Advanced - technical details, minimal explanations
- **5**: Expert - concise reference, no basic explanations

## Components

- `worker.py` - FastAPI service and main processing logic
- `transcribe.py` - Whisper transcription wrapper
- `summary.py` - LLM summarization prompts and parsing
- `vision.py` - Image analysis (OCR + LLM)
- `image_placement.py` - Image-to-section matching
- `llm.py` - LLM client (vLLM/OpenAI-compatible)
- `test_transcribe.py` - Standalone transcription test

## Configuration

See root `README.md` for full documentation.

