from typing import Protocol

from ..domain.entities import Itinerary, ItineraryDetails


class ItineraryRepository(Protocol):
    def save(self, itinerary: Itinerary) -> Itinerary: ...

    def list_all(self) -> list[Itinerary]: ...

    def get_by_id(self, itinerary_id: str) -> Itinerary | None: ...

    def delete(self, itinerary: Itinerary) -> None: ...


class AirportValidator(Protocol):
    async def validate(self, details: ItineraryDetails) -> None: ...


class CreatedEventPublisher(Protocol):
    async def publish(self, itinerary: Itinerary) -> None: ...
