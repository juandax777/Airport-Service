from datetime import date

from pydantic import BaseModel, Field

from ..domain.entities import Itinerary, ItineraryDetails


class ItineraryInput(BaseModel):
    user_name: str = Field(min_length=1)
    departure_airport_id: str
    arrival_airport_id: str
    travel_date: date
    duration_minutes: int = Field(gt=0)

    def to_details(self) -> ItineraryDetails:
        return ItineraryDetails(**self.model_dump())


class ItineraryResponse(ItineraryInput):
    id: str

    @classmethod
    def from_entity(cls, itinerary: Itinerary) -> "ItineraryResponse":
        return cls(
            id=itinerary.id,
            user_name=itinerary.user_name,
            departure_airport_id=itinerary.departure_airport_id,
            arrival_airport_id=itinerary.arrival_airport_id,
            travel_date=itinerary.travel_date,
            duration_minutes=itinerary.duration_minutes,
        )
