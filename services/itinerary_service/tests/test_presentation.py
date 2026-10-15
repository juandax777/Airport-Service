import pytest
from fastapi.testclient import TestClient

from services.itinerary_service.app import main as itinerary_main
from services.itinerary_service.app.application.exceptions import (
    AirportDoesNotExist,
    AirportServiceUnavailable,
    AirportsMustDiffer,
    EventPublicationFailed,
    ItineraryNotFound,
)


class FakeRepository:
    def initialize(self) -> None:
        pass


class FailingUseCases:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def _raise(self):
        raise self.error

    async def create(self, _details):
        self._raise()

    def list_all(self):
        self._raise()

    def get(self, _item_id):
        self._raise()

    async def update(self, _item_id, _details):
        self._raise()

    def delete(self, _item_id):
        self._raise()


@pytest.mark.parametrize(
    ("error", "method", "path", "status_code", "detail"),
    [
        (
            AirportsMustDiffer("Departure and arrival must differ"),
            "post",
            "/api/v1/itineraries",
            422,
            "Departure and arrival must differ",
        ),
        (
            AirportDoesNotExist("MDE"),
            "post",
            "/api/v1/itineraries",
            422,
            "Airport MDE does not exist",
        ),
        (
            AirportServiceUnavailable("Airport service unavailable"),
            "post",
            "/api/v1/itineraries",
            503,
            "Airport service unavailable",
        ),
        (
            ItineraryNotFound("Itinerary not found"),
            "get",
            "/api/v1/itineraries/itinerary-1",
            404,
            "Itinerary not found",
        ),
        (
            EventPublicationFailed("Itinerary saved but event publication failed"),
            "post",
            "/api/v1/itineraries",
            503,
            "Itinerary saved but event publication failed",
        ),
    ],
)
def test_http_routes_map_application_errors(
    monkeypatch,
    error: Exception,
    method: str,
    path: str,
    status_code: int,
    detail: str,
) -> None:
    repository = FakeRepository()
    use_cases = FailingUseCases(error)
    monkeypatch.setattr(itinerary_main, "create_engine_from_url", lambda _url: object())
    monkeypatch.setattr(
        itinerary_main,
        "SqlAlchemyItineraryRepository",
        lambda _engine: repository,
    )
    monkeypatch.setattr(
        itinerary_main,
        "ItineraryUseCases",
        lambda **_kwargs: use_cases,
    )
    application = itinerary_main.create_app()
    payload = {
        "user_name": "Ana",
        "departure_airport_id": "BOG",
        "arrival_airport_id": "MDE",
        "travel_date": "2026-11-01",
        "duration_minutes": 60,
    }

    with TestClient(application) as client:
        if method == "post":
            response = client.post(path, json=payload)
        else:
            response = client.get(path)

    assert response.status_code == status_code
    assert response.json() == {"detail": detail}
