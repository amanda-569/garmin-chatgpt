from __future__ import annotations

from datetime import date
from typing import Protocol

from app.models import ActivitySummary


class ActivityProvider(Protocol):
    def list_activities(
        self,
        start_date: date,
        end_date: date,
        activity_type: str | None = None,
    ) -> list[ActivitySummary]: ...
