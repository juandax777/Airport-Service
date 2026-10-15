import httpx

from ..application.exceptions import (
    AirportDoesNotExist,
    AirportServiceUnavailable,
    AirportsMustDiffer,
)
from ..domain.entities import ItineraryDetails


class HttpAirportValidator:
    def __init__(self, base_url: str, timeout: float = 5) -> None:
        self.base_url = base_url
        self.timeout = timeout

    async def validate(self, details: ItineraryDetails) -> None:
        if details.departure_airport_id == details.arrival_airport_id:
            raise AirportsMustDiffer("Departure and arrival must differ")

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            for airport_id in (
                details.departure_airport_id,
                details.arrival_airport_id,
            ):
                try:
                    response = await client.get(f"/api/v1/airports/{airport_id}")
                except httpx.HTTPError as exc:
                    raise AirportServiceUnavailable("Airport service unavailable") from exc
                if response.status_code == 404:
                    raise AirportDoesNotExist(airport_id)
                response.raise_for_status()
