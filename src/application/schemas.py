from pydantic import BaseModel


class MarketChartSchema(BaseModel):
    prices: list[list[float]]
    market_caps: list[list[float]]
    total_volumes: list[list[float]]
