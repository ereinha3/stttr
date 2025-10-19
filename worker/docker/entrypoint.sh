#!/usr/bin/env bash
set -euo pipefail

# Configure cache directories (use mounted volume if provided)
export HF_HOME=${HF_HOME:-/workspace}
export TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE:-/workspace}
export TORCH_HOME=${TORCH_HOME:-/workspace}
export VLLM_CACHE_ROOT=${VLLM_CACHE_ROOT:-/workspace}
export VLLM_CONFIG_ROOT=${VLLM_CONFIG_ROOT:-/workspace}

VLLM_MODEL_NAME=${VLLM_MODEL:-Intel/gpt-oss-20b-int4-AutoRound}
VLLM_PORT=${VLLM_PORT:-8000}
VLLM_GPU_UTIL=${VLLM_GPU_UTIL:-0.92}
VLLM_MAX_LEN=${VLLM_MAX_LEN:-16384}
VLLM_MAX_BATCH_TOKENS=${VLLM_MAX_BATCH_TOKENS:-16384}

LOG_DIR=${LOG_DIR:-/tmp}
mkdir -p "$LOG_DIR"

python3 -m vllm.entrypoints.openai.api_server \
  --model "$VLLM_MODEL_NAME" \
  --port "$VLLM_PORT" \
  --gpu-memory-utilization "$VLLM_GPU_UTIL" \
  --max-model-len "$VLLM_MAX_LEN" \
  --max-num-batched-tokens "$VLLM_MAX_BATCH_TOKENS" \
  --quantization bitsandbytes \
  --load-format bitsandbytes \
  --speculative-config '{"method":"ngram","num_speculative_tokens":3,"prompt_lookup_max":6}' \
  >"$LOG_DIR"/vllm.log 2>&1 &
VLLM_PID=$!

echo "Waiting for vLLM to become ready..."
for i in {1..60}; do
  if curl --silent --max-time 1 "http://127.0.0.1:${VLLM_PORT}/health" > /dev/null; then
    echo "vLLM ready"
    break
  fi
  sleep 2
  if ! kill -0 $VLLM_PID 2>/dev/null; then
    echo "vLLM process exited" >&2
    cat "$LOG_DIR"/vllm.log || true
    exit 1
  fi
  if [[ $i -eq 60 ]]; then
    echo "Timed out waiting for vLLM" >&2
    cat "$LOG_DIR"/vllm.log || true
    exit 1
  fi

done

uvicorn worker.worker:app \
  --host "${HOST:-0.0.0.0}" \
  --port "${PORT:-9000}" \
  --log-level info
