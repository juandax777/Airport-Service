import httpx
import pytest

from services.airport_service.app.infrastructure.adapters.api_colombia_airport import (
    ApiColombiaAirportAdapter,
)
from services.airport_service.app.main import create_app


@pytest.mark.asyncio
async def test_provider_adapter_maps_list_payload_and_handles_provider_404() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/Airport":
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": 12,
                            "name": "El Dorado",
                            "city": {"name": "Bogotá"},
                            "latitude": 4.7,
                            "longitude": -74.1,
                        }
                    ]
                },
            )
        if request.url.path == "/Airport/SKBO":
            return httpx.Response(
                200,
                json={"data": {"id": "SKBO", "name": "El Dorado"}},
            )
        if request.url.path == "/Airport/missing":
            return httpx.Response(404)
        return httpx.Response(500)

    async with httpx.AsyncClient(
        base_url="https://provider.test", transport=httpx.MockTransport(handler)
    ) as client:
        adapter = ApiColombiaAirportAdapter("https://provider.test", client=client)

        airports = await adapter.list()
        airport = await adapter.get("SKBO")
        missing = await adapter.get("missing")

    assert len(airports) == 1
    assert airports[0].id == "12"
    assert airports[0].city == "Bogotá"
    assert airport is not None
    assert airport.name == "El Dorado"
    assert missing is None


@pytest.mark.asyncio
async def test_provider_http_error_maps_to_airport_route_503() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "maintenance"})

    provider_client = httpx.AsyncClient(
        base_url="https://provider.test", transport=httpx.MockTransport(handler)
    )
    adapter = ApiColombiaAirportAdapter("https://provider.test", client=provider_client)
    app = create_app(adapter)

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://airport.test"
        ) as client:
            response = await client.get("/api/v1/airports")
    finally:
        await provider_client.aclose()

    assert response.status_code == 503
    assert response.json() == {"detail": "Airport provider unavailable"}
