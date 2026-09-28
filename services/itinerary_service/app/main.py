import json
import os
import uuid
from datetime import UTC, date, datetime

import aio_pika
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Date, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./itineraries.db")
AIRPORT_SERVICE_URL = os.getenv("AIRPORT_SERVICE_URL", "http://localhost:8001")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
engine = create_engine(DATABASE_URL)

class Base(DeclarativeBase): pass
class ItineraryRow(Base):
    __tablename__ = "itineraries"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_name: Mapped[str] = mapped_column(String)
    departure_airport_id: Mapped[str] = mapped_column(String)
    arrival_airport_id: Mapped[str] = mapped_column(String)
    travel_date: Mapped[date] = mapped_column(Date)
    duration_minutes: Mapped[int] = mapped_column(Integer)

class ItineraryInput(BaseModel):
    user_name: str = Field(min_length=1)
    departure_airport_id: str
    arrival_airport_id: str
    travel_date: date
    duration_minutes: int = Field(gt=0)
class Itinerary(ItineraryInput): id: str

def output(row: ItineraryRow) -> Itinerary:
    return Itinerary(id=row.id, user_name=row.user_name, departure_airport_id=row.departure_airport_id, arrival_airport_id=row.arrival_airport_id, travel_date=row.travel_date, duration_minutes=row.duration_minutes)

async def validate_airports(data: ItineraryInput):
    if data.departure_airport_id == data.arrival_airport_id: raise HTTPException(422, "Departure and arrival must differ")
    async with httpx.AsyncClient(base_url=AIRPORT_SERVICE_URL, timeout=5) as client:
        for airport_id in (data.departure_airport_id, data.arrival_airport_id):
            try: response = await client.get(f"/api/v1/airports/{airport_id}")
            except httpx.HTTPError as exc: raise HTTPException(503, "Airport service unavailable") from exc
            if response.status_code == 404: raise HTTPException(422, f"Airport {airport_id} does not exist")
            response.raise_for_status()

async def publish(created: Itinerary):
    event = {"event_id": str(uuid.uuid4()), "event_type": "ItineraryCreatedEvent", "version": "1.0", "occurred_at": datetime.now(UTC).isoformat(), "data": created.model_dump(mode="json")}
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel(); exchange = await channel.declare_exchange("itineraries", aio_pika.ExchangeType.TOPIC, durable=True)
        await exchange.publish(aio_pika.Message(body=json.dumps(event).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT), routing_key="itinerary.created")

app = FastAPI(title="Itinerary Service", version="1.0.0")
@app.on_event("startup")
def startup(): Base.metadata.create_all(engine)
@app.get("/health/live")
def live(): return {"status":"ok"}
@app.get("/health/ready")
def ready(): return {"status":"ready"}
@app.post("/api/v1/itineraries", response_model=Itinerary, status_code=201)
async def create(data: ItineraryInput):
    await validate_airports(data)
    row = ItineraryRow(id=str(uuid.uuid4()), **data.model_dump())
    with Session(engine) as session: session.add(row); session.commit(); session.refresh(row); result = output(row)
    try: await publish(result)
    except Exception as exc: raise HTTPException(503, "Itinerary saved but event publication failed") from exc
    return result
@app.get("/api/v1/itineraries", response_model=list[Itinerary])
def list_all():
    with Session(engine) as session: return [output(x) for x in session.query(ItineraryRow).all()]
@app.get("/api/v1/itineraries/{item_id}", response_model=Itinerary)
def get_one(item_id: str):
    with Session(engine) as session:
        row=session.get(ItineraryRow,item_id)
        if not row: raise HTTPException(404,"Itinerary not found")
        return output(row)
@app.put("/api/v1/itineraries/{item_id}", response_model=Itinerary)
async def update(item_id: str, data: ItineraryInput):
    await validate_airports(data)
    with Session(engine) as session:
        row=session.get(ItineraryRow,item_id)
        if not row: raise HTTPException(404,"Itinerary not found")
        for key,value in data.model_dump().items(): setattr(row,key,value)
        session.commit(); session.refresh(row); return output(row)
@app.delete("/api/v1/itineraries/{item_id}", status_code=204)
def delete(item_id: str):
    with Session(engine) as session:
        row=session.get(ItineraryRow,item_id)
        if not row: raise HTTPException(404,"Itinerary not found")
        session.delete(row); session.commit()
