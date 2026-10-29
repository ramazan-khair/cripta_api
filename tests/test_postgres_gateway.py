from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.schemas import MarketChartSchema
from src.infrastructure.gateways import PostgresIdempotencyGateway


@pytest.mark.asyncio
async def test_get_returns_none_for_unknown_key(
    session: AsyncSession,
) -> None:
    gateway = PostgresIdempotencyGateway(session)
    key = f"missing-{uuid4()}"

    result = await gateway.get(key)

    assert result is None


@pytest.mark.asyncio
async def test_save_then_get_returns_same_response(
    session: AsyncSession,
    market_chart_response: MarketChartSchema,
) -> None:
    gateway = PostgresIdempotencyGateway(session)
    key = f"test-{uuid4()}"

    created = await gateway.create(key)

    assert created is True

    await gateway.save(key, market_chart_response)

    result = await gateway.get(key)

    assert result == market_chart_response
