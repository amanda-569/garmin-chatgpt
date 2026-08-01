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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
