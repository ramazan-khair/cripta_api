import httpx
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.schemas import MarketChartRequest, MarketChartSchema
from src.config import Config
from src.infrastructure.persistence.models import IdempotencyRecord


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


class PostgresIdempotencyGateway:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, key: str) -> bool:
        statement = (
            insert(IdempotencyRecord)
            .values(idempotency_key=key, response_data=None)
            .on_conflict_do_nothing(index_elements=[IdempotencyRecord.idempotency_key])
            .returning(IdempotencyRecord.idempotency_key)
        )

        result = await self.session.execute(statement)
        created_key = result.scalar_one_or_none()

        return created_key is not None


    async def get(
            self,
            key: str
    ) -> MarketChartSchema | None:
        statement = select(IdempotencyRecord).where(IdempotencyRecord.idempotency_key == key)

        result = await self.session.execute(statement)

        record = result.scalar_one_or_none()

        if record is None or record.response_data is None:
            return None

        return MarketChartSchema.model_validate(record.response_data)


    async def save(
            self,
            key: str,
            response: MarketChartSchema
    ) -> None:
        statement = (update(IdempotencyRecord)
                     .where(IdempotencyRecord.idempotency_key == key)
                     .values(response_data=response.model_dump(mode="json"))
                     )

        await self.session.execute(statement)
        await self.session.commit()

    async def delete(self, key: str) -> None:
        statement = delete(IdempotencyRecord).where(IdempotencyRecord.idempotency_key == key)

        await self.session.execute(statement)
        await self.session.commit()