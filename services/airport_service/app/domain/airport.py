from pydantic import BaseModel, ConfigDict


class Airport(BaseModel):
    """Airport shape exposed by Airport Service."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
