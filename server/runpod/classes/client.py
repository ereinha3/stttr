import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10

class Client:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {os.environ['RUNPOD_API_KEY']}",
            "Content-Type": "application/json",
        }

        
    def request(self, method, url, json = None) -> requests.Response:
        func = getattr(requests, method)
        try:
            if json:
                resp = func(
                    url,
                    headers=self.headers,
                    json=json if json is not None else {},
                    timeout=DEFAULT_TIMEOUT,
                )
            else:
                resp = func(
                    url,
                    headers=self.headers,
                    timeout=DEFAULT_TIMEOUT,
                )
            if method != "get" and resp.status_code >= 400:
                logger.error(f"Received status code {resp.status_code}")
                logger.error(resp.text)
                raise Exception()
            return resp
        except Exception as e:
            logger.error(f"{e}")
            return None
        

class V1_Client(Client):
    def __init__(self):
        super().__init__()
        self.post_api = "https://rest.runpod.io/v1/{route}"
        self.get_api = "https://rest.runpod.io/v1/{route}"
        self.delete_api = "https://rest.runpod.io/v1/{route}/{id}"

    def get(self, route) -> requests.Response:
        try:
            resp = self.request("get", self.get_api.format(route=route))
            return resp
        except Exception as e:
            logger.error(f"Error: {e}")
            raise Exception(f"Error: {e}")

    def post(self, route, data) -> requests.Response:
        try:
            resp = self.request("post", self.post_api.format(route=route), json=data)
            return resp
        except Exception as e:
            logger.error(f"Error: {e}")
            raise Exception(f"Error: {e}")


    def delete(self, route, id) -> requests.Response:
        try:
            resp = self.request("delete", self.delete_api.format(route=route, id=id))
            return resp
        except Exception as e:
            logger.error(f"Error: {e}")
            raise Exception(f"Error: {e}")


class GQL_Client(Client):

    def __init__(self):
        super().__init__()
        self.api = "https://api.runpod.io/graphql"

    def post(self, json) -> requests.Response:
        try:
            resp = self.request("post", self.api, json=json)
            return resp
        except Exception as e:
            logger.error(f"Error: {e}")
            raise Exception(f"Error: {e}")

    def get(self, json) -> requests.Response:
        try:
            resp = self.request("get", self.api, json=json)
            return resp
        except Exception as e:
            logger.error(f"Error: {e}")
            raise Exception(f"Error: {e}")


V1_API = V1_Client()
GQL_API = GQL_Client()