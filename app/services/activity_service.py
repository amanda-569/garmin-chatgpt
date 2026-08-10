from __future__ import annotations

from datetime import date
from typing import cast

from app.models import ActivitySummary
from app.providers.activity_base import (
    ActivityProvider,
)
from app.services.run_service import (
    provider as shared_provider,
)

activity_provider = cast(
    ActivityProvider,
    shared_provider,
)


def list_activities(
    start_date: date,
    end_date: date,
    activity_type: str | None = None,
) -> list[ActivitySummary]:
    if end_date < start_date:
        raise ValueError("end_date cannot be before start_date.")

    return activity_provider.list_activities(
        start_date=start_date,
        end_date=end_date,
        activity_type=activity_type,
    )
