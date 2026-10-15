from fastapi.testclient import TestClient

from services.web_app.app.application.ports.service_gateway import (
    ServiceResponse,
    ServiceUnavailable,
)
from services.web_app.app.main import create_app


class FakeGateway:
    def __init__(self, response: ServiceResponse | None = None, fail: bool = False) -> None:
        self.response = response or ServiceResponse(b'{"ok":true}', 202, "application/json")
        self.fail = fail
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
        if self.fail:
            raise ServiceUnavailable
        return self.response


def test_dashboard_is_rendered_by_web_delivery_adapter() -> None:
    response = TestClient(create_app(FakeGateway())).get("/")

    assert response.status_code == 200
    assert "Explorar aeropuertos" in response.text


def test_airport_proxy_preserves_path_method_and_upstream_response() -> None:
    gateway = FakeGateway(ServiceResponse(b'{"airports":[]}', 202, "application/json"))
    response = TestClient(create_app(gateway)).get("/ui-api/airports/map-points")

    assert response.status_code == 202
    assert response.json() == {"airports": []}
    assert gateway.calls[0][1:3] == ("GET", "/api/v1/airports/map-points")


def test_itinerary_proxy_forwards_method_body_and_content_type() -> None:
    gateway = FakeGateway(ServiceResponse(b'{"id":"42"}', 201, "application/json"))
    response = TestClient(create_app(gateway)).post(
        "/ui-api/itineraries",
        content=b'{"name":"trip"}',
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 201
    assert response.json() == {"id": "42"}
    assert gateway.calls[0][1:] == (
        "POST",
        "/api/v1/itineraries",
        b'{"name":"trip"}',
        "application/json",
    )


def test_proxy_returns_existing_service_unavailable_response() -> None:
    response = TestClient(create_app(FakeGateway(fail=True))).get("/ui-api/airports")

    assert response.status_code == 503
    assert response.json() == {"detail": "El servicio no está disponible"}
