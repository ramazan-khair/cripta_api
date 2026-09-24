from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from src.domain.entities import MarketChart


class MarketChartGateway(Protocol):
    async def get_market_chart(
            self,
            coin_id: str,
            vs_currency: str,
            from_timestamp: int,
            to_timestamp: int,
            interval: int | None = None,
            precision: int | None = None
    ) -> MarketChart:
        ...


