from typing import Protocol

from ...domain.airport import Airport


class AirportCatalog(Protocol):
    """Outbound port for obtaining normalized airports."""

    async def list(self) -> list[Airport]: ...

    async def get(self, airport_id: str) -> Airport | None: ...
