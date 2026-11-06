from src.application.exceptions import IdempotencyRequestInProgress
from src.application.interfaces import (
    IdempotencyGateway,
    IdempotencyKeyGenerator,
    MarketChartGateway,
    TransactionManager,
)
from src.application.schemas import MarketChartRequest, MarketChartSchema


class GetMarketChartInteractor:
    def __init__(
            self,
            market_chart_gateway: MarketChartGateway,
            idempotency_gateway: IdempotencyGateway,
            idempotency_key_generator: IdempotencyKeyGenerator,
            transaction_manager: TransactionManager,
    ) -> None:
        self.market_chart_gateway = market_chart_gateway
        self.idempotency_gateway = idempotency_gateway
        self.idempotency_key_generator = idempotency_key_generator
        self.transaction_manager = transaction_manager

    async def __call__(self, data: MarketChartRequest) -> MarketChartSchema:
        key = self.idempotency_key_generator(data)

        try:
            created = await self.idempotency_gateway.create(key)

            if not created:
                saved_response = await self.idempotency_gateway.get(key)

                if saved_response is None:
                    raise IdempotencyRequestInProgress(
                        "A request with this key is still being processed"
                    )

                return saved_response

            response = await self.market_chart_gateway.get_market_chart(data)

            await self.idempotency_gateway.save(key, response)

            await self.transaction_manager.commit()

            return response

        except BaseException:
            await self.transaction_manager.rollback()
            raise