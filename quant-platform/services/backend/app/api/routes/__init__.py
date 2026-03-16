from fastapi import APIRouter, FastAPI

from . import health, strategy, market


def register_routes(app: FastAPI) -> None:
    router = APIRouter()

    router.include_router(health.router)
    router.include_router(strategy.router)
    router.include_router(market.router)

    app.include_router(router)
