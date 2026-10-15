import json
import logging

import aio_pika

from ..application.exceptions import InvalidItineraryCreatedEvent
from ..application.ports import NotificationRepository
from ..application.use_cases import handle_itinerary_created

logger = logging.getLogger(__name__)


class RabbitMqNotificationConsumer:
    def __init__(self, url: str, repository: NotificationRepository) -> None:
        self.url = url
        self.repository = repository

    async def run(self) -> None:
        connection = await aio_pika.connect_robust(self.url)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                "itineraries", aio_pika.ExchangeType.TOPIC, durable=True
            )
            queue = await channel.declare_queue("notifications", durable=True)
            await queue.bind(exchange, "itinerary.created")

            async with queue.iterator() as messages:
                async for message in messages:
                    try:
                        async with message.process():
                            try:
                                event = json.loads(message.body)
                            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                                raise InvalidItineraryCreatedEvent(
                                    "Message body must contain valid JSON"
                                ) from exc
                            handle_itinerary_created(event, self.repository)
                    except InvalidItineraryCreatedEvent as exc:
                        logger.warning("Rejected malformed itinerary event: %s", exc)
