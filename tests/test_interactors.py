from unittest.mock import MagicMock

import pytest

from src.application.interactors import GetMarketChartInteractor
from src.application.schemas import MarketChartRequest, MarketChartSchema


@pytest.mark.asyncio
async def test_cache_hit_returns_saved_response_without_market_api_call(
    interactor: GetMarketChartInteractor,
    market_chart_request: MarketChartRequest,
    market_chart_response: MarketChartSchema,
    market_chart_gateway: MagicMock,
    idempotency_gateway: MagicMock,
    idempotency_key_generator: MagicMock,
) -> None:
    idempotency_key_generator.return_value = "cached-key"
    idempotency_gateway.get.return_value = market_chart_response

    result = await interactor(market_chart_request)

    assert result == market_chart_response
    idempotency_key_generator.assert_called_once_with(market_chart_request)
    idempotency_gateway.get.assert_awaited_once_with("cached-key")
    market_chart_gateway.get_market_chart.assert_not_awaited()
    idempotency_gateway.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_cache_miss_fetches_and_saves_response(
    interactor: GetMarketChartInteractor,
    market_chart_request: MarketChartRequest,
    market_chart_response: MarketChartSchema,
    market_chart_gateway: MagicMock,
    idempotency_gateway: MagicMock,
    idempotency_key_generator: MagicMock,
) -> None:
    idempotency_key_generator.return_value = "new-key"
    idempotency_gateway.get.return_value = None
    market_chart_gateway.get_market_chart.return_value = market_chart_response

    result = await interactor(market_chart_request)

    assert result == market_chart_response
    market_chart_gateway.get_market_chart.assert_awaited_once_with(
        market_chart_request
    )
    idempotency_gateway.save.assert_awaited_once_with(
        "new-key",
        market_chart_response,
    )


@pytest.mark.asyncio
async def test_upstream_error_is_propagated_without_saving(
    interactor: GetMarketChartInteractor,
    market_chart_request: MarketChartRequest,
    market_chart_gateway: MagicMock,
    idempotency_gateway: MagicMock,
    idempotency_key_generator: MagicMock,
) -> None:
    idempotency_key_generator.return_value = "failed-key"
    idempotency_gateway.get.return_value = None
    market_chart_gateway.get_market_chart.side_effect = RuntimeError(
        "CoinGecko unavailable"
    )

    with pytest.raises(RuntimeError, match="CoinGecko unavailable"):
        await interactor(market_chart_request)

    idempotency_gateway.save.assert_not_awaited()

