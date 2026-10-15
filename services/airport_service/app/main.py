import logging

from fastapi import FastAPI

from .application.ports.airport_catalog import AirportCatalog
from .application.use_cases.airport_catalog import AirportCatalogUseCase
from .config import Settings, settings
from .domain.airport import Airport
from .infrastructure.adapters.api_colombia_airport import (
    ApiColombiaAirportAdapter,
    adapt_airport,
    normalize_coordinates,
)
from .presentation.api import create_router, install_correlation_middleware

logging.basicConfig(level=logging.INFO, format="%(message)s")


def create_app(adapter: AirportCatalog | None = None) -> FastAPI:
    app = FastAPI(title="Airport Service", version="1.0.0")
    airport_adapter = adapter or ApiColombiaAirportAdapter(
        settings.api_colombia_base_url,
        request_timeout_seconds=settings.request_timeout_seconds,
    )
    app.state.adapter = airport_adapter
    app.state.catalog = AirportCatalogUseCase(airport_adapter)
    app.include_router(create_router(app.state.catalog))
    install_correlation_middleware(app)
    return app


# Compatibility exports for existing tests and callers using the old module path.
__all__ = [
    "Airport",
    "ApiColombiaAirportAdapter",
    "Settings",
    "adapt_airport",
    "create_app",
    "normalize_coordinates",
    "settings",
]

app = create_app()
