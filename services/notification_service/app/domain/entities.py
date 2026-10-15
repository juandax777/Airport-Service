from dataclasses import dataclass


@dataclass(frozen=True)
class Notification:
    event_id: str
    itinerary_id: str
    status: str
