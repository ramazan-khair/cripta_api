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
    precision: str | None = None


class MarketChartGateway(Protocol):
    async def get_market_chart(self, data: MarketChartRequest) -> MarketChartSchema: ...
