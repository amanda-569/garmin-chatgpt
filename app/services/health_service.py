from __future__ import annotations

from datetime import date, datetime
from typing import cast
from zoneinfo import ZoneInfo

from app.config import settings
from app.models import CycleDay, RecoveryDay
from app.providers.health_base import HealthProvider
from app.services.run_service import (
    provider as shared_provider,
)

# Reuse the existing authenticated Garmin provider.
#
# This avoids:
# - a second Garmin login
# - a second Blob-token download
# - duplicate token-refresh handling
health_provider = cast(
    HealthProvider,
    shared_provider,
)


def get_local_date() -> date:
    timezone = ZoneInfo(settings.user_timezone)

    return datetime.now(timezone).date()


def get_recovery_day(
    target_date: date,
) -> RecoveryDay:
    return health_provider.get_recovery_day(target_date)


def get_latest_recovery() -> RecoveryDay:
    return get_recovery_day(get_local_date())


def get_cycle_day(
    target_date: date,
) -> CycleDay:
    return health_provider.get_cycle_day(target_date)


def get_latest_cycle_day() -> CycleDay:
    return get_cycle_day(get_local_date())
