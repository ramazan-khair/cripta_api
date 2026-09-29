from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from src.application.interactors import GetMarketChartInteractor
from src.application.interfaces import MarketChartRequest
from src.application.schemas import MarketChartSchema
from src.controllers.schemas import MarketChartQuery

router = APIRouter(route_class=DishkaRoute)


@router.get(
    "/coins/{coin_id}/market-chart",
)
async def get_market_chart(
    interactor: FromDishka[GetMarketChartInteractor],
    coin_id: str,
    query: MarketChartQuery = Depends(),  # noqa: B008
) -> MarketChartSchema:

    data = MarketChartRequest(
        coin_id=coin_id,
        vs_currency=query.vs_currency,
        from_timestamp=query.from_timestamp,
        to_timestamp=query.to_timestamp,
        interval=query.interval,
        precision=query.precision,
    )

    return await interactor(data)
