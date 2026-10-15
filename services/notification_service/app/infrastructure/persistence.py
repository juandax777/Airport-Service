from sqlalchemy import String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from ..domain.entities import Notification


class Base(DeclarativeBase):
    pass


class NotificationRow(Base):
    __tablename__ = "notifications"

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    itinerary_id: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)


class SqlAlchemyNotificationRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def initialize(self) -> None:
        Base.metadata.create_all(self.engine)

    def get_by_event_id(self, event_id: str) -> Notification | None:
        with Session(self.engine) as session:
            row = session.get(NotificationRow, event_id)
            if row is None:
                return None
            return Notification(
                event_id=row.event_id,
                itinerary_id=row.itinerary_id,
                status=row.status,
            )

    def save(self, notification: Notification) -> None:
        with Session(self.engine) as session:
            session.add(
                NotificationRow(
                    event_id=notification.event_id,
                    itinerary_id=notification.itinerary_id,
                    status=notification.status,
                )
            )
            session.commit()


def create_engine_from_url(database_url: str) -> Engine:
    return create_engine(database_url)
