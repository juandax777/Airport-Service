import asyncio
import json
import os

import aio_pika
from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

engine=create_engine(os.getenv("DATABASE_URL","sqlite:///./notifications.db"))
class Base(DeclarativeBase): pass
class Notification(Base):
    __tablename__="notifications"
    event_id: Mapped[str]=mapped_column(String,primary_key=True)
    itinerary_id: Mapped[str]=mapped_column(String)
    status: Mapped[str]=mapped_column(String)
def handler(event: dict):
    with Session(engine) as session:
        if session.get(Notification,event["event_id"]): return
        session.add(Notification(event_id=event["event_id"], itinerary_id=event["data"]["id"], status="simulated_sent")); session.commit()
async def run():
    Base.metadata.create_all(engine)
    connection=await aio_pika.connect_robust(os.getenv("RABBITMQ_URL","amqp://guest:guest@localhost/"))
    channel=await connection.channel(); exchange=await channel.declare_exchange("itineraries",aio_pika.ExchangeType.TOPIC,durable=True); queue=await channel.declare_queue("notifications",durable=True); await queue.bind(exchange,"itinerary.created")
    async with queue.iterator() as messages:
        async for message in messages:
            async with message.process(): handler(json.loads(message.body))
if __name__ == "__main__": asyncio.run(run())
