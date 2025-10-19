from .client import V1_API
import logging

logger = logging.getLogger(__name__)

class Storage:
    def __init__(self, size_gb: int, custom_precision: bool = False):
        self.size_gb = size_gb
        self.custom_precision = custom_precision

    def list_storage(self):
        try:
            resp = V1_API.get(
                route="networkvolumes",
            )
            return resp.json()
        except Exception as e:
            logger.error(f"{e}")
            raise Exception(f"Error: {e}")

class FoundStorage(Storage):
    def __init__(self, datadict: dict, **kwargs):
        super().__init__(**kwargs)
        self.arch = datadict['arch']
        self.author = datadict['author']
        self.model = datadict['model']
        self.gpu_count = datadict['gpu_count']
        self.precision = datadict['precision']
        self.service = datadict['service']
        self._set_name()
        self._set_id()

    def _set_name(self):
        if self.service == 'nim':
            self.name = f"{self.service}.{self.author}.{self.model}.{self.arch.replace(' ', '-')}x{self.gpu_count}.{self.precision}"
        elif self.custom_precision:
            self.name = f"{self.service}.{self.author}.{self.model}.{self.precision}"
        else:
            self.name = f"{self.service}.{self.author}.{self.model}"

    def _set_id(self):
        if not self.name:
            raise ValueError("Name not set")
        available_storages = self.list_storage()
        found = False
        for storage in available_storages:
            if storage['name'] == self.name:
                self.id = storage['id']
                found = True
        if not found:
            self.id = self.create()['id']

    def create(self):
        try:
            if not self.name:
                raise ValueError("Name not set")
            resp = V1_API.post(
                route="networkvolumes",
                data={
                    "dataCenterId": "US-CA-2",
                    "name": self.name,
                    "size": self.size_gb,
                },
            )
            return resp.json()
        except Exception as e:
            logger.error(f"{e}")
            raise Exception(f"Error: {e}")

    def delete(self):
        try:
            resp = V1_API.delete(
                route="networkvolumes",
                id=self.get_id(),
            )
            return resp.json()
        except Exception as e:
            logger.error(f"{e}")
            raise Exception(f"Error: {e}")

    
if __name__ == "__main__":
    storage = Storage(size_gb=100)
    logger.info(storage.list_storage())