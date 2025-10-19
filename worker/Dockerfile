FROM nvidia/cuda:12.2.2-cudnn9-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VLLM_BASE_URL=http://127.0.0.1:8000 \
    VLLM_MODEL=Intel/gpt-oss-20b-int4-AutoRound \
    HOST=0.0.0.0 \
    PORT=9000

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv git ffmpeg curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN python3 -m pip install --upgrade pip setuptools && \
    python3 -m pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN chmod +x docker/entrypoint.sh

EXPOSE 8000 9000

ENTRYPOINT ["/app/docker/entrypoint.sh"]

