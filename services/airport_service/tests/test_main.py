from app.main import Airport, create_app
from fastapi.testclient import TestClient


class FakeAdapter:
    async def list(self): return [Airport(id="1", name="El Dorado", city="Bogotá", latitude=4.7, longitude=-74.1)]
    async def get(self, airport_id): return (await self.list())[0] if airport_id == "1" else None

def test_get_airport():
    client = TestClient(create_app(FakeAdapter()))
    assert client.get("/api/v1/airports/1").json()["name"] == "El Dorado"

def test_list_airports_and_return_correlation_id():
    response = TestClient(create_app(FakeAdapter())).get(
        "/api/v1/airports", headers={"X-Correlation-ID": "test-request"}
    )
    assert response.status_code == 200
    assert response.json()[0]["id"] == "1"
    assert response.headers["X-Correlation-ID"] == "test-request"

def test_not_found():
    assert TestClient(create_app(FakeAdapter())).get("/api/v1/airports/x").status_code == 404

def test_map_points():
    assert TestClient(create_app(FakeAdapter())).get("/api/v1/airports/map-points").json()[0]["lat"] == 4.7
