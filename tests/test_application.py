import httpx
import pytest

from src.application.schemas import MarketChartRequest, MarketChartSchema
from src.config import Config
from src.infrastructure.gateways import CoinGeckoGateway


@pytest.mark.asyncio
async def test_gateway_sends_expected_http_request_and_parses_response(
    market_chart_request: MarketChartRequest,
    market_chart_response: MarketChartSchema,
    coingecko_config: Config,
) -> None:
    received_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        received_requests.append(request)
        return httpx.Response(200, json=market_chart_response.model_dump(mode="json"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        gateway = CoinGeckoGateway(client=client, config=coingecko_config)
        result = await gateway.get_market_chart(market_chart_request)

    assert result == market_chart_response
    assert len(received_requests) == 1

    request = received_requests[0]
    assert request.method == "GET"
    assert request.url.path.endswith("/coins/bitcoin/market_chart/range")
    assert request.url.params["vs_currency"] == "usd"
    assert request.url.params["from"] == "1700000000"
    assert request.url.params["to"] == "1700086400"
    assert request.url.params["interval"] == "hourly"
    assert request.url.params["precision"] == "2"
    assert request.headers["x-cg-demo-api-key"] == "test-api-key"


@pytest.mark.asyncio
async def test_gateway_propagates_http_error(
    market_chart_request: MarketChartRequest,
    coingecko_config: Config,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "unavailable"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        gateway = CoinGeckoGateway(client=client, config=coingecko_config)

        with pytest.raises(httpx.HTTPStatusError):
            await gateway.get_market_chart(market_chart_request)
