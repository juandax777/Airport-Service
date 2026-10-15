from fastapi import APIRouter, Response

from ..application.use_cases import ItineraryUseCases
from .schemas import ItineraryInput, ItineraryResponse


def create_router(use_cases: ItineraryUseCases) -> APIRouter:
    router = APIRouter()

    @router.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/health/ready")
    def ready() -> dict[str, str]:
        return {"status": "ready"}

    @router.post(
        "/api/v1/itineraries",
        response_model=ItineraryResponse,
        status_code=201,
    )
    async def create(data: ItineraryInput) -> ItineraryResponse:
        return ItineraryResponse.from_entity(await use_cases.create(data.to_details()))

    @router.get("/api/v1/itineraries", response_model=list[ItineraryResponse])
    def list_all() -> list[ItineraryResponse]:
        return [ItineraryResponse.from_entity(item) for item in use_cases.list_all()]

    @router.get("/api/v1/itineraries/{item_id}", response_model=ItineraryResponse)
    def get_one(item_id: str) -> ItineraryResponse:
        return ItineraryResponse.from_entity(use_cases.get(item_id))

    @router.put("/api/v1/itineraries/{item_id}", response_model=ItineraryResponse)
    async def update(item_id: str, data: ItineraryInput) -> ItineraryResponse:
        updated = await use_cases.update(item_id, data.to_details())
        return ItineraryResponse.from_entity(updated)

    @router.delete("/api/v1/itineraries/{item_id}", status_code=204)
    def delete(item_id: str) -> Response:
        use_cases.delete(item_id)
        return Response(status_code=204)

    return router
