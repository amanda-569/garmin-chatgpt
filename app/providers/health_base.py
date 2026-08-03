from __future__ import annotations

from datetime import date
from typing import Protocol

from app.models import CycleDay, RecoveryDay


class HealthProvider(Protocol):
    def get_recovery_day(
        self,
        target_date: date,
    ) -> RecoveryDay: ...

    def get_cycle_day(
        self,
        target_date: date,
    ) -> CycleDay: ...
