from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_colombia_base_url: str = "https://api-colombia.com/api/v1"
    request_timeout_seconds: float = 5.0


settings = Settings()
