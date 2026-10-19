import asyncio
import os
import sys
from collections.abc import AsyncGenerator
from typing import cast
from unittest.mock import MagicMock, create_autospec

import pytest
import pytest_asyncio
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.application import interfaces
from src.application.interactors import GetMarketChartInteractor
from src.application.schemas import MarketChartRequest, MarketChartSchema
from src.config import Config, PostgresConfig
from src.infrastructure.persistence.base import Base
from src.infrastructure.persistence.models import IdempotencyRecord  # noqa: F401
from src.ioc import AppProvider

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )


@pytest.fixture(scope="session")
def postgres_config() -> PostgresConfig:
    return PostgresConfig(
        POSTGRES_USER=os.environ["POSTGRES_USER"],
        POSTGRES_PASSWORD=os.environ["POSTGRES_PASSWORD"],
        POSTGRES_HOST=os.environ["POSTGRES_HOST"],
        POSTGRES_PORT=int(os.environ["POSTGRES_PORT"]),
        POSTGRES_DB=os.environ["POSTGRES_DB"],
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
    engine = create_async_engine(database_uri)

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
        yield db_session
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
def market_chart_gateway() -> MagicMock:
    return cast(
        MagicMock,
        create_autospec(
            interfaces.MarketChartGateway,
            instance=True,
            spec_set=True,
        ),
    )


@pytest.fixture
def idempotency_gateway() -> MagicMock:
    return cast(
        MagicMock,
        create_autospec(
            interfaces.IdempotencyGateway,
            instance=True,
            spec_set=True,
        ),
    )


@pytest.fixture
def idempotency_key_generator() -> MagicMock:
    return MagicMock(return_value="test-key")


@pytest.fixture
def interactor(
    market_chart_gateway: MagicMock,
    idempotency_gateway: MagicMock,
    idempotency_key_generator: MagicMock,
) -> GetMarketChartInteractor:
    return GetMarketChartInteractor(
        market_chart_gateway=cast(
            interfaces.MarketChartGateway,
            market_chart_gateway,
        ),
        idempotency_gateway=cast(
            interfaces.IdempotencyGateway,
            idempotency_gateway,
        ),
        idempotency_key_generator=cast(
            interfaces.IdempotencyKeyGenerator,
            idempotency_key_generator,
        ),
    )


@pytest.fixture
def coingecko_config() -> MagicMock:
    config = MagicMock(spec=Config)
    config.coingecko_api_key = "test-api-key"
    config.coingecko_base_url = "https://api.example.test/api/v3"
    return config
