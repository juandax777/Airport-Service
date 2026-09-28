from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    airport_service_url: str = "http://127.0.0.1:8001"
    itinerary_service_url: str = "http://127.0.0.1:8002"


settings = Settings()
app = FastAPI(title="Itinerary Web", version="1.0.0", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")


def page(request: Request, template: str, title: str, **context):
    return templates.TemplateResponse(request, template, {"title": title, **context})


@app.get("/")
def dashboard(request: Request):
    return page(request, "dashboard.html", "Explorar aeropuertos", active="dashboard")


@app.get("/itineraries")
def itineraries(request: Request):
    return page(request, "itineraries.html", "Mis itinerarios", active="itineraries")


@app.get("/itineraries/new")
def create_itinerary(request: Request):
    return page(request, "form.html", "Crear itinerario", active="itineraries", mode="create", item_id="")


@app.get("/itineraries/{item_id}")
def itinerary_detail(request: Request, item_id: str):
    return page(request, "detail.html", "Detalle del itinerario", active="itineraries", item_id=item_id)


@app.get("/itineraries/{item_id}/edit")
def edit_itinerary(request: Request, item_id: str):
    return page(request, "form.html", "Editar itinerario", active="itineraries", mode="edit", item_id=item_id)


@app.get("/health/live")
def health():
    return {"status": "ok"}


async def forward(base_url: str, method: str, path: str, request: Request) -> Response:
    body = await request.body()
    headers = {"content-type": request.headers.get("content-type", "application/json")}
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=15) as client:
            upstream = await client.request(method, path, content=body or None, headers=headers)
    except httpx.HTTPError:
        return Response('{"detail":"El servicio no está disponible"}', status_code=503, media_type="application/json")
    return Response(upstream.content, status_code=upstream.status_code, media_type=upstream.headers.get("content-type", "application/json"))


@app.api_route("/ui-api/airports{path:path}", methods=["GET"])
async def airport_proxy(request: Request, path: str = ""):
    return await forward(settings.airport_service_url, request.method, f"/api/v1/airports{path}", request)


@app.api_route("/ui-api/itineraries{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def itinerary_proxy(request: Request, path: str = ""):
    return await forward(settings.itinerary_service_url, request.method, f"/api/v1/itineraries{path}", request)
