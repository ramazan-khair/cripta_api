
from src.application.interfaces import (
    IdempotencyGateway,
    IdempotencyKeyGenerator,
    MarketChartGateway,
)
from src.application.schemas import MarketChartRequest, MarketChartSchema


class GetMarketChartInteractor:
    def __init__(
            self,
            market_chart_gateway: MarketChartGateway,
            idempotency_gateway: IdempotencyGateway,
            idempotency_key_generator: IdempotencyKeyGenerator
    ) -> None:
        self.market_chart_gateway = market_chart_gateway
        self.idempotency_gateway = idempotency_gateway
        self.idempotency_key_generator = idempotency_key_generator

    async def __call__(self, data: MarketChartRequest) -> MarketChartSchema:
        key = self.idempotency_key_generator(data)

        saved_response = await self.idempotency_gateway.get(key)

        if saved_response is not None:
            return saved_response

        response = await self.market_chart_gateway.get_market_chart(data)

        await self.idempotency_gateway.save(key, response)

        return response
