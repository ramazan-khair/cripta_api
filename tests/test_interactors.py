import asyncio
from dataclasses import asdict

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.exceptions import IdempotencyRequestInProgress
from src.application.idempotency import Sha256IdempotencyKeyGenerator
from src.application.interactors import GetMarketChartInteractor
from src.application.schemas import MarketChartRequest, MarketChartSchema
from src.config import Config
from src.infrastructure.gateways import CoinGeckoGateway, PostgresIdempotencyGateway
from src.infrastructure.persistence.models import IdempotencyRecord


def build_interactor(
        session: AsyncSession,
        http_client: httpx.AsyncClient,
        config: Config,
) -> GetMarketChartInteractor:
    return GetMarketChartInteractor(
        market_chart_gateway=CoinGeckoGateway(http_client, config),
        idempotency_gateway=PostgresIdempotencyGateway(session),
        idempotency_key_generator=Sha256IdempotencyKeyGenerator(),
        transaction_manager=session,
    )

async def remove_idempotency_record(
        session: AsyncSession,
        market_chart_request: MarketChartRequest,
) -> None:
    key = Sha256IdempotencyKeyGenerator()(market_chart_request)

    await session.execute(
        delete(IdempotencyRecord).where(
            IdempotencyRecord.idempotency_key == key
        )
    )
    await session.commit()


@pytest.mark.asyncio
async def test_repeated_request_returns_persisted_response_without_second_upstream_request(
        session: AsyncSession,
        market_chart_request: MarketChartRequest,
        market_chart_response: MarketChartSchema,
        coingecko_config: Config,
) -> None:
    upstream_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        upstream_requests.append(request)
        return httpx.Response(200, json=market_chart_response.model_dump(mode="json"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        interactor = build_interactor(session, client, coingecko_config)

        first_result = await interactor(market_chart_request)
        second_result = await interactor(market_chart_request)

    assert first_result == market_chart_response
    assert second_result == market_chart_response
    assert len(upstream_requests) == 1
    assert upstream_requests[0].method == "GET"
    assert upstream_requests[0].url.path.endswith(
        "/coins/bitcoin/market_chart/range"
    )

    await remove_idempotency_record(session, market_chart_request)


@pytest.mark.asyncio
async def test_request_with_reserved_key_and_no_response_is_reported_as_in_progress(
        session: AsyncSession,
        market_chart_request: MarketChartRequest,
        coingecko_config: Config,
) -> None:
    key_generator = Sha256IdempotencyKeyGenerator()
    idempotency_gateway = PostgresIdempotencyGateway(session)

    key = key_generator(market_chart_request)
    assert await idempotency_gateway.create(key) is True
    await session.commit()

    upstream_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        upstream_requests.append(request)
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        interactor = build_interactor(session, client, coingecko_config)

        with pytest.raises(IdempotencyRequestInProgress):
            await interactor(market_chart_request)

    assert upstream_requests == []

    await remove_idempotency_record(session, market_chart_request)


@pytest.mark.asyncio
async def test_upstream_failure_releases_key_and_allows_retry(
        session: AsyncSession,
        market_chart_request: MarketChartRequest,
        market_chart_response: MarketChartSchema,
        coingecko_config: Config,
) -> None:
    upstream_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        upstream_requests.append(request)

        if len(upstream_requests) == 1:
            return httpx.Response(503, json={"error": "temporarily unavailable"})
        return httpx.Response(200, json=market_chart_response.model_dump(mode="json"))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        interactor = build_interactor(session, client, coingecko_config)
        idempotency_gateway = PostgresIdempotencyGateway(session)
        key = Sha256IdempotencyKeyGenerator()(market_chart_request)

        with pytest.raises(httpx.HTTPStatusError):
            await interactor(market_chart_request)

        assert await idempotency_gateway.get(key) is None

        retry_result = await interactor(market_chart_request)

    assert retry_result == market_chart_response
    assert len(upstream_requests) == 2

    await remove_idempotency_record(session, market_chart_request)


@pytest.mark.asyncio
async def test_concurrent_identical_requests_share_one_upstream(
        api_app: FastAPI,
        session_maker: async_sessionmaker[AsyncSession],
        market_chart_request: MarketChartRequest,
        market_chart_response: MarketChartSchema,
        upstream_requests: list[httpx.Request],
) -> None:
    async with session_maker() as session: # TODO: test isolation
        await remove_idempotency_record(session, market_chart_request)

    query_params = asdict(market_chart_request)
    query_params.pop("coin_id")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_app),
        base_url="http://test",
    ) as client:
        responses = await asyncio.gather(
            *[
                client.get(
                    f"/coins/{market_chart_request.coin_id}/market-chart",
                    params=query_params,
                )
                for _ in range(10)
            ]
        )

    assert all(response.status_code == 200 for response in responses)

    assert all(
        response.json() == market_chart_response.model_dump(mode="json")
        for response in responses
    )

    assert len(upstream_requests) == 1