from unittest.mock import MagicMock

import httpx
import pytest

from src.application.schemas import MarketChartRequest, MarketChartSchema
from src.infrastructure.gateways import CoinGeckoGateway


@pytest.mark.asyncio
async def test_gateway_builds_request_and_parses_response(
    market_chart_request: MarketChartRequest,
    market_chart_response: MarketChartSchema,
    coingecko_config: MagicMock,
) -> None:
    payload = {
        "prices": [[1_700_000_000_000, 67_000.0]],
        "market_caps": [[1_700_000_000_000, 1_300_000_000_000.0]],
        "total_volumes": [[1_700_000_000_000, 25_000_000_000.0]],
    }
    captured: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as client:
        gateway = CoinGeckoGateway(client=client, config=coingecko_config)
        result = await gateway.get_market_chart(market_chart_request)

    request = captured["request"]
    assert request.method == "GET"
    assert request.url.path.endswith("/coins/bitcoin/market_chart/range")
    assert request.url.params["vs_currency"] == "usd"
    assert request.url.params["from"] == "1700000000"
    assert request.url.params["to"] == "1700086400"
    assert request.headers["x-cg-demo-api-key"] == "test-api-key"
    assert result == market_chart_response


@pytest.mark.asyncio
async def test_gateway_propagates_http_error(
    market_chart_request: MarketChartRequest,
    coingecko_config: MagicMock,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "unavailable"})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    ) as client:
        gateway = CoinGeckoGateway(client=client, config=coingecko_config)

        with pytest.raises(httpx.HTTPStatusError):
            await gateway.get_market_chart(market_chart_request)
