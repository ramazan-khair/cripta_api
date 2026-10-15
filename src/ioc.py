from collections.abc import AsyncIterable, AsyncIterator

import httpx
from dishka import AnyOf, Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application import interfaces
from src.application.idempotency import Sha256IdempotencyKeyGenerator
from src.application.interactors import GetMarketChartInteractor
from src.application.interfaces import (
    IdempotencyGateway,
    IdempotencyKeyGenerator,
    MarketChartGateway,
)
from src.config import Config
from src.infrastructure.gateways import CoinGeckoGateway, PostgresIdempotencyGateway
from src.infrastructure.resources.database import new_session_maker


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_httpx_async_client(self) -> AsyncIterator[httpx.AsyncClient]:
        async with httpx.AsyncClient() as client:
            yield client

    @provide(scope=Scope.APP)
    def get_session_maker(self, config: Config) -> async_sessionmaker[AsyncSession]:
        return new_session_maker(config.postgres)

    @provide(scope=Scope.REQUEST)
    async def get_session(
            self, session_maker: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[
        AnyOf[
            AsyncSession,
            interfaces.TransactionManager,
        ]
    ]:
        async with session_maker() as session:
            yield session


    @provide(scope=Scope.APP)
    def get_coingecko_gateway(self, client: httpx.AsyncClient, config: Config) -> interfaces.MarketChartGateway:
        return CoinGeckoGateway(client=client, config=config)

    @provide(scope=Scope.REQUEST)
    def get_postgres_idempotency_gateway(self, session: AsyncSession) -> interfaces.IdempotencyGateway:
        return PostgresIdempotencyGateway(session=session)

    @provide(scope=Scope.APP)
    def get_idempotency_key_generator(self) -> interfaces.IdempotencyKeyGenerator:
        return Sha256IdempotencyKeyGenerator()

    @provide(scope=Scope.REQUEST)
    def get_market_chart_interactor(
            self,
            market_chart_gateway: MarketChartGateway,
            idempotency_gateway: IdempotencyGateway,
            idempotency_key_generator: IdempotencyKeyGenerator,
    ) -> GetMarketChartInteractor:
        return GetMarketChartInteractor(
            market_chart_gateway=market_chart_gateway,
            idempotency_gateway=idempotency_gateway,
            idempotency_key_generator=idempotency_key_generator,
        )

