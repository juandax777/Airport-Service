from typing import Protocol

from ..domain.entities import Notification


class NotificationRepository(Protocol):
    def get_by_event_id(self, event_id: str) -> Notification | None: ...

    def save(self, notification: Notification) -> None: ...
