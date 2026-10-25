from os import environ as env

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class PostgresConfig(BaseModel):
    host: str = Field(alias='POSTGRES_HOST')
    port: int = Field(alias='POSTGRES_PORT')
    login: str = Field(alias='POSTGRES_USER')
    password: str = Field(alias='POSTGRES_PASSWORD')
    database: str = Field(alias='POSTGRES_DB')


class Config(BaseModel):
    postgres: PostgresConfig = Field(
        default_factory=lambda: PostgresConfig(
            POSTGRES_HOST=env["POSTGRES_HOST"],
            POSTGRES_PORT=int(env["POSTGRES_PORT"]),
            POSTGRES_USER=env["POSTGRES_USER"],
            POSTGRES_PASSWORD=env["POSTGRES_PASSWORD"],
            POSTGRES_DB=env["POSTGRES_DB"],
        )
    )
    coingecko_api_key: str = env["COINGECKO_API_KEY"]
    coingecko_base_url: str = env["COINGECKO_BASE_URL"]

config_ = Config()
