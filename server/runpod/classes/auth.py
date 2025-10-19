from .client import V1_API

class Auth:
    def __init__(self, name: str, password: str, username: str):
        self.name = name
        self.password = password
        self.username = username    
        self._set_id()  

    def _set_id(self):
        available_auths = self.list()
        found = False
        for auth in available_auths:
            if auth['name'] == self.name:
                self.id = auth['id']
                found = True
        if not found:
            self.id = self.create()['id']


    def create(self):
        try:
            resp = V1_API.post(
                route="containerregistryauth",
                data={
                    "name": self.name,
                    "password": self.password,
                    "username": self.username,
                },
            )
            return resp.json()
        except Exception as e:
            print(f"Error: {e}")
            raise Exception(f"Error: {e}")

    def list(self):
        try:
            resp = V1_API.get(
                route="containerregistryauth",
            )
            return resp.json()
        except Exception as e:
            print(f"Error: {e}")
            raise Exception(f"Error: {e}")

    def delete(self):
        try:
            resp = V1_API.delete(
                route="containerregistryauth",
                id=self.get_id(),
            )
            return resp.json()
        except Exception as e:
            print(f"Error: {e}")
            raise Exception(f"Error: {e}")

