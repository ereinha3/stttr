from classes import Template, Storage

docker_args = [
    "--model openai/gpt-oss-120b",
    "--port 8000",
    "--api-server-count 4",
    "--max-model-len 131072",
    "--max-num-batched-tokens 131072",
    "--calculate-kv-scales",
    "--enable-prefix-caching",
    "--speculative-config '{\"method\":\"ngram\",\"num_speculative_tokens\":4,\"prompt_lookup_max\":8}'"
]

template = Template(
    image_name="vllm/vllm-openai:gptoss",
    container_disk_in_gb=200,
    volume_mount_path="/workspace",
    http_ports=[8000],
    tcp_ports=[],
    docker_args=docker_args,
    readme="Template for serving OpenAI GPT-OSS-120B model with MXFP4 weights and MXFP8 activations.",
    env={
        "HF_HOME": "/workspace",
        "VLLM_USE_TRTLLM_ATTENTION": "1",
        "VLLM_USE_TRTLLM_DECODE_ATTENTION": "1",
        "VLLM_USE_TRTLLM_CONTEXT_ATTENTION": "1",
        # Getting rid of this puts activations in mxfp8
        # Both have mxfp4 weights by default
        # "VLLM_USE_FLASHINFER_MXFP4_BF16_MOE": "1",
        "VLLM_USE_FLASHINFER_MXFP4_MOE": "1",
    }
)

storage = Storage(size_gb=150)

__all__ = ["template", "storage"]