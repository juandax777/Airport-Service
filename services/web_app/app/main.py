from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .application.ports.service_gateway import ServiceGateway
from .application.proxy_services import ProxyInternalService
from .config import Settings, settings
from .infrastructure.http_service_gateway import HttpxServiceGateway
from .presentation.routes import APP_ROOT, create_router


def create_app(gateway: ServiceGateway | None = None) -> FastAPI:
    service_gateway = gateway or HttpxServiceGateway()
    proxy = ProxyInternalService(
        service_gateway,
        airport_service_url=settings.airport_service_url,
        itinerary_service_url=settings.itinerary_service_url,
    )
    app = FastAPI(title="Itinerary Web", version="1.0.0", docs_url=None, redoc_url=None)
    app.state.proxy = proxy
    app.mount("/static", StaticFiles(directory=APP_ROOT / "static"), name="static")
    app.include_router(create_router(proxy))
    return app


__all__ = ["Settings", "create_app", "settings"]

app = create_app()
