from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from ..application.ports.service_gateway import (
    ServiceResponse,
    ServiceUnavailable,
)
from ..application.proxy_services import ProxyInternalService

APP_ROOT = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=APP_ROOT / "templates")


def page(request: Request, template: str, title: str, **context):
    return templates.TemplateResponse(request, template, {"title": title, **context})


def create_router(proxy: ProxyInternalService) -> APIRouter:
    router = APIRouter()

    @router.get("/")
    def dashboard(request: Request):
        return page(request, "dashboard.html", "Explorar aeropuertos", active="dashboard")

    @router.get("/itineraries")
    def itineraries(request: Request):
        return page(request, "itineraries.html", "Mis itinerarios", active="itineraries")

    @router.get("/itineraries/new")
    def create_itinerary(request: Request):
        return page(
            request,
            "form.html",
            "Crear itinerario",
            active="itineraries",
            mode="create",
            item_id="",
        )

    @router.get("/itineraries/{item_id}")
    def itinerary_detail(request: Request, item_id: str):
        return page(
            request,
            "detail.html",
            "Detalle del itinerario",
            active="itineraries",
            item_id=item_id,
        )

    @router.get("/itineraries/{item_id}/edit")
    def edit_itinerary(request: Request, item_id: str):
        return page(
            request,
            "form.html",
            "Editar itinerario",
            active="itineraries",
            mode="edit",
            item_id=item_id,
        )

    @router.get("/health/live")
    def health():
        return {"status": "ok"}

    async def forward(
        request: Request,
        path: str,
        call: Callable[[str, str, bytes, str], Awaitable[ServiceResponse]],
    ):
        body = await request.body()
        content_type = request.headers.get("content-type", "application/json")
        try:
            upstream = await call(
                request.method,
                path,
                body,
                content_type,
            )
        except ServiceUnavailable:
            return Response(
                '{"detail":"El servicio no está disponible"}',
                status_code=503,
                media_type="application/json",
            )
        return Response(
            upstream.content,
            status_code=upstream.status_code,
            media_type=upstream.media_type,
        )

    @router.api_route("/ui-api/airports{path:path}", methods=["GET"])
    async def airport_proxy(request: Request, path: str = ""):
        return await forward(request, path, proxy.airports)

    @router.api_route(
        "/ui-api/itineraries{path:path}", methods=["GET", "POST", "PUT", "DELETE"]
    )
    async def itinerary_proxy(request: Request, path: str = ""):
        return await forward(request, path, proxy.itineraries)

    return router
