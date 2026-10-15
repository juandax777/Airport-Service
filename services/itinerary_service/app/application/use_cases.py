import uuid
from collections.abc import Callable
from dataclasses import replace

from ..domain.entities import Itinerary, ItineraryDetails
from .exceptions import EventPublicationFailed, ItineraryNotFound
from .ports import AirportValidator, CreatedEventPublisher, ItineraryRepository


class ItineraryUseCases:
    def __init__(
        self,
        repository: ItineraryRepository,
        airport_validator: AirportValidator,
        event_publisher: CreatedEventPublisher,
        id_generator: Callable[[], str] | None = None,
    ) -> None:
        self.repository = repository
        self.airport_validator = airport_validator
        self.event_publisher = event_publisher
        self.id_generator = id_generator or (lambda: str(uuid.uuid4()))

    async def create(self, details: ItineraryDetails) -> Itinerary:
        await self.airport_validator.validate(details)
        itinerary = Itinerary.create(self.id_generator(), details)
        saved = self.repository.save(itinerary)
        try:
            await self.event_publisher.publish(saved)
        except Exception as exc:
            raise EventPublicationFailed(
                "Itinerary saved but event publication failed"
            ) from exc
        return saved

    def list_all(self) -> list[Itinerary]:
        return self.repository.list_all()

    def get(self, itinerary_id: str) -> Itinerary:
        itinerary = self.repository.get_by_id(itinerary_id)
        if itinerary is None:
            raise ItineraryNotFound("Itinerary not found")
        return itinerary

    async def update(self, itinerary_id: str, details: ItineraryDetails) -> Itinerary:
        await self.airport_validator.validate(details)
        current = self.repository.get_by_id(itinerary_id)
        if current is None:
            raise ItineraryNotFound("Itinerary not found")
        return self.repository.save(replace(current, **details.__dict__))

    def delete(self, itinerary_id: str) -> None:
        itinerary = self.repository.get_by_id(itinerary_id)
        if itinerary is None:
            raise ItineraryNotFound("Itinerary not found")
        self.repository.delete(itinerary)
