from ...domain.airport import Airport
from ..ports.airport_catalog import AirportCatalog


class AirportCatalogUseCase:
    """Application operations used by the HTTP delivery adapter."""

    def __init__(self, catalog: AirportCatalog) -> None:
        self.catalog = catalog

    async def list_airports(self) -> list[Airport]:
        return await self.catalog.list()

    async def get_airport(self, airport_id: str) -> Airport | None:
        return await self.catalog.get(airport_id)
