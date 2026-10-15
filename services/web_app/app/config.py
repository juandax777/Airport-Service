from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    airport_service_url: str = "http://127.0.0.1:8001"
    itinerary_service_url: str = "http://127.0.0.1:8002"


settings = Settings()
