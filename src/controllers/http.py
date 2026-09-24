from dishka.integrations.fastapi import FromDishka, DishkaRoute
from fastapi import APIRouter, Query

from src.application.interactors import GetMarketChartInteractor
from src.controllers.schemas import MarketChartSchema

router = APIRouter(route_class=DishkaRoute)


@router.get(
    "/coins/{coin_id}/market-chart",
)
async def get_market_chart(
    interactor: FromDishka[GetMarketChartInteractor],
    coin_id: str,
    vs_currency: str,
    from_timestamp: int = Query(alias="from"),
    to_timestamp: int = Query(alias="to"),
    interval: str | None = None,
    precision: str | None = None,
) -> MarketChartSchema:
    market_chart = await interactor(
        coin_id=coin_id,
        vs_currency=vs_currency,
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp,
        interval=interval,
        precision=precision
    )

    return MarketChartSchema(
        prices=market_chart.prices,
        market_caps=market_chart.market_caps,
        total_volumes=market_chart.total_volumes
    )
