from dataclasses import dataclass

from pydantic import BaseModel


class MarketChartSchema(BaseModel):
    prices: list[list[float]]
    market_caps: list[list[float]]
    total_volumes: list[list[float]]


@dataclass(slots=True)
class MarketChartRequest:
    coin_id: str
    vs_currency: str
    from_timestamp: int
    to_timestamp: int
    interval: str | None = None
    precision: str | None = None