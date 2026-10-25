import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.schemas import MarketChartSchema
from src.infrastructure.gateways import PostgresIdempotencyGateway
from src.infrastructure.persistence.models import IdempotencyRecord


@pytest.mark.asyncio
async def test_get_returns_none_for_unknown_key(
    session: AsyncSession,
) -> None:
    gateway = PostgresIdempotencyGateway(session)

    assert await gateway.get("missing-idempotency-key") is None


@pytest.mark.asyncio
async def test_save_then_get_returns_same_response(
    session: AsyncSession,
    market_chart_response: MarketChartSchema,
) -> None:
    key = "test-idempotency-key"

    await session.execute(
        delete(IdempotencyRecord).where(
            IdempotencyRecord.idempotency_key == key
        )
    )
    await session.commit()

    gateway = PostgresIdempotencyGateway(session)
    await gateway.save(key, market_chart_response)

    result = await gateway.get(key)

    assert result == market_chart_response
