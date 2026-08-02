from typing import Literal
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    run_provider: Literal["mock", "garmin"] = "mock"
    garmin_token_directory: Path = Path(".secrets/garmin")
    garmin_lookback_days: int = 30
    garmin_temperature_unit: Literal[
        "fahrenheit",
        "celsius",
    ] = "fahrenheit"
    connector_api_key: SecretStr
    garmin_token_storage: Literal[
        "local",
        "vercel_blob",
    ] = "local"

    garmin_token_blob_path: str = "garmin_tokens.json"

    blob_store_id: str | None = None
    blob_read_write_token: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
