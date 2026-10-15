from datetime import date

import pytest

from services.itinerary_service.app.application.exceptions import EventPublicationFailed
from services.itinerary_service.app.application.use_cases import ItineraryUseCases
from services.itinerary_service.app.domain.entities import Itinerary, ItineraryDetails
from services.itinerary_service.app.infrastructure.rabbitmq_publisher import (
    build_itinerary_created_event,
)


class FakeRepository:
    def __init__(self) -> None:
        self.items: dict[str, Itinerary] = {}

    def save(self, itinerary: Itinerary) -> Itinerary:
        self.items[itinerary.id] = itinerary
        return itinerary

    def list_all(self) -> list[Itinerary]:
        return list(self.items.values())

    def get_by_id(self, itinerary_id: str) -> Itinerary | None:
        return self.items.get(itinerary_id)

    def delete(self, itinerary: Itinerary) -> None:
        del self.items[itinerary.id]


class FakeAirportValidator:
    async def validate(self, details: ItineraryDetails) -> None:
        return None


class FakePublisher:
    def __init__(self, error: Exception | None = None) -> None:
        self.published: list[Itinerary] = []
        self.error = error

    async def publish(self, itinerary: Itinerary) -> None:
        if self.error:
            raise self.error
        self.published.append(itinerary)


def details() -> ItineraryDetails:
    return ItineraryDetails(
        user_name="Ana",
        departure_airport_id="BOG",
        arrival_airport_id="MDE",
        travel_date=date(2026, 11, 1),
        duration_minutes=60,
    )


def test_created_event_uses_asyncapi_itinerary_id_field() -> None:
    itinerary = Itinerary.create("itinerary-1", details())

    event = build_itinerary_created_event(itinerary, event_id="event-1")

    assert event["data"]["itinerary_id"] == "itinerary-1"
    assert "id" not in event["data"]


@pytest.mark.asyncio
async def test_create_persists_and_publishes_itinerary() -> None:
    repository = FakeRepository()
    publisher = FakePublisher()
    service = ItineraryUseCases(
        repository, FakeAirportValidator(), publisher, id_generator=lambda: "itinerary-1"
    )

    created = await service.create(details())

    assert created.id == "itinerary-1"
    assert repository.get_by_id(created.id) == created
    assert publisher.published == [created]


@pytest.mark.asyncio
async def test_publish_failure_reports_error_after_itinerary_is_saved() -> None:
    repository = FakeRepository()
    service = ItineraryUseCases(
        repository,
        FakeAirportValidator(),
        FakePublisher(RuntimeError("broker unavailable")),
        id_generator=lambda: "itinerary-1",
    )

    with pytest.raises(EventPublicationFailed):
        await service.create(details())

    assert repository.get_by_id("itinerary-1") is not None
