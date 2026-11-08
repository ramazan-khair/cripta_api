from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from src.config import Config
from src.controllers.http import router
from src.ioc import AppProvider

config = Config()

container = make_async_container(AppProvider(), context={Config: config})


def get_app() -> FastAPI:
    app = FastAPI(title="Crypto API")

    app.include_router(router)

    setup_dishka(container, app)

    return app
