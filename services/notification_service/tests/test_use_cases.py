import pytest

from services.notification_service.app.application.exceptions import (
    InvalidItineraryCreatedEvent,
)
from services.notification_service.app.application.use_cases import handle_itinerary_created
from services.notification_service.app.domain.entities import Notification


class FakeRepository:
    def __init__(self) -> None:
        self.items: dict[str, Notification] = {}

    def get_by_event_id(self, event_id: str) -> Notification | None:
        return self.items.get(event_id)

    def save(self, notification: Notification) -> None:
        self.items[notification.event_id] = notification


def event() -> dict:
    return {
        "event_id": "event-1",
        "event_type": "ItineraryCreatedEvent",
        "version": "1.0",
        "data": {"itinerary_id": "itinerary-1"},
    }


def test_handler_persists_notification_from_asyncapi_itinerary_id() -> None:
    repository = FakeRepository()

    handle_itinerary_created(event(), repository)

    assert repository.items["event-1"] == Notification(
        event_id="event-1",
        itinerary_id="itinerary-1",
        status="simulated_sent",
    )


def test_handler_ignores_duplicate_event_delivery() -> None:
    repository = FakeRepository()
    original = Notification("event-1", "itinerary-1", "simulated_sent")
    repository.save(original)

    handle_itinerary_created(event(), repository)

    assert repository.items == {"event-1": original}


def test_handler_accepts_legacy_id_for_queued_events() -> None:
    repository = FakeRepository()
    legacy_event = event()
    legacy_event["data"] = {"id": "legacy-itinerary-1"}

    handle_itinerary_created(legacy_event, repository)

    assert repository.items["event-1"].itinerary_id == "legacy-itinerary-1"


def test_handler_prefers_canonical_id_when_both_shapes_are_present() -> None:
    repository = FakeRepository()
    canonical_event = event()
    canonical_event["data"]["id"] = "legacy-itinerary-1"

    handle_itinerary_created(canonical_event, repository)

    assert repository.items["event-1"].itinerary_id == "itinerary-1"


def test_handler_rejects_malformed_events_with_clear_reason() -> None:
    repository = FakeRepository()

    with pytest.raises(
        InvalidItineraryCreatedEvent,
        match=r"itinerary_id \(or legacy id\)",
    ):
        handle_itinerary_created({"event_id": "event-1", "data": {}}, repository)
