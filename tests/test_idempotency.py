import re
from dataclasses import replace

from src.application.idempotency import Sha256IdempotencyKeyGenerator
from src.application.schemas import MarketChartRequest


def test_same_request_produces_same_key(market_chart_request: MarketChartRequest) -> None:
    generator = Sha256IdempotencyKeyGenerator()
    assert generator(market_chart_request) == generator(market_chart_request)

def test_changed_request_produces_different_key(market_chart_request: MarketChartRequest) -> None:
    generator = Sha256IdempotencyKeyGenerator()
    changed = replace(market_chart_request, coin_id="ethereum")
    assert generator(market_chart_request) != generator(changed)


def test_key_is_sha256_hex_digest(market_chart_request: MarketChartRequest) -> None:
    key = Sha256IdempotencyKeyGenerator()(market_chart_request)
    assert re.fullmatch("[0-9a-f]{64}", key)