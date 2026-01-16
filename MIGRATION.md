# Migration Guide - Moving Whispr to New Machine

## Quick Setup on New Machine

### 1. Prerequisites

```bash
# Install Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Install NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify GPU access
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

### 2. Clone Repository

```bash
git clone <your-repo-url> whispr
cd whispr
```

### 3. Build Container

```bash
cd worker
docker build -t whispr-worker:4090 .
```

**Note**: First build takes ~10-15 minutes (downloads base images, installs dependencies)

### 4. Run Container

```bash
# Create directories
mkdir -p artifacts test-samples

# Run container
docker run -d --gpus all \
  --name whispr \
  -p 9000:9000 \
  -v $(pwd)/artifacts:/app/artifacts \
  -v $(pwd)/../test-samples:/app/test-samples:ro \
  -v whispr-models:/app/models \
  whispr-worker:4090
```

**First startup**: Takes ~2-3 minutes to download Qwen2.5-7B-AWQ model (~5GB)

### 5. Verify

```bash
# Wait for services (check logs)
docker logs -f whispr

# When you see "Ready! Services:", test:
curl http://localhost:9000/health
```

## Data Migration

### Model Cache (Optional - Speeds Up Startup)

If you have the model cache from the old machine:

```bash
# On old machine: Export model cache
docker run --rm -v whispr-models:/models alpine tar czf - /models > models-backup.tar.gz

# On new machine: Import model cache
docker volume create whispr-models
docker run --rm -v whispr-models:/models -v $(pwd):/backup alpine tar xzf /backup/models-backup.tar.gz -C /
```

### Test Samples

Copy your test audio files to `test-samples/`:

```bash
cp /path/to/audio/*.m4a test-samples/
```

## Quick Test

```bash
# Test transcription
docker run --rm --gpus all \
  -v $(pwd)/test-samples:/app/test-samples:ro \
  -v whispr-models:/app/models \
  whispr-worker:4090 \
  python3 -m worker.test_transcribe \
    /app/test-samples/Telemetry.m4a \
    --output-dir /app/artifacts/test

# Test full pipeline
curl -X POST http://localhost:9000/process \
  -F "audio=@test-samples/Telemetry.m4a" \
  -F "title=Test" \
  -F "understanding_level=2"
```

## Troubleshooting

### GPU Not Detected

```bash
# Check NVIDIA drivers
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

### Container Won't Start

```bash
# Check logs
docker logs whispr

# Common issues:
# - Model download failed: Check internet connection
# - Out of memory: Reduce VLLM_GPU_MEMORY_UTILIZATION in Dockerfile
# - Port conflict: Change -p 9000:9000 to different port
```

### Model Download Slow

The model is cached in Docker volume `whispr-models`. First download is slow (~5GB), subsequent starts are fast.

## Environment Variables

You can override defaults when running:

```bash
docker run -d --gpus all \
  -e VLLM_GPU_MEMORY_UTILIZATION=0.40 \
  -e LLM_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ \
  -p 9000:9000 \
  whispr-worker:4090
```

## Next Steps

1. Test with your audio files
2. Test image processing with conference photos
3. Review generated markdown output
4. Adjust understanding_level as needed

See `README.md` and `TODO.md` for full documentation.

