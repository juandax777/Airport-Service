from typing import Any

import httpx

from ...domain.airport import Airport


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
    """Translate API Colombia's external representation to the service model."""
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
    """HTTP adapter implementing the AirportCatalog outbound port."""

    def __init__(
        self,
        base_url: str,
        client: httpx.AsyncClient | None = None,
        request_timeout_seconds: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client
        self.request_timeout_seconds = request_timeout_seconds

    async def _request(self, path: str) -> Any:
        if self.client:
            response = await self.client.get(path)
        else:
            async with httpx.AsyncClient(
                base_url=self.base_url, timeout=self.request_timeout_seconds
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
