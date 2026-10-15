from dataclasses import dataclass
from typing import Protocol

from src.application.schemas import MarketChartSchema


@dataclass(slots=True)
class MarketChartRequest:
    coin_id: str
    vs_currency: str
    from_timestamp: int
    to_timestamp: int
    interval: str | None = None
    precision: int | None = None


class MarketChartGateway(Protocol):
    async def get_market_chart(self, data: MarketChartRequest) -> MarketChartSchema: ...


class TransactionManager(Protocol):
    async def commit(self) -> None: ...


class IdempotencyGateway(Protocol):
    async def get(
            self,
            key: str,
    ) -> MarketChartSchema | None: ...

    async def save(
            self,
            key: str,
            response: MarketChartSchema,
    ) -> None: ...


class IdempotencyKeyGenerator(Protocol):
    def __call__(self, data: MarketChartRequest) -> str: ...