import json
from datetime import date
from typing import ClassVar

import httpx
import pytest
from sqlalchemy import create_engine

from services.itinerary_service.app.application.exceptions import (
    AirportDoesNotExist,
    AirportServiceUnavailable,
    AirportsMustDiffer,
)
from services.itinerary_service.app.domain.entities import Itinerary, ItineraryDetails
from services.itinerary_service.app.infrastructure import airport_http, rabbitmq_publisher
from services.itinerary_service.app.infrastructure.airport_http import HttpAirportValidator
from services.itinerary_service.app.infrastructure.persistence import (
    SqlAlchemyItineraryRepository,
)
from services.itinerary_service.app.infrastructure.rabbitmq_publisher import (
    RabbitMqCreatedEventPublisher,
)


def sample_itinerary() -> Itinerary:
    return Itinerary(
        id="itinerary-1",
        user_name="Ana",
        departure_airport_id="BOG",
        arrival_airport_id="MDE",
        travel_date=date(2026, 11, 1),
        duration_minutes=60,
    )


def test_sqlite_itinerary_repository_supports_crud() -> None:
    repository = SqlAlchemyItineraryRepository(create_engine("sqlite://"))
    repository.initialize()
    original = sample_itinerary()

    assert repository.get_by_id(original.id) is None
    assert repository.save(original) == original
    assert repository.get_by_id(original.id) == original
    assert repository.list_all() == [original]

    updated = Itinerary(
        **{**original.__dict__, "user_name": "Beatriz", "duration_minutes": 90}
    )
    assert repository.save(updated) == updated
    assert repository.get_by_id(original.id) == updated

    repository.delete(updated)
    assert repository.get_by_id(original.id) is None
    assert repository.list_all() == []


class FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "http://airport.test")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError(
                "airport request failed", request=request, response=response
            )


class FakeHttpClient:
    responses: ClassVar[list[FakeResponse]] = []
    error: ClassVar[Exception | None] = None
    calls: ClassVar[list[str]] = []

    def __init__(self, *, base_url: str, timeout: float) -> None:
        self.base_url = base_url
        self.timeout = timeout
        type(self).calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def get(self, path: str) -> FakeResponse:
        type(self).calls.append(path)
        if type(self).error is not None:
            raise type(self).error
        return type(self).responses.pop(0)


@pytest.mark.asyncio
async def test_http_airport_validator_checks_both_airports(monkeypatch) -> None:
    FakeHttpClient.responses = [FakeResponse(200), FakeResponse(200)]
    FakeHttpClient.error = None
    monkeypatch.setattr(airport_http.httpx, "AsyncClient", FakeHttpClient)
    validator = HttpAirportValidator("http://airport.test", timeout=2)

    await validator.validate(sample_itinerary_details())

    assert FakeHttpClient.calls == [
        "/api/v1/airports/BOG",
        "/api/v1/airports/MDE",
    ]


@pytest.mark.asyncio
async def test_http_airport_validator_maps_missing_airport(monkeypatch) -> None:
    FakeHttpClient.responses = [FakeResponse(404)]
    FakeHttpClient.error = None
    monkeypatch.setattr(airport_http.httpx, "AsyncClient", FakeHttpClient)

    with pytest.raises(AirportDoesNotExist, match="Airport BOG does not exist"):
        await HttpAirportValidator("http://airport.test").validate(sample_itinerary_details())


@pytest.mark.asyncio
async def test_http_airport_validator_maps_transport_failure(monkeypatch) -> None:
    FakeHttpClient.error = httpx.ConnectError("offline")
    monkeypatch.setattr(airport_http.httpx, "AsyncClient", FakeHttpClient)

    with pytest.raises(AirportServiceUnavailable, match="Airport service unavailable"):
        await HttpAirportValidator("http://airport.test").validate(sample_itinerary_details())


@pytest.mark.asyncio
async def test_http_airport_validator_rejects_same_airport_without_http(monkeypatch) -> None:
    FakeHttpClient.calls = []
    FakeHttpClient.error = None
    monkeypatch.setattr(airport_http.httpx, "AsyncClient", FakeHttpClient)
    details = sample_itinerary_details(arrival_airport_id="BOG")

    with pytest.raises(AirportsMustDiffer):
        await HttpAirportValidator("http://airport.test").validate(details)

    assert FakeHttpClient.calls == []


def sample_itinerary_details(
    departure_airport_id: str = "BOG",
    arrival_airport_id: str = "MDE",
) -> ItineraryDetails:
    return ItineraryDetails(
        user_name="Ana",
        departure_airport_id=departure_airport_id,
        arrival_airport_id=arrival_airport_id,
        travel_date=date(2026, 11, 1),
        duration_minutes=60,
    )


class FakeExchange:
    def __init__(self) -> None:
        self.message = None
        self.routing_key = None

    async def publish(self, message, *, routing_key: str) -> None:
        self.message = message
        self.routing_key = routing_key


class FakeChannel:
    def __init__(self) -> None:
        self.exchange = FakeExchange()
        self.exchange_declaration = None

    async def declare_exchange(self, name, exchange_type, *, durable: bool):
        self.exchange_declaration = (name, exchange_type, durable)
        return self.exchange


class FakeConnection:
    def __init__(self) -> None:
        self.channel_instance = FakeChannel()
        self.closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        self.closed = True

    async def channel(self):
        return self.channel_instance


@pytest.mark.asyncio
async def test_rabbitmq_publisher_sends_canonical_event(monkeypatch) -> None:
    connection = FakeConnection()
    requested_urls = []

    async def connect_robust(url: str):
        requested_urls.append(url)
        return connection

    class FakeMessage:
        def __init__(self, *, body: bytes, delivery_mode) -> None:
            self.body = body
            self.delivery_mode = delivery_mode

    monkeypatch.setattr(rabbitmq_publisher.aio_pika, "connect_robust", connect_robust)
    monkeypatch.setattr(rabbitmq_publisher.aio_pika, "Message", FakeMessage)

    await RabbitMqCreatedEventPublisher("amqp://broker.test/").publish(sample_itinerary())

    exchange = connection.channel_instance.exchange
    event = json.loads(exchange.message.body)
    assert requested_urls == ["amqp://broker.test/"]
    assert connection.channel_instance.exchange_declaration == (
        "itineraries",
        rabbitmq_publisher.aio_pika.ExchangeType.TOPIC,
        True,
    )
    assert exchange.routing_key == "itinerary.created"
    assert event["data"]["itinerary_id"] == "itinerary-1"
    assert "id" not in event["data"]
    assert connection.closed
