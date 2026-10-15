import json
import uuid
from datetime import UTC, datetime

import aio_pika

from ..domain.entities import Itinerary


def build_itinerary_created_event(
    itinerary: Itinerary,
    event_id: str | None = None,
    occurred_at: datetime | None = None,
) -> dict:
    return {
        "event_id": event_id or str(uuid.uuid4()),
        "event_type": "ItineraryCreatedEvent",
        "version": "1.0",
        "occurred_at": (occurred_at or datetime.now(UTC)).isoformat(),
        "data": {
            "itinerary_id": itinerary.id,
            "user_name": itinerary.user_name,
            "departure_airport_id": itinerary.departure_airport_id,
            "arrival_airport_id": itinerary.arrival_airport_id,
            "travel_date": itinerary.travel_date.isoformat(),
            "duration_minutes": itinerary.duration_minutes,
        },
    }


class RabbitMqCreatedEventPublisher:
    def __init__(self, url: str) -> None:
        self.url = url

    async def publish(self, itinerary: Itinerary) -> None:
        event = build_itinerary_created_event(itinerary)
        connection = await aio_pika.connect_robust(self.url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                "itineraries", aio_pika.ExchangeType.TOPIC, durable=True
            )
            message = aio_pika.Message(
                body=json.dumps(event).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await exchange.publish(message, routing_key="itinerary.created")
