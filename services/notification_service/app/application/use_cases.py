from ..domain.entities import Notification
from .exceptions import InvalidItineraryCreatedEvent
from .ports import NotificationRepository


def _event_identifiers(event: object) -> tuple[str, str]:
    if not isinstance(event, dict):
        raise InvalidItineraryCreatedEvent("Event payload must be a JSON object")

    event_id = event.get("event_id")
    if not isinstance(event_id, str) or not event_id.strip():
        raise InvalidItineraryCreatedEvent("Event must contain a non-empty string event_id")

    data = event.get("data")
    if not isinstance(data, dict):
        raise InvalidItineraryCreatedEvent("Event data must be a JSON object")

    if "itinerary_id" in data:
        itinerary_id = data["itinerary_id"]
        if not isinstance(itinerary_id, str) or not itinerary_id.strip():
            raise InvalidItineraryCreatedEvent(
                "Event data.itinerary_id must be a non-empty string"
            )
    elif "id" in data:
        itinerary_id = data["id"]
        if not isinstance(itinerary_id, str) or not itinerary_id.strip():
            raise InvalidItineraryCreatedEvent("Legacy event data.id must be a non-empty string")
    else:
        raise InvalidItineraryCreatedEvent(
            "Event data must contain itinerary_id (or legacy id)"
        )

    return event_id, itinerary_id


def handle_itinerary_created(event: object, repository: NotificationRepository) -> None:
    """Persist one simulated notification, ignoring duplicate delivery."""
    event_id, itinerary_id = _event_identifiers(event)
    if repository.get_by_event_id(event_id) is not None:
        return

    notification = Notification(
        event_id=event_id,
        itinerary_id=itinerary_id,
        status="simulated_sent",
    )
    repository.save(notification)
