from collections.abc import AsyncIterator

import httpx
from dishka import Provider, Scope, provide

from src.application.interactors import GetMarketChartInteractor
from src.config import Config
from src.infrastructure.gateways import CoinGeckoGateway


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_httpx_async_client(self) -> AsyncIterator[httpx.AsyncClient]:
        async with httpx.AsyncClient() as client:
            yield client

    @provide(scope=Scope.APP)
    def get_coingecko_gateway(self, client: httpx.AsyncClient, config: Config) -> CoinGeckoGateway:
        return CoinGeckoGateway(client=client, config=config)

    @provide(scope=Scope.REQUEST)
    def get_market_chart_interactor(self, gateway: CoinGeckoGateway) -> GetMarketChartInteractor:
        return GetMarketChartInteractor(gateway=gateway)
