from pydantic import BaseModel


class MarketChartQuery(BaseModel):
    vs_currency: str
    from_timestamp: int
    to_timestamp: int
    interval: str | None = None
    precision: str | None = None
