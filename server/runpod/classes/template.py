from typing import List, Optional
import logging
from .auth import Auth
from .client import GQL_API, V1_API

logger = logging.getLogger(__name__)

class Template:
    def __init__(self, 
        image_name: str, 
        container_disk_in_gb: int, 
        readme: Optional[str] = None, 
        http_ports: Optional[List[int]] = None, 
        tcp_ports: Optional[List[int]] = None, 
        docker_args: Optional[list] = None, 
        env: Optional[dict] = None,
        volume_mount_path: Optional[str] = "/workspace",
        container_registry_auth: Optional[Auth] = None,
    ):
        self.image_name = image_name
        self.container_disk_in_gb = container_disk_in_gb
        self.container_registry_auth = container_registry_auth
        self.volume_mount_path = volume_mount_path
        self.http_ports = http_ports
        self.tcp_ports = tcp_ports
        self.docker_args = docker_args
        self.env = env
        self.readme = readme

    def list_templates(self):
        try:
            resp = V1_API.get(
                route="templates",
            )
            return resp.json()
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return 404

class FoundTemplate(Template):
    def __init__(self, datadict: dict, **kwargs):
        super().__init__(**kwargs)
        self.arch = datadict['arch']
        self.author = datadict['author']
        self.model = datadict['model']
        self.gpu_count = int(datadict['gpu_count'])
        self.precision = datadict['precision']
        self.service = datadict['service']
        self._set_name()
        self._set_id()

    def _set_name(self):
        self.name = f"{self.service}.{self.author}.{self.model}.{self.arch.replace(' ', '-')}x{self.gpu_count}.{self.precision}"

    def _set_id(self):
        available_templates = self.list_templates()
        found = False
        for template in available_templates:
            if template['name'] == self.name:
                self.id = template['id']
                found = True
        if not found:
            self.id = self.create()['id']

    def create(self):
        try:
            input_data = {
                "name": self.name,
                "imageName": self.image_name,
                "containerDiskInGb": self.container_disk_in_gb,
                "volumeInGb": 0,
                "volumeMountPath": self.volume_mount_path,
                "containerRegistryAuthId": self.container_registry_auth.id if self.container_registry_auth else None,
                "ports": " ".join([f"{port}/http" for port in self.http_ports] + [f"{port}/tcp" for port in self.tcp_ports]) if self.http_ports or self.tcp_ports else None,
                "readme": self.readme if self.readme else f"{self.image_name} template",
                "dockerArgs": " ".join(self.docker_args or []),
                "env": [{"key": k, "value": v} for k, v in (self.env or {}).items()],
            }
            input_data = {key: value for key, value in input_data.items() if value is not None}
            resp = GQL_API.post(
                json={
                "query": f"""mutation Save($input: SaveTemplateInput!) 
                {{ 
                    saveTemplate(input: $input) {{ 
                        id 
                        {' '.join([
                            key if key != 'env' else 'env { key value }' for key in input_data.keys()
                            ])
                        }
                    }}
                }}""",
                    "variables": 
                        {
                            "input": input_data
                        }
                    }
                )
            return resp.json()['data']['saveTemplate']
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return 404

    def delete(self):
        try:
            resp = V1_API.delete(
                route="templates",
                id=self.get_id(),

            )
            return resp.json()
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return 404

    def __str__(self):
        return f"FoundTemplate(id={self.id}, name={self.name}, arch={self.arch}, author={self.author}, model={self.model}, gpu_count={self.gpu_count}, precision={self.precision}, service={self.service})"