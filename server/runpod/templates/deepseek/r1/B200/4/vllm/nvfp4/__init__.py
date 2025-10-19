from classes import Template, Storage

docker_args = [
    "--model nvidia/DeepSeek-R1-FP4",
    "--port 8000",
    "--trust-remote-code",
    "--tensor-parallel-size 4",
    "--enable-expert-parallel",
    "--max-model-len 128k",
    "--max-num-batched-tokens 32k",
    "--calculate-kv-scales",
    "--enable-prefix-caching",
    "--api-server-count 4",
    "--speculative-config '{\"method\":\"deepseek_mtp\",\"num_speculative_tokens\":3}'",
    "--reasoning-parser deepseek_r1",
    "--enable-eplb",
    "--distributed-executor-backend mp",
    "--max-parallel-loading-workers 12",
    "--gpu-memory-utilization 0.92",
    "--eplb-config '{\"window_size\":2000,\"step_interval\":3000,\"log_balancedness\":true}'"
]


template = Template(
    image_name="vllm/vllm-openai:latest",
    container_disk_in_gb=200,
    volume_mount_path="/workspace",
    http_ports=[8000],
    tcp_ports=[],
    docker_args=docker_args,
    env={
        "VLLM_ATTENTION_BACKEND": "CUTLASS_MLA",
        "VLLM_USE_FLASHINFER_MOE_FP4": "1",
        "HF_HUB_ENABLE_HF_TRANSFER": "0",
        "HF_HOME": "/workspace",
    }
)

storage = Storage(size_gb=600, custom_precision=True)


__all__ = ["template", "storage"]

if __name__ == "__main__":
    print(template.name)