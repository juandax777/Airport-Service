import pytest

from services.web_app.app.application.ports.service_gateway import ServiceResponse
from services.web_app.app.application.proxy_services import ProxyInternalService


class FakeGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, bytes, str]] = []

    async def request(
        self,
        base_url: str,
        method: str,
        path: str,
        body: bytes,
        content_type: str,
    ) -> ServiceResponse:
        self.calls.append((base_url, method, path, body, content_type))
        return ServiceResponse(b"{}", 200, "application/json")


@pytest.mark.asyncio
async def test_proxy_use_case_routes_airport_and_itinerary_requests_to_ports() -> None:
    gateway = FakeGateway()
    proxy = ProxyInternalService(gateway, "http://airport", "http://itinerary")

    await proxy.airports("GET", "/map-points", b"", "application/json")
    await proxy.itineraries("POST", "/42", b'{"name":"trip"}', "application/json")

    assert gateway.calls == [
        ("http://airport", "GET", "/api/v1/airports/map-points", b"", "application/json"),
        (
            "http://itinerary",
            "POST",
            "/api/v1/itineraries/42",
            b'{"name":"trip"}',
            "application/json",
        ),
    ]
