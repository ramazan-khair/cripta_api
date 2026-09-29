from src.application.interfaces import MarketChartGateway, MarketChartRequest
from src.application.schemas import MarketChartSchema


class GetMarketChartInteractor:
    def __init__(self, gateway: MarketChartGateway) -> None:
        self._gateway = gateway

    async def __call__(self, data: MarketChartRequest) -> MarketChartSchema:
        return await self._gateway.get_market_chart(data)
