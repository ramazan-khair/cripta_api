from dishka import provide, Scope, Provider

from src.application.interactors import GetMarketChartInteractor
from src.config import Config
from src.infrastructure.gateways import CoinGeckoGateway


class AppProvider(Provider):

    @provide(scope=Scope.APP)
    def get_coingecko_gateway(
        self,
        config: Config
    ) -> CoinGeckoGateway:
        return CoinGeckoGateway(
            api_key=config.coingecko_api_key
        )

    @provide(scope=Scope.REQUEST)
    def get_market_chart_interactor(
        self,
        gateway: CoinGeckoGateway
    ) -> GetMarketChartInteractor:
        return GetMarketChartInteractor(
            gateway=gateway
        )
