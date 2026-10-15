import asyncio
import os

from .application.use_cases import handle_itinerary_created
from .infrastructure.persistence import (
    SqlAlchemyNotificationRepository,
    create_engine_from_url,
)
from .infrastructure.rabbitmq_consumer import RabbitMqNotificationConsumer

database_url = os.getenv("DATABASE_URL", "sqlite:///./notifications.db")
rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
repository = SqlAlchemyNotificationRepository(create_engine_from_url(database_url))


def handler(event: dict) -> None:
    """Compatibility entry point for handling a decoded event."""
    handle_itinerary_created(event, repository)


async def run() -> None:
    repository.initialize()
    await RabbitMqNotificationConsumer(rabbitmq_url, repository).run()


if __name__ == "__main__":
    asyncio.run(run())
