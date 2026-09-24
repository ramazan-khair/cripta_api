from src.application.interfaces import MarketChartGateway
from src.domain.entities import MarketChart


class GetMarketChartInteractor:

    def __init__(
        self,
        gateway: MarketChartGateway
    ) -> None:
        self._gateway = gateway

    async def __call__(
        self,
        coin_id: str,
        vs_currency: str,
        from_timestamp: int,
        to_timestamp: int,
        interval: str | None = None,
        precision: str | None = None
    ) -> MarketChart:
        return await self._gateway.get_market_chart(
            coin_id=coin_id,
            vs_currency=vs_currency,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            interval=interval,
            precision=precision
        )