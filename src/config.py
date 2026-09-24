from os import environ as env

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Config(BaseModel):
    coingecko_api_key: str = env["COINGECKO_API_KEY"]