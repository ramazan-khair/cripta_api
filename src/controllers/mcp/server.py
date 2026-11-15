from dishka import FromDishka, make_async_container
from dishka_fastmcp import dishka_lifespan, inject, setup_dishka
from fastmcp import FastMCP

from src.application.interactors import GetMarketChartInteractor
from src.application.schemas import MarketChartRequest
from src.config import Config
from src.ioc import AppProvider

config = Config()

container = make_async_container(
    AppProvider(),
    context={Config: config},
)

mcp = FastMCP(
    name="Crypto API MCP",
    lifespan=dishka_lifespan(container),
)

setup_dishka(container, mcp)


@mcp.tool
@inject
async def get_market_chart(
    interactor: FromDishka[GetMarketChartInteractor],
    market_chart_request: MarketChartRequest,
) -> dict[str, object]:
    response = await interactor(market_chart_request)

    return response.model_dump(mode="json")
