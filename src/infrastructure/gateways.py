import httpx

from src.domain.entities import MarketChart


class CoinGeckoGateway:

    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(
        self,
        api_key: str,
    ) -> None:
        self._api_key = api_key

    async def get_market_chart(
        self,
        coin_id: str,
        vs_currency: str,
        from_timestamp: int,
        to_timestamp: int,
        interval: str | None = None,
        precision: str | None = None
    ) -> MarketChart:

        url = (
            f"{self.BASE_URL}/coins/"
            f"{coin_id}/market_chart/range"
        )

        params = {
            "vs_currency": vs_currency,
            "from": from_timestamp,
            "to": to_timestamp
        }

        if interval is not None:
            params["interval"] = interval

        if precision is not None:
            params["precision"] = precision

        headers = {
            "x-cg-demo-api-key": self._api_key
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers=headers
            )

        response.raise_for_status()

        data = response.json()

        return MarketChart(
            prices=data["prices"],
            market_caps=data["market_caps"],
            total_volumes=data["total_volumes"]
        )
