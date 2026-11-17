"""Consume Amazon MQ batches using the existing notification use case."""

import base64
import hashlib
import json
import logging
import os
from functools import lru_cache

import boto3
from sqlalchemy import text

from .application.exceptions import InvalidItineraryCreatedEvent
from .application.use_cases import handle_itinerary_created
from .infrastructure.persistence import (
    SqlAlchemyNotificationRepository,
    create_engine_from_url,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@lru_cache(maxsize=1)
def repository() -> SqlAlchemyNotificationRepository:
    secret = boto3.client("secretsmanager").get_secret_value(
        SecretId=os.environ["DATABASE_SECRET_ARN"]
    )
    return SqlAlchemyNotificationRepository(create_engine_from_url(secret["SecretString"]))


def quarantine(repo: SqlAlchemyNotificationRepository, record: dict) -> None:
    envelope = json.dumps(record, sort_keys=True)
    digest = hashlib.sha256(envelope.encode()).hexdigest()
    with repo.engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO notification_quarantine (message_hash, envelope) "
                "VALUES (:digest, :envelope) ON CONFLICT (message_hash) DO NOTHING"
            ),
            {"digest": digest, "envelope": envelope},
        )
    logger.warning("notification_quarantined")


def decode(record: dict) -> object:
    try:
        payload = json.loads(base64.b64decode(record["data"], validate=True))
    except (KeyError, TypeError, ValueError):
        raise InvalidItineraryCreatedEvent("Invalid RabbitMQ message data") from None

    if isinstance(payload, dict):
        if payload.get("event_type", "ItineraryCreatedEvent") != "ItineraryCreatedEvent":
            raise InvalidItineraryCreatedEvent("Unexpected event type")
        if payload.get("version", "1.0") != "1.0":
            raise InvalidItineraryCreatedEvent("Unsupported event version")
    return payload


def handler(event: dict, _context: object) -> None:
    queues = event["rmqMessagesByQueue"]
    if not isinstance(queues, dict) or not queues:
        raise ValueError("Expected an Amazon MQ RabbitMQ batch")

    repo = repository()
    for records in queues.values():
        if not isinstance(records, list):
            raise TypeError("Expected an Amazon MQ message list")
        for record in records:
            if not isinstance(record, dict):
                raise TypeError("Expected an Amazon MQ record")
            try:
                handle_itinerary_created(decode(record), repo)
            except InvalidItineraryCreatedEvent:
                quarantine(repo, record)
