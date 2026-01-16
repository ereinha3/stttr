# Whispr Worker - Self-contained AI container
# Target: NVIDIA RTX 4090 (24GB VRAM)
# Components: Whisper large-v3 (~4GB) + Qwen2.5-7B-Instruct-AWQ (~5GB quantized)

FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=9000 \
    PYTHONPATH=/app/src \
    # vLLM settings - using AWQ quantized model for memory efficiency
    VLLM_PORT=8000 \
    VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ \
    VLLM_GPU_MEMORY_UTILIZATION=0.50 \
    VLLM_QUANTIZATION=awq \
    # Worker LLM settings (points to local vLLM)
    LLM_BASE_URL=http://127.0.0.1:8000 \
    LLM_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ \
    LLM_API_KEY=not-needed \
    # HuggingFace cache
    HF_HOME=/app/models \
    TRANSFORMERS_CACHE=/app/models \
    # Tesseract
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# System dependencies including Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv python3-dev \
    git ffmpeg curl build-essential \
    tesseract-ocr tesseract-ocr-eng libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./requirements.txt

# Install PyTorch with CUDA, vLLM, and other deps
RUN python3 -m pip install --upgrade pip setuptools wheel && \
    python3 -m pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu124 && \
    python3 -m pip install --no-cache-dir vllm>=0.6.0 && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application code into src/worker
COPY . /app/src/worker/

# Create directories
RUN mkdir -p /app/artifacts /app/models /app/logs

# Make entrypoint executable
RUN chmod +x /app/src/worker/docker/entrypoint.sh

EXPOSE 8000 9000

# Use custom entrypoint that starts vLLM + worker
ENTRYPOINT ["/app/src/worker/docker/entrypoint.sh"]
