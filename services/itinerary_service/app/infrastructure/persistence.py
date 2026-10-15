from datetime import date

from sqlalchemy import Date, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from ..domain.entities import Itinerary


class Base(DeclarativeBase):
    pass


class ItineraryRow(Base):
    __tablename__ = "itineraries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_name: Mapped[str] = mapped_column(String)
    departure_airport_id: Mapped[str] = mapped_column(String)
    arrival_airport_id: Mapped[str] = mapped_column(String)
    travel_date: Mapped[date] = mapped_column(Date)
    duration_minutes: Mapped[int] = mapped_column(Integer)


def _to_entity(row: ItineraryRow) -> Itinerary:
    return Itinerary(
        id=row.id,
        user_name=row.user_name,
        departure_airport_id=row.departure_airport_id,
        arrival_airport_id=row.arrival_airport_id,
        travel_date=row.travel_date,
        duration_minutes=row.duration_minutes,
    )


class SqlAlchemyItineraryRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def initialize(self) -> None:
        Base.metadata.create_all(self.engine)

    def save(self, itinerary: Itinerary) -> Itinerary:
        with Session(self.engine) as session:
            row = session.get(ItineraryRow, itinerary.id)
            if row is None:
                row = ItineraryRow(id=itinerary.id)
                session.add(row)
            row.user_name = itinerary.user_name
            row.departure_airport_id = itinerary.departure_airport_id
            row.arrival_airport_id = itinerary.arrival_airport_id
            row.travel_date = itinerary.travel_date
            row.duration_minutes = itinerary.duration_minutes
            session.commit()
            session.refresh(row)
            return _to_entity(row)

    def list_all(self) -> list[Itinerary]:
        with Session(self.engine) as session:
            return [_to_entity(row) for row in session.query(ItineraryRow).all()]

    def get_by_id(self, itinerary_id: str) -> Itinerary | None:
        with Session(self.engine) as session:
            row = session.get(ItineraryRow, itinerary_id)
            return _to_entity(row) if row else None

    def delete(self, itinerary: Itinerary) -> None:
        with Session(self.engine) as session:
            row = session.get(ItineraryRow, itinerary.id)
            if row is not None:
                session.delete(row)
                session.commit()


def create_engine_from_url(database_url: str) -> Engine:
    return create_engine(database_url)
