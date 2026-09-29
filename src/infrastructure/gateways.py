import httpx

from src.application.interfaces import MarketChartRequest
from src.application.schemas import MarketChartSchema
from src.config import Config


class CoinGeckoGateway:
    def __init__(self, client: httpx.AsyncClient, config: Config) -> None:
        self.client = client
        self.api_key = config.coingecko_api_key
        self.base_url = config.coingecko_base_url

    async def get_market_chart(self, data: MarketChartRequest) -> MarketChartSchema:

        url = f"{self.base_url}/coins/{data.coin_id}/market_chart/range"

        params: dict[str, str | int | float | bool | None] = {
            "vs_currency": data.vs_currency,
            "from": data.from_timestamp,
            "to": data.to_timestamp,
        }

        if data.interval is not None:
            params["interval"] = data.interval

        if data.precision is not None:
            params["precision"] = data.precision

        headers = {"x-cg-demo-api-key": self.api_key}

        response = await self.client.get(url, params=params, headers=headers)

        response.raise_for_status()

        response_data = response.json()

        return MarketChartSchema(
            prices=response_data["prices"],
            market_caps=response_data["market_caps"],
            total_volumes=response_data["total_volumes"],
        )
