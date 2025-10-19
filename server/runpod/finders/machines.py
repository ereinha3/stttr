from runpod.classes import GQL_API, Machine

import logging
logger = logging.getLogger(__name__)

class MachineFinder:
    def __init__(self):
        pass

    def get_machines(self) -> list:
        try:
            resp = GQL_API.post(
                json={
                    "operationName": "getMachinesForHostDashboard",
                    "query": """
                    query getMachinesForHostDashboard {
                        myself {
                            id
                            machineQuota 
                            nodeGroups {
                                id 
                                name
                                throughput
                                createdAt
                                listed
                                    __typename
                            }
                            machinesSummary {
                                cpuTypeId 
                                displayName 
                                diskProfitPerHr 
                                gpuRented 
                                gpuTotal 
                                gpuTypeId 
                                id 
                                listed 
                                machineType 
                                onDemandPods 
                                podProfitPerHr 
                                spotPods 
                                cpuRented 
                                vcpuTotal 
                                __typename 
                            }
                            machines {
                                id
                                name
                                hostPricePerGpu
                                hostMinBidPerGpu
                                registered
                                listed
                                verified
                                idleJobTemplateId
                                idleJobTemplate {
                                    imageName
                                    name
                                    id
                                    __typename
                                }
                                gpuPowerLimitPercentageSelf
                                margin
                                moboName
                                cpuType {
                                    displayName
                                    __typename
                                }
                                gpuTypeId
                                gpuType {
                                    memoryInGb
                                    displayName
                                    securePrice
                                    communityPrice
                                    secureSpotPrice
                                    communitySpotPrice
                                    manufacturer
                                    __typename
                                }
                                dataCenterId
                                cpuCount
                                diskReserved
                                diskTotal
                                diskMBps
                                downloadMbps
                                gpuReserved
                                gpuTotal
                                memoryReserved
                                memoryTotal
                                installCert
                                pcieLink
                                pcieLinkWidth
                                uploadMbps
                                vcpuReserved
                                secureCloud
                                vcpuTotal
                                supportPublicIp
                                uptimePercentListedOneWeek
                                uptimePercentListedFourWeek
                                maintenanceStart
                                maintenanceEnd
                                machineSystem {
                                    os
                                    cudaVersion
                                    kernelVersion
                                    privateIp
                                    publicIp
                                    __typename
                                }
                                machineType
                                nodeGroupId
                                lastSyncAt
                                minPodGpuCount
                                maintenanceMode
                                diskMBps
                                __typename
                            }
                            __typename
                        }
                    }
                    """,
                    "variables": {}
                }
            )
            if resp is None:
                logger.error("Received None response from API")
                raise Exception("Received None response from API")
            resp = resp.json()
            if len(resp['data']['myself']['machinesSummary']) != len(resp['data']['myself']['machines']):
                raise Exception("Machines summary and machines do not match")
            else:
                machine_summaries = resp['data']['myself']['machinesSummary']
                machine_summaries_dict = {machine_summary['id']: machine_summary for machine_summary in machine_summaries}
                machines = resp['data']['myself']['machines']
                machines_dict = {machine['id']: machine for machine in machines}
                if machines_dict.keys() != machine_summaries_dict.keys():
                    raise Exception("Machines and machines summary do not match")
                else:
                    for machine_id in machines_dict.keys():
                        machines_dict[machine_id].update(machine_summaries_dict[machine_id])
                machines = [machine for machine in machines_dict.values()]
            return machines
        except Exception as e:
            logger.error(f"{e}")
            raise Exception(f"{e}")

    def list_machines(self) -> list:
        return sorted([Machine(machine) for machine in self.get_machines()], key=lambda x: x.memory_in_gb, reverse=True)

    def find_available_machines(self):
        machines = self.list_machines()
        return [machine for machine in machines if machine.listed == 1 and machine.gpu_rented < machine.gpu_total and machine.data_center_id == "US-CA-2"]


info = MachineFinder()

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(name)s \t- %(message)s'
    )

    loggers_to_ignore = ["urllib3.connectionpool", "httpx"]
    for logger_name in loggers_to_ignore:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    def recursive_print(obj: dict, depth: int = 0, use_set: list = [], recursed=False):
        for key, value in sorted(obj.items(), key=lambda x: x[0]):
            if key not in use_set and not recursed:
                continue
            if isinstance(value, dict):
                logger.info('\t' * depth + key + ":")
                recursive_print(value, depth + 1, use_set, recursed=True)
            else:
                logger.info('\t' * depth + key + ": " + str(value))

    BOLD='\033[1m'
    RESET = '\033[0m'

    machines = info.get_machines()

    logger.info(f"{BOLD}Keys (union):{RESET}")
    recursive_print(machines[0], use_set=machines[0].keys())
    logger.info('-'*50)
    
    # Show key counts
    logger.info(f"{BOLD}Key Statistics:{RESET}")
    logger.info(f"Total keys: {len(machines[0].keys())}")
    logger.info('-'*50)

    machines = info.list_machines()

    example_archs = {machine.display_name: machine for machine in machines}

    logger.info(f"{BOLD}Architectures:{RESET}")
    logger.info(f"{'arch':<12}" + f"{''*4:<4}" + f"{'gpu_type_id':<32}" + f"{''*4:<4}" + f"{'display_name':<16}" + f"{''*4:<4}" + f"{'community_spot_price':<20}" + f"{''*4:<4}" + f"{'secure_spot_price':<16}" + f"{''*4:<8}" + f"{'memory_in_gb':<6}")
    for arch, machine in example_archs.items():
        logger.info(f"{arch:<12}" + f"{''*4:<4}" + f"{machine.gpu_type_id:<32}" + f"{''*4:<4}" + f"{machine.display_name:<16}" + f"{''*4:<4}" + f"{machine.community_spot_price:<20}" + f"{''*4:<4}" + f"{machine.secure_spot_price:<16}" + f"{''*5:<9}" + f"{machine.memory_in_gb:<6}")
    logger.info('-'*50)

    found = False
    not_ccdc_machines = []
    for machine in machines:
        if not machine.data_center_id == "US-CA-2":
            not_ccdc_machines.append(machine)
            found = True

    if found:
            logger.info(f"{BOLD}Machines not in CCDC:{RESET}")
            logger.info(f"{'machine_id':<12}" + f"{''*4:<4}" + f"{'gpu_type_id':<32}" + f"{''*4:<4}" + f"{'display_name':<16}" + f"{''*4:<4}" + f"{'gpu_rented/gpu_total':<16}" + f"{''*4:<6}" + f"{'data_center_id':<18}" + f"{''*4:<6}" + f"{'cuda_version':<18}" + f"{''*4:<6}" + f"{'memory_in_gb':<6}")
            for machine in not_ccdc_machines:
                logger.info(f"{machine.id:<12}" + f"{''*4:<4}" + f"{machine.gpu_type_id:<32}" + f"{''*4:<4}" + f"{machine.display_name:<16}" + f"{''*4:<4}" + f"{machine.gpu_rented}/{machine.gpu_total:<20}" + f"{''*4:<4}" + f"{machine.data_center_id:<16}" + f"{''*4:<8}" + f"{machine.cuda_version:<16}" + f"{''*4:<8}" + f"{machine.memory_in_gb:<6}")
    else:
        logger.info(f"{BOLD}All machines in CCDC:{RESET}")
    logger.info('-'*50)
    
    
    available_machines = info.find_available_machines()
    logger.info(f"{BOLD}Available machines:{RESET}")
    logger.info(f"{'machine_id':<12}" + f"{''*4:<4}" + f"{'gpu_type_id':<32}" + f"{''*4:<4}" + f"{'display_name':<16}" + f"{''*4:<4}" + f"{'gpu_rented/gpu_total':<16}" + f"{''*4:<6}" + f"{'data_center_id':<18}" + f"{''*4:<6}" + f"{'cuda_version':<18}" + f"{''*4:<6}" + f"{'memory_in_gb':<6}")
    for machine in available_machines:
        logger.info(f"{machine.id:<12}" + f"{''*4:<4}" + f"{machine.gpu_type_id:<32}" + f"{''*4:<4}" + f"{machine.display_name:<16}" + f"{''*4:<4}" + f"{machine.gpu_rented}/{machine.gpu_total:<20}" + f"{''*4:<4}" + f"{machine.data_center_id:<16}" + f"{''*4:<8}" + f"{machine.cuda_version:<16}" + f"{''*4:<8}" + f"{machine.memory_in_gb:<6}")
    

