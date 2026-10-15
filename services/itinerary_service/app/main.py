import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .application.exceptions import (
    AirportDoesNotExist,
    AirportServiceUnavailable,
    AirportsMustDiffer,
    EventPublicationFailed,
    ItineraryNotFound,
)
from .application.use_cases import ItineraryUseCases
from .infrastructure.airport_http import HttpAirportValidator
from .infrastructure.persistence import (
    SqlAlchemyItineraryRepository,
    create_engine_from_url,
)
from .infrastructure.rabbitmq_publisher import RabbitMqCreatedEventPublisher
from .presentation.api import create_router


def create_app() -> FastAPI:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./itineraries.db")
    airport_service_url = os.getenv(
        "AIRPORT_SERVICE_URL", "http://localhost:8001"
    )
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")

    repository = SqlAlchemyItineraryRepository(create_engine_from_url(database_url))
    use_cases = ItineraryUseCases(
        repository=repository,
        airport_validator=HttpAirportValidator(airport_service_url),
        event_publisher=RabbitMqCreatedEventPublisher(rabbitmq_url),
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        repository.initialize()
        yield

    application = FastAPI(
        title="Itinerary Service", version="1.0.0", lifespan=lifespan
    )
    application.include_router(create_router(use_cases))

    @application.exception_handler(AirportsMustDiffer)
    async def airports_must_differ_handler(_, exc: AirportsMustDiffer):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @application.exception_handler(AirportDoesNotExist)
    async def airport_missing_handler(_, exc: AirportDoesNotExist):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @application.exception_handler(AirportServiceUnavailable)
    async def airport_unavailable_handler(_, exc: AirportServiceUnavailable):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @application.exception_handler(ItineraryNotFound)
    async def itinerary_missing_handler(_, exc: ItineraryNotFound):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @application.exception_handler(EventPublicationFailed)
    async def event_publication_failed_handler(_, exc: EventPublicationFailed):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    return application


app = create_app()
