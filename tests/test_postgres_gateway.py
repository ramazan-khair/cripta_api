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
async def test_idempotency_key_can_be_reserved_only_once(
    session: AsyncSession,
) -> None:
    gateway = PostgresIdempotencyGateway(session)
    key = f"reservation-{uuid4()}"

    first_reservation = await gateway.create(key)
    duplicate_reservation = await gateway.create(key)

    assert first_reservation is True
    assert duplicate_reservation is False


@pytest.mark.asyncio
async def test_saved_response_can_be_read_back(
    session: AsyncSession,
    market_chart_response: MarketChartSchema,
) -> None:
    gateway = PostgresIdempotencyGateway(session)
    key = f"response-{uuid4()}"

    assert await gateway.create(key) is True
    await gateway.save(key, market_chart_response)

    result = await gateway.get(key)

    assert result == market_chart_response


@pytest.mark.asyncio
async def test_deleting_reservation_allows_a_new_attempt(
    session: AsyncSession,
) -> None:
    gateway = PostgresIdempotencyGateway(session)
    key = f"retry-{uuid4()}"

    assert await gateway.create(key) is True
    await gateway.delete(key)

    assert await gateway.get(key) is None
    assert await gateway.create(key) is True
