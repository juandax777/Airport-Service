import logging
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    api_colombia_base_url: str = "https://api-colombia.com/api/v1"
    request_timeout_seconds: float = 5.0


settings = Settings()
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("airport-service")


class Airport(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    name: str
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None


def normalize_coordinates(
    latitude: Any, longitude: Any
) -> tuple[float | None, float | None]:
    """Normalize API Colombia coordinates to (latitude, longitude)."""
    try:
        lat = float(latitude) if latitude is not None else None
        lon = float(longitude) if longitude is not None else None
    except (TypeError, ValueError):
        return None, None
    if lat is None or lon is None:
        return lat, lon

    inside_colombia = -5 <= lat <= 14 and -82 <= lon <= -66
    swapped_inside_colombia = -5 <= lon <= 14 and -82 <= lat <= -66
    return (lon, lat) if not inside_colombia and swapped_inside_colombia else (lat, lon)


def adapt_airport(raw: dict[str, Any]) -> Airport:
    """Adapter from API Colombia's external representation to the domain model."""
    coordinates = raw.get("coordinates") or {}
    raw_city = raw.get("city") or raw.get("municipality")
    city = raw_city.get("name") if isinstance(raw_city, dict) else raw_city
    latitude, longitude = normalize_coordinates(
        raw.get("latitude")
        if raw.get("latitude") is not None
        else coordinates.get("latitude"),
        raw.get("longitude")
        if raw.get("longitude") is not None
        else coordinates.get("longitude"),
    )
    return Airport(
        id=str(raw.get("id") or raw.get("_id") or raw.get("identification") or ""),
        name=raw.get("name") or raw.get("airportName") or "Unknown airport",
        city=city,
        latitude=latitude,
        longitude=longitude,
    )


class ApiColombiaAirportAdapter:
    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None):
        self.base_url, self.client = base_url.rstrip("/"), client

    async def _request(self, path: str) -> Any:
        if self.client:
            response = await self.client.get(path)
        else:
            async with httpx.AsyncClient(
                base_url=self.base_url, timeout=settings.request_timeout_seconds
            ) as client:
                response = await client.get(path)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def list(self) -> list[Airport]:
        payload = await self._request("/Airport")
        rows = payload if isinstance(payload, list) else payload.get("data", [])
        return [adapt_airport(row) for row in rows]

    async def get(self, airport_id: str) -> Airport | None:
        payload = await self._request(f"/Airport/{airport_id}")
        if payload is None:
            return None
        return adapt_airport(payload.get("data", payload))


def create_app(adapter: ApiColombiaAirportAdapter | None = None) -> FastAPI:
    app = FastAPI(title="Airport Service", version="1.0.0")
    app.state.adapter = adapter or ApiColombiaAirportAdapter(
        settings.api_colombia_base_url
    )

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

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready")
    def ready() -> dict[str, str]:
        return {"status": "ready"}

    @app.get("/api/v1/airports", response_model=list[Airport])
    async def list_airports() -> list[Airport]:
        try:
            return await app.state.adapter.list()
        except httpx.HTTPError as exc:
            raise HTTPException(503, "Airport provider unavailable") from exc

    @app.get("/api/v1/airports/map-points")
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

    @app.get("/api/v1/airports/{airport_id}", response_model=Airport)
    async def get_airport(airport_id: str) -> Airport:
        try:
            airport = await app.state.adapter.get(airport_id)
        except httpx.HTTPError as exc:
            raise HTTPException(503, "Airport provider unavailable") from exc
        if airport is None:
            raise HTTPException(404, "Airport not found")
        return airport

    return app


app = create_app()
