from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models import ActivitySummary


def map_garmin_activity_to_summary(
    raw_activity: dict[str, Any],
) -> ActivitySummary:
    activity_type = raw_activity.get(
        "activityType",
        {},
    )

    type_key = (
        activity_type.get("typeKey") or activity_type.get("typeKeyLocal") or "unknown"
    )

    started_at_text = raw_activity.get("startTimeLocal") or raw_activity.get(
        "startTimeGMT"
    )

    if not started_at_text:
        raise ValueError("Garmin activity has no start time.")

    started_at = datetime.fromisoformat(started_at_text)

    return ActivitySummary(
        activity_id=int(raw_activity["activityId"]),
        activity_type=type_key,
        name=(raw_activity.get("activityName") or type_key),
        started_at=started_at,
        distance_meters=(raw_activity.get("distance")),
        duration_seconds=(raw_activity.get("duration")),
        average_heart_rate=(raw_activity.get("averageHR")),
        maximum_heart_rate=(raw_activity.get("maxHR")),
        elevation_gain_meters=(raw_activity.get("elevationGain")),
    )
