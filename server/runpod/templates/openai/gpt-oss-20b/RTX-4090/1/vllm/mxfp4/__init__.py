"""Template definition for serving gpt-oss-20b via vLLM."""

from server.runpod.classes import Template, Storage

docker_args = [
    "--model Intel/gpt-oss-20b-int4-AutoRound",
    "--port 8000",
    "--gpu-memory-utilization 0.92",
    "--max-model-len 16384",
    "--max-num-batched-tokens 16384",
    "--calculate-kv-scales",
    "--enable-prefix-caching",
    "--quantization bitsandbytes",
    "--load-format bitsandbytes",
    "--speculative-config '{\"method\":\"ngram\",\"num_speculative_tokens\":3,\"prompt_lookup_max\":6}'",
]

template = Template(
    image_name="vllm/vllm-openai:v0.8.5",
    container_disk_in_gb=100,
    volume_mount_path="/workspace",
    http_ports=[8000],
    tcp_ports=[],
    readme="GPT-OSS-20B on 4090 with INT4/BB quantization.",
    docker_args=docker_args,
    env={
        "HF_HOME": "/workspace",
        "VLLM_CONFIG_ROOT": "/workspace",
        "VLLM_CACHE_ROOT": "/workspace",
    },
)

storage = Storage(size_gb=80, custom_precision=True)

__all__ = ["template", "storage"]