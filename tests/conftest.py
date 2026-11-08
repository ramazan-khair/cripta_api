import asyncio
import os
import sys
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import httpx
import pytest
import pytest_asyncio
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.application import interfaces
from src.application.schemas import MarketChartRequest, MarketChartSchema
from src.config import Config, PostgresConfig
from src.controllers.http import router
from src.infrastructure.persistence.base import Base
from src.infrastructure.persistence.models import IdempotencyRecord  # noqa: F401
from src.ioc import AppProvider

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def postgres_config() -> PostgresConfig:
    return PostgresConfig(
        POSTGRES_USER=os.environ["POSTGRES_USER"],
        POSTGRES_PASSWORD=os.environ["POSTGRES_PASSWORD"],
        POSTGRES_HOST=os.environ["POSTGRES_HOST"],
        POSTGRES_PORT=int(os.environ["POSTGRES_PORT"]),
        POSTGRES_DB=os.environ["POSTGRES_DB"],
        POSTGRES_POOL_SIZE=int(os.environ.get("POSTGRES_POOL_SIZE", "5")),
        POSTGRES_MAX_OVERFLOW=int(os.environ.get("POSTGRES_MAX_OVERFLOW", "10")),
    )


@pytest_asyncio.fixture(scope="session")
async def session_maker(
    postgres_config: PostgresConfig,
) -> async_sessionmaker[AsyncSession]:
    database_uri = (
        f"postgresql+psycopg://{postgres_config.login}:"
        f"{postgres_config.password}@{postgres_config.host}:"
        f"{postgres_config.port}/{postgres_config.database}"
    )
    engine = create_async_engine(
        database_uri,
        pool_size=postgres_config.pool_size,
        max_overflow=postgres_config.max_overflow,
        connect_args={
            "connect_timeout": 5,
        },
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def session(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession]:
    async with session_maker() as db_session:
        try:
            yield db_session
        finally:
            await db_session.rollback()


@pytest.fixture
def mock_provider(session: AsyncSession) -> Provider:
    class MockProvider(Provider):
        @provide(scope=Scope.REQUEST)
        async def get_session(self) -> AsyncSession:
            return session

        @provide(scope=Scope.REQUEST)
        async def get_transaction_manager(
            self,
            db_session: AsyncSession,
        ) -> AsyncGenerator[interfaces.TransactionManager]:
            async with db_session.begin_nested() as trx:
                yield trx

    return MockProvider()


@pytest.fixture
def container(mock_provider: Provider) -> AsyncContainer:
    return make_async_container(
        AppProvider(),
        mock_provider,
        context={Config: MagicMock(spec=Config)},
    )


@pytest.fixture
def market_chart_request() -> MarketChartRequest:
    return MarketChartRequest(
        coin_id="bitcoin",
        vs_currency="usd",
        from_timestamp=1_700_000_000,
        to_timestamp=1_700_086_400,
        interval="hourly",
        precision="2",
    )


@pytest.fixture
def market_chart_response() -> MarketChartSchema:
    return MarketChartSchema(
        prices=[[1_700_000_000_000, 67_000.0]],
        market_caps=[[1_700_000_000_000, 1_300_000_000_000.0]],
        total_volumes=[[1_700_000_000_000, 25_000_000_000.0]],
    )


@pytest.fixture
def coingecko_config(postgres_config: PostgresConfig) -> Config:
    return Config(
        postgres=postgres_config,
        coingecko_api_key="test-api-key",
        coingecko_base_url="https://api.example.test/api/v3",
    )


@pytest.fixture
def upstream_requests() -> list[httpx.Request]:
    return []


@pytest.fixture
def upstream_transport(
    market_chart_response: MarketChartSchema,
    upstream_requests: list[httpx.Request],
) -> httpx.AsyncBaseTransport:
    async def handler(request: httpx.Request) -> httpx.Response:
        upstream_requests.append(request)

        await asyncio.sleep(0.15)

        return httpx.Response(status_code=200, json=market_chart_response.model_dump(mode="json"))

    return httpx.MockTransport(handler)


@pytest.fixture
def api_app(
    session_maker: async_sessionmaker[AsyncSession],
    coingecko_config: Config,
    upstream_transport: httpx.AsyncBaseTransport,
) -> FastAPI:
    class TestAppProvider(AppProvider):
        @provide(scope=Scope.APP)
        async def get_httpx_async_client(self) -> AsyncGenerator[httpx.AsyncClient]:
            async with httpx.AsyncClient(
                transport=upstream_transport,
            ) as client:
                yield client

        @provide(scope=Scope.APP)
        def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
            return session_maker

    container = make_async_container(
        TestAppProvider(),
        context={Config: coingecko_config},
    )

    app = FastAPI()
    app.include_router(router)

    setup_dishka(container, app)

    return app
