import httpx
import pytest

import services.web_app.app.infrastructure.http_service_gateway as gateway_module
from services.web_app.app.application.ports.service_gateway import ServiceUnavailable
from services.web_app.app.infrastructure.http_service_gateway import HttpxServiceGateway


def use_mock_transport(monkeypatch, handler) -> None:
    real_async_client = httpx.AsyncClient

    def mocked_client(*args, **kwargs):
        return real_async_client(
            *args,
            transport=httpx.MockTransport(handler),
            **kwargs,
        )

    monkeypatch.setattr(gateway_module.httpx, "AsyncClient", mocked_client)


@pytest.mark.asyncio
async def test_http_gateway_forwards_request_and_preserves_upstream_response(
    monkeypatch,
) -> None:
    observed: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        observed.append(request)
        return httpx.Response(
            202,
            content=b'{"accepted":true}',
            headers={"content-type": "application/json"},
        )

    use_mock_transport(monkeypatch, handler)
    result = await HttpxServiceGateway().request(
        "https://itinerary.test",
        "POST",
        "/api/v1/itineraries",
        b'{"name":"trip"}',
        "application/json",
    )

    assert result.status_code == 202
    assert result.content == b'{"accepted":true}'
    assert result.media_type == "application/json"
    assert observed[0].method == "POST"
    assert observed[0].url.path == "/api/v1/itineraries"
    assert observed[0].content == b'{"name":"trip"}'
    assert observed[0].headers["content-type"] == "application/json"


@pytest.mark.asyncio
async def test_http_gateway_wraps_transport_errors_as_service_unavailable(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("unavailable", request=request)

    use_mock_transport(monkeypatch, handler)

    with pytest.raises(ServiceUnavailable):
        await HttpxServiceGateway().request(
            "https://airport.test",
            "GET",
            "/api/v1/airports",
            b"",
            "application/json",
        )
