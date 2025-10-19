import random
import time
import logging

from .client import GQL_API
from .template import FoundTemplate
from .storage import FoundStorage
from .machine import Machine

logger = logging.getLogger(__name__)


class Pod:
    def __init__(self, 
    template: FoundTemplate, 
    storage: FoundStorage,
    machine: Machine,
    ):

        self.template = template
        self.storage = storage
        self.machine = machine

    def create(self):
        try:
            input_data = {
                "name": self.template.name + '.' + str(random.randint(1000, 9999)),
                "gpuCount": self.template.gpu_count,
                "templateId": self.template.id,
                "networkVolumeId": self.storage.id,
                "gpuTypeId": self.machine.gpu_type_id,
                "dataCenterId": self.machine.data_center_id,
                "containerRegistryAuthId": self.template.container_registry_auth.id if self.template.container_registry_auth else None,
                "containerDiskInGb": self.template.container_disk_in_gb,
                "volumeInGb": self.storage.size_gb,
                }
            
            if self.machine.secure_cloud:
                input_data['bidPerGpu'] = self.machine.secure_spot_price
            else:
                input_data['bidPerGpu'] = self.machine.community_spot_price
            
            input_data = {key: value for key, value in input_data.items() if value}

            logger.debug(f"Input Data: {input_data}")


            resp = GQL_API.post(
                json={
                    "operationName": "RENT_POD",
                    "query": """
                    mutation RENT_POD($input: PodRentInterruptableInput!) { 
                        podRentInterruptable(input: $input) {
                            id
                            ipAddress {
                                address
                            }
                            ports
                            env
                            machineId
                            machine { 
                                podHostId 
                                __typename 
                            }
                        }
                    }""",
                    "variables": 
                    {
                        "input": input_data
                    }
                }
            )
            resp = resp.json()
            if 'errors' in resp:
                logger.error(f"Pod creation failed with errors: {resp['errors']}")
                raise Exception(resp['errors'])
            else:
                logger.debug("Pod created successfully: %s", resp)
                return resp
        except Exception as e:
            logger.error(f"{e}")
            raise Exception(f"Error: {e}")

    def get_ip_address(self, id: str):
        query = """
        query podRuntime($input: PodFilter) {
            pod(input: $input) {
                ipAddress { address }
                runtime {
                    ports {
                        ip
                        isIpPublic
                        type
                        privatePort
                        publicPort
                    }
                }
            }
        }
        """
        variables = {"input": {"podId": id}}

        total_wait_time = 15 * 60 # 15 minutes
        wait_time = 0
        while wait_time < total_wait_time:
            try:
                resp = GQL_API.post(
                    json={
                        "operationName": "podRuntime",
                        "query": query,
                        "variables": variables,
                    }
                )
                payload = resp.json()
                runtime = payload['data']['pod']['runtime']
                if runtime:
                    print(runtime)
                    ports = runtime['ports']
                    for port in ports:
                        if port['type'] == 'http':
                            return f"{port['ip']}:{port['publicPort']}"
                else:
                    logger.debug("Sleeping for 10 seconds...")
                    time.sleep(10)
                    wait_time += 10
                    logger.debug(f"Waited for {wait_time // 60}:{wait_time % 60}...")

                if wait_time > total_wait_time:
                    raise Exception("Pod ports not available after 15 minutes")
            except Exception as e:
                logger.debug(f"{e}")
                continue
        
        return None


# operationName : "RENT_POD"
# query: "mutation RENT_POD($input: PodRentNonInterruptableInput!) {\n  podRentNonInterruptable(input: $input) {\n    id\n    imageName\n    env\n    machineId\n    machine {\n      podHostId\n      __typename\n    }\n    __typename\n  }\n}"
# variables: 
# {
    # input: 
        # {
            # templateId: "runpod-torch-v21",
            # machineId: "7jlgeyzup7ud",
            # name: "self-rented-machine7jlgeyzup7ud",
            # containerDiskInGb: 5,
            # costPerHr: 1000,
            # gpuCount: 1,
            # startJupyter: true,
            # startSsh: true,
            # volumeInGb: 0,
            # volumeKey: null
        # }
# }