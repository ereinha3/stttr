"""Template definition for the Whisper worker pod."""

from server.runpod.classes import Template, Storage

template = Template(
    image_name="ghcr.io/your-org/whispr-worker:latest",
    container_disk_in_gb=40,
    volume_mount_path="/workspace",
    http_ports=[],
    tcp_ports=[],
    readme="Whispr worker image handling transcription and enrichment calls.",
    env={},
)

storage = Storage(size_gb=40)

__all__ = ["template", "storage"]

