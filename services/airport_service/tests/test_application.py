import pytest
from app.application.use_cases.airport_catalog import AirportCatalogUseCase
from app.domain.airport import Airport


class FakeAirportCatalog:
    async def list(self) -> list[Airport]:
        return [Airport(id="SKBO", name="El Dorado")]

    async def get(self, airport_id: str) -> Airport | None:
        if airport_id == "SKBO":
            return Airport(id="SKBO", name="El Dorado")
        return None


@pytest.mark.asyncio
async def test_catalog_use_case_delegates_list_and_get_to_port() -> None:
    use_case = AirportCatalogUseCase(FakeAirportCatalog())

    airports = await use_case.list_airports()
    airport = await use_case.get_airport("SKBO")
    missing = await use_case.get_airport("unknown")

    assert airports == [Airport(id="SKBO", name="El Dorado")]
    assert airport == Airport(id="SKBO", name="El Dorado")
    assert missing is None
