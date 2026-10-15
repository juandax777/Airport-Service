from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ItineraryDetails:
    user_name: str
    departure_airport_id: str
    arrival_airport_id: str
    travel_date: date
    duration_minutes: int


@dataclass(frozen=True)
class Itinerary:
    id: str
    user_name: str
    departure_airport_id: str
    arrival_airport_id: str
    travel_date: date
    duration_minutes: int

    @classmethod
    def create(cls, itinerary_id: str, details: ItineraryDetails) -> "Itinerary":
        return cls(id=itinerary_id, **details.__dict__)
