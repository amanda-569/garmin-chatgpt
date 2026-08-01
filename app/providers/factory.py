from app.config import settings
from app.providers.base import RunProvider
from app.providers.garmin_provider import GarminRunProvider
from app.providers.mock_provider import MockRunProvider


def create_run_provider() -> RunProvider:
    if settings.run_provider == "mock":
        return MockRunProvider()

    if settings.run_provider == "garmin":
        return GarminRunProvider()

    raise ValueError(f"Unsupported run provider: {settings.run_provider}")
