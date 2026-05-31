from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """12-factor config. Env vars are prefixed PINPOINT_ (e.g. PINPOINT_DATABASE_URL)."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="PINPOINT_", extra="ignore")

    database_url: str = "postgresql://pinpoint:pinpoint@localhost:55432/pinpoint"
    env_name: str = "dev"


settings = Settings()
