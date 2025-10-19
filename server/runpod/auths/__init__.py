from runpod.classes import Auth
from dotenv import load_dotenv
import os

load_dotenv()

NIM_PASSWORD = os.environ['NIM_PASSWORD']
NIM_USERNAME = os.environ['NIM_USERNAME']

nim = Auth(
    name="docker login nvcr.io",
    password=NIM_PASSWORD,
    username=NIM_USERNAME,
)

__all__ = ["nim"]