from classes import Template, Storage

docker_args = [
    "--model QuixiAI/Qwen3-30B-A3B-AWQ",
    "--port 8000",
    "--quantization awq",
    "--api-server-count 4",
    "--max-model-len 20480",
    "--dtype bfloat16",
    "--gpu-memory-utilization 0.92",
    "--enable-chunked-prefill",
    "--long-prefill-token-threshold 4096",
    "--kv-cache-dtype fp8",
    "--max-num-batched-tokens 20480",
    "--calculate-kv-scales",
    "--enable-prefix-caching",
    "--speculative-config '{\"method\":\"ngram\",\"num_speculative_tokens\":3,\"prompt_lookup_max\":8}'"
]

template = Template(
    image_name="vllm/vllm-openai:gptoss",
    container_disk_in_gb=200,
    volume_mount_path="/workspace",
    http_ports=[8000],
    tcp_ports=[],
    readme="Template for serving OpenAI GPT-OSS-120B model with MXFP4 weights and MXFP8 activations.",
    docker_args=docker_args,
    env={
        "HF_HOME": "/workspace",
        "VLLM_USE_TRTLLM_ATTENTION": "1",
        "VLLM_USE_TRTLLM_DECODE_ATTENTION": "1",
        "VLLM_USE_TRTLLM_CONTEXT_ATTENTION": "1",
        "VLLM_USE_FLASHINFER_MXFP4_MOE": "1",
    }
)

storage = Storage(size_gb=150, custom_precision=True)

__all__ = ["template", "storage"]