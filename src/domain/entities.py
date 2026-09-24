from dataclasses import dataclass


@dataclass(slots=True)
class MarketChart:
    prices: list[list[float]]
    market_caps: list[list[float]]
    total_volumes: list[list[float]]