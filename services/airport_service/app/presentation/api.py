import logging
from typing import Any

import httpx
from fastapi import APIRouter, FastAPI, HTTPException, Request

from ..application.use_cases.airport_catalog import AirportCatalogUseCase
from ..domain.airport import Airport

logger = logging.getLogger("airport-service")


def create_router(catalog: AirportCatalogUseCase) -> APIRouter:
    router = APIRouter()

    @router.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/health/ready")
    def ready() -> dict[str, str]:
        return {"status": "ready"}

    @router.get("/api/v1/airports", response_model=list[Airport])
    async def list_airports() -> list[Airport]:
        try:
            return await catalog.list_airports()
        except httpx.HTTPError as exc:
            raise HTTPException(503, "Airport provider unavailable") from exc

    @router.get("/api/v1/airports/map-points")
    async def map_points() -> list[dict[str, Any]]:
        airports = await list_airports()
        return [
            {
                "id": airport.id,
                "name": airport.name,
                "lat": airport.latitude,
                "lon": airport.longitude,
            }
            for airport in airports
            if airport.latitude is not None and airport.longitude is not None
        ]

    @router.get("/api/v1/airports/{airport_id}", response_model=Airport)
    async def get_airport(airport_id: str) -> Airport:
        try:
            airport = await catalog.get_airport(airport_id)
        except httpx.HTTPError as exc:
            raise HTTPException(503, "Airport provider unavailable") from exc
        if airport is None:
            raise HTTPException(404, "Airport not found")
        return airport

    return router


def install_correlation_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def correlation_log(request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", "generated-local")
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        logger.info(
            '{"service":"airport","correlation_id":"%s","status":%s}',
            correlation_id,
            response.status_code,
        )
        return response
