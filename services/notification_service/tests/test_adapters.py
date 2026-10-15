import json

import aio_pika
import pytest
from sqlalchemy import create_engine

from services.notification_service.app.domain.entities import Notification
from services.notification_service.app.infrastructure import rabbitmq_consumer
from services.notification_service.app.infrastructure.persistence import (
    SqlAlchemyNotificationRepository,
)
from services.notification_service.app.infrastructure.rabbitmq_consumer import (
    RabbitMqNotificationConsumer,
)


def test_sqlite_notification_repository_persists_and_reads_notification() -> None:
    repository = SqlAlchemyNotificationRepository(create_engine("sqlite://"))
    repository.initialize()
    notification = Notification(
        event_id="event-1",
        itinerary_id="itinerary-1",
        status="simulated_sent",
    )

    assert repository.get_by_event_id(notification.event_id) is None

    repository.save(notification)

    assert repository.get_by_event_id(notification.event_id) == notification


class FakeMessageProcess:
    def __init__(self, message) -> None:
        self.message = message

    async def __aenter__(self):
        return self.message

    async def __aexit__(self, exc_type, *_):
        if exc_type:
            self.message.rejected = True
        else:
            self.message.acked = True
        return False


class FakeMessage:
    def __init__(self, body: bytes) -> None:
        self.body = body
        self.acked = False
        self.rejected = False

    def process(self):
        return FakeMessageProcess(self)


class FakeMessageStream:
    def __init__(self, messages: list[FakeMessage]) -> None:
        self.messages = iter(messages)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.messages)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeQueue:
    def __init__(self, stream: FakeMessageStream) -> None:
        self.stream = stream
        self.binding = None

    async def bind(self, exchange, routing_key: str) -> None:
        self.binding = (exchange, routing_key)

    def iterator(self) -> FakeMessageStream:
        return self.stream


class FakeExchange:
    pass


class FakeChannel:
    def __init__(self, queue: FakeQueue) -> None:
        self.queue = queue
        self.exchange = FakeExchange()
        self.exchange_declaration = None
        self.queue_declaration = None

    async def declare_exchange(self, name, exchange_type, *, durable: bool):
        self.exchange_declaration = (name, exchange_type, durable)
        return self.exchange

    async def declare_queue(self, name: str, *, durable: bool):
        self.queue_declaration = (name, durable)
        return self.queue


class FakeConnection:
    def __init__(self, channel: FakeChannel) -> None:
        self.channel_instance = channel
        self.closed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        self.closed = True
        return False

    async def channel(self):
        return self.channel_instance


@pytest.mark.asyncio
async def test_rabbitmq_consumer_handles_canonical_and_legacy_events_and_rejects_bad_ones(
    monkeypatch, caplog
) -> None:
    messages = [
        FakeMessage(
            json.dumps(
                {"event_id": "event-1", "data": {"itinerary_id": "canonical-1"}}
            ).encode()
        ),
        FakeMessage(
            json.dumps({"event_id": "event-2", "data": {"id": "legacy-2"}}).encode()
        ),
        FakeMessage(b"not-json"),
        FakeMessage(json.dumps({"event_id": "event-4", "data": {}}).encode()),
    ]
    queue = FakeQueue(FakeMessageStream(messages))
    channel = FakeChannel(queue)
    connection = FakeConnection(channel)
    requested_urls = []

    async def connect_robust(url: str):
        requested_urls.append(url)
        return connection

    monkeypatch.setattr(rabbitmq_consumer.aio_pika, "connect_robust", connect_robust)
    repository = SqlAlchemyNotificationRepository(create_engine("sqlite://"))
    repository.initialize()

    await RabbitMqNotificationConsumer("amqp://broker.test/", repository).run()

    assert requested_urls == ["amqp://broker.test/"]
    assert channel.exchange_declaration == (
        "itineraries",
        aio_pika.ExchangeType.TOPIC,
        True,
    )
    assert channel.queue_declaration == ("notifications", True)
    assert queue.binding == (channel.exchange, "itinerary.created")
    assert repository.get_by_event_id("event-1").itinerary_id == "canonical-1"
    assert repository.get_by_event_id("event-2").itinerary_id == "legacy-2"
    assert [message.acked for message in messages] == [True, True, False, False]
    assert [message.rejected for message in messages] == [False, False, True, True]
    assert "Rejected malformed itinerary event" in caplog.text
    assert connection.closed
