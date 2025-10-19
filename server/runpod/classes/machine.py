import logging
import os

logger = logging.getLogger(__name__)


class Machine:
    def __init__(self, machine_dict: dict):
        self._parse_dict(machine_dict)

    def _parse(self, var_name: str, info: dict, data_type: type):
        key_tokens = var_name.split('_')
        capitalized_key_tokens = [token.capitalize() if idx > 0 else token for idx,token in enumerate(key_tokens)]
        key = ''.join(capitalized_key_tokens)
        value = info.get(key, None)
        setattr(self, var_name, data_type(value) if value else data_type())

    def _parse_dict(self, machine_dict: dict):

        self._parse('id', machine_dict, str)
        self._parse('gpu_type_id', machine_dict, str)
        self._parse('data_center_id', machine_dict, str)
        self._parse('secure_cloud', machine_dict, bool)
        self._parse('registered', machine_dict, bool)
        self._parse('listed', machine_dict, bool)

        self._parse('cpu_count', machine_dict, int)
        self._parse('gpu_rented', machine_dict, int)
        self._parse('gpu_total', machine_dict, int)
        self.gpu_available = self.gpu_total - self.gpu_rented

        gpu_type_dict = machine_dict.get('gpuType', {})
        self._parse('secure_spot_price', gpu_type_dict, float)
        self._parse('community_spot_price', gpu_type_dict, float)
        self._parse('display_name', gpu_type_dict, str)
        self._parse('memory_in_gb', gpu_type_dict, int)

        machine_system = machine_dict.get('machineSystem', {})
        self._parse('os', machine_system, str)
        self._parse('cuda_version', machine_system, str)
        self._parse('kernel_version', machine_system, str)
        self._parse('private_ip', machine_system, str)
        self._parse('public_ip', machine_system, str)

    def __str__(self):
        return f"Machine(id={self.id}, display_name={self.display_name}, secure_spot_price={self.secure_spot_price}, community_spot_price={self.community_spot_price}, os={self.os}, cuda_version={self.cuda_version}, kernel_version={self.kernel_version}, private_ip={self.private_ip}, public_ip={self.public_ip})"


# machine_id: str,

# registered: bool, 
# listed: bool, 

# gpu_type_id: str, 

# gpu_type: dict, 
# # Withing gpuType

#     display_name: str,
#     secure_spot_price: float, 
#     community_spot_price: float, 

# machine_system: dict,
# # Within machineSystem

#     os: str,
#     cuda_version: str,
#     kernel_version: str,
#     private_ip: str,
#     public_ip: str,

# data_center_id: str,

# gpu_total: int,
# gpu_rented: int,

# cpu_count: int,

# secure_cloud: bool,