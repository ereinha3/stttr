#!/usr/bin/env bash
set -euo pipefail

# Whispr Self-Contained AI Container Entrypoint
# Starts vLLM server, waits for it, then starts the worker

echo "=============================================="
echo "  Whispr AI Container - RTX 4090 Edition"
echo "=============================================="
echo ""

# Configuration
VLLM_MODEL_NAME=${VLLM_MODEL:-Qwen/Qwen2.5-7B-Instruct-AWQ}
VLLM_PORT=${VLLM_PORT:-8000}
VLLM_GPU_UTIL=${VLLM_GPU_MEMORY_UTILIZATION:-0.50}
VLLM_MAX_LEN=${VLLM_MAX_MODEL_LEN:-8192}
VLLM_QUANT=${VLLM_QUANTIZATION:-awq}
WORKER_PORT=${PORT:-9000}
LOG_DIR=${LOG_DIR:-/app/logs}

mkdir -p "$LOG_DIR"

echo "[1/3] Starting vLLM server..."
echo "      Model: $VLLM_MODEL_NAME"
echo "      Quantization: $VLLM_QUANT"
echo "      GPU Memory: ${VLLM_GPU_UTIL}"
echo "      Port: $VLLM_PORT"
echo ""

# Build vLLM command with optional quantization
VLLM_CMD="python3 -m vllm.entrypoints.openai.api_server \
    --model $VLLM_MODEL_NAME \
    --port $VLLM_PORT \
    --host 0.0.0.0 \
    --gpu-memory-utilization $VLLM_GPU_UTIL \
    --max-model-len $VLLM_MAX_LEN \
    --trust-remote-code \
    --disable-log-requests"

# Add quantization if specified
if [ -n "$VLLM_QUANT" ] && [ "$VLLM_QUANT" != "none" ]; then
    VLLM_CMD="$VLLM_CMD --quantization $VLLM_QUANT"
fi

# Start vLLM in background
eval "$VLLM_CMD" >"$LOG_DIR/vllm.log" 2>&1 &
VLLM_PID=$!

echo "[2/3] Waiting for vLLM to load model..."

# Wait for vLLM to be ready (can take a few minutes for first download)
MAX_WAIT=600  # 10 minutes max for model download
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl --silent --max-time 2 "http://127.0.0.1:${VLLM_PORT}/health" >/dev/null 2>&1; then
        echo "      ✓ vLLM ready after ${WAITED}s"
        break
    fi
    
    # Check if vLLM process died
    if ! kill -0 $VLLM_PID 2>/dev/null; then
        echo "      ✗ vLLM process died unexpectedly"
        echo ""
        echo "=== vLLM Logs ==="
        cat "$LOG_DIR/vllm.log" || true
        exit 1
    fi
    
    # Progress indicator every 30s
    if [ $((WAITED % 30)) -eq 0 ] && [ $WAITED -gt 0 ]; then
        echo "      ... still loading (${WAITED}s elapsed)"
    fi
    
    sleep 5
    WAITED=$((WAITED + 5))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "      ✗ Timed out waiting for vLLM"
    cat "$LOG_DIR/vllm.log" || true
    exit 1
fi

echo ""
echo "[3/3] Starting Whispr worker on port $WORKER_PORT..."
echo ""
echo "=============================================="
echo "  Ready! Services:"
echo "    - vLLM API:    http://0.0.0.0:$VLLM_PORT"
echo "    - Worker API:  http://0.0.0.0:$WORKER_PORT"
echo "=============================================="
echo ""

# Start worker (foreground)
exec python3 -m uvicorn worker.worker:app \
    --host 0.0.0.0 \
    --port "$WORKER_PORT" \
    --log-level info
